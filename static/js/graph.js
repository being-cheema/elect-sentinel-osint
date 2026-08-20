/**
 * Interactive Propagation & Actor Network Graph Engine
 * Canvas-based physics simulation with zoom/pan, dragging, and node inspector.
 */

let canvas, ctx;
let nodes = [];
let links = [];
let isSimulating = false;
let animFrameId = null;

// Transform State
let scale = 1.0;
let panX = 0;
let panY = 0;
let isDraggingCanvas = false;
let dragStartX = 0;
let dragStartY = 0;
let draggedNode = null;
let hoveredNode = null;

async function initNetworkGraph() {
    canvas = document.getElementById('network-canvas');
    if (!canvas) return;

    ctx = canvas.getContext('2d');
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Attach interaction listeners
    setupCanvasListeners();

    try {
        const res = await fetch('/api/network');
        const data = await res.json();

        // Update sidebar telemetry
        document.getElementById('graph-stat-nodes').textContent = data.metrics.total_nodes || 0;
        document.getElementById('graph-stat-edges').textContent = data.metrics.total_edges || 0;
        document.getElementById('graph-stat-cib').textContent = data.metrics.cib_swarms_detected || 0;

        // Render top hubs
        const hubList = document.getElementById('graph-top-hubs');
        if (hubList && data.metrics.top_hubs) {
            hubList.innerHTML = data.metrics.top_hubs.map(h => `
                <div class="hub-item" onclick="selectGraphNode('${h.node}')">
                    <span>${escapeHtml(h.node)}</span>
                    <strong class="text-cyan">${h.connections} links</strong>
                </div>
            `).join('');
        }

        // Initialize node positions
        const width = canvas.width;
        const height = canvas.height;

        nodes = data.nodes.map(n => ({
            ...n,
            x: (width / 2) + (Math.random() - 0.5) * 350,
            y: (height / 2) + (Math.random() - 0.5) * 300,
            vx: 0,
            vy: 0,
            radius: n.size || 12
        }));

        // Map link endpoints to node objects
        const nodeMap = new Map(nodes.map(n => [n.id, n]));
        links = data.links.map(l => ({
            ...l,
            sourceNode: nodeMap.get(l.source),
            targetNode: nodeMap.get(l.target)
        })).filter(l => l.sourceNode && l.targetNode);

        // Reset transform & start simulation
        panX = 0;
        panY = 0;
        scale = 1.0;
        isSimulating = true;
        if (animFrameId) cancelAnimationFrame(animFrameId);
        runSimulationLoop();

    } catch (err) {
        console.error("Failed to load network:", err);
    }
}

function resizeCanvas() {
    if (!canvas) return;
    const rect = canvas.parentElement.getBoundingClientRect();
    canvas.width = rect.width;
    canvas.height = rect.height;
}

function runSimulationLoop() {
    if (!isSimulating) return;

    // Physics step
    const cx = canvas.width / 2;
    const cy = canvas.height / 2;
    const kRepulsion = 1200;
    const kSpring = 0.04;
    const springLength = 80;
    const damping = 0.82;

    // 1. Repulsion between all node pairs
    for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
            const n1 = nodes[i];
            const n2 = nodes[j];
            const dx = n2.x - n1.x;
            const dy = n2.y - n1.y;
            const distSq = dx * dx + dy * dy + 100;
            const dist = Math.sqrt(distSq);
            const force = kRepulsion / distSq;
            const fx = (dx / dist) * force;
            const fy = (dy / dist) * force;

            n1.vx -= fx;
            n1.vy -= fy;
            n2.vx += fx;
            n2.vy += fy;
        }
    }

    // 2. Spring force along links
    for (let i = 0; i < links.length; i++) {
        const l = links[i];
        const n1 = l.sourceNode;
        const n2 = l.targetNode;
        const dx = n2.x - n1.x;
        const dy = n2.y - n1.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const disp = dist - springLength;
        const force = kSpring * disp;
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;

        n1.vx += fx;
        n1.vy += fy;
        n2.vx -= fx;
        n2.vy -= fy;
    }

    // 3. Centering force & update positions
    for (let i = 0; i < nodes.length; i++) {
        const n = nodes[i];
        if (n === draggedNode) continue; // Don't move actively dragged node

        n.vx += (cx - n.x) * 0.002;
        n.vy += (cy - n.y) * 0.002;

        n.vx *= damping;
        n.vy *= damping;

        n.x += n.vx;
        n.y += n.vy;
    }

    // Render Canvas
    drawGraph();

    animFrameId = requestAnimationFrame(runSimulationLoop);
}

