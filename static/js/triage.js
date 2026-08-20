/**
 * Analyst Triage Queue & Deep Forensic Inspector Controller
 * Powers live query filtering, triage workflow updates, and modal digital evidence inspection.
 */

let triageDebounceTimer = null;
let currentPostData = null;

async function loadTriagePosts() {
    const tbody = document.getElementById('triage-table-body');
    if (!tbody) return;

    const category = document.getElementById('triage-filter-category')?.value || 'all';
    const platform = document.getElementById('triage-filter-platform')?.value || 'all';
    const priority = document.getElementById('triage-filter-priority')?.value || 'all';
    const status = document.getElementById('triage-filter-status')?.value || 'all';
    const minConfusion = document.getElementById('triage-min-confusion')?.value || 0;
    const search = document.getElementById('triage-search')?.value || '';

    tbody.innerHTML = `
        <tr>
            <td colspan="9" style="text-align: center; padding: 30px;">
                <i class="fa-solid fa-spinner fa-spin fa-2x text-cyan"></i>
                <p style="margin-top: 10px; color: var(--text-muted);">Querying monitored OSINT feed...</p>
            </td>
        </tr>
    `;

    try {
        const queryParams = new URLSearchParams({
            category,
            platform,
            priority,
            triage_status: status,
            min_confusion: minConfusion,
            search,
            limit: 60
        });

        const res = await fetch(`/api/posts?${queryParams}`);
        const posts = await res.json();

        if (!posts || posts.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="9" style="text-align: center; padding: 40px;">
                        <i class="fa-solid fa-check-double fa-2x text-emerald"></i>
                        <p style="margin-top: 8px; color: var(--text-muted);">No posts match the current filter criteria.</p>
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = posts.map(p => {
            const prioClass = `badge-${p.priority.toLowerCase()}`;
            const confColor = p.confusion_score > 75 ? 'text-crimson' : (p.confusion_score > 50 ? 'text-amber' : 'text-cyan');
            const botProb = (p.bot_probability || 0) * 100;
            const botColor = botProb > 50 ? 'text-crimson font-weight-bold' : 'text-muted';
            const contradictionIcon = p.contradiction_flag ? `<span title="Contradicts Statutory Ground Truth" class="text-crimson" style="margin-left: 6px;"><i class="fa-solid fa-triangle-exclamation"></i></span>` : '';

            return `
                <tr>
                    <td><span class="badge badge-priority ${prioClass}">${p.priority}</span></td>
                    <td><strong class="${confColor}">${p.confusion_score}</strong>/100 ${contradictionIcon}</td>
                    <td><span style="text-transform: capitalize;">${getPlatformIcon(p.source_platform)} ${p.source_platform}</span></td>
                    <td>
                        <div><strong>${escapeHtml(p.author_handle)}</strong></div>
                        <div class="text-muted" style="font-size: 10px; font-family: var(--font-mono);">${p.author_followers || 0} followers</div>
                    </td>
                    <td>
                        <div class="post-claim-text">${escapeHtml(p.text)}</div>
                    </td>
                    <td><span style="font-size: 11px; font-family: var(--font-mono);">${escapeHtml(p.location_district)}</span></td>
                    <td><span class="${botColor}">${botProb.toFixed(0)}%</span></td>
                    <td>
                        <span class="badge" style="background: rgba(56, 189, 248, 0.1); border: 1px solid var(--border-color); color: var(--text-main); font-size: 10px;">
                            ${escapeHtml(p.triage_status.replace(/_/g, ' '))}
                        </span>
                    </td>
                    <td>
                        <button class="btn btn-sm btn-outline" onclick="openForensicModal('${p.id}')" title="Inspect Evidence & Triage">
                            <i class="fa-solid fa-microscope"></i> Inspect
                        </button>
                    </td>
                </tr>
            `;
        }).join('');

    } catch (err) {
        console.error("Failed to load posts:", err);
        tbody.innerHTML = `<tr><td colspan="9" style="color: var(--crimson); text-align: center;">Error loading posts</td></tr>`;
    }
}

function updateMinConf(val) {
    document.getElementById('min-conf-display').textContent = val;
    loadTriagePosts();
}

function debounceTriageSearch() {
    clearTimeout(triageDebounceTimer);
    triageDebounceTimer = setTimeout(() => {
        loadTriagePosts();
    }, 300);
}

// Deep Forensic Modal Inspector
async function openForensicModal(postId) {
    const modal = document.getElementById('forensic-modal');
    modal.classList.add('active');

    try {
        const res = await fetch(`/api/posts/${postId}`);
        const post = await res.json();
        currentPostData = post;

        // Populate fields
        document.getElementById('modal-post-id').textContent = post.id;
        document.getElementById('modal-title').textContent = `INSPECT EVIDENCE: ${post.id}`;
        document.getElementById('modal-post-text').textContent = post.text;
        document.getElementById('modal-platform').innerHTML = `${getPlatformIcon(post.source_platform)} ${post.source_platform.toUpperCase()}`;
        document.getElementById('modal-author').textContent = post.author_handle;
        document.getElementById('modal-location').textContent = post.location_district;
        document.getElementById('modal-timestamp').textContent = new Date(post.timestamp).toLocaleString();
        document.getElementById('modal-sha256').textContent = post.sha256_hash || 'CALCULATED_ON_INGEST';

        document.getElementById('modal-confusion-score').textContent = `${post.confusion_score}/100`;
        document.getElementById('modal-category').textContent = post.category.replace(/_/g, ' ').toUpperCase();
        document.getElementById('modal-category').className = `badge badge-${post.category}`;
        document.getElementById('modal-bot-prob').textContent = `${((post.bot_probability || 0) * 100).toFixed(0)}%`;
        document.getElementById('modal-urgency').textContent = `${((post.urgency_score || 0) * 100).toFixed(0)}%`;
        document.getElementById('modal-uncertainty').textContent = `${((post.epistemic_uncertainty || 0) * 100).toFixed(0)}%`;

        const prioBadge = document.getElementById('modal-priority-badge');
        prioBadge.textContent = post.priority;
        prioBadge.className = `badge badge-priority badge-${post.priority.toLowerCase()}`;

        // Contradiction Box
        const contSection = document.getElementById('modal-contradiction-section');
        const contBox = document.getElementById('modal-contradiction-box');
        if (post.contradiction_flag || (post.fact_verification && post.fact_verification.contradicts)) {
            contSection.style.display = 'block';
            const fv = post.fact_verification || {};
            contBox.innerHTML = `
                <div style="font-weight: 700; color: var(--crimson); margin-bottom: 6px;">
                    <i class="fa-solid fa-triangle-exclamation"></i> CONTRADICTS: ${fv.topic || 'Official Election Standards'}
                </div>
                <div style="font-size: 11px; margin-bottom: 6px;">
                    <strong>Official Rule:</strong> ${escapeHtml(fv.official_rule || 'Statutory federal & state election protocols.')}
                </div>
                <div style="font-size: 11px; color: var(--text-muted); margin-bottom: 8px;">
                    <strong>Authority Source:</strong> ${escapeHtml(fv.verification_source || 'Election Oversight Board')}
                </div>
                <div style="background: rgba(16, 185, 129, 0.1); border-left: 3px solid var(--emerald); padding: 8px; border-radius: 4px; font-size: 11px;">
                    <strong>Rapid Debunk Directive:</strong> ${escapeHtml(fv.debunk_text || 'Reiterate verified standards through official channels.')}
                </div>
            `;
        } else {
            contSection.style.display = 'none';
        }

        // Triage Controls
        document.getElementById('modal-triage-status').value = post.triage_status || 'new';
        document.getElementById('modal-priority-select').value = post.priority || 'P3';
        document.getElementById('modal-analyst-notes').value = post.analyst_notes || '';

    } catch (err) {
        console.error("Failed to load post details:", err);
        showToast("Error loading forensic evidence", "danger");
    }
}

function closeForensicModal() {
    document.getElementById('forensic-modal').classList.remove('active');
    currentPostData = null;
}

async function savePostTriage() {
    if (!currentPostData) return;

    const triage_status = document.getElementById('modal-triage-status').value;
    const priority = document.getElementById('modal-priority-select').value;
    const analyst_notes = document.getElementById('modal-analyst-notes').value;

    try {
        const res = await fetch(`/api/posts/${currentPostData.id}/triage`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                triage_status,
                priority,
                analyst_notes
            })
        });

        if (res.ok) {
            showToast(`Post ${currentPostData.id} updated to [${triage_status.toUpperCase()}]`, "success");
            closeForensicModal();
            loadTriagePosts();
            refreshTelemetry();
        } else {
            showToast("Failed to save triage update", "danger");
        }
    } catch (err) {
        showToast("Network error saving triage", "danger");
    }
}
