from __future__ import annotations

import json
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Deque, Dict, List, Optional, Set, Tuple

import redis

from backend.settings import settings
from backend.logging import logger


@dataclass
class NoteEntry:
    ts: int
    user_id: str
    text: str


@dataclass
class RoomState:
    tenant: str
    doc_id: str
    base_version: int = 0
    lww_state: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # path -> {"value": Any, "ts": int, "user_id": str}
    notes: List[NoteEntry] = field(default_factory=list)
    op_log: Deque[Dict[str, Any]] = field(default_factory=lambda: deque(maxlen=1000))
    members: Set[str] = field(default_factory=set)
    ops_since_snapshot: int = 0


class CollabRoomManager:
    """
    In-memory room manager with Redis Pub/Sub fanout and snapshotting.
    LWW semantics for parameter map; append-only list for notes.
    Snapshots persisted in Redis hash: { state, notes, base_version } per (tenant, doc_id).
    """

    def __init__(self) -> None:
        self._rooms: Dict[Tuple[str, str], RoomState] = {}
        self._redis = redis.from_url(settings.REDIS_URL)
        self._channel_prefix = getattr(settings, "COLLAB_REDIS_CHANNEL_PREFIX", "collab")
        self._snapshot_interval = int(getattr(settings, "COLLAB_SNAPSHOT_INTERVAL", 50))

    def _room_key(self, tenant: str, doc_id: str) -> Tuple[str, str]:
        return (tenant, doc_id)

    def _channel(self, tenant: str, doc_id: str) -> str:
        return f"{self._channel_prefix}:{tenant}:{doc_id}"

    def get_room(self, tenant: str, doc_id: str) -> RoomState:
        key = self._room_key(tenant, doc_id)
        if key not in self._rooms:
            # hydrate from snapshot if exists
            state = self.load_snapshot(tenant, doc_id)
            if state is None:
                state = RoomState(tenant=tenant, doc_id=doc_id)
            self._rooms[key] = state
        return self._rooms[key]

    def join(self, tenant: str, doc_id: str, user_id: str) -> RoomState:
        room = self.get_room(tenant, doc_id)
        room.members.add(user_id)
        logger.info("ws_join_room", tenant=tenant, doc_id=doc_id, user_id=user_id, members=len(room.members))
        return room

    def leave(self, tenant: str, doc_id: str, user_id: str) -> None:
        room = self.get_room(tenant, doc_id)
        if user_id in room.members:
            room.members.remove(user_id)
        logger.info("ws_leave_room", tenant=tenant, doc_id=doc_id, user_id=user_id, members=len(room.members))

    def apply_ops(self, tenant: str, doc_id: str, user_id: str, base_version: int, ops: List[Dict[str, Any]]) -> int:
        """
        Apply a list of LWW/append_note ops. Returns new opVersion (base_version after apply).
        If client's base_version is stale or ahead, we still apply but server is source of truth.
        """
        room = self.get_room(tenant, doc_id)

        for op in ops:
            op_type = op.get("type")
            path = op.get("path")
            ts = int(op.get("ts") or int(time.time() * 1000))
            if op_type == "set":
                prev = room.lww_state.get(path)
                if prev is None or ts > int(prev.get("ts", 0)) or (
                    ts == int(prev.get("ts", 0)) and user_id > str(prev.get("user_id", ""))
                ):
                    room.lww_state[path] = {"value": op.get("value"), "ts": ts, "user_id": user_id}
            elif op_type == "append_note":
                val = op.get("value") or {}
                text = str(val.get("text", ""))
                room.notes.append(NoteEntry(ts=ts, user_id=user_id, text=text))
            else:
                logger.warn("ws_unknown_op_type", tenant=tenant, doc_id=doc_id, user_id=user_id, op_type=op_type)

            room.op_log.append({"user_id": user_id, "op": op, "applied_at": int(time.time() * 1000)})

        room.base_version += 1
        room.ops_since_snapshot += 1

        # snapshot if interval reached
        if room.ops_since_snapshot >= self._snapshot_interval:
            try:
                self.save_snapshot(room)
                room.ops_since_snapshot = 0
                logger.info("ws_snapshot_saved", tenant=tenant, doc_id=doc_id, base_version=room.base_version)
            except Exception as e:
                logger.error("ws_snapshot_error", tenant=tenant, doc_id=doc_id, error=str(e))

        # publish to Redis for cross-worker broadcast
        payload = {
            "tenant": tenant,
            "doc_id": doc_id,
            "user_id": user_id,
            "opVersion": room.base_version,
            "ops": ops,
        }
        try:
            self._redis.publish(self._channel(tenant, doc_id), json.dumps(payload))
        except Exception as e:
            logger.error("ws_pubsub_publish_error", tenant=tenant, doc_id=doc_id, error=str(e))

        return room.base_version

    def current_snapshot(self, tenant: str, doc_id: str) -> Dict[str, Any]:
        room = self.get_room(tenant, doc_id)
        # materialize state map
        state = {k: v.get("value") for k, v in room.lww_state.items()}
        notes = [{"ts": n.ts, "user_id": n.user_id, "text": n.text} for n in room.notes]
        return {"baseVersion": room.base_version, "state": state, "notes": notes}

    # Snapshot persistence (Redis)
    def _snapshot_key(self, tenant: str, doc_id: str) -> str:
        return f"{self._channel_prefix}:snapshot:{tenant}:{doc_id}"

    def save_snapshot(self, room: RoomState) -> None:
        key = self._snapshot_key(room.tenant, room.doc_id)
        doc = {
            "base_version": room.base_version,
            "lww_state": room.lww_state,
            "notes": [{"ts": n.ts, "user_id": n.user_id, "text": n.text} for n in room.notes],
        }
        self._redis.set(key, json.dumps(doc))

    def load_snapshot(self, tenant: str, doc_id: str) -> Optional[RoomState]:
        key = self._snapshot_key(tenant, doc_id)
        raw = self._redis.get(key)
        if not raw:
            return None
        try:
            doc = json.loads(raw)
            room = RoomState(tenant=tenant, doc_id=doc_id)
            room.base_version = int(doc.get("base_version", 0))
            room.lww_state = doc.get("lww_state", {})
            room.notes = [NoteEntry(**n) for n in doc.get("notes", [])]
            room.ops_since_snapshot = 0
            return room
        except Exception as e:
            logger.error("ws_snapshot_load_error", tenant=tenant, doc_id=doc_id, error=str(e))
            return None


# Singleton
room_manager = CollabRoomManager()
