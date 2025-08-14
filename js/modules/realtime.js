/**
 * Real-time WebSocket Client Module
 * Handles real-time collaboration, live updates, and progress tracking
 */

import { showNotification } from './auth.js';

class RealtimeManager {
    constructor() {
        this.socket = null;
        this.isConnected = false;
        this.currentRoom = null;
        this.currentUser = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.eventHandlers = new Map();
        this.typingTimeout = null;
        this.isTyping = false;
    }

    init() {
        this.connect();
        this.setupEventHandlers();
    }

    connect() {
        try {
            // Connect to WebSocket server
            this.socket = io('http://localhost:5002', {
                transports: ['websocket', 'polling'],
                timeout: 20000,
                reconnection: true,
                reconnectionAttempts: this.maxReconnectAttempts,
                reconnectionDelay: this.reconnectDelay
            });

            this.setupSocketHandlers();
            console.log('WebSocket connection initiated');
        } catch (error) {
            console.error('Failed to connect to WebSocket server:', error);
            this.scheduleReconnect();
        }
    }

    setupSocketHandlers() {
        if (!this.socket) return;

        this.socket.on('connect', () => {
            console.log('Connected to WebSocket server');
            this.isConnected = true;
            this.reconnectAttempts = 0;
            this.emit('connection_status', { status: 'connected' });
            
            // Show connection notification
            showNotification('Connected to real-time server', 'success');
        });

        this.socket.on('disconnect', () => {
            console.log('Disconnected from WebSocket server');
            this.isConnected = false;
            this.currentRoom = null;
            this.emit('connection_status', { status: 'disconnected' });
            
            // Show disconnection notification
            showNotification('Disconnected from real-time server', 'warning');
        });

        this.socket.on('connected', (data) => {
            console.log('WebSocket connection confirmed:', data);
            this.isConnected = true;
        });

        this.socket.on('user_joined', (data) => {
            console.log('User joined:', data);
            this.emit('user_joined', data);
            this.updateUserList();
            
            // Show notification
            showNotification(`${data.username} joined the session`, 'info');
        });

        this.socket.on('user_left', (data) => {
            console.log('User left:', data);
            this.emit('user_left', data);
            this.updateUserList();
            
            // Show notification
            showNotification(`${data.username} left the session`, 'info');
        });

        this.socket.on('room_info', (data) => {
            console.log('Room info received:', data);
            this.currentRoom = data.room;
            this.emit('room_info', data);
            this.updateUserList();
        });

        this.socket.on('collaboration_started', (data) => {
            console.log('Collaboration started:', data);
            this.emit('collaboration_started', data);
            
            // Show notification
            showNotification(`Collaboration started for ${data.document_type} document`, 'success');
        });

        this.socket.on('document_updated', (data) => {
            console.log('Document updated:', data);
            this.emit('document_updated', data);
            
            // Show typing indicator
            this.showTypingIndicator(data.username, true);
            
            // Hide typing indicator after delay
            setTimeout(() => {
                this.showTypingIndicator(data.username, false);
            }, 3000);
        });

        this.socket.on('user_typing', (data) => {
            console.log('User typing:', data);
            this.showTypingIndicator(data.username, data.is_typing);
        });

        this.socket.on('progress_update', (data) => {
            console.log('Progress update:', data);
            this.emit('progress_update', data);
            this.updateProgressBar(data);
        });

        this.socket.on('notification', (data) => {
            console.log('Notification received:', data);
            showNotification(data.message, data.type || 'info');
        });

        this.socket.on('error', (data) => {
            console.error('WebSocket error:', data);
            showNotification(`WebSocket error: ${data.message}`, 'error');
        });

        this.socket.on('connect_error', (error) => {
            console.error('WebSocket connection error:', error);
            this.isConnected = false;
            this.scheduleReconnect();
        });
    }

