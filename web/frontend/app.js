/**
 * Scholarship Copilot - Frontend Application
 * Handles UI interactions and communication with FastAPI backend
 */

const API_BASE = 'http://localhost:8000/api/v1';

// Application State
let state = {
    sessionId: null,
    currentApp: null,
    tools: [],
    isLoading: false
};

// Initialize app on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing Copilot...');
    initializeSession();
    setupEventListeners();
    loadTools();
});

/**
 * Create a new session
 */
async function initializeSession() {
    try {
        const response = await fetch(`${API_BASE}/sessions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: generateUserId() })
        });

        const data = await response.json();
        state.sessionId = data.session_id;
        document.getElementById('sessionId').textContent = `Session: ${state.sessionId.substring(0, 8)}...`;
        console.log('Session created:', state.sessionId);
    } catch (error) {
        console.error('Failed to create session:', error);
        addMessage('system', 'Failed to create session. Please refresh the page.');
    }
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    document.getElementById('chatForm').addEventListener('submit', handleQuerySubmit);
    document.getElementById('newSessionBtn').addEventListener('click', () => {
        location.reload();
    });
}

/**
 * Handle chat form submission
 */
async function handleQuerySubmit(e) {
    e.preventDefault();

    const queryInput = document.getElementById('queryInput');
    const query = queryInput.value.trim();

    if (!query || state.isLoading) return;

    // Add user message to UI
    addMessage('user', query);
    queryInput.value = '';

    // Show loading indicator
    setLoading(true);

    try {
        const response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                query: query,
                session_id: state.sessionId
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        addMessage('assistant', data.response);

        // Update current app if changed
        await updateApplicationContext();
    } catch (error) {
        console.error('Chat error:', error);
        addMessage('system', `Error: ${error.message}`);
    } finally {
        setLoading(false);
        document.getElementById('queryInput').focus();
    }
}

/**
 * Load and display available tools
 */
async function loadTools() {
    try {
        const response = await fetch(`${API_BASE}/tools`);
        const data = await response.json();

        state.tools = data.tools;
        displayTools(data.tools);
    } catch (error) {
        console.error('Failed to load tools:', error);
    }
}

/**
 * Display available tools in sidebar
 */
function displayTools(tools) {
    const toolsList = document.getElementById('toolsList');

    if (tools.length === 0) {
        toolsList.innerHTML = '<p>No tools available</p>';
        return;
    }

    const toolsHtml = tools
        .slice(0, 5) // Show first 5 tools
        .map(tool => `<div class="tool-item">
            <strong>${tool.name}</strong>
            <p style="font-size: 0.75rem; color: #6b7280; margin-top: 0.25rem;">
                ${tool.description}
            </p>
        </div>`)
        .join('');

    toolsList.innerHTML = toolsHtml + (tools.length > 5 ?
        `<p style="font-size: 0.75rem; color: #9ca3af; margin-top: 0.5rem;">...and ${tools.length - 5} more</p>` : '');
}

/**
 * Update current application context
 */
async function updateApplicationContext() {
    try {
        const response = await fetch(`${API_BASE}/sessions/${state.sessionId}`);
        const data = await response.json();

        if (data.context && data.context.current_application) {
            state.currentApp = data.context.current_application;
            const appDiv = document.getElementById('currentApp');
            appDiv.innerHTML = `
                <strong>Current Application</strong>
                <p style="margin-top: 0.5rem; font-size: 0.875rem;">
                    ${data.context.current_application}
                </p>
            `;
        }
    } catch (error) {
        console.error('Failed to update application context:', error);
    }
}

/**
 * Add message to chat
 */
function addMessage(role, content) {
    const messagesDiv = document.getElementById('chatMessages');

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    const p = document.createElement('p');
    p.textContent = content;
    messageDiv.appendChild(p);

    messagesDiv.appendChild(messageDiv);

    // Scroll to bottom
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

/**
 * Set loading state
 */
function setLoading(isLoading) {
    state.isLoading = isLoading;
    const loadingDiv = document.getElementById('loading');
    const sendBtn = document.querySelector('.button-send');

    if (isLoading) {
        loadingDiv.style.display = 'flex';
        sendBtn.disabled = true;
    } else {
        loadingDiv.style.display = 'none';
        sendBtn.disabled = false;
    }
}

/**
 * Generate a unique user ID
 */
function generateUserId() {
    return `user_${Math.random().toString(36).substring(2, 11)}`;
}

/**
 * Format timestamp
 */
function formatTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}
