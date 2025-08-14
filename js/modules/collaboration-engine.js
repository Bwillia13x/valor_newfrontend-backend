/**
 * Collaboration Engine - Real-time Multi-user Financial Modeling
 * Handles WebSocket communication, presence tracking, and conflict resolution
 */

class CollaborationEngine {
    constructor() {
        this.socket = null;
        this.roomId = null;
        this.userId = null;
        this.userName = null;
        this.isConnected = false;
        this.presenceUsers = new Map();
        this.collaborationCallbacks = new Map();
        this.operationalTransform = new OperationalTransform();
        
        // Bind methods
        this.connect = this.connect.bind(this);
        this.disconnect = this.disconnect.bind(this);
        this.joinRoom = this.joinRoom.bind(this);
        this.leaveRoom = this.leaveRoom.bind(this);
        this.sendUpdate = this.sendUpdate.bind(this);
        this.onUserJoin = this.onUserJoin.bind(this);
        this.onUserLeave = this.onUserLeave.bind(this);
        this.onDataUpdate = this.onDataUpdate.bind(this);
        this.onCursorUpdate = this.onCursorUpdate.bind(this);
        this.onCommentUpdate = this.onCommentUpdate.bind(this);
    }

    /**
     * Initialize collaboration with user details
     */
    init(userId, userName, roomId = null) {
        this.userId = userId;
        this.userName = userName;
        this.roomId = roomId || this.generateRoomId();
        
        console.log(`[Collaboration] Initialized for user: ${userName} (${userId}) in room: ${this.roomId}`);
        
        // Auto-connect if room is provided
        if (roomId) {
            this.connect();
        }
    }

