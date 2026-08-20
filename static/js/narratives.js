/**
 * Narrative Intelligence Hub Controller
 * Displays clustered disinformation storylines, lifecycle stages, viral velocity, and sample posts.
 */

let allNarratives = [];
let activeLifecycleFilter = 'all';

async function loadNarratives() {
    const grid = document.getElementById('narratives-grid');
    if (!grid) return;
    
    grid.innerHTML = `
        <div class="empty-state" style="grid-column: 1 / -1;">
            <i class="fa-solid fa-spinner fa-spin fa-2x text-cyan"></i>
            <p style="margin-top: 10px;">Clustering incoming election signals...</p>
        </div>
    `;

    try {
        const res = await fetch('/api/narratives');
        allNarratives = await res.json();
        renderNarrativeCards();
    } catch (err) {
        console.error("Failed to load narratives:", err);
        grid.innerHTML = `<div class="empty-state" style="grid-column: 1 / -1; color: var(--crimson);">Failed to load narratives</div>`;
    }
}

function filterNarratives(lifecycle) {
    activeLifecycleFilter = lifecycle;
    document.querySelectorAll('.filter-pill').forEach(pill => {
        pill.classList.toggle('active', pill.textContent.toLowerCase() === lifecycle || (lifecycle === 'all' && pill.textContent.toLowerCase() === 'all'));
    });
    renderNarrativeCards();
}

function searchNarratives() {
    renderNarrativeCards();
}

function renderNarrativeCards() {
    const grid = document.getElementById('narratives-grid');
    if (!grid) return;

    const searchTerm = (document.getElementById('narrative-search-input')?.value || '').toLowerCase();

    const filtered = allNarratives.filter(n => {
        const matchLifecycle = (activeLifecycleFilter === 'all') || (n.lifecycle === activeLifecycleFilter);
        const matchSearch = !searchTerm || 
            n.title.toLowerCase().includes(searchTerm) || 
            (n.summary && n.summary.toLowerCase().includes(searchTerm)) ||
            (n.keywords && n.keywords.some(k => k.toLowerCase().includes(searchTerm)));
        return matchLifecycle && matchSearch;
    });

    if (filtered.length === 0) {
        grid.innerHTML = `
            <div class="empty-state" style="grid-column: 1 / -1;">
                <i class="fa-solid fa-folder-open fa-2x text-muted"></i>
                <p style="margin-top: 8px;">No narratives match current filter criteria.</p>
            </div>
        `;
        return;
    }

    grid.innerHTML = filtered.map(n => {
        const badgeClass = `badge-${n.lifecycle}`;
        const confColor = n.confusion_index > 75 ? 'var(--crimson)' : (n.confusion_index > 50 ? 'var(--amber)' : 'var(--cyan)');
        
        const platformBadges = (n.platforms_involved || []).map(p => `
            <span class="tag"><i class="fa-solid fa-satellite-dish"></i> ${p.toUpperCase()}</span>
        `).join('');

        const keywordTags = (n.keywords || []).map(k => `
            <span class="tag">#${escapeHtml(k)}</span>
        `).join('');

        const samplePostsHtml = (n.sample_posts || []).map(sp => `
            <div style="font-size: 11px; padding: 6px 8px; background: rgba(10, 16, 30, 0.6); border-radius: 4px; margin-top: 4px; border-left: 2px solid ${confColor};">
                <strong style="color: var(--cyan);">${escapeHtml(sp.author_handle)}:</strong> ${escapeHtml(sp.text.substring(0, 95))}...
            </div>
        `).join('');

        return `
            <div class="narrative-card">
                <div class="narrative-header">
                    <div>
                        <span class="badge ${badgeClass}">${n.lifecycle.replace('_', ' ')}</span>
                        <h3 class="narrative-title" style="margin-top: 8px;">${escapeHtml(n.title)}</h3>
                    </div>
                </div>

                <div class="narrative-metrics">
                    <div>
                        <div class="metric-stat-val" style="color: ${confColor};">${n.confusion_index}</div>
                        <div class="metric-stat-lbl">CONFUSION INDEX</div>
                    </div>
                    <div>
                        <div class="metric-stat-val text-cyan">${n.total_volume}</div>
                        <div class="metric-stat-lbl">POST VOLUME</div>
                    </div>
                    <div>
                        <div class="metric-stat-val text-amber">${n.velocity}/hr</div>
                        <div class="metric-stat-lbl">VELOCITY</div>
                    </div>
                </div>

                <p style="font-size: 12px; color: var(--text-muted); line-height: 1.4;">
                    ${escapeHtml(n.summary)}
                </p>

                <div class="tag-cloud">
                    ${platformBadges}
                    ${keywordTags}
                </div>

                <div style="margin-top: 6px;">
                    <div style="font-size: 10px; font-family: var(--font-mono); color: var(--text-muted); margin-bottom: 4px;">
                        <i class="fa-solid fa-list-ul"></i> RECENT CAPTURED SIGNALS (${(n.sample_posts || []).length})
                    </div>
                    ${samplePostsHtml}
                </div>

                <div style="display: flex; gap: 8px; margin-top: 10px;">
                    <button class="btn btn-sm btn-outline" style="flex: 1;" onclick="drillDownNarrative('${n.id}')">
                        <i class="fa-solid fa-filter"></i> View Posts in Triage
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

function drillDownNarrative(narrativeId) {
    switchTab('triage');
    const searchInput = document.getElementById('triage-search');
    if (searchInput) {
        searchInput.value = narrativeId;
        loadTriagePosts();
    }
}