function drawGraph() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    ctx.save();
    ctx.translate(panX, panY);
    ctx.scale(scale, scale);

    // Draw Links
    for (let i = 0; i < links.length; i++) {
        const l = links[i];
        ctx.beginPath();
        ctx.moveTo(l.sourceNode.x, l.sourceNode.y);
        ctx.lineTo(l.targetNode.x, l.targetNode.y);

        if (l.type === 'COORDINATED_SWARM') {
            ctx.strokeStyle = 'rgba(239, 68, 68, 0.75)';
            ctx.lineWidth = 2.5;
            ctx.setLineDash([4, 4]);
        } else if (l.type === 'POSTED_IN') {
            ctx.strokeStyle = 'rgba(6, 182, 212, 0.35)';
            ctx.lineWidth = 1.2;
            ctx.setLineDash([]);
        } else {
            ctx.strokeStyle = 'rgba(168, 85, 247, 0.3)';
            ctx.lineWidth = 1.0;
            ctx.setLineDash([]);
        }
        ctx.stroke();
    }
    ctx.setLineDash([]);

    // Draw Nodes
    for (let i = 0; i < nodes.length; i++) {
        const n = nodes[i];
        const isHovered = (n === hoveredNode);

        ctx.beginPath();
        ctx.arc(n.x, n.y, n.radius * (isHovered ? 1.3 : 1), 0, Math.PI * 2);
        ctx.fillStyle = n.color || '#3b82f6';
        ctx.fill();

        ctx.strokeStyle = isHovered ? '#ffffff' : 'rgba(255, 255, 255, 0.3)';
        ctx.lineWidth = isHovered ? 2.5 : 1;
        ctx.stroke();

        // Node Label
        ctx.font = `${isHovered ? 'bold ' : ''}10px 'JetBrains Mono', monospace`;
        ctx.fillStyle = '#ffffff';
        ctx.textAlign = 'center';
        ctx.fillText(n.label, n.x, n.y + n.radius + 12);
    }

    ctx.restore();
}

function setupCanvasListeners() {
    canvas.onmousedown = (e) => {
        const mouse = getCanvasMousePos(e);
        const clickedNode = findNodeAt(mouse.x, mouse.y);

        if (clickedNode) {
            draggedNode = clickedNode;
            selectNode(clickedNode);
        } else {
            isDraggingCanvas = true;
            dragStartX = e.clientX - panX;
            dragStartY = e.clientY - panY;
        }
    };

    window.onmousemove = (e) => {
        if (!canvas) return;
        const rect = canvas.getBoundingClientRect();
        if (e.clientX < rect.left || e.clientX > rect.right || e.clientY < rect.top || e.clientY > rect.bottom) {
            return;
        }

        const mouse = getCanvasMousePos(e);
        hoveredNode = findNodeAt(mouse.x, mouse.y);

        if (draggedNode) {
            draggedNode.x = mouse.x;
            draggedNode.y = mouse.y;
            draggedNode.vx = 0;
            draggedNode.vy = 0;
        } else if (isDraggingCanvas) {
            panX = e.clientX - dragStartX;
            panY = e.clientY - dragStartY;
        }
    };

    window.onmouseup = () => {
        draggedNode = null;
        isDraggingCanvas = false;
    };

    canvas.onwheel = (e) => {
        e.preventDefault();
        const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
        zoomGraph(zoomFactor);
    };
}

function getCanvasMousePos(e) {
    const rect = canvas.getBoundingClientRect();
    const clientX = e.clientX - rect.left;
    const clientY = e.clientY - rect.top;
    return {
        x: (clientX - panX) / scale,
        y: (clientY - panY) / scale
    };
}

function findNodeAt(x, y) {
    for (let i = nodes.length - 1; i >= 0; i--) {
        const n = nodes[i];
        const dx = n.x - x;
        const dy = n.y - y;
        if (Math.sqrt(dx * dx + dy * dy) <= n.radius + 4) {
            return n;
        }
    }
    return null;
}

function zoomGraph(factor) {
    scale = Math.max(0.4, Math.min(3.0, scale * factor));
}

function selectNode(node) {
    const card = document.getElementById('selected-node-card');
    if (!card) return;

    if (node.type === 'narrative') {
        card.innerHTML = `
            <div style="font-size: 11px; font-family: var(--font-mono); color: var(--crimson); margin-bottom: 4px;">[DISINFO NARRATIVE]</div>
            <h4 style="color: #fff; font-size: 13px; margin-bottom: 6px;">${escapeHtml(node.label)}</h4>
            <div class="meta-item"><span>Category:</span> <strong>${node.category}</strong></div>
            <div class="meta-item"><span>Lifecycle:</span> <span class="badge badge-${node.lifecycle}">${node.lifecycle}</span></div>
            <div class="meta-item"><span>Confusion Index:</span> <strong class="text-crimson">${node.confusion}/100</strong></div>
        `;
    } else if (node.type === 'account') {
        const botPct = ((node.bot_probability || 0) * 100).toFixed(0);
        card.innerHTML = `
            <div style="font-size: 11px; font-family: var(--font-mono); color: ${botPct > 50 ? 'var(--crimson)' : 'var(--emerald)'}; margin-bottom: 4px;">
                [${botPct > 50 ? 'SUSPECT BOT / ASTROTURF' : 'ORGANIC ACCOUNT'}]
            </div>
            <h4 style="color: #fff; font-size: 13px; margin-bottom: 6px;">${escapeHtml(node.label)}</h4>
            <div class="meta-item"><span>Platform:</span> <strong>${node.platform}</strong></div>
            <div class="meta-item"><span>Followers:</span> <strong>${node.followers}</strong></div>
            <div class="meta-item"><span>Bot Probability:</span> <strong class="${botPct > 50 ? 'text-crimson' : 'text-emerald'}">${botPct}%</strong></div>
        `;
    } else {
        card.innerHTML = `
            <div style="font-size: 11px; font-family: var(--font-mono); color: var(--purple); margin-bottom: 4px;">[HASHTAG CLUSTER]</div>
            <h4 style="color: #fff; font-size: 13px;">${escapeHtml(node.label)}</h4>
        `;
    }
}

function selectGraphNode(nodeId) {
    const node = nodes.find(n => n.id === nodeId);
    if (node) {
        selectNode(node);
        // Center on node
        panX = (canvas.width / 2) - node.x * scale;
        panY = (canvas.height / 2) - node.y * scale;
    }
}
