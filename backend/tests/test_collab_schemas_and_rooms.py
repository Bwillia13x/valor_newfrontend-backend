import json
import time
from typing import Any, Dict, List

import pytest

from backend.collab.schemas import Envelope, PresenceUpdate, LWWOp, OpSubmit, SnapshotRequest, make_envelope
from backend.collab.rooms import CollabRoomManager, RoomState, room_manager


class TestSchemas:
    def test_envelope_valid(self):
        env = Envelope(type="join_room", tenant="t1", doc_id="d1", user_id="u1")
        assert env.type == "join_room"
        assert env.version == 1
        assert env.tenant == "t1"
        assert env.doc_id == "d1"
        assert env.user_id == "u1"

    def test_presence_update_defaults(self):
        p = PresenceUpdate()
        assert p.status == "active"
        assert p.cursor is None

    def test_lwwop_and_submit_valid(self):
        op = LWWOp(path="inputs.wacc", type="set", value=9.5, ts=int(time.time() * 1000))
        sub = OpSubmit(baseVersion=0, ops=[op])
        assert sub.baseVersion == 0
        assert len(sub.ops) == 1
        assert sub.ops[0].path == "inputs.wacc"

    def test_make_envelope_helper(self):
        payload = {"baseVersion": 0, "ops": []}
        body = make_envelope("op_submit", "tenantA", "docX", "user42", payload, request_id="req-1")
        assert body["type"] == "op_submit"
        assert body["tenant"] == "tenantA"
        assert body["doc_id"] == "docX"
        assert body["user_id"] == "user42"
        assert body["request_id"] == "req-1"
        assert "payload" in body
        assert body["payload"]["baseVersion"] == 0


class TestRoomsLWW:
    def new_manager(self, monkeypatch) -> CollabRoomManager:
        # Use a fresh manager with a fake redis client
        mgr = CollabRoomManager()
        class FakeRedis:
            def __init__(self):
                self.store = {}
                self.published = []

            def set(self, key, val):
                self.store[key] = val

            def get(self, key):
                return self.store.get(key)

            def publish(self, ch, payload):
                self.published.append((ch, payload))
                return 1

        monkeypatch.setattr(mgr, "_redis", FakeRedis(), raising=False)
        # Reduce snapshot interval for tests
        monkeypatch.setattr(mgr, "_snapshot_interval", 2, raising=False)
        return mgr

    def test_join_leave(self, monkeypatch):
        mgr = self.new_manager(monkeypatch)
        room = mgr.join("t1", "d1", "u1")
        assert "u1" in room.members
        mgr.leave("t1", "d1", "u1")
        assert "u1" not in room.members

    def test_apply_ops_lww_set(self, monkeypatch):
        mgr = self.new_manager(monkeypatch)
        mgr.join("t1", "d1", "u1")
        t1 = int(time.time() * 1000)
        op1 = {"path": "inputs.wacc", "type": "set", "value": 9.0, "ts": t1}
        v1 = mgr.apply_ops("t1", "d1", "u1", base_version=0, ops=[op1])
        snap = mgr.current_snapshot("t1", "d1")
        assert v1 == 1
        assert snap["baseVersion"] == 1
        assert snap["state"]["inputs.wacc"] == 9.0

        # later timestamp should win
        t2 = t1 + 10
        op2 = {"path": "inputs.wacc", "type": "set", "value": 8.5, "ts": t2}
        v2 = mgr.apply_ops("t1", "d1", "u1", base_version=v1, ops=[op2])
        snap2 = mgr.current_snapshot("t1", "d1")
        assert v2 == 2
        assert snap2["state"]["inputs.wacc"] == 8.5

    def test_apply_ops_lww_tie_breaker_userid(self, monkeypatch):
        mgr = self.new_manager(monkeypatch)
        # same ts, larger user_id lexicographically should win
        ts = int(time.time() * 1000)
        mgr.join("t1", "d1", "u1")
        mgr.apply_ops("t1", "d1", "u1", 0, [{"path": "inputs.ebit", "type": "set", "value": 20, "ts": ts}])
        mgr.join("t1", "d1", "u9")
        mgr.apply_ops("t1", "d1", "u9", 1, [{"path": "inputs.ebit", "type": "set", "value": 25, "ts": ts}])
        snap = mgr.current_snapshot("t1", "d1")
        # u9 should win because "u9" > "u1"
        assert snap["state"]["inputs.ebit"] == 25

    def test_append_note(self, monkeypatch):
        mgr = self.new_manager(monkeypatch)
        mgr.join("t1", "d1", "u1")
        ts = int(time.time() * 1000)
        note = {"path": "notes", "type": "append_note", "value": {"text": "hello"}, "ts": ts}
        v = mgr.apply_ops("t1", "d1", "u1", 0, [note])
        snap = mgr.current_snapshot("t1", "d1")
        assert v == 1
        assert len(snap["notes"]) == 1
        assert snap["notes"][0]["text"] == "hello"

    def test_snapshot_persistence_interval(self, monkeypatch):
        mgr = self.new_manager(monkeypatch)
        mgr.join("t1", "d1", "u1")
        op = {"path": "inputs.rev", "type": "set", "value": 100, "ts": int(time.time() * 1000)}
        mgr.apply_ops("t1", "d1", "u1", 0, [op])
        mgr.apply_ops("t1", "d1", "u1", 1, [op])
        # With interval=2, snapshot should be saved now
        key = f"{getattr(mgr, '_channel_prefix')}:" + f"snapshot:t1:d1"
        raw = mgr._redis.get(key)
        assert raw is not None
        data = json.loads(raw)
        assert data["base_version"] == 2
        assert "lww_state" in data