    setupEventHandlers() {
        // Handle page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.emit('user_activity', { status: 'inactive' });
            } else {
                this.emit('user_activity', { status: 'active' });
            }
        });

        // Handle beforeunload
        window.addEventListener('beforeunload', () => {
            if (this.currentRoom) {
                this.leaveRoom(this.currentRoom);
            }
        });
    }

    scheduleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
            
            console.log(`Scheduling reconnect attempt ${this.reconnectAttempts} in ${delay}ms`);
            
            setTimeout(() => {
                if (!this.isConnected) {
                    this.connect();
                }
            }, delay);
        } else {
            console.error('Max reconnection attempts reached');
            showNotification('Failed to reconnect to real-time server', 'error');
        }
    }

    setUserInfo(userId, username) {
        this.currentUser = { userId, username };
    }

    joinRoom(room, userId = null, username = null) {
        if (!this.isConnected || !this.socket) {
            console.error('Cannot join room: not connected');
            return false;
        }

        const userData = {
            room: room,
            user_id: userId || this.currentUser?.userId || 'anonymous',
            username: username || this.currentUser?.username || 'Anonymous User'
        };

        this.socket.emit('join_room', userData);
        this.currentRoom = room;
        
        console.log(`Joining room: ${room}`);
        return true;
    }

    leaveRoom(room, userId = null) {
        if (!this.isConnected || !this.socket) {
            console.error('Cannot leave room: not connected');
            return false;
        }

        const userData = {
            room: room,
            user_id: userId || this.currentUser?.userId || 'anonymous',
            username: this.currentUser?.username || 'Anonymous User'
        };

        this.socket.emit('leave_room', userData);
        
        if (this.currentRoom === room) {
            this.currentRoom = null;
        }
        
        console.log(`Leaving room: ${room}`);
        return true;
    }

    startCollaboration(documentType, documentId, userId = null, username = null) {
        if (!this.isConnected || !this.socket || !this.currentRoom) {
            console.error('Cannot start collaboration: not connected or no room');
            return false;
        }

        const collaborationData = {
            document_type: documentType,
            document_id: documentId,
            room: this.currentRoom,
            user_id: userId || this.currentUser?.userId || 'anonymous',
            username: username || this.currentUser?.username || 'Anonymous User'
        };

        this.socket.emit('start_collaboration', collaborationData);
        
        console.log(`Starting collaboration for ${documentType} document ${documentId}`);
        return true;
    }

    updateDocument(room, updates, userId = null) {
        if (!this.isConnected || !this.socket) {
            console.error('Cannot update document: not connected');
            return false;
        }

        const updateData = {
            room: room,
            updates: updates,
            user_id: userId || this.currentUser?.userId || 'anonymous',
            username: this.currentUser?.username || 'Anonymous User'
        };

        this.socket.emit('update_document', updateData);
        return true;
    }

    setTypingStatus(room, isTyping, userId = null) {
        if (!this.isConnected || !this.socket) {
            return false;
        }

        // Clear existing timeout
        if (this.typingTimeout) {
            clearTimeout(this.typingTimeout);
        }

        // Set typing status
        if (isTyping && !this.isTyping) {
            this.isTyping = true;
            this.socket.emit('user_typing', {
                room: room,
                is_typing: true,
                user_id: userId || this.currentUser?.userId || 'anonymous',
                username: this.currentUser?.username || 'Anonymous User'
            });
        }

        // Set timeout to stop typing indicator
        if (isTyping) {
            this.typingTimeout = setTimeout(() => {
                this.isTyping = false;
                this.socket.emit('user_typing', {
                    room: room,
                    is_typing: false,
                    user_id: userId || this.currentUser?.userId || 'anonymous',
                    username: this.currentUser?.username || 'Anonymous User'
                });
            }, 3000);
        }

        return true;
    }

    sendProgressUpdate(room, operationId, progress, status) {
        if (!this.isConnected || !this.socket) {
            return false;
        }

        this.socket.emit('progress_update', {
            room: room,
            operation_id: operationId,
            progress: progress,
            status: status,
            message: `${status}: ${Math.round(progress * 100)}%`
        });

        return true;
    }

    on(event, handler) {
        if (!this.eventHandlers.has(event)) {
            this.eventHandlers.set(event, []);
        }
        this.eventHandlers.get(event).push(handler);
    }

    off(event, handler) {
        if (this.eventHandlers.has(event)) {
            const handlers = this.eventHandlers.get(event);
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
    }

    emit(event, data) {
        if (this.eventHandlers.has(event)) {
            this.eventHandlers.get(event).forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    console.error(`Error in event handler for ${event}:`, error);
                }
            });
        }
    }

    handleConnectionStatus(data) {
        // Update UI to show connection status
        const statusIndicator = document.getElementById('connection-status');
        if (statusIndicator) {
            statusIndicator.textContent = data.status === 'connected' ? '🟢 Connected' : '🔴 Disconnected';
            statusIndicator.className = data.status === 'connected' ? 'status-connected' : 'status-disconnected';
        }
    }

    handleUserJoined(data) {
        // Update user list UI
        this.updateUserList();
    }

    handleUserLeft(data) {
        // Update user list UI
        this.updateUserList();
    }

    handleDocumentUpdate(data) {
        // Apply document updates to the UI
        if (data.updates) {
            // Example: Update form fields
            Object.keys(data.updates).forEach(key => {
                const element = document.getElementById(key);
                if (element && element.value !== data.updates[key]) {
                    element.value = data.updates[key];
                    // Trigger change event
                    element.dispatchEvent(new Event('change', { bubbles: true }));
                }
            });
        }
    }

    handleProgressUpdate(data) {
        // Update progress bar
        this.updateProgressBar(data);
    }

    showTypingIndicator(username, isTyping) {
        // Show/hide typing indicator in UI
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            if (isTyping) {
                typingIndicator.textContent = `${username} is typing...`;
                typingIndicator.style.display = 'block';
            } else {
                typingIndicator.style.display = 'none';
            }
        }
    }

    updateProgressBar(data) {
        // Update progress bar UI
        const progressBar = document.getElementById('progress-bar');
        const progressText = document.getElementById('progress-text');
        
        if (progressBar) {
            progressBar.style.width = `${data.progress * 100}%`;
            progressBar.setAttribute('aria-valuenow', data.progress * 100);
        }
        
        if (progressText) {
            progressText.textContent = `${data.message || ''} ${Math.round(data.progress * 100)}%`;
        }
    }

    updateUserList() {
        // Update user list in UI
        const userList = document.getElementById('user-list');
        if (userList && this.currentRoom) {
            // This would typically fetch the current user list from the server
            // For now, we'll just show a placeholder
            userList.innerHTML = '<li>Loading users...</li>';
        }
    }

    isConnected() {
        return this.isConnected;
    }

    getRooms() {
        return this.currentRoom ? [this.currentRoom] : [];
    }

    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
        }
        this.isConnected = false;
        this.currentRoom = null;
        this.currentUser = null;
    }
}