    /**
     * Connect to WebSocket server
     */
    connect() {
        if (this.isConnected) {
            console.log('[Collaboration] Already connected');
            return;
        }

        try {
            // Connect to WebSocket server (backend will handle the upgrade)
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/collaboration`;
            
            this.socket = new WebSocket(wsUrl);
            
            this.socket.onopen = () => {
                this.isConnected = true;
                console.log('[Collaboration] Connected to server');
                this.emit('connected');
                
                // Join room if we have one
                if (this.roomId) {
                    this.joinRoom(this.roomId);
                }
            };
            
            this.socket.onmessage = (event) => {
                this.handleMessage(JSON.parse(event.data));
            };
            
            this.socket.onclose = () => {
                this.isConnected = false;
                console.log('[Collaboration] Disconnected from server');
                this.emit('disconnected');
                
                // Attempt to reconnect after 5 seconds
                setTimeout(() => {
                    if (!this.isConnected) {
                        this.connect();
                    }
                }, 5000);
            };
            
            this.socket.onerror = (error) => {
                console.error('[Collaboration] WebSocket error:', error);
                this.emit('error', error);
            };
            
        } catch (error) {
            console.error('[Collaboration] Failed to connect:', error);
            this.emit('error', error);
        }
    }

    /**
     * Disconnect from WebSocket server
     */
    disconnect() {
        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }
        this.isConnected = false;
        this.presenceUsers.clear();
        console.log('[Collaboration] Disconnected');
    }

    /**
     * Join a collaboration room
     */
    joinRoom(roomId) {
        if (!this.isConnected) {
            console.warn('[Collaboration] Not connected, cannot join room');
            return;
        }
        
        this.roomId = roomId;
        this.send({
            type: 'join_room',
            roomId: roomId,
            userId: this.userId,
            userName: this.userName
        });
        
        console.log(`[Collaboration] Joined room: ${roomId}`);
    }

    /**
     * Leave current room
     */
    leaveRoom() {
        if (this.roomId) {
            this.send({
                type: 'leave_room',
                roomId: this.roomId,
                userId: this.userId
            });
            this.roomId = null;
            console.log('[Collaboration] Left room');
        }
    }

    /**
     * Send data update to other users
     */
    sendUpdate(dataType, data, version) {
        if (!this.isConnected || !this.roomId) {
            return;
        }
        
        const update = {
            type: 'data_update',
            roomId: this.roomId,
            userId: this.userId,
            userName: this.userName,
            dataType: dataType,
            data: data,
            version: version,
            timestamp: Date.now()
        };
        
        this.send(update);
    }

    /**
     * Send cursor position update
     */
    sendCursorUpdate(position) {
        if (!this.isConnected || !this.roomId) {
            return;
        }
        
        this.send({
            type: 'cursor_update',
            roomId: this.roomId,
            userId: this.userId,
            userName: this.userName,
            position: position,
            timestamp: Date.now()
        });
    }

    /**
     * Send comment/annotation update
     */
    sendCommentUpdate(comment) {
        if (!this.isConnected || !this.roomId) {
            return;
        }
        
        this.send({
            type: 'comment_update',
            roomId: this.roomId,
            userId: this.userId,
            userName: this.userName,
            comment: comment,
            timestamp: Date.now()
        });
    }

    /**
     * Handle incoming WebSocket messages
     */
    handleMessage(message) {
        switch (message.type) {
            case 'user_joined':
                this.onUserJoin(message);
                break;
            case 'user_left':
                this.onUserLeave(message);
                break;
            case 'data_update':
                this.onDataUpdate(message);
                break;
            case 'cursor_update':
                this.onCursorUpdate(message);
                break;
            case 'comment_update':
                this.onCommentUpdate(message);
                break;
            case 'presence_update':
                this.onPresenceUpdate(message);
                break;
            case 'error':
                console.error('[Collaboration] Server error:', message.error);
                this.emit('error', message.error);
                break;
            default:
                console.warn('[Collaboration] Unknown message type:', message.type);
        }
    }

    /**
     * Handle user joining the room
     */
    onUserJoin(message) {
        const user = {
            id: message.userId,
            name: message.userName,
            joinedAt: message.timestamp
        };
        
        this.presenceUsers.set(user.id, user);
        console.log(`[Collaboration] User joined: ${user.name}`);
        this.emit('userJoined', user);
    }

    /**
     * Handle user leaving the room
     */
    onUserLeave(message) {
        const user = this.presenceUsers.get(message.userId);
        if (user) {
            this.presenceUsers.delete(message.userId);
            console.log(`[Collaboration] User left: ${user.name}`);
            this.emit('userLeft', user);
        }
    }

    /**
     * Handle data updates from other users
     */
    onDataUpdate(message) {
        if (message.userId === this.userId) {
            return; // Ignore our own updates
        }
        
        console.log(`[Collaboration] Data update from ${message.userName}:`, message.dataType);
        
        // Apply operational transformation for conflict resolution
        const transformedData = this.operationalTransform.apply(message.data, message.version);
        
        this.emit('dataUpdate', {
            userId: message.userId,
            userName: message.userName,
            dataType: message.dataType,
            data: transformedData,
            version: message.version,
            timestamp: message.timestamp
        });
    }

    /**
     * Handle cursor updates from other users
     */
    onCursorUpdate(message) {
        if (message.userId === this.userId) {
            return; // Ignore our own updates
        }
        
        this.emit('cursorUpdate', {
            userId: message.userId,
            userName: message.userName,
            position: message.position,
            timestamp: message.timestamp
        });
    }

    /**
     * Handle comment updates from other users
     */
    onCommentUpdate(message) {
        if (message.userId === this.userId) {
            return; // Ignore our own updates
        }
        
        this.emit('commentUpdate', {
            userId: message.userId,
            userName: message.userName,
            comment: message.comment,
            timestamp: message.timestamp
        });
    }

    /**
     * Handle presence updates
     */
    onPresenceUpdate(message) {
        this.presenceUsers.clear();
        message.users.forEach(user => {
            this.presenceUsers.set(user.id, user);
        });
        
        this.emit('presenceUpdate', Array.from(this.presenceUsers.values()));
    }

    /**
     * Send message to WebSocket server
     */
    send(message) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify(message));
        } else {
            console.warn('[Collaboration] Cannot send message - not connected');
        }
    }

    /**
     * Register event listeners
     */
    on(event, callback) {
        if (!this.collaborationCallbacks.has(event)) {
            this.collaborationCallbacks.set(event, []);
        }
        this.collaborationCallbacks.get(event).push(callback);
    }

    /**
     * Emit events to registered listeners
     */
    emit(event, data) {
        const callbacks = this.collaborationCallbacks.get(event);
        if (callbacks) {
            callbacks.forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`[Collaboration] Error in ${event} callback:`, error);
                }
            });
        }
    }

    /**
     * Get current presence users
     */
    getPresenceUsers() {
        return Array.from(this.presenceUsers.values());
    }

    /**
     * Generate unique room ID
     */
    generateRoomId() {
        return 'room_' + Math.random().toString(36).substr(2, 9);
    }

    /**
     * Get connection status
     */
    getStatus() {
        return {
            connected: this.isConnected,
            roomId: this.roomId,
            userId: this.userId,
            userName: this.userName,
            presenceCount: this.presenceUsers.size
        };
    }
}

/**
 * Operational Transform for Conflict Resolution
 * Handles concurrent editing conflicts using operational transformation
 */
class OperationalTransform {
    constructor() {
        this.version = 0;
        this.pendingOperations = [];
    }

    /**
     * Apply operational transformation to resolve conflicts
     */
    apply(data, version) {
        // Simple version-based conflict resolution
        // In a production system, this would implement full operational transformation
        if (version > this.version) {
            this.version = version;
            return data;
        }
        
        // Merge changes if versions are compatible
        return this.mergeChanges(data, version);
    }

    /**
     * Merge changes from different versions
     */
    mergeChanges(data, version) {
        // Simple merge strategy - in production, implement proper OT
        return data;
    }

    /**
     * Increment version
     */
    incrementVersion() {
        return ++this.version;
    }
}

// Export for use in other modules
window.CollaborationEngine = CollaborationEngine;