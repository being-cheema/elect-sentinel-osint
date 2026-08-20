/**
 * Ground Truth Knowledge Base Controller
 * Manages verified election regulations, statutory rules, and counter-messaging templates.
 */

async function loadGroundTruthFacts() {
    const grid = document.getElementById('facts-cards-grid');
    if (!grid) return;

    grid.innerHTML = `
        <div class="empty-state" style="grid-column: 1 / -1;">
            <i class="fa-solid fa-spinner fa-spin fa-2x text-cyan"></i>
            <p style="margin-top: 10px;">Loading verified statutory facts...</p>
        </div>
    `;

    try {
        const res = await fetch('/api/facts');
        const facts = await res.json();

        if (!facts || facts.length === 0) {
            grid.innerHTML = `<div class="empty-state" style="grid-column: 1 / -1;">No ground truth records found.</div>`;
            return;
        }

        grid.innerHTML = facts.map(f => `
            <div class="fact-card">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div>
                        <span class="badge" style="background: rgba(6, 182, 212, 0.15); color: var(--cyan); border: 1px solid var(--cyan);">
                            ${escapeHtml(f.id)} // ${escapeHtml(f.category.replace(/_/g, ' ').toUpperCase())}
                        </span>
                        <h3 style="font-size: 14px; font-weight: 700; color: #fff; margin-top: 8px;">
                            ${escapeHtml(f.topic)}
                        </h3>
                    </div>
                </div>

                <div class="fact-rule-box">
                    <div style="font-size: 10px; font-family: var(--font-mono); color: var(--cyan); margin-bottom: 4px;">
                        <i class="fa-solid fa-gavel"></i> OFFICIAL STATUTORY RULE:
                    </div>
                    ${escapeHtml(f.official_rule)}
                </div>

                <div class="fact-debunk-box">
                    <div style="font-size: 10px; font-family: var(--font-mono); color: var(--emerald); margin-bottom: 4px;">
                        <i class="fa-solid fa-bullhorn"></i> RAPID REBUTTAL TEMPLATE:
                    </div>
                    ${escapeHtml(f.debunk_template)}
                </div>

                <div style="display: flex; justify-content: space-between; align-items: center; font-size: 10px; font-family: var(--font-mono); color: var(--text-muted); margin-top: 4px;">
                    <span><i class="fa-solid fa-building-columns"></i> ${escapeHtml(f.verification_source)}</span>
                    <button class="btn btn-sm btn-outline" onclick="copyDebunk('${escapeHtml(f.debunk_template)}')">
                        <i class="fa-solid fa-copy"></i> Copy Fact Rebuttal
                    </button>
                </div>
            </div>
        `).join('');

    } catch (err) {
        console.error("Failed to load ground truth:", err);
    }
}

function copyDebunk(text) {
    navigator.clipboard.writeText(text);
    showToast("Copied fact-check rebuttal to clipboard", "success");
}

function openNewFactModal() {
    document.getElementById('new-fact-modal').classList.add('active');
}

function closeNewFactModal() {
    document.getElementById('new-fact-modal').classList.remove('active');
}

async function submitNewFact() {
    const category = document.getElementById('newfact-category').value;
    const topic = document.getElementById('newfact-topic').value.trim();
    const official_rule = document.getElementById('newfact-rule').value.trim();
    const jurisdiction = document.getElementById('newfact-jurisdiction').value.trim() || 'National';
    const verification_source = document.getElementById('newfact-source').value.trim();
    const debunk_template = document.getElementById('newfact-debunk').value.trim();

    if (!topic || !official_rule || !verification_source || !debunk_template) {
        showToast("Please fill all required fields", "danger");
        return;
    }

    try {
        const res = await fetch('/api/facts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                category,
                topic,
                official_rule,
                jurisdiction,
                verification_source,
                debunk_template
            })
        });

        if (res.ok) {
            showToast("Official ground truth standard added", "success");
            closeNewFactModal();
            loadGroundTruthFacts();
        } else {
            showToast("Failed to save ground truth", "danger");
        }
    } catch (err) {
        showToast("Network error creating fact", "danger");
    }
}
