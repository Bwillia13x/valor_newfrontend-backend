"""
WebSocket Manager - Real-time Collaboration Backend
Handles WebSocket connections for collaboration, video conferencing, and presence tracking
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Set, Optional
from dataclasses import dataclass
from flask_socketio import SocketIO, emit, join_room, leave_room, rooms
from flask import request

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class User:
    """User information for presence tracking"""
    id: str
    name: str
    room_id: str
    socket_id: str
    joined_at: datetime
    last_seen: datetime
    is_online: bool = True

class WebSocketManager:
    """Manages WebSocket connections and real-time features"""
    
    def __init__(self, app=None):
        self.app = app
        self.socketio = None
        self.users: Dict[str, User] = {}
        self.rooms: Dict[str, Set[str]] = {}
        self.collaboration_data: Dict[str, Dict] = {}
        # Presence: room_id -> { user_id: { "tenant": str, "last_seen": datetime, "meta": dict } }
        self.presence: Dict[str, Dict[str, Dict]] = {}
        self.presence_ttl_seconds: int = 90  # auto-expire if not seen in this window
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize WebSocket manager with Flask app"""
        self.app = app
        
        # Initialize SocketIO
        self.socketio = SocketIO(
            app,
            cors_allowed_origins="*",
            async_mode='threading'
        )
        
        # Register event handlers
        self.register_handlers()
        
        logger.info("WebSocket Manager initialized")
    
    def register_handlers(self):
        """Register WebSocket event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection"""
            logger.info(f"Client connected: {request.sid}")
            emit('connected', {'status': 'connected', 'sid': request.sid})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            logger.info(f"Client disconnected: {request.sid}")
            self.handle_user_disconnect(request.sid)
        
        @self.socketio.on('join_room')
        def handle_join_room(data):
            """Handle room join request"""
            try:
                room_id = data.get('roomId')
                user_id = data.get('userId')
                user_name = data.get('userName')
                
                if not all([room_id, user_id, user_name]):
                    emit('error', {'message': 'Missing required fields'})
                    return
                
                self.handle_user_join_room(room_id, user_id, user_name, request.sid)
                # Presence update
                tenant = (data.get('tenant') or request.headers.get('X-Tenant-ID') or 'default')
                meta = data.get('meta') or {}
                self._presence_touch(room_id, user_id, tenant, meta)
                emit('presence_state', self.get_presence_state(room_id), room=request.sid)
                emit('presence_update', {'roomId': room_id, 'userId': user_id, 'state': 'join'}, room=room_id, include_self=False)
                
            except Exception as e:
                logger.error(f"Error joining room: {e}")
                emit('error', {'message': 'Failed to join room'})
        
        @self.socketio.on('leave_room')
        def handle_leave_room(data):
            """Handle room leave request"""
            try:
                room_id = data.get('roomId')
                user_id = data.get('userId')
                
                if not all([room_id, user_id]):
                    emit('error', {'message': 'Missing required fields'})
                    return
                
                self.handle_user_leave_room(room_id, user_id, request.sid)
                # Presence update
                self._presence_remove(room_id, user_id)
                emit('presence_update', {'roomId': room_id, 'userId': user_id, 'state': 'leave'}, room=room_id, include_self=False)
                
            except Exception as e:
                logger.error(f"Error leaving room: {e}")
                emit('error', {'message': 'Failed to leave room'})
        
        @self.socketio.on('data_update')
        def handle_data_update(data):
            """Handle data update from client"""
            try:
                room_id = data.get('roomId')
                user_id = data.get('userId')
                user_name = data.get('userName')
                data_type = data.get('dataType')
                update_data = data.get('data')
                version = data.get('version')
                
                if not all([room_id, user_id, data_type, update_data]):
                    emit('error', {'message': 'Missing required fields'})
                    return
                
                self.handle_data_update(room_id, user_id, user_name, data_type, update_data, version)
                
            except Exception as e:
                logger.error(f"Error handling data update: {e}")
                emit('error', {'message': 'Failed to process data update'})
        
        @self.socketio.on('cursor_update')
        def handle_cursor_update(data):
            """Handle cursor position update"""
            try:
                room_id = data.get('roomId')
                user_id = data.get('userId')
                user_name = data.get('userName')
                position = data.get('position')
                
                if not all([room_id, user_id, position]):
                    emit('error', {'message': 'Missing required fields'})
                    return
                
                self.handle_cursor_update(room_id, user_id, user_name, position)
                # Touch presence heartbeat
                tenant = (data.get('tenant') or request.headers.get('X-Tenant-ID') or 'default')
                self._presence_touch(room_id, user_id, tenant, {})
                
            except Exception as e:
                logger.error(f"Error handling cursor update: {e}")
                emit('error', {'message': 'Failed to process cursor update'})
        
        @self.socketio.on('comment_update')
        def handle_comment_update(data):
            """Handle comment/annotation update"""
            try:
                room_id = data.get('roomId')
                user_id = data.get('userId')
                user_name = data.get('userName')
                comment = data.get('comment')
                
                if not all([room_id, user_id, comment]):
                    emit('error', {'message': 'Missing required fields'})
                    return
                
                self.handle_comment_update(room_id, user_id, user_name, comment)
                # Touch presence heartbeat
                tenant = (data.get('tenant') or request.headers.get('X-Tenant-ID') or 'default')
                self._presence_touch(room_id, user_id, tenant, {})
                
            except Exception as e:
                logger.error(f"Error handling comment update: {e}")
                emit('error', {'message': 'Failed to process comment update'})
        
        @self.socketio.on('video_signal')
        def handle_video_signal(data):
            """Handle video conference signaling"""
            try:
                room_id = data.get('roomId')
                from_user_id = data.get('fromUserId')
                to_user_id = data.get('toUserId')
                signal_type = data.get('type')
                signal_data = data.get('data')
                
                if not all([room_id, from_user_id, to_user_id, signal_type]):
                    emit('error', {'message': 'Missing required fields'})
                    return
                
                self.handle_video_signal(room_id, from_user_id, to_user_id, signal_type, signal_data)
                # Touch presence heartbeat
                tenant = (data.get('tenant') or request.headers.get('X-Tenant-ID') or 'default')
                self._presence_touch(room_id, from_user_id, tenant, {})
                
            except Exception as e:
                logger.error(f"Error handling video signal: {e}")
                emit('error', {'message': 'Failed to process video signal'})
    
    def handle_user_join_room(self, room_id: str, user_id: str, user_name: str, socket_id: str):
        """Handle user joining a room"""
        try:
            # Create or update user
            user = User(
                id=user_id,
                name=user_name,
                room_id=room_id,
                socket_id=socket_id,
                joined_at=datetime.now(),
                last_seen=datetime.now()
            )
            self.users[user_id] = user
            
            # Add user to room
            if room_id not in self.rooms:
                self.rooms[room_id] = set()
            self.rooms[room_id].add(user_id)
            
            # Join SocketIO room
            join_room(room_id)
            
            # Notify other users in room
            emit('user_joined', {
                'userId': user_id,
                'userName': user_name,
                'timestamp': datetime.now().isoformat()
            }, room=room_id, include_self=False)
            
            # Send current room users to new user
            room_users = self.get_room_users(room_id)
            emit('room_users', {
                'users': room_users,
                'timestamp': datetime.now().isoformat()
            })
            
            # Send current collaboration data
            if room_id in self.collaboration_data:
                emit('collaboration_data', {
                    'data': self.collaboration_data[room_id],
                    'timestamp': datetime.now().isoformat()
                })
            
            logger.info(f"User {user_name} ({user_id}) joined room {room_id}")
            
        except Exception as e:
            logger.error(f"Error handling user join room: {e}")
            emit('error', {'message': 'Failed to join room'})
    
    def handle_user_leave_room(self, room_id: str, user_id: str, socket_id: str):
        """Handle user leaving a room"""
        try:
            # Get user info
            user = self.users.get(user_id)
            if not user:
                return
            
            # Remove user from room
            if room_id in self.rooms and user_id in self.rooms[room_id]:
                self.rooms[room_id].remove(user_id)
                
                # Remove room if empty
                if not self.rooms[room_id]:
                    del self.rooms[room_id]
            
            # Leave SocketIO room
            leave_room(room_id)
            
            # Notify other users
            emit('user_left', {
                'userId': user_id,
                'userName': user.name,
                'timestamp': datetime.now().isoformat()
            }, room=room_id, include_self=False)
            
            # Mark user as offline
            user.is_online = False
            user.last_seen = datetime.now()
            
            logger.info(f"User {user.name} ({user_id}) left room {room_id}")
            
        except Exception as e:
            logger.error(f"Error handling user leave room: {e}")
    
    def handle_user_disconnect(self, socket_id: str):
        """Handle user disconnection"""
        try:
            # Find user by socket ID
            user = None
            for u in self.users.values():
                if u.socket_id == socket_id:
                    user = u
                    break
            
            if user:
                # Handle leaving room
                self.handle_user_leave_room(user.room_id, user.id, socket_id)
                
                # Remove user
                del self.users[user.id]
                
                logger.info(f"User {user.name} ({user.id}) disconnected")
            
        except Exception as e:
            logger.error(f"Error handling user disconnect: {e}")
    
    def handle_data_update(self, room_id: str, user_id: str, user_name: str, 
                          data_type: str, update_data: dict, version: int = None):
        """Handle data update from client"""
        try:
            # Store collaboration data
            if room_id not in self.collaboration_data:
                self.collaboration_data[room_id] = {}
            
            if data_type not in self.collaboration_data[room_id]:
                self.collaboration_data[room_id][data_type] = {}
            
            # Update data with version control
            if version is not None:
                current_version = self.collaboration_data[room_id][data_type].get('version', 0)
                if version > current_version:
                    self.collaboration_data[room_id][data_type] = {
                        'data': update_data,
                        'version': version,
                        'lastUpdatedBy': user_id,
                        'lastUpdatedAt': datetime.now().isoformat()
                    }
            
            # Broadcast to other users in room
            emit('data_update', {
                'userId': user_id,
                'userName': user_name,
                'dataType': data_type,
                'data': update_data,
                'version': version,
                'timestamp': datetime.now().isoformat()
            }, room=room_id, include_self=False)
            
            logger.info(f"Data update from {user_name} in room {room_id}: {data_type}")
            
        except Exception as e:
            logger.error(f"Error handling data update: {e}")
    
    def handle_cursor_update(self, room_id: str, user_id: str, user_name: str, position: dict):
        """Handle cursor position update"""
        try:
            # Broadcast cursor position to other users
            emit('cursor_update', {
                'userId': user_id,
                'userName': user_name,
                'position': position,
                'timestamp': datetime.now().isoformat()
            }, room=room_id, include_self=False)
            
        except Exception as e:
            logger.error(f"Error handling cursor update: {e}")
    
    def handle_comment_update(self, room_id: str, user_id: str, user_name: str, comment: dict):
        """Handle comment/annotation update"""
        try:
            # Store comment in collaboration data
            if room_id not in self.collaboration_data:
                self.collaboration_data[room_id] = {}
            
            if 'comments' not in self.collaboration_data[room_id]:
                self.collaboration_data[room_id]['comments'] = []
            
            comment_data = {
                'id': comment.get('id'),
                'text': comment.get('text'),
                'position': comment.get('position'),
                'author': user_id,
                'authorName': user_name,
                'timestamp': datetime.now().isoformat()
            }
            
            self.collaboration_data[room_id]['comments'].append(comment_data)
            
            # Broadcast to other users
            emit('comment_update', {
                'userId': user_id,
                'userName': user_name,
                'comment': comment_data,
                'timestamp': datetime.now().isoformat()
            }, room=room_id, include_self=False)
            
            logger.info(f"Comment from {user_name} in room {room_id}")
            
        except Exception as e:
            logger.error(f"Error handling comment update: {e}")
    
    def handle_video_signal(self, room_id: str, from_user_id: str, to_user_id: str, 
                           signal_type: str, signal_data: dict):
        """Handle video conference signaling"""
        try:
            # Forward signal to target user
            target_user = self.users.get(to_user_id)
            if target_user:
                emit('video_signal', {
                    'roomId': room_id,
                    'fromUserId': from_user_id,
                    'toUserId': to_user_id,
                    'type': signal_type,
                    'data': signal_data,
                    'timestamp': datetime.now().isoformat()
                }, room=target_user.socket_id)
            
        except Exception as e:
            logger.error(f"Error handling video signal: {e}")
    
    def get_room_users(self, room_id: str) -> list:
        """Get list of users in a room"""
        users = []
        if room_id in self.rooms:
            for user_id in self.rooms[room_id]:
                user = self.users.get(user_id)
                if user and user.is_online:
                    users.append({
                        'id': user.id,
                        'name': user.name,
                        'joinedAt': user.joined_at.isoformat()
                    })
        return users
    
    def get_user_status(self, user_id: str) -> Optional[dict]:
        """Get user status"""
        user = self.users.get(user_id)
        if user:
            return {
                'id': user.id,
                'name': user.name,
                'roomId': user.room_id,
                'isOnline': user.is_online,
                'joinedAt': user.joined_at.isoformat(),
                'lastSeen': user.last_seen.isoformat()
            }
        return None
    
    def get_room_status(self, room_id: str) -> dict:
        """Get room status"""
        users = self.get_room_users(room_id)
        collaboration_data = self.collaboration_data.get(room_id, {})
        presence = self.get_presence_state(room_id)
        
        return {
            'roomId': room_id,
            'userCount': len(users),
            'users': users,
            'hasCollaborationData': bool(collaboration_data),
            'dataTypes': list(collaboration_data.keys()),
            'presence': presence
        }
    
    def cleanup_inactive_users(self):
        """Clean up inactive users and expire stale presence"""
        current_time = datetime.now()
        inactive_users = []
        
        for user_id, user in self.users.items():
            # Mark as inactive if not seen for 5 minutes
            if (current_time - user.last_seen).total_seconds() > 300:
                inactive_users.append(user_id)
        
        for user_id in inactive_users:
            self.handle_user_disconnect(self.users[user_id].socket_id)
        
        # Expire presence older than TTL
        for room_id, mapping in list(self.presence.items()):
            for uid, info in list(mapping.items()):
                if (current_time - info.get('last_seen', current_time)).total_seconds() > self.presence_ttl_seconds:
                    del mapping[uid]
            if not mapping:
                del self.presence[room_id]
    
    def run(self, host='0.0.0.0', port=5002, debug=False):
        """Run the WebSocket server"""
        if self.socketio:
            self.socketio.run(self.app, host=host, port=port, debug=debug)
        else:
            raise RuntimeError("WebSocket manager not initialized")
    
    # -------------------------
    # Presence helpers
    # -------------------------
    def _presence_touch(self, room_id: str, user_id: str, tenant: str, meta: dict):
        now = datetime.now()
        if room_id not in self.presence:
            self.presence[room_id] = {}
        self.presence[room_id][user_id] = {
            'tenant': tenant,
            'last_seen': now,
            'meta': meta or {}
        }
    
    def _presence_remove(self, room_id: str, user_id: str):
        if room_id in self.presence and user_id in self.presence[room_id]:
            del self.presence[room_id][user_id]
            if not self.presence[room_id]:
                del self.presence[room_id]
    
    def get_presence_state(self, room_id: str) -> dict:
        state = []
        mapping = self.presence.get(room_id, {})
        for uid, info in mapping.items():
            state.append({
                'userId': uid,
                'tenant': info.get('tenant'),
                'lastSeen': info.get('last_seen').isoformat() if info.get('last_seen') else None,
                'meta': info.get('meta', {})
            })
        return {'roomId': room_id, 'users': state, 'count': len(state)}

# Global instance
websocket_manager = WebSocketManager()
