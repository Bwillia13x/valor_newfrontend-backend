// Valor IVX - Frontend Authentication Module
// Handles user authentication, token management, and session persistence

// Environment configuration
const config = {
  // Auto-detect environment
  isProduction: window.location.protocol === 'https:' || window.location.hostname !== 'localhost',
  apiBaseUrl: window.location.protocol === 'https:' 
    ? 'https://api.valor-ivx.com' 
    : 'http://localhost:5002',
  // Fallback for development
  devApiUrl: 'http://localhost:5002'
};

// Authentication state management
const auth = {
  token: null,
  refreshToken: null,
  user: null,
  isAuthenticated: false,
  lastActivity: Date.now()
};

// Initialize authentication from localStorage
export function initAuth() {
  const savedToken = localStorage.getItem('valor_auth_token');
  const savedRefreshToken = localStorage.getItem('valor_refresh_token');
  const savedUser = localStorage.getItem('valor_user');
  
  if (savedToken && savedRefreshToken) {
    auth.token = savedToken;
    auth.refreshToken = savedRefreshToken;
    auth.user = savedUser ? JSON.parse(savedUser) : null;
    auth.isAuthenticated = true;
    auth.lastActivity = Date.now();
    
    // Validate token on startup
    validateToken();
  }
  
  // Set up activity tracking for session timeout
  setupActivityTracking();
  
  updateAuthUI();
}

// Setup activity tracking for session timeout
function setupActivityTracking() {
  const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'];
  
  events.forEach(event => {
    document.addEventListener(event, () => {
      auth.lastActivity = Date.now();
    });
  });
  
  // Check for session timeout every minute
  setInterval(() => {
    const sessionTimeout = config.isProduction ? 60 * 60 * 1000 : 24 * 60 * 60 * 1000; // 1 hour prod, 24 hours dev
    if (auth.isAuthenticated && (Date.now() - auth.lastActivity) > sessionTimeout) {
      logoutUser();
      showNotification('Session expired. Please login again.', 'warning');
    }
  }, 60000);
}

// Get API base URL
function getApiUrl() {
  if (config.isProduction) {
    return config.apiBaseUrl;
  }
  return config.devApiUrl;
}

// Register new user
export async function registerUser(username, email, password) {
  try {
    const response = await fetch(`${getApiUrl()}/api/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
      },
      body: JSON.stringify({
        username,
        email,
        password
      })
    });
    
    const data = await response.json();
    
    if (response.ok) {
      // Auto-login after successful registration
      return await loginUser(username, password);
    } else {
      return {
        success: false,
        error: data.error || 'Registration failed'
      };
    }
  } catch (error) {
    return {
      success: false,
      error: 'Network error during registration'
    };
  }
}

// Login user
export async function loginUser(username, password) {
  try {
    const response = await fetch(`${getApiUrl()}/api/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
      },
      body: JSON.stringify({
        username,
        password
      })
    });
    
    const data = await response.json();
    
    if (response.ok) {
      auth.token = data.access_token;
      auth.refreshToken = data.refresh_token;
      auth.user = data.user;
      auth.isAuthenticated = true;
      auth.lastActivity = Date.now();
      
      // Save to localStorage with encryption in production
      if (config.isProduction) {
        // In production, we could add additional encryption
        localStorage.setItem('valor_auth_token', auth.token);
        localStorage.setItem('valor_refresh_token', auth.refreshToken);
        localStorage.setItem('valor_user', JSON.stringify(auth.user));
      } else {
        localStorage.setItem('valor_auth_token', auth.token);
        localStorage.setItem('valor_refresh_token', auth.refreshToken);
        localStorage.setItem('valor_user', JSON.stringify(auth.user));
      }
      
      updateAuthUI();
      
      return {
        success: true,
        user: auth.user
      };
    } else {
      return {
        success: false,
        error: data.error || 'Login failed'
      };
    }
  } catch (error) {
    return {
      success: false,
      error: 'Network error during login'
    };
  }
}

