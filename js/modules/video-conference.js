/**
 * Video Conference Module - Real-time Collaboration
 * Enables video/audio communication for collaborative financial modeling
 */

class VideoConference {
    constructor() {
        this.localStream = null;
        this.remoteStreams = new Map();
        this.peerConnections = new Map();
        this.localVideo = null;
        this.remoteVideos = new Map();
        this.isInitialized = false;
        this.isMuted = false;
        this.isVideoOff = false;
        this.roomId = null;
        this.userId = null;
        this.userName = null;
        
        // WebRTC configuration
        this.rtcConfig = {
            iceServers: [
                { urls: 'stun:stun.l.google.com:19302' },
                { urls: 'stun:stun1.l.google.com:19302' }
            ]
        };
        
        // Signal server connection
        this.signalSocket = null;
        this.signalServerUrl = null;
    }

    /**
     * Initialize video conference
     */
    async init(userId, userName, roomId, signalServerUrl = null) {
        try {
            this.userId = userId;
            this.userName = userName;
            this.roomId = roomId;
            this.signalServerUrl = signalServerUrl || this.getDefaultSignalServerUrl();
            
            // Check WebRTC support
            if (!this.checkWebRTCSupport()) {
                throw new Error('WebRTC not supported');
            }
            
            // Connect to signal server
            await this.connectToSignalServer();
            
            // Get user media
            await this.getUserMedia();
            
            // Create local video element
            this.createLocalVideo();
            
            this.isInitialized = true;
            console.log('[VideoConference] Initialized successfully');
            
            // Join room
            this.joinRoom();
            
        } catch (error) {
            console.error('[VideoConference] Initialization failed:', error);
            throw error;
        }
    }

    /**
     * Check WebRTC support
     */
    checkWebRTCSupport() {
        return !!(navigator.mediaDevices && 
                 navigator.mediaDevices.getUserMedia && 
                 window.RTCPeerConnection);
    }

