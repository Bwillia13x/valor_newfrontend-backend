/**
 * Valor IVX - Main Application Entry Point
 * Phase 2: Enhanced with Real-time Collaboration, PWA, and Advanced Features
 */

// Global application state
window.ValorIVX = {
    // Core modules
    dcfEngine: null,
    lboEngine: null,
    maEngine: null,
    monteCarlo: null,
    sensitivityAnalysis: null,
    charting: null,
    scenarios: null,
    financialData: null,
    uiHandlers: null,
    backend: null,
    utils: null,
    
    // Phase 2: New modules
    collaborationEngine: null,
    conflictResolver: null,
    advancedCharting: null,
    pwaManager: null,
    videoConference: null,
    
    // Application state
    currentModule: 'dcf',
    currentUser: null,
    collaborationRoom: null,
    isCollaborating: false,
    isOnline: navigator.onLine,
    
    // Initialize application
    async init() {
        try {
            console.log('[ValorIVX] Initializing application...');
            
            // Initialize core modules
            await this.initCoreModules();
            
            // Initialize Phase 2 modules
            await this.initPhase2Modules();
            
            // Set up event listeners
            this.setupEventListeners();
            
            // Initialize UI
            this.initUI();
            
            // Check for collaboration mode
            this.checkCollaborationMode();
            
            console.log('[ValorIVX] Application initialized successfully');
            
        } catch (error) {
            console.error('[ValorIVX] Initialization failed:', error);
            this.showError('Application initialization failed. Please refresh the page.');
        }
    },
    
    /**
     * Initialize core modules
     */
    async initCoreModules() {
        // Initialize utility modules first
        this.utils = new Utils();
        this.backend = new BackendAPI();
        
        // Initialize financial engines
        this.dcfEngine = new DCFEngine();
        this.lboEngine = new LBOEngine();
        this.maEngine = new MAEngine();
        this.monteCarlo = new MonteCarlo();
        this.sensitivityAnalysis = new SensitivityAnalysis();
        
        // Initialize UI and data modules
        this.charting = new Charting();
        this.scenarios = new Scenarios();
        this.financialData = new FinancialData();
        this.uiHandlers = new UIHandlers();
        
        console.log('[ValorIVX] Core modules initialized');
    },
    
    /**
     * Initialize Phase 2 modules
     */
    async initPhase2Modules() {
        // Initialize collaboration engine
        this.collaborationEngine = new CollaborationEngine();
        this.conflictResolver = new ConflictResolver();
        
        // Initialize advanced charting
        this.advancedCharting = new AdvancedCharting();
        
        // Initialize PWA manager
        this.pwaManager = new PWAManager();
        
        // Initialize video conference (optional)
        if (this.checkWebRTCSupport()) {
            this.videoConference = new VideoConference();
        }
        
        console.log('[ValorIVX] Phase 2 modules initialized');
    },
    
    /**
     * Set up event listeners
     */
    setupEventListeners() {
        // Online/offline status
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.onOnline();
        });
        
        window.addEventListener('offline', () => {
            this.isOnline = false;
            this.onOffline();
        });
        
        // Collaboration events
        if (this.collaborationEngine) {
            this.collaborationEngine.on('userJoined', (user) => {
                this.onUserJoined(user);
            });
            
            this.collaborationEngine.on('userLeft', (user) => {
                this.onUserLeft(user);
            });
            
            this.collaborationEngine.on('dataUpdate', (update) => {
                this.onDataUpdate(update);
            });
            
            this.collaborationEngine.on('cursorUpdate', (update) => {
                this.onCursorUpdate(update);
            });
            
            this.collaborationEngine.on('commentUpdate', (update) => {
                this.onCommentUpdate(update);
            });
        }
        
        // PWA events
        if (this.pwaManager) {
            this.pwaManager.on('connected', () => {
                this.onPWAConnected();
            });
            
            this.pwaManager.on('disconnected', () => {
                this.onPWADisconnected();
            });
        }
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            this.handleKeyboardShortcuts(e);
        });
        
        // Touch events for mobile
        this.setupTouchEvents();
        
        console.log('[ValorIVX] Event listeners set up');
    },
    
    /**
     * Initialize UI
     */
    initUI() {
        // Initialize UI handlers
        this.uiHandlers.init();
        
        // Set up mobile-responsive navigation
        this.setupMobileNavigation();
        
        // Initialize collaboration UI
        this.initCollaborationUI();
        
        // Initialize advanced charting UI
        this.initAdvancedChartingUI();
        
        // Initialize PWA UI
        this.initPWAUI();
        
        console.log('[ValorIVX] UI initialized');
    },
    
    /**
     * Set up mobile-responsive navigation
     */
    setupMobileNavigation() {
        const navToggle = document.getElementById('nav-toggle');
        const navMenu = document.getElementById('nav-menu');
        
        if (navToggle && navMenu) {
            navToggle.addEventListener('click', () => {
                navMenu.classList.toggle('active');
            });
        }
        
        // Close nav when clicking outside
        document.addEventListener('click', (e) => {
            if (navMenu && navMenu.classList.contains('active')) {
                if (!navMenu.contains(e.target) && !navToggle.contains(e.target)) {
                    navMenu.classList.remove('active');
                }
            }
        });
    },
    
    /**
     * Initialize collaboration UI
     */
    initCollaborationUI() {
        // Create collaboration status indicator
        const statusIndicator = document.createElement('div');
        statusIndicator.id = 'collaboration-status';
        statusIndicator.className = 'collaboration-status';
        // Create status indicator safely
        const statusDiv = document.createElement('div');
        statusDiv.className = 'status-indicator';
        
        const statusDot = document.createElement('span');
        statusDot.className = 'status-dot';
        
        const statusText = document.createElement('span');
        statusText.className = 'status-text';
        statusText.textContent = 'Offline';
        
        const presenceList = document.createElement('div');
        presenceList.className = 'presence-list';
        
        statusDiv.appendChild(statusDot);
        statusDiv.appendChild(statusText);
        statusIndicator.appendChild(statusDiv);
        statusIndicator.appendChild(presenceList);
        
        document.body.appendChild(statusIndicator);
        
        // Create collaboration controls
        const controls = document.createElement('div');
        controls.id = 'collaboration-controls';
        controls.className = 'collaboration-controls';
        // Create controls safely
        const joinBtn = document.createElement('button');
        joinBtn.id = 'join-room-btn';
        joinBtn.className = 'btn primary';
        joinBtn.textContent = 'Join Room';
        
        const shareBtn = document.createElement('button');
        shareBtn.id = 'share-room-btn';
        shareBtn.className = 'btn';
        shareBtn.style.display = 'none';
        shareBtn.textContent = 'Share Room';
        
        const leaveBtn = document.createElement('button');
        leaveBtn.id = 'leave-room-btn';
        leaveBtn.className = 'btn';
        leaveBtn.style.display = 'none';
        leaveBtn.textContent = 'Leave Room';
        
        controls.appendChild(joinBtn);
        controls.appendChild(shareBtn);
        controls.appendChild(leaveBtn);
        
        document.body.appendChild(controls);
        
        // Set up collaboration button handlers
        this.setupCollaborationHandlers();
    },
    
    /**
     * Set up collaboration button handlers
     */
    setupCollaborationHandlers() {
        const joinBtn = document.getElementById('join-room-btn');
        const shareBtn = document.getElementById('share-room-btn');
        const leaveBtn = document.getElementById('leave-room-btn');
        
        if (joinBtn) {
            joinBtn.addEventListener('click', () => {
                this.showJoinRoomDialog();
            });
        }
        
        if (shareBtn) {
            shareBtn.addEventListener('click', () => {
                this.shareRoom();
            });
        }
        
        if (leaveBtn) {
            leaveBtn.addEventListener('click', () => {
                this.leaveRoom();
            });
        }
    },
    
    /**
     * Initialize advanced charting UI
     */
    initAdvancedChartingUI() {
        // Add chart type selector
        const chartSelector = document.createElement('div');
        chartSelector.className = 'chart-selector';
        // Create chart selector safely
        const select = document.createElement('select');
        select.id = 'chart-type-select';
        
        const options = [
            { value: 'standard', text: 'Standard Charts' },
            { value: 'waterfall', text: 'Waterfall Chart' },
            { value: 'tornado', text: 'Tornado Diagram' },
            { value: 'spider', text: 'Spider Chart' },
            { value: '3d', text: '3D Charts' }
        ];
        
        options.forEach(option => {
            const optionElement = document.createElement('option');
            optionElement.value = option.value;
            optionElement.textContent = option.text;
            select.appendChild(optionElement);
        });
        
        chartSelector.appendChild(select);
        
        // Add to chart container
        const chartContainer = document.querySelector('.charts');
        if (chartContainer) {
            chartContainer.appendChild(chartSelector);
        }
        
        // Set up chart type change handler
        const chartTypeSelect = document.getElementById('chart-type-select');
        if (chartTypeSelect) {
            chartTypeSelect.addEventListener('change', (e) => {
                this.changeChartType(e.target.value);
            });
        }
    },
    
    /**
     * Initialize PWA UI
     */
    initPWAUI() {
        // Add PWA status indicator
        const pwaStatus = document.createElement('div');
        pwaStatus.id = 'pwa-status';
        pwaStatus.className = 'pwa-status';
        // Create PWA status safely
        const pwaIndicator = document.createElement('div');
        pwaIndicator.className = 'pwa-indicator';
        
        const pwaIcon = document.createElement('span');
        pwaIcon.className = 'pwa-icon';
        pwaIcon.textContent = '📱';
        
        const pwaText = document.createElement('span');
        pwaText.className = 'pwa-text';
        pwaText.textContent = 'PWA Ready';
        
        pwaIndicator.appendChild(pwaIcon);
        pwaIndicator.appendChild(pwaText);
        pwaStatus.appendChild(pwaIndicator);
        
        document.body.appendChild(pwaStatus);
        
        // Add offline indicator
        const offlineIndicator = document.createElement('div');
        offlineIndicator.id = 'offline-indicator';
        offlineIndicator.className = 'offline-indicator';
        offlineIndicator.innerHTML = `
            <div class="offline-message">
                <span class="offline-icon">📶</span>
                <span>You're offline. Changes will be synced when online.</span>
            </div>
        `;
        
        document.body.appendChild(offlineIndicator);
        
        // Show/hide offline indicator based on connection status
        this.updateOfflineIndicator();
    },
    
    /**
     * Check for collaboration mode
     */
    checkCollaborationMode() {
        const urlParams = new URLSearchParams(window.location.search);
        const collaboration = urlParams.get('collaboration');
        const roomId = urlParams.get('room');
        const userId = urlParams.get('user');
        const userName = urlParams.get('name');
        
        if (collaboration === 'true' && roomId && userId && userName) {
            this.joinCollaborationRoom(roomId, userId, userName);
        }
    },
    
    /**
     * Join collaboration room
     */
    async joinCollaborationRoom(roomId, userId, userName) {
        try {
            this.currentUser = { id: userId, name: userName };
            this.collaborationRoom = roomId;
            
            // Initialize collaboration engine
            this.collaborationEngine.init(userId, userName, roomId);
            
            // Update UI
            this.updateCollaborationUI(true);
            
            // Show success message
            this.showSuccess(`Joined collaboration room: ${roomId}`);
            
        } catch (error) {
            console.error('[ValorIVX] Failed to join collaboration room:', error);
            this.showError('Failed to join collaboration room');
        }
    },
    
    /**
     * Show join room dialog
     */
    showJoinRoomDialog() {
        const dialog = document.createElement('div');
        dialog.className = 'modal';
        dialog.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2>Join Collaboration Room</h2>
                    <span class="close">&times;</span>
                </div>
                <div class="modal-body">
                    <form id="join-room-form">
                        <div class="form-group">
                            <label for="user-name">Your Name:</label>
                            <input type="text" id="user-name" required>
                        </div>
                        <div class="form-group">
                            <label for="room-id">Room ID:</label>
                            <input type="text" id="room-id" placeholder="Enter room ID or leave empty to create new">
                        </div>
                        <div class="form-actions">
                            <button type="submit" class="btn primary">Join Room</button>
                            <button type="button" class="btn" onclick="this.closest('.modal').remove()">Cancel</button>
                        </div>
                    </form>
                </div>
            </div>
        `;
        
        document.body.appendChild(dialog);
        
        // Handle form submission
        const form = document.getElementById('join-room-form');
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            
            const userName = document.getElementById('user-name').value;
            const roomId = document.getElementById('room-id').value || this.generateRoomId();
            const userId = this.generateUserId();
            
            dialog.remove();
            this.joinCollaborationRoom(roomId, userId, userName);
        });
        
        // Handle close button
        const closeBtn = dialog.querySelector('.close');
        closeBtn.addEventListener('click', () => {
            dialog.remove();
        });
    },
    
    /**
     * Share room
     */
    shareRoom() {
        if (!this.collaborationRoom) return;
        
        const shareUrl = `${window.location.origin}${window.location.pathname}?collaboration=true&room=${this.collaborationRoom}&user=${this.currentUser.id}&name=${encodeURIComponent(this.currentUser.name)}`;
        
        if (navigator.share) {
            navigator.share({
                title: 'Join Valor IVX Collaboration',
                text: 'Join me in this financial modeling session',
                url: shareUrl
            });
        } else {
            // Fallback to clipboard
            navigator.clipboard.writeText(shareUrl).then(() => {
                this.showSuccess('Room link copied to clipboard');
            });
        }
    },
    
    /**
     * Leave room
     */
    leaveRoom() {
        if (this.collaborationEngine) {
            this.collaborationEngine.leaveRoom();
        }
        
        this.isCollaborating = false;
        this.collaborationRoom = null;
        this.currentUser = null;
        
        this.updateCollaborationUI(false);
        this.showSuccess('Left collaboration room');
    },
    
    /**
     * Update collaboration UI
     */
    updateCollaborationUI(isCollaborating) {
        const joinBtn = document.getElementById('join-room-btn');
        const shareBtn = document.getElementById('share-room-btn');
        const leaveBtn = document.getElementById('leave-room-btn');
        const statusIndicator = document.getElementById('collaboration-status');
        
        if (isCollaborating) {
            if (joinBtn) joinBtn.style.display = 'none';
            if (shareBtn) shareBtn.style.display = 'inline-block';
            if (leaveBtn) leaveBtn.style.display = 'inline-block';
            if (statusIndicator) statusIndicator.classList.add('active');
        } else {
            if (joinBtn) joinBtn.style.display = 'inline-block';
            if (shareBtn) shareBtn.style.display = 'none';
            if (leaveBtn) leaveBtn.style.display = 'none';
            if (statusIndicator) statusIndicator.classList.remove('active');
        }
    },
    
    /**
     * Change chart type
     */
    changeChartType(chartType) {
        // This would integrate with the advanced charting module
        console.log('[ValorIVX] Changing chart type to:', chartType);
        
        // Update chart based on type
        switch (chartType) {
            case 'waterfall':
                this.createWaterfallChart();
                break;
            case 'tornado':
                this.createTornadoChart();
                break;
            case 'spider':
                this.createSpiderChart();
                break;
            case '3d':
                this.create3DChart();
                break;
            default:
                this.createStandardChart();
        }
    },
    
    /**
     * Create waterfall chart
     */
    createWaterfallChart() {
        // Example waterfall chart data
        const data = [
            { label: 'Revenue', value: 1000, type: 'base' },
            { label: 'Costs', value: -600, type: 'negative' },
            { label: 'Taxes', value: -100, type: 'negative' },
            { label: 'Net Income', value: 300, type: 'total' }
        ];
        
        this.advancedCharting.createWaterfallChart('chart-container', data, {
            title: 'Financial Waterfall Chart'
        });
    },
    
    /**
     * Create tornado chart
     */
    createTornadoChart() {
        // Example tornado chart data
        const data = [
            { label: 'Revenue Growth', impact: 15.2 },
            { label: 'EBITDA Margin', impact: -8.7 },
            { label: 'Discount Rate', impact: -12.3 },
            { label: 'Terminal Growth', impact: 6.8 }
        ];
        
        this.advancedCharting.createTornadoChart('chart-container', data, {
            title: 'Sensitivity Analysis'
        });
    },
    
    /**
     * Create spider chart
     */
    createSpiderChart() {
        // Example spider chart data
        const data = {
            categories: ['Growth', 'Profitability', 'Efficiency', 'Liquidity', 'Leverage'],
            values: [75, 60, 85, 45, 30]
        };
        
        this.advancedCharting.createSpiderChart('chart-container', data, {
            title: 'Financial Metrics Overview'
        });
    },
    
    /**
     * Create 3D chart
     */
    create3DChart() {
        // Example 3D chart data
        const data = [
            { x: 1, y: 2, z: 3 },
            { x: 2, y: 4, z: 6 },
            { x: 3, y: 6, z: 9 }
        ];
        
        this.advancedCharting.create3DChart('chart-container', data, {
            chartType: '3d_scatter',
            title: '3D Scatter Plot'
        });
    },
    
    /**
     * Create standard chart
     */
    createStandardChart() {
        // Use existing charting module
        this.charting.createChart('chart-container', this.getCurrentData());
    },
    
    /**
     * Get current data for charts
     */
    getCurrentData() {
        // Return current module data
        switch (this.currentModule) {
            case 'dcf':
                return this.dcfEngine.getChartData();
            case 'lbo':
                return this.lboEngine.getChartData();
            case 'ma':
                return this.maEngine.getChartData();
            default:
                return [];
        }
    },
    
    /**
     * Set up touch events for mobile
     */
    setupTouchEvents() {
        // Add touch support for charts
        const charts = document.querySelectorAll('canvas');
        charts.forEach(canvas => {
            canvas.addEventListener('touchstart', (e) => {
                e.preventDefault();
                this.handleTouchStart(e);
            });
            
            canvas.addEventListener('touchmove', (e) => {
                e.preventDefault();
                this.handleTouchMove(e);
            });
            
            canvas.addEventListener('touchend', (e) => {
                e.preventDefault();
                this.handleTouchEnd(e);
            });
        });
    },
    
    /**
     * Handle touch events
     */
    handleTouchStart(e) {
        // Handle touch start for mobile interaction
        console.log('[ValorIVX] Touch start:', e);
    },
    
    handleTouchMove(e) {
        // Handle touch move for mobile interaction
        console.log('[ValorIVX] Touch move:', e);
    },
    
    handleTouchEnd(e) {
        // Handle touch end for mobile interaction
        console.log('[ValorIVX] Touch end:', e);
    },
    
    /**
     * Handle keyboard shortcuts
     */
    handleKeyboardShortcuts(e) {
        // Ctrl/Cmd + S: Save
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
            e.preventDefault();
            this.saveCurrentState();
        }
        
        // Ctrl/Cmd + Z: Undo
        if ((e.ctrlKey || e.metaKey) && e.key === 'z') {
            e.preventDefault();
            this.undo();
        }
        
        // Ctrl/Cmd + Y: Redo
        if ((e.ctrlKey || e.metaKey) && e.key === 'y') {
            e.preventDefault();
            this.redo();
        }
        
        // Ctrl/Cmd + Enter: Run analysis
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            this.runAnalysis();
        }
    },
    
    /**
     * Online event handler
     */
    onOnline() {
        this.isOnline = true;
        this.updateOfflineIndicator();
        
        // Sync offline data
        if (this.pwaManager) {
            this.pwaManager.processSyncQueue();
        }
        
        this.showSuccess('Connection restored');
    },
    
    /**
     * Offline event handler
     */
    onOffline() {
        this.isOnline = false;
        this.updateOfflineIndicator();
        
        this.showWarning('You are now offline. Changes will be saved locally.');
    },
    
    /**
     * Update offline indicator
     */
    updateOfflineIndicator() {
        const indicator = document.getElementById('offline-indicator');
        if (indicator) {
            indicator.style.display = this.isOnline ? 'none' : 'block';
        }
    },
    
    /**
     * User joined collaboration
     */
    onUserJoined(user) {
        this.showSuccess(`${user.name} joined the session`);
        this.updatePresenceList();
    },
    
    /**
     * User left collaboration
     */
    onUserLeft(user) {
        this.showInfo(`${user.name} left the session`);
        this.updatePresenceList();
    },
    
    /**
     * Data update from collaboration
     */
    onDataUpdate(update) {
        console.log('[ValorIVX] Data update from:', update.userName);
        
        // Apply update using conflict resolver
        if (this.conflictResolver) {
            const operation = this.conflictResolver.createOperation(
                update.userId,
                update.dataType,
                update.data,
                'update'
            );
            
            // Apply to current state
            this.applyCollaborationUpdate(operation);
        }
    },
    
    /**
     * Cursor update from collaboration
     */
    onCursorUpdate(update) {
        // Show cursor position from other users
        this.showRemoteCursor(update);
    },
    
    /**
     * Comment update from collaboration
     */
    onCommentUpdate(update) {
        // Add comment to UI
        this.addCollaborationComment(update);
    },
    
    /**
     * PWA connected
     */
    onPWAConnected() {
        console.log('[ValorIVX] PWA connected');
    },
    
    /**
     * PWA disconnected
     */
    onPWADisconnected() {
        console.log('[ValorIVX] PWA disconnected');
    },
    
    /**
     * Check WebRTC support
     */
    checkWebRTCSupport() {
        return !!(navigator.mediaDevices && 
                 navigator.mediaDevices.getUserMedia && 
                 window.RTCPeerConnection);
    },
    
    /**
     * Generate room ID
     */
    generateRoomId() {
        return 'room_' + Math.random().toString(36).substr(2, 9);
    },
    
    /**
     * Generate user ID
     */
    generateUserId() {
        return 'user_' + Math.random().toString(36).substr(2, 9);
    },
    
    /**
     * Update presence list
     */
    updatePresenceList() {
        if (!this.collaborationEngine) return;
        
        const presenceList = document.querySelector('.presence-list');
        if (presenceList) {
            const users = this.collaborationEngine.getPresenceUsers();
            
            // Clear existing content
            presenceList.textContent = '';
            
            // Create user elements safely
            users.forEach(user => {
                const userDiv = document.createElement('div');
                userDiv.className = 'presence-user';
                userDiv.textContent = user.name; // Use textContent to prevent XSS
                presenceList.appendChild(userDiv);
            });
        }
    },
    
    /**
     * Apply collaboration update
     */
    applyCollaborationUpdate(operation) {
        // Apply update to current module
        switch (operation.dataType) {
            case 'dcf_inputs':
                this.dcfEngine.applyUpdate(operation.data);
                break;
            case 'lbo_inputs':
                this.lboEngine.applyUpdate(operation.data);
                break;
            case 'ma_inputs':
                this.maEngine.applyUpdate(operation.data);
                break;
            case 'scenarios':
                this.scenarios.applyUpdate(operation.data);
                break;
        }
        
        // Update UI
        this.uiHandlers.updateUI();
    },
    
    /**
     * Show remote cursor
     */
    showRemoteCursor(update) {
        // Implementation for showing remote cursors
        console.log('[ValorIVX] Remote cursor:', update);
    },
    
    /**
     * Add collaboration comment
     */
    addCollaborationComment(update) {
        // Implementation for adding comments
        console.log('[ValorIVX] Collaboration comment:', update);
    },
    
    /**
     * Save current state
     */
    saveCurrentState() {
        // Save current module state
        switch (this.currentModule) {
            case 'dcf':
                this.dcfEngine.save();
                break;
            case 'lbo':
                this.lboEngine.save();
                break;
            case 'ma':
                this.maEngine.save();
                break;
        }
        
        this.showSuccess('State saved');
    },
    
    /**
     * Undo last action
     */
    undo() {
        // Implementation for undo functionality
        console.log('[ValorIVX] Undo');
    },
    
    /**
     * Redo last action
     */
    redo() {
        // Implementation for redo functionality
        console.log('[ValorIVX] Redo');
    },
    
    /**
     * Run analysis
     */
    runAnalysis() {
        // Run current module analysis
        switch (this.currentModule) {
            case 'dcf':
                this.dcfEngine.runAnalysis();
                break;
            case 'lbo':
                this.lboEngine.runAnalysis();
                break;
            case 'ma':
                this.maEngine.runAnalysis();
                break;
        }
    },
    
    /**
     * Show success message
     */
    showSuccess(message) {
        this.showMessage(message, 'success');
    },
    
    /**
     * Show error message
     */
    showError(message) {
        this.showMessage(message, 'error');
    },
    
    /**
     * Show warning message
     */
    showWarning(message) {
        this.showMessage(message, 'warning');
    },
    
    /**
     * Show info message
     */
    showInfo(message) {
        this.showMessage(message, 'info');
    },
    
    /**
     * Show message
     */
    showMessage(message, type = 'info') {
        const messageEl = document.createElement('div');
        messageEl.className = `message message-${type}`;
        messageEl.textContent = message;
        
        document.body.appendChild(messageEl);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (messageEl.parentElement) {
                messageEl.remove();
            }
        }, 3000);
    }
};

function setupServiceWorkerUpdates() {
  if (!('serviceWorker' in navigator)) return;

  function showUpdatePrompt(registration) {
    // Minimal inline prompt to avoid importing additional modules here
    const prompt = document.createElement('div');
    prompt.className = 'pwa-update-notification';
    // Create update prompt safely
    const content = document.createElement('div');
    content.className = 'pwa-update-content';
    
    const span = document.createElement('span');
    span.textContent = 'Update available';
    
    const buttonDiv = document.createElement('div');
    buttonDiv.style.display = 'flex';
    buttonDiv.style.gap = '8px';
    buttonDiv.style.marginLeft = 'auto';
    
    const updateBtn = document.createElement('button');
    updateBtn.id = 'sw-refresh-now';
    updateBtn.className = 'btn primary';
    updateBtn.style.padding = '6px 10px';
    updateBtn.style.fontSize = '12px';
    updateBtn.textContent = 'Update now';
    
    const dismissBtn = document.createElement('button');
    dismissBtn.id = 'sw-dismiss';
    dismissBtn.className = 'btn';
    dismissBtn.style.padding = '6px 10px';
    dismissBtn.style.fontSize = '12px';
    dismissBtn.textContent = 'Later';
    
    buttonDiv.appendChild(updateBtn);
    buttonDiv.appendChild(dismissBtn);
    content.appendChild(span);
    content.appendChild(buttonDiv);
    prompt.appendChild(content);
    document.body.appendChild(prompt);

    const cleanup = () => prompt.remove();

    prompt.querySelector('#sw-dismiss')?.addEventListener('click', cleanup);
    prompt.querySelector('#sw-refresh-now')?.addEventListener('click', () => {
      cleanup();
      if (registration.waiting) {
        registration.waiting.postMessage({ type: 'SKIP_WAITING' });
      }
    });

    // Reload when the new SW takes control
    navigator.serviceWorker.addEventListener('controllerchange', () => {
      window.location.reload();
    }, { once: true });
  }

  navigator.serviceWorker.register('/sw.js')
    .then((registration) => {
      // If there's an already waiting worker, prompt immediately
      if (registration.waiting) {
        showUpdatePrompt(registration);
        return;
      }

      // Listen for updates being found
      registration.addEventListener('updatefound', () => {
        const newWorker = registration.installing;
        if (!newWorker) return;
        newWorker.addEventListener('statechange', () => {
          if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
            // A new update has been installed and is waiting
            showUpdatePrompt(registration);
          }
        });
      });

      // Also check periodically for updates
      setInterval(() => registration.update().catch(() => {}), 60 * 60 * 1000); // hourly
    })
    .catch(() => {
      // ignore SW registration errors silently to avoid impacting UX
    });
}

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.ValorIVX.init();
    setupServiceWorkerUpdates();
});

// Export for use in other modules
window.ValorIVX = window.ValorIVX;
