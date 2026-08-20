/**
 * Intelligence Dossiers & Briefing Generator Controller
 * Packages investigation cases, evidence tables, and synthesis briefings.
 */

let allCases = [];
let currentCaseId = null;
let currentReportMarkdown = '';

async function loadCases() {
    const container = document.getElementById('cases-list-container');
    if (!container) return;

    try {
        const res = await fetch('/api/cases');
        allCases = await res.json();

        if (!allCases || allCases.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fa-solid fa-folder-plus fa-2x text-muted"></i>
                    <p style="margin-top: 8px;">No active dossiers. Click "+ New Dossier" to initialize an investigation case.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = allCases.map(c => {
            const threatColor = c.threat_level === 'critical' ? 'var(--crimson)' : (c.threat_level === 'high' ? 'var(--amber)' : 'var(--cyan)');
            return `
                <div class="case-card ${c.id === currentCaseId ? 'active' : ''}" onclick="selectCase('${c.id}')">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                        <span class="badge" style="background: ${threatColor}; color: #000; font-weight: 800; font-size: 10px;">
                            ${escapeHtml(c.threat_level.toUpperCase())}
                        </span>
                        <span style="font-size: 10px; font-family: var(--font-mono); color: var(--text-muted);">
                            ${escapeHtml(c.id)}
                        </span>
                    </div>
                    <strong style="color: #fff; font-size: 13px; display: block; margin-bottom: 6px;">
                        ${escapeHtml(c.title)}
                    </strong>
                    <div style="display: flex; justify-content: space-between; font-size: 10px; color: var(--text-muted); font-family: var(--font-mono);">
                        <span><i class="fa-solid fa-user-shield"></i> ${escapeHtml(c.analyst)}</span>
                        <span><i class="fa-solid fa-clock"></i> ${new Date(c.updated_at).toLocaleDateString()}</span>
                    </div>
                </div>
            `;
        }).join('');

        // Auto-select first case if none active
        if (!currentCaseId && allCases.length > 0) {
            selectCase(allCases[0].id);
        }

    } catch (err) {
        console.error("Failed to load cases:", err);
    }
}

async function selectCase(caseId) {
    currentCaseId = caseId;
    loadCases(); // Update active highlights

    const preview = document.getElementById('report-content-view');
    const actions = document.getElementById('report-actions-bar');
    if (!preview) return;

    preview.innerHTML = `
        <div class="empty-state">
            <i class="fa-solid fa-spinner fa-spin fa-2x text-cyan"></i>
            <h3 style="margin-top: 12px;">Synthesizing OSINT Intelligence Briefing...</h3>
            <p>Aggregating narrative lifecycles, forensic SHA-256 hashes, and counter-messaging recommendations...</p>
        </div>
    `;

    try {
        const res = await fetch(`/api/cases/${caseId}/report`);
        const report = await res.json();
        currentReportMarkdown = report.markdown_report;

        if (actions) actions.style.display = 'flex';

        // Render Markdown to HTML
        const html = renderMarkdownToHtml(report.markdown_report);
        preview.innerHTML = `
            <div class="report-markdown-body">
                ${html}
            </div>
        `;

    } catch (err) {
        console.error("Failed to render case report:", err);
        preview.innerHTML = `<div class="empty-state" style="color: var(--crimson);">Failed to synthesize briefing.</div>`;
    }
}

function renderMarkdownToHtml(md) {
    if (!md) return '';
    let html = md
        // Headers
        .replace(/^# (.*$)/gim, '<h1>$1</h1>')
        .replace(/^## (.*$)/gim, '<h2>$1</h2>')
        .replace(/^### (.*$)/gim, '<h3>$1</h3>')
        // Bold & Code
        .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/gim, '<em>$1</em>')
        .replace(/`(.*?)`/gim, '<code>$1</code>')
        // Dividers
        .replace(/^---/gim, '<hr class="divider">')
        // Lists
        .replace(/^\- (.*$)/gim, '<li>$1</li>');

    // Tables
    const tableRegex = /\|(.+)\|/gim;
    if (html.includes('|')) {
        const lines = html.split('\n');
        let inTable = false;
        let tableHtml = '<table>';
        const finalLines = [];

        for (let line of lines) {
            if (line.trim().startsWith('|') && line.trim().endsWith('|')) {
                if (line.includes(':---') || line.includes('---:')) {
                    continue; // Skip markdown separator row
                }
                const cells = line.split('|').slice(1, -1).map(c => c.trim());
                if (!inTable) {
                    inTable = true;
                    tableHtml += '<thead><tr>' + cells.map(c => `<th>${c}</th>`).join('') + '</tr></thead><tbody>';
                } else {
                    tableHtml += '<tr>' + cells.map(c => `<td>${c}</td>`).join('') + '</tr>';
                }
            } else {
                if (inTable) {
                    tableHtml += '</tbody></table>';
                    finalLines.push(tableHtml);
                    tableHtml = '<table>';
                    inTable = false;
                }
                finalLines.push(line);
            }
        }
        if (inTable) {
            tableHtml += '</tbody></table>';
            finalLines.push(tableHtml);
        }
        html = finalLines.join('\n');
    }

    return html;
}

function copyReportMarkdown() {
    if (!currentReportMarkdown) return;
    navigator.clipboard.writeText(currentReportMarkdown);
    showToast("Full Intelligence Briefing Markdown copied to clipboard", "success");
}

function printReport() {
    window.print();
}

function openNewCaseModal() {
    document.getElementById('new-case-modal').classList.add('active');
}

function closeNewCaseModal() {
    document.getElementById('new-case-modal').classList.remove('active');
}

async function submitNewCase() {
    const title = document.getElementById('newcase-title').value.trim();
    const threat_level = document.getElementById('newcase-threat').value;
    const analyst = document.getElementById('newcase-analyst').value.trim() || 'Lead OSINT Analyst';
    const executive_summary = document.getElementById('newcase-summary').value.trim();
    const recommended_action = document.getElementById('newcase-action').value.trim();

    if (!title) {
        showToast("Please enter an investigation title", "danger");
        return;
    }

    try {
        const res = await fetch('/api/cases', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                title,
                threat_level,
                analyst,
                executive_summary,
                recommended_action,
                narrative_ids: [],
                post_ids: []
            })
        });

        const data = await res.json();
        showToast("Investigation dossier created successfully", "success");
        closeNewCaseModal();
        currentCaseId = data.case_id;
        loadCases();
    } catch (err) {
        showToast("Network error creating case", "danger");
    }
}
