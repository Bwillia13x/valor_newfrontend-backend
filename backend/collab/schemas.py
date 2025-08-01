from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, constr


# Common envelope for all WS messages
class Envelope(BaseModel):
    type: constr(strip_whitespace=True)
    version: int = 1
    tenant: str
    doc_id: str
    user_id: str
    request_id: Optional[str] = None


# Presence
class PresenceUpdate(BaseModel):
    cursor: Optional[Dict[str, Any]] = None
    status: Literal["active", "idle", "offline"] = "active"
    meta: Optional[Dict[str, Any]] = None


# LWW parameter update op and notes append op
class LWWOp(BaseModel):
    # path for parameter map key (e.g., "inputs.wacc" or "notes")
    path: str
    # supported op types: set for parameters; append_note for notes stream
    type: Literal["set", "append_note"]
    value: Any
    # timestamp in ms (client assigned), used for tie-breakers
    ts: int


class OpSubmit(BaseModel):
    baseVersion: int
    ops: List[LWWOp]


class OpAck(BaseModel):
    opVersion: int


class OpBroadcast(BaseModel):
    opVersion: int
    ops: List[LWWOp]
    user_id: str


class JoinRoom(BaseModel):
    pass


class LeaveRoom(BaseModel):
    pass


class SnapshotRequest(BaseModel):
    pass


class SnapshotResponse(BaseModel):
    baseVersion: int
    state: Dict[str, Any]
    notes: List[Dict[str, Any]]


class ErrorMessage(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


# Factory helpers to build envelopes with payloads
def make_envelope(msg_type: str, tenant: str, doc_id: str, user_id: str, payload: Dict[str, Any], request_id: Optional[str] = None, version: int = 1) -> Dict[str, Any]:
    env = Envelope(type=msg_type, version=version, tenant=tenant, doc_id=doc_id, user_id=user_id, request_id=request_id)
    body = env.dict()
    body["payload"] = payload
    return body