// Create singleton instance
const realtimeManager = new RealtimeManager();

// Export functions for external use
export function initRealtime() {
    realtimeManager.init();
}

export function joinCollaborationRoom(documentType, documentId, userId, username) {
    const room = `collab_${documentType}_${documentId}`;
    realtimeManager.joinRoom(room, userId, username);
    realtimeManager.startCollaboration(documentType, documentId, userId, username);
}

export function leaveCollaborationRoom(room) {
    realtimeManager.leaveRoom(room);
}

export function updateDocumentRealtime(room, updates) {
    realtimeManager.updateDocument(room, updates);
}

export function setTypingStatus(room, isTyping) {
    realtimeManager.setTypingStatus(room, isTyping);
}

export function sendProgressUpdate(room, operationId, progress, status) {
    realtimeManager.sendProgressUpdate(room, operationId, progress, status);
}

export function onRealtimeEvent(event, handler) {
    realtimeManager.on(event, handler);
}

export function offRealtimeEvent(event, handler) {
    realtimeManager.off(event, handler);
}

export function isRealtimeConnected() {
    return realtimeManager.isConnected();
}

export function getRealtimeRooms() {
    return realtimeManager.getRooms();
}

// Initialize real-time features when module is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Set up connection status handler
    realtimeManager.on('connection_status', realtimeManager.handleConnectionStatus.bind(realtimeManager));
    
    // Set up other event handlers
    realtimeManager.on('user_joined', realtimeManager.handleUserJoined.bind(realtimeManager));
    realtimeManager.on('user_left', realtimeManager.handleUserLeft.bind(realtimeManager));
    realtimeManager.on('document_updated', realtimeManager.handleDocumentUpdate.bind(realtimeManager));
    realtimeManager.on('progress_update', realtimeManager.handleProgressUpdate.bind(realtimeManager));
    
    // Initialize real-time manager
    realtimeManager.init();
});

export default realtimeManager; 