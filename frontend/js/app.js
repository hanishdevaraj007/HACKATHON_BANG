/**
 * Meridian Security Platform — Application Shell
 * Component C team will extend this.
 *
 * OWNER: Component C team
 * SEE: docs/COMPONENT_BOUNDARIES.md
 *
 * Communication:
 *   REST API:   http://localhost:8000/api/v1/
 *   WebSocket:  ws://localhost:8000/ws
 */

const CONFIG = {
    API_BASE: 'http://localhost:8000/api/v1',
    WS_URL: 'ws://localhost:8000/ws',
};

// WebSocket connection placeholder
let ws = null;

function updateConnectionStatus(connected) {
    const el = document.getElementById('connection-status');
    if (connected) {
        el.className = 'status-connected';
        el.textContent = '● Connected';
    } else {
        el.className = 'status-disconnected';
        el.textContent = '● Disconnected';
    }
}

function connectWebSocket() {
    try {
        ws = new WebSocket(CONFIG.WS_URL);
        ws.onopen = () => updateConnectionStatus(true);
        ws.onclose = () => {
            updateConnectionStatus(false);
            // Reconnect after 5 seconds
            setTimeout(connectWebSocket, 5000);
        };
        ws.onerror = () => updateConnectionStatus(false);
        ws.onmessage = (event) => {
            // Component C team: handle incoming events here
            console.log('WS message:', event.data);
        };
    } catch (e) {
        updateConnectionStatus(false);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('Meridian Security Platform — Dashboard initialized');
    // Uncomment when backend is running:
    // connectWebSocket();
});
