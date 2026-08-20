/**
 * Threat Radar & Executive Overview Controller
 * Renders Chart.js threat charts, category breakdown, live alerts, and content stream.
 */

let categoryChart = null;
let platformChart = null;

async function loadThreatRadar() {
    await refreshTelemetry();
    loadLiveStreamTicker();
}

function updateRadarCharts(data) {
    // 1. Category Distribution Chart (Doughnut)
    const catCanvas = document.getElementById('categoryDistributionChart');
    if (catCanvas && data.categories) {
        const labels = data.categories.map(c => c.category.replace(/_/g, ' ').toUpperCase());
        const counts = data.categories.map(c => c.count);

        const colors = [
            '#ef4444', // voter_suppression
            '#f59e0b', // integrity_tampering
            '#a855f7', // synthetic_deepfake
            '#ec4899', // impersonation
            '#3b82f6', // premature_results
            '#eab308', // voter_intimidation
            '#10b981'  // legitimate_news
        ];

        if (categoryChart) {
            categoryChart.data.labels = labels;
            categoryChart.data.datasets[0].data = counts;
            categoryChart.update();
        } else {
            categoryChart = new Chart(catCanvas, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: counts,
                        backgroundColor: colors,
                        borderColor: '#0d1424',
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                color: '#94a3b8',
                                font: { family: "'JetBrains Mono', monospace", size: 10 },
                                boxWidth: 12,
                                padding: 10
                            }
                        }
                    }
                }
            });
        }
    }

    // 2. Platform Spread Chart (Bar)
    const platCanvas = document.getElementById('platformSpreadChart');
    if (platCanvas && data.platforms) {
        const labels = data.platforms.map(p => p.source_platform.toUpperCase());
        const counts = data.platforms.map(p => p.count);

        if (platformChart) {
            platformChart.data.labels = labels;
            platformChart.data.datasets[0].data = counts;
            platformChart.update();
        } else {
            platformChart = new Chart(platCanvas, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Indexed Posts',
                        data: counts,
                        backgroundColor: 'rgba(6, 182, 212, 0.65)',
                        borderColor: '#06b6d4',
                        borderWidth: 1,
                        borderRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            ticks: { color: '#94a3b8', font: { family: "'JetBrains Mono', monospace", size: 10 } },
                            grid: { color: 'rgba(56, 189, 248, 0.05)' }
                        },
                        y: {
                            ticks: { color: '#94a3b8', font: { family: "'JetBrains Mono', monospace", size: 10 } },
                            grid: { color: 'rgba(56, 189, 248, 0.08)' }
                        }
                    },
                    plugins: {
                        legend: { display: false }
                    }
                }
            });
        }
    }
}

function renderAlertsList(alerts) {
    const list = document.getElementById('radar-alerts-list');
    if (!list) return;

    if (!alerts || alerts.length === 0) {
        list.innerHTML = `
            <div class="empty-state" style="padding: 20px;">
                <i class="fa-solid fa-shield-check fa-2x text-emerald"></i>
                <p style="margin-top: 8px;">No active critical alerts. System telemetry nominal.</p>
            </div>
        `;
        return;
    }

    list.innerHTML = alerts.map(a => `
        <div class="alert-card" onclick="inspectAlertPost('${a.related_id}')">
            <div class="alert-header">
                <span class="badge badge-priority badge-p0">${a.severity}</span>
                <span class="text-muted"><i class="fa-regular fa-clock"></i> ${new Date(a.timestamp).toLocaleTimeString()}</span>
            </div>
            <div class="alert-msg">${escapeHtml(a.message)}</div>
        </div>
    `).join('');
}

async function loadLiveStreamTicker() {
    const ticker = document.getElementById('radar-stream-ticker');
    if (!ticker) return;
    try {
        const res = await fetch('/api/posts?limit=15');
        const posts = await res.json();
        ticker.innerHTML = posts.map(p => formatTickerItem(p)).join('');
    } catch (err) {
        console.error("Failed to load ticker:", err);
    }
}

function prependStreamTicker(posts) {
    const ticker = document.getElementById('radar-stream-ticker');
    if (!ticker) return;
    posts.forEach(p => {
        const itemHtml = formatTickerItem(p);
        const temp = document.createElement('div');
        temp.innerHTML = itemHtml;
        const elem = temp.firstElementChild;
        ticker.insertBefore(elem, ticker.firstChild);
        if (ticker.children.length > 25) {
            ticker.removeChild(ticker.lastChild);
        }
    });
}

function formatTickerItem(p) {
    const badgeClass = p.confusion_score > 75 ? 'badge-p0' : (p.confusion_score > 50 ? 'badge-p1' : 'badge-p2');
    const platIcon = getPlatformIcon(p.source_platform);
    return `
        <div class="ticker-item" onclick="openForensicModal('${p.id}')">
            <div class="ticker-left">
                <span class="badge ${badgeClass}">${p.confusion_score}/100</span>
                <span class="text-muted">${platIcon} <strong>${escapeHtml(p.author_handle)}</strong>:</span>
                <span class="ticker-text">${escapeHtml(p.text)}</span>
            </div>
            <div class="text-muted" style="font-family: var(--font-mono); font-size: 11px;">
                <i class="fa-solid fa-location-dot"></i> ${escapeHtml(p.location_district)}
            </div>
        </div>
    `;
}

function getPlatformIcon(platform) {
    switch (platform.toLowerCase()) {
        case 'twitter': return '<i class="fa-brands fa-x-twitter text-cyan"></i>';
        case 'telegram': return '<i class="fa-brands fa-telegram text-cyan"></i>';
        case 'reddit': return '<i class="fa-brands fa-reddit text-amber"></i>';
        case 'tiktok': return '<i class="fa-brands fa-tiktok"></i>';
        case '4chan': return '<i class="fa-solid fa-clover text-emerald"></i>';
        case 'facebook': return '<i class="fa-brands fa-facebook text-blue"></i>';
        default: return '<i class="fa-solid fa-newspaper text-muted"></i>';
    }
}

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}

function inspectAlertPost(postId) {
    if (postId) {
        openForensicModal(postId);
    }
}
