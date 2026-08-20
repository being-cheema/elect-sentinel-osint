/**
 * Live Global OSINT Scanner Controller
 * Powers ad-hoc text & social media forensic analysis with global geographic resolution.
 */

async function runCustomOsintScan() {
    const text = document.getElementById('scanner-input-text')?.value?.trim();
    const author = document.getElementById('scanner-input-author')?.value?.trim() || '@analyst_scan';
    const platform = document.getElementById('scanner-input-platform')?.value || 'web';
    const resultsContainer = document.getElementById('scanner-results-container');

    if (!text) {
        showToast("Please enter text or claim to scan", "danger");
        return;
    }

    resultsContainer.innerHTML = `
        <div class="empty-state">
            <i class="fa-solid fa-spinner fa-spin fa-2x text-cyan"></i>
            <h3 style="margin-top: 12px;">Running Global OSINT Linguistic & Epistemic Diagnostics...</h3>
            <p>Evaluating threat vectors, uncertainty markers, and resolving country location...</p>
        </div>
    `;

    try {
        const res = await fetch('/api/osint/scan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, author, platform })
        });

        const data = await res.json();
        const a = data.analysis;
        const fc = data.fact_check;
        const loc = data.resolved_location || { district: 'Global / International' };

        const confColor = a.confusion_score > 75 ? 'var(--crimson)' : (a.confusion_score > 50 ? 'var(--amber)' : 'var(--cyan)');
        const botPct = ((a.bot_probability || 0) * 100).toFixed(0);

        const markersHtml = (a.matched_markers || []).map(m => `
            <span class="tag" style="background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); font-size: 11px;">
                ${escapeHtml(m)}
            </span>
        `).join('');

        let contradictionBoxHtml = '';
        if (fc && fc.contradicts) {
            contradictionBoxHtml = `
                <div class="contradiction-alert-box" style="margin-top: 14px;">
                    <div style="font-weight: 700; color: var(--crimson); font-size: 13px; margin-bottom: 6px;">
                        <i class="fa-solid fa-triangle-exclamation"></i> STATUTORY GROUND TRUTH CONTRADICTION DETECTED
                    </div>
                    <div style="font-size: 11px; margin-bottom: 4px;"><strong>Contradicted Standard:</strong> ${escapeHtml(fc.topic)}</div>
                    <div style="font-size: 11px; margin-bottom: 4px;"><strong>Official Regulation:</strong> ${escapeHtml(fc.official_rule)}</div>
                    <div style="font-size: 11px; color: var(--text-muted); margin-bottom: 8px;"><strong>Verification Authority:</strong> ${escapeHtml(fc.verification_source)}</div>
                    <div style="background: rgba(16, 185, 129, 0.15); border-left: 3px solid var(--emerald); padding: 8px 10px; border-radius: 4px; font-size: 11px;">
                        <strong>Rapid Counter-Fact Directive:</strong> ${escapeHtml(fc.debunk_text)}
                    </div>
                </div>
            `;
        } else {
            contradictionBoxHtml = `
                <div style="background: rgba(16, 185, 129, 0.08); border: 1px solid var(--emerald); border-radius: 6px; padding: 10px 12px; margin-top: 14px; font-size: 11px; color: var(--emerald);">
                    <i class="fa-solid fa-circle-check"></i> No direct statutory contradictions detected against current ground truth rules.
                </div>
            `;
        }

        resultsContainer.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
                <span class="badge badge-priority badge-${a.priority.toLowerCase()}">PRIORITY: ${a.priority}</span>
                <span style="font-family: var(--font-mono); font-size: 11px; color: var(--text-muted);">
                    SHA-256: <code class="hash-code">${data.sha256_fingerprint.substring(0, 18)}...</code>
                </span>
            </div>

            <div class="narrative-metrics" style="margin-bottom: 14px;">
                <div>
                    <div class="metric-stat-val" style="color: ${confColor};">${a.confusion_score}/100</div>
                    <div class="metric-stat-lbl">CONFUSION THREAT</div>
                </div>
                <div>
                    <div class="metric-stat-val text-amber">${botPct}%</div>
                    <div class="metric-stat-lbl">INAUTHENTICITY / BOT</div>
                </div>
                <div>
                    <div class="metric-stat-val text-cyan">${((a.urgency_score || 0) * 100).toFixed(0)}%</div>
                    <div class="metric-stat-lbl">OUTRAGE / URGENCY</div>
                </div>
            </div>

            <div class="meta-item" style="margin-bottom: 10px;">
                <span>Resolved Geographic Origin:</span>
                <strong class="text-cyan"><i class="fa-solid fa-location-dot"></i> ${escapeHtml(loc.district)}</strong>
            </div>

            <div style="margin-bottom: 12px;">
                <div style="font-size: 11px; font-family: var(--font-mono); color: var(--text-muted); margin-bottom: 4px;">
                    CLASSIFICATION CATEGORY:
                </div>
                <span class="badge" style="background: rgba(6, 182, 212, 0.15); border: 1px solid var(--cyan); color: var(--cyan); font-size: 11px;">
                    ${a.category.replace(/_/g, ' ').toUpperCase()}
                </span>
            </div>

            <div style="margin-bottom: 12px;">
                <div style="font-size: 11px; font-family: var(--font-mono); color: var(--text-muted); margin-bottom: 6px;">
                    EXTRACTED DISINFORMATION TRIGGERS (${(a.matched_markers || []).length}):
                </div>
                <div class="tag-cloud">
                    ${markersHtml || '<span style="font-size: 11px; color: var(--text-muted);">No explicit disinformation n-grams detected. Content appears narrative-neutral.</span>'}
                </div>
            </div>

            ${contradictionBoxHtml}
        `;

    } catch (err) {
        console.error("OSINT Scan error:", err);
        resultsContainer.innerHTML = `<div class="empty-state" style="color: var(--crimson);">Scan failed. Please check network.</div>`;
    }
}
