/**
 * Core Application Controller for ELECT-SENTINEL OSINT (Global Live)
 * Handles SSE Live Telemetry Stream, Tab Navigation, Global State,
 * Autonomous Global Live Feeds, and Web Audio Alerts.
 */

// Global State
const state = {
    currentTab: 'radar',
    audioEnabled: true,
    telemetry: {},
    activePostInModal: null,
    activeCase: null
};

// Web Audio API Sound Synthesizer for alerts
let audioCtx = null;

function playAlertChime(severity = 'P0') {
    if (!state.audioEnabled) return;
    try {
        if (!audioCtx) {
            audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        }
        if (audioCtx.state === 'suspended') {
            audioCtx.resume();
        }
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.type = severity === 'P0' ? 'sawtooth' : 'sine';
        osc.frequency.setValueAtTime(severity === 'P0' ? 880 : 587, audioCtx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(severity === 'P0' ? 440 : 293, audioCtx.currentTime + 0.35);
        
        gain.gain.setValueAtTime(0.15, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.35);
        
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start();
        osc.stop(audioCtx.currentTime + 0.35);
    } catch (e) {
        console.warn("Audio playback not permitted yet:", e);
    }
}

function toggleAudio() {
    state.audioEnabled = !state.audioEnabled;
    const icon = document.getElementById('audio-icon');
    if (state.audioEnabled) {
        icon.className = 'fa-solid fa-volume-high text-cyan';
        showToast("Audio threat alerts enabled", "success");
    } else {
        icon.className = 'fa-solid fa-volume-xmark text-muted';
        showToast("Audio threat alerts muted", "normal");
    }
}

// Toast Notifications
function showToast(message, type = "normal") {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type === 'danger' ? 'toast-danger' : (type === 'success' ? 'toast-success' : '')}`;
    toast.innerHTML = `<i class="fa-solid fa-${type === 'danger' ? 'triangle-exclamation' : (type === 'success' ? 'check' : 'info')}"></i> ${message}`;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 4500);
}

// Tab Switching
function switchTab(tabId) {
    state.currentTab = tabId;
    
    // Update nav tab buttons
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.classList.toggle('active', tab.getAttribute('data-tab') === tabId);
    });

    // Update active pane
    document.querySelectorAll('.tab-pane').forEach(pane => {
        pane.classList.toggle('active', pane.id === `tab-${tabId}`);
    });

    // Refresh tab-specific views
    if (tabId === 'radar') loadThreatRadar();
    if (tabId === 'narratives') loadNarratives();
    if (tabId === 'triage') loadTriagePosts();
    if (tabId === 'graph') initNetworkGraph();
    if (tabId === 'map') initGeospatialMap();
    if (tabId === 'facts') loadGroundTruthFacts();
    if (tabId === 'reports') loadCases();
}

// Global Telemetry Polling & Refresh
async function refreshTelemetry() {
    try {
        const res = await fetch('/api/telemetry/overview');
        const data = await res.json();
        state.telemetry = data;

        // Update KPIs
        document.getElementById('kpi-val-posts').textContent = data.total_monitored_posts || '0';
        document.getElementById('kpi-val-narratives').textContent = data.active_narratives || '0';
        document.getElementById('kpi-val-confusion').textContent = `${data.mean_confusion_score || 0}/100`;
        document.getElementById('kpi-val-cib').textContent = data.cib_swarms_detected || '0';
        document.getElementById('kpi-val-alerts').textContent = data.unread_alerts_count || '0';

        // Update Threat Display
        const threatText = document.getElementById('threat-status-text');
        const threatCard = document.getElementById('threat-level-card');
        threatText.textContent = data.threat_level || 'NOMINAL';
        threatText.style.color = data.threat_color || '#10b981';
        threatCard.style.borderColor = data.threat_color || 'var(--border-color)';

        // Refresh charts if on radar tab
        if (state.currentTab === 'radar') {
            updateRadarCharts(data);
            renderAlertsList(data.recent_alerts || []);
        }
    } catch (err) {
        console.error("Failed to load telemetry overview:", err);
    }
}

// SSE Live Telemetry Stream Listener
function initLiveStream() {
    try {
        const evtSource = new EventSource('/api/stream');
        evtSource.onmessage = (event) => {
            try {
                const payload = JSON.parse(event.data);
                if (payload.type === 'update') {
                    if (payload.new_alerts && payload.new_alerts.length > 0) {
                        playAlertChime('P0');
                        payload.new_alerts.forEach(a => {
                            showToast(`[${a.severity}] ${a.message}`, "danger");
                        });
                    }
                    if (payload.new_posts && payload.new_posts.length > 0) {
                        prependStreamTicker(payload.new_posts);
                    }
                    refreshTelemetry();
                }
            } catch (e) {
                console.error("SSE parse error:", e);
            }
        };
        evtSource.onerror = () => {
            console.warn("SSE stream disconnected. Retrying in 5s...");
            evtSource.close();
            setTimeout(initLiveStream, 5000);
        };
    } catch (e) {
        console.warn("SSE not supported or connection error:", e);
    }
}

// Real-Time Global Feed Operations
async function pollGlobalLiveFeeds() {
    showToast("Synchronizing with real-world global election feeds & social streams...", "normal");
    try {
        const res = await fetch('/api/ingest/refresh-live', { method: 'POST' });
        const data = await res.json();
        showToast(`Ingested ${data.articles_ingested} live global articles & posts`, "success");
        refreshTelemetry();
        if (state.currentTab === 'radar') loadThreatRadar();
        if (state.currentTab === 'triage') loadTriagePosts();
        if (state.currentTab === 'narratives') loadNarratives();
        if (state.currentTab === 'graph') initNetworkGraph();
        if (state.currentTab === 'map') initGeospatialMap();
    } catch (err) {
        showToast("Failed to poll global feeds", "danger");
    }
}

async function purgeAndRefreshLive() {
    if (!confirm("Wipe historical database and fetch a completely clean 100% real live global stream?")) {
        return;
    }
    showToast("Wiping database and ingesting fresh live global feeds...", "normal");
    try {
        const res = await fetch('/api/admin/purge-and-refresh', { method: 'POST' });
        const data = await res.json();
        showToast(`Fresh live stream active! Ingested ${data.live_articles_ingested} real global articles`, "success");
        refreshTelemetry();
        if (state.currentTab === 'radar') loadThreatRadar();
        if (state.currentTab === 'triage') loadTriagePosts();
        if (state.currentTab === 'narratives') loadNarratives();
        if (state.currentTab === 'graph') initNetworkGraph();
        if (state.currentTab === 'map') initGeospatialMap();
    } catch (err) {
        showToast("Failed to purge and refresh live stream", "danger");
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // Initialize application
    refreshTelemetry();
    switchTab('radar');
    initLiveStream();

    // Regular interval refresh
    setInterval(refreshTelemetry, 8000);
});