// Logout user
export function logoutUser() {
  auth.token = null;
  auth.refreshToken = null;
  auth.user = null;
  auth.isAuthenticated = false;
  
  // Clear localStorage
  localStorage.removeItem('valor_auth_token');
  localStorage.removeItem('valor_refresh_token');
  localStorage.removeItem('valor_user');
  
  updateAuthUI();
}

// Refresh access token
export async function refreshAccessToken() {
  if (!auth.refreshToken) {
    return false;
  }
  
  try {
    const response = await fetch(`${getApiUrl()}/api/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
      },
      body: JSON.stringify({
        refresh_token: auth.refreshToken
      })
    });
    
    const data = await response.json();
    
    if (response.ok) {
      auth.token = data.access_token;
      auth.lastActivity = Date.now();
      localStorage.setItem('valor_auth_token', auth.token);
      return true;
    } else {
      // Refresh token expired, logout user
      logoutUser();
      return false;
    }
  } catch (error) {
    logoutUser();
    return false;
  }
}

// Validate current token
export async function validateToken() {
  if (!auth.token) {
    return false;
  }
  
  try {
    const response = await fetch(`${getApiUrl()}/api/auth/profile`, {
      headers: {
        'Authorization': `Bearer ${auth.token}`,
        'X-Requested-With': 'XMLHttpRequest'
      }
    });
    
    if (response.ok) {
      const data = await response.json();
      auth.user = data.user;
      auth.lastActivity = Date.now();
      localStorage.setItem('valor_user', JSON.stringify(auth.user));
      return true;
    } else if (response.status === 401) {
      // Token expired, try to refresh
      return await refreshAccessToken();
    } else {
      logoutUser();
      return false;
    }
  } catch (error) {
    logoutUser();
    return false;
  }
}

// Get authenticated headers for API requests
export function getAuthHeaders() {
  if (!auth.token) {
    return {
      'X-Requested-With': 'XMLHttpRequest'
    };
  }
  
  return {
    'Authorization': `Bearer ${auth.token}`,
    'X-Requested-With': 'XMLHttpRequest'
  };
}

// Check if user is authenticated
export function isAuthenticated() {
  return auth.isAuthenticated;
}

// Get current user
export function getCurrentUser() {
  return auth.user;
}

// Update authentication UI
function updateAuthUI() {
  const authContainer = document.getElementById('authContainer');
  const userInfo = document.getElementById('userInfo');
  const loginForm = document.getElementById('loginForm');
  const registerForm = document.getElementById('registerForm');
  
  if (!authContainer) return;
  
  if (auth.isAuthenticated && auth.user) {
    // Show authenticated state
    if (userInfo) {
      userInfo.style.display = 'block';
      userInfo.innerHTML = `
        <div class="user-profile">
          <span class="username">${auth.user.username}</span>
          <span class="email">${auth.user.email}</span>
          <span class="session-status">${config.isProduction ? '🔒 Secure' : '🛠️ Development'}</span>
        </div>
        <button id="logoutBtn" class="btn-secondary">Logout</button>
      `;
      
      // Add logout event listener
      const logoutBtn = document.getElementById('logoutBtn');
      if (logoutBtn) {
        logoutBtn.addEventListener('click', logoutUser);
      }
    }
    
    if (loginForm) loginForm.style.display = 'none';
    if (registerForm) registerForm.style.display = 'none';
    
    // Enable authenticated features
    enableAuthenticatedFeatures();
  } else {
    // Show login/register forms
    if (userInfo) userInfo.style.display = 'none';
    if (loginForm) loginForm.style.display = 'block';
    if (registerForm) registerForm.style.display = 'block';
    
    // Disable authenticated features
    disableAuthenticatedFeatures();
  }
}

// Enable features that require authentication
function enableAuthenticatedFeatures() {
  const authRequiredButtons = document.querySelectorAll('[data-auth-required]');
  authRequiredButtons.forEach(button => {
    button.disabled = false;
    button.style.opacity = '1';
  });
}

// Disable features that require authentication
function disableAuthenticatedFeatures() {
  const authRequiredButtons = document.querySelectorAll('[data-auth-required]');
  authRequiredButtons.forEach(button => {
    button.disabled = true;
    button.style.opacity = '0.5';
  });
}

// Initialize authentication UI
export function initAuthUI() {
  // Create authentication container if it doesn't exist
  let authContainer = document.getElementById('authContainer');
  if (!authContainer) {
    authContainer = document.createElement('div');
    authContainer.id = 'authContainer';
    authContainer.className = 'auth-container';
    
    // Insert after the brand div in the header
    const brand = document.querySelector('.brand');
    if (brand && brand.parentNode) {
      brand.parentNode.insertBefore(authContainer, brand.nextSibling);
    }
  }
  
  // Create authentication UI elements
  authContainer.innerHTML = `
    <div id="userInfo" class="user-info" style="display: none;">
      <!-- User info will be populated here -->
    </div>
    
    <div id="loginForm" class="auth-form">
      <h3>Login</h3>
      <form id="loginFormElement">
        <input type="text" id="loginUsername" placeholder="Username or Email" required>
        <input type="password" id="loginPassword" placeholder="Password" required>
        <button type="submit" class="btn-primary">Login</button>
      </form>
      <p class="auth-switch">Don't have an account? <a href="#" id="showRegister">Register</a></p>
    </div>
    
    <div id="registerForm" class="auth-form" style="display: none;">
      <h3>Register</h3>
      <form id="registerFormElement">
        <input type="text" id="registerUsername" placeholder="Username" required>
        <input type="email" id="registerEmail" placeholder="Email" required>
        <input type="password" id="registerPassword" placeholder="Password (min 8 chars)" required>
        <button type="submit" class="btn-primary">Register</button>
      </form>
      <p class="auth-switch">Already have an account? <a href="#" id="showLogin">Login</a></p>
    </div>
  `;
  
  // Add event listeners
  setupAuthEventListeners();
  
  // Initialize authentication state
  initAuth();
}

// Setup authentication event listeners
function setupAuthEventListeners() {
  // Login form
  const loginFormElement = document.getElementById('loginFormElement');
  if (loginFormElement) {
    loginFormElement.addEventListener('submit', async (e) => {
      e.preventDefault();
      
      const username = document.getElementById('loginUsername').value;
      const password = document.getElementById('loginPassword').value;
      
      const result = await loginUser(username, password);
      
      if (result.success) {
        showNotification('Login successful!', 'success');
      } else {
        showNotification(result.error, 'error');
      }
    });
  }
  
  // Register form
  const registerFormElement = document.getElementById('registerFormElement');
  if (registerFormElement) {
    registerFormElement.addEventListener('submit', async (e) => {
      e.preventDefault();
      
      const username = document.getElementById('registerUsername').value;
      const email = document.getElementById('registerEmail').value;
      const password = document.getElementById('registerPassword').value;
      
      const result = await registerUser(username, email, password);
      
      if (result.success) {
        showNotification('Registration successful!', 'success');
      } else {
        showNotification(result.error, 'error');
      }
    });
  }
  
  // Form switching
  const showRegister = document.getElementById('showRegister');
  const showLogin = document.getElementById('showLogin');
  
  if (showRegister) {
    showRegister.addEventListener('click', (e) => {
      e.preventDefault();
      document.getElementById('loginForm').style.display = 'none';
      document.getElementById('registerForm').style.display = 'block';
    });
  }
  
  if (showLogin) {
    showLogin.addEventListener('click', (e) => {
      e.preventDefault();
      document.getElementById('registerForm').style.display = 'none';
      document.getElementById('loginForm').style.display = 'block';
    });
  }
}

// Show notification
function showNotification(message, type = 'info') {
  // Create notification element
  const notification = document.createElement('div');
  notification.className = `notification notification-${type}`;
  notification.textContent = message;
  
  // Add to page
  document.body.appendChild(notification);
  
  // Remove after 3 seconds
  setTimeout(() => {
    if (notification.parentNode) {
      notification.parentNode.removeChild(notification);
    }
  }, 3000);
}

// Export authentication state for other modules
export { auth, config }; 