    /**
     * Get default signal server URL
     */
    getDefaultSignalServerUrl() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        return `${protocol}//${window.location.host}/ws/video`;
    }

    /**
     * Connect to signal server
     */
    async connectToSignalServer() {
        return new Promise((resolve, reject) => {
            try {
                this.signalSocket = new WebSocket(this.signalServerUrl);
                
                this.signalSocket.onopen = () => {
                    console.log('[VideoConference] Connected to signal server');
                    resolve();
                };
                
                this.signalSocket.onmessage = (event) => {
                    this.handleSignalMessage(JSON.parse(event.data));
                };
                
                this.signalSocket.onerror = (error) => {
                    console.error('[VideoConference] Signal server error:', error);
                    reject(error);
                };
                
                this.signalSocket.onclose = () => {
                    console.log('[VideoConference] Disconnected from signal server');
                    this.reconnectToSignalServer();
                };
                
            } catch (error) {
                reject(error);
            }
        });
    }

    /**
     * Reconnect to signal server
     */
    async reconnectToSignalServer() {
        if (this.isInitialized) {
            console.log('[VideoConference] Attempting to reconnect...');
            setTimeout(async () => {
                try {
                    await this.connectToSignalServer();
                    this.joinRoom();
                } catch (error) {
                    console.error('[VideoConference] Reconnection failed:', error);
                }
            }, 3000);
        }
    }

    /**
     * Get user media (camera and microphone)
     */
    async getUserMedia() {
        try {
            this.localStream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 640 },
                    height: { ideal: 480 },
                    facingMode: 'user'
                },
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });
            
            console.log('[VideoConference] Got user media');
        } catch (error) {
            console.error('[VideoConference] Failed to get user media:', error);
            throw error;
        }
    }

    /**
     * Create local video element
     */
    createLocalVideo() {
        this.localVideo = document.createElement('video');
        this.localVideo.autoplay = true;
        this.localVideo.muted = true;
        this.localVideo.playsInline = true;
        this.localVideo.style.width = '100%';
        this.localVideo.style.height = '100%';
        this.localVideo.style.objectFit = 'cover';
        this.localVideo.style.borderRadius = '8px';
        
        if (this.localStream) {
            this.localVideo.srcObject = this.localStream;
        }
    }

    /**
     * Join video conference room
     */
    joinRoom() {
        if (!this.signalSocket || this.signalSocket.readyState !== WebSocket.OPEN) {
            console.warn('[VideoConference] Signal server not connected');
            return;
        }
        
        this.sendSignal({
            type: 'join_room',
            roomId: this.roomId,
            userId: this.userId,
            userName: this.userName
        });
        
        console.log(`[VideoConference] Joined room: ${this.roomId}`);
    }

    /**
     * Leave video conference room
     */
    leaveRoom() {
        if (this.signalSocket && this.signalSocket.readyState === WebSocket.OPEN) {
            this.sendSignal({
                type: 'leave_room',
                roomId: this.roomId,
                userId: this.userId
            });
        }
        
        // Close peer connections
        this.peerConnections.forEach(connection => {
            connection.close();
        });
        this.peerConnections.clear();
        
        // Stop local stream
        if (this.localStream) {
            this.localStream.getTracks().forEach(track => track.stop());
        }
        
        console.log(`[VideoConference] Left room: ${this.roomId}`);
    }

    /**
     * Handle signal server messages
     */
    handleSignalMessage(message) {
        switch (message.type) {
            case 'user_joined':
                this.onUserJoined(message);
                break;
            case 'user_left':
                this.onUserLeft(message);
                break;
            case 'offer':
                this.handleOffer(message);
                break;
            case 'answer':
                this.handleAnswer(message);
                break;
            case 'ice_candidate':
                this.handleIceCandidate(message);
                break;
            case 'room_users':
                this.onRoomUsers(message);
                break;
            default:
                console.warn('[VideoConference] Unknown signal message:', message.type);
        }
    }

    /**
     * Handle user joining
     */
    async onUserJoined(message) {
        if (message.userId === this.userId) {
            return; // Ignore our own join
        }
        
        console.log(`[VideoConference] User joined: ${message.userName}`);
        
        // Create peer connection
        const peerConnection = new RTCPeerConnection(this.rtcConfig);
        this.peerConnections.set(message.userId, peerConnection);
        
        // Add local stream
        if (this.localStream) {
            this.localStream.getTracks().forEach(track => {
                peerConnection.addTrack(track, this.localStream);
            });
        }
        
        // Handle remote stream
        peerConnection.ontrack = (event) => {
            this.handleRemoteStream(message.userId, event.streams[0]);
        };
        
        // Handle ICE candidates
        peerConnection.onicecandidate = (event) => {
            if (event.candidate) {
                this.sendSignal({
                    type: 'ice_candidate',
                    roomId: this.roomId,
                    fromUserId: this.userId,
                    toUserId: message.userId,
                    candidate: event.candidate
                });
            }
        };
        
        // Create and send offer
        try {
            const offer = await peerConnection.createOffer();
            await peerConnection.setLocalDescription(offer);
            
            this.sendSignal({
                type: 'offer',
                roomId: this.roomId,
                fromUserId: this.userId,
                toUserId: message.userId,
                offer: offer
            });
        } catch (error) {
            console.error('[VideoConference] Failed to create offer:', error);
        }
    }

    /**
     * Handle user leaving
     */
    onUserLeft(message) {
        if (message.userId === this.userId) {
            return; // Ignore our own leave
        }
        
        console.log(`[VideoConference] User left: ${message.userName}`);
        
        // Close peer connection
        const peerConnection = this.peerConnections.get(message.userId);
        if (peerConnection) {
            peerConnection.close();
            this.peerConnections.delete(message.userId);
        }
        
        // Remove remote video
        this.removeRemoteVideo(message.userId);
    }

    /**
     * Handle offer from another user
     */
    async handleOffer(message) {
        const peerConnection = this.peerConnections.get(message.fromUserId);
        if (!peerConnection) {
            console.warn('[VideoConference] No peer connection for offer');
            return;
        }
        
        try {
            await peerConnection.setRemoteDescription(message.offer);
            
            const answer = await peerConnection.createAnswer();
            await peerConnection.setLocalDescription(answer);
            
            this.sendSignal({
                type: 'answer',
                roomId: this.roomId,
                fromUserId: this.userId,
                toUserId: message.fromUserId,
                answer: answer
            });
        } catch (error) {
            console.error('[VideoConference] Failed to handle offer:', error);
        }
    }

    /**
     * Handle answer from another user
     */
    async handleAnswer(message) {
        const peerConnection = this.peerConnections.get(message.fromUserId);
        if (!peerConnection) {
            console.warn('[VideoConference] No peer connection for answer');
            return;
        }
        
        try {
            await peerConnection.setRemoteDescription(message.answer);
        } catch (error) {
            console.error('[VideoConference] Failed to handle answer:', error);
        }
    }

    /**
     * Handle ICE candidate
     */
    async handleIceCandidate(message) {
        const peerConnection = this.peerConnections.get(message.fromUserId);
        if (!peerConnection) {
            console.warn('[VideoConference] No peer connection for ICE candidate');
            return;
        }
        
        try {
            await peerConnection.addIceCandidate(message.candidate);
        } catch (error) {
            console.error('[VideoConference] Failed to add ICE candidate:', error);
        }
    }

    /**
     * Handle room users list
     */
    onRoomUsers(message) {
        console.log(`[VideoConference] Room users: ${message.users.length}`);
        // Could be used to show participant list
    }

    /**
     * Handle remote stream
     */
    handleRemoteStream(userId, stream) {
        // Create remote video element
        const remoteVideo = document.createElement('video');
        remoteVideo.autoplay = true;
        remoteVideo.playsInline = true;
        remoteVideo.style.width = '100%';
        remoteVideo.style.height = '100%';
        remoteVideo.style.objectFit = 'cover';
        remoteVideo.style.borderRadius = '8px';
        remoteVideo.srcObject = stream;
        
        this.remoteVideos.set(userId, remoteVideo);
        
        // Add to container if provided
        const container = document.getElementById('video-conference-container');
        if (container) {
            container.appendChild(remoteVideo);
        }
        
        console.log(`[VideoConference] Added remote video for user: ${userId}`);
    }

    /**
     * Remove remote video
     */
    removeRemoteVideo(userId) {
        const remoteVideo = this.remoteVideos.get(userId);
        if (remoteVideo && remoteVideo.parentElement) {
            remoteVideo.parentElement.removeChild(remoteVideo);
        }
        this.remoteVideos.delete(userId);
    }

    /**
     * Send signal message
     */
    sendSignal(message) {
        if (this.signalSocket && this.signalSocket.readyState === WebSocket.OPEN) {
            this.signalSocket.send(JSON.stringify(message));
        } else {
            console.warn('[VideoConference] Signal server not connected');
        }
    }

    /**
     * Toggle microphone
     */
    toggleMute() {
        if (!this.localStream) return;
        
        const audioTrack = this.localStream.getAudioTracks()[0];
        if (audioTrack) {
            audioTrack.enabled = !audioTrack.enabled;
            this.isMuted = !audioTrack.enabled;
            console.log(`[VideoConference] Microphone ${this.isMuted ? 'muted' : 'unmuted'}`);
        }
    }

    /**
     * Toggle video
     */
    toggleVideo() {
        if (!this.localStream) return;
        
        const videoTrack = this.localStream.getVideoTracks()[0];
        if (videoTrack) {
            videoTrack.enabled = !videoTrack.enabled;
            this.isVideoOff = !videoTrack.enabled;
            console.log(`[VideoConference] Video ${this.isVideoOff ? 'off' : 'on'}`);
        }
    }

    /**
     * Switch camera
     */
    async switchCamera() {
        if (!this.localStream) return;
        
        try {
            // Stop current video track
            const currentVideoTrack = this.localStream.getVideoTracks()[0];
            if (currentVideoTrack) {
                currentVideoTrack.stop();
            }
            
            // Get new video track with different facing mode
            const newStream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 640 },
                    height: { ideal: 480 },
                    facingMode: currentVideoTrack?.getSettings().facingMode === 'user' ? 'environment' : 'user'
                }
            });
            
            const newVideoTrack = newStream.getVideoTracks()[0];
            
            // Replace video track in local stream
            this.localStream.removeTrack(currentVideoTrack);
            this.localStream.addTrack(newVideoTrack);
            
            // Update local video
            if (this.localVideo) {
                this.localVideo.srcObject = this.localStream;
            }
            
            // Update peer connections
            this.peerConnections.forEach(peerConnection => {
                const sender = peerConnection.getSenders().find(s => s.track?.kind === 'video');
                if (sender) {
                    sender.replaceTrack(newVideoTrack);
                }
            });
            
            console.log('[VideoConference] Camera switched');
        } catch (error) {
            console.error('[VideoConference] Failed to switch camera:', error);
        }
    }

    /**
     * Get local video element
     */
    getLocalVideo() {
        return this.localVideo;
    }

    /**
     * Get remote video elements
     */
    getRemoteVideos() {
        return Array.from(this.remoteVideos.values());
    }

    /**
     * Get participant count
     */
    getParticipantCount() {
        return this.remoteVideos.size + 1; // +1 for local user
    }

    /**
     * Get connection status
     */
    getConnectionStatus() {
        const status = {
            isInitialized: this.isInitialized,
            isConnected: this.signalSocket?.readyState === WebSocket.OPEN,
            isMuted: this.isMuted,
            isVideoOff: this.isVideoOff,
            participantCount: this.getParticipantCount(),
            peerConnections: this.peerConnections.size
        };
        
        return status;
    }

    /**
     * Destroy video conference
     */
    destroy() {
        this.leaveRoom();
        
        if (this.signalSocket) {
            this.signalSocket.close();
            this.signalSocket = null;
        }
        
        if (this.localStream) {
            this.localStream.getTracks().forEach(track => track.stop());
            this.localStream = null;
        }
        
        this.peerConnections.clear();
        this.remoteVideos.clear();
        this.isInitialized = false;
        
        console.log('[VideoConference] Destroyed');
    }
}

// Export for use in other modules
window.VideoConference = VideoConference;