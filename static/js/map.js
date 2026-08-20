/**
 * Geospatial Hotspots & Jurisdiction Threat Map Controller
 * Uses Leaflet.js with Dark Matter styling to map localized election confusion density.
 */

let leafletMap = null;
let mapMarkers = [];

async function initGeospatialMap() {
    const mapElem = document.getElementById('leaflet-map');
    if (!mapElem) return;

    if (!leafletMap) {
        leafletMap = L.map('leaflet-map', {
            zoomControl: true,
            attributionControl: false
        }).setView([38.5, -96.0], 4);

        // Dark Matter map tiles
        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            maxZoom: 18,
            subdomains: 'abcd'
        }).addTo(leafletMap);
    } else {
        setTimeout(() => leafletMap.invalidateSize(), 150);
    }

    try {
        const res = await fetch('/api/geospatial');
        const hotspots = await res.json();

        // Clear existing markers
        mapMarkers.forEach(m => leafletMap.removeLayer(m));
        mapMarkers = [];

        // Render Hotspots & List
        const listElem = document.getElementById('jurisdiction-list');
        let listHtml = '';

        hotspots.forEach(h => {
            const confColor = h.avg_confusion > 75 ? '#ef4444' : (h.avg_confusion > 50 ? '#f59e0b' : '#06b6d4');
            const radius = Math.max(12, Math.min(28, 10 + (h.post_count * 2.5)));

            // Circle marker
            const circle = L.circleMarker([h.lat, h.lon], {
                radius: radius,
                fillColor: confColor,
                color: '#ffffff',
                weight: 1.5,
                opacity: 0.9,
                fillOpacity: 0.65
            }).addTo(leafletMap);

            circle.bindPopup(`
                <div style="font-family: var(--font-main); color: #fff; padding: 4px;">
                    <h4 style="color: ${confColor}; font-size: 13px; margin-bottom: 4px;">${escapeHtml(h.district)}</h4>
                    <div style="font-size: 11px; margin-bottom: 3px;"><strong>Mean Confusion:</strong> ${h.avg_confusion}/100</div>
                    <div style="font-size: 11px; margin-bottom: 3px;"><strong>Signal Count:</strong> ${h.post_count} posts</div>
                    <div style="font-size: 11px; margin-bottom: 6px;"><strong>Top Threat Vector:</strong> ${escapeHtml(h.primary_category.replace(/_/g, ' '))}</div>
                    <button onclick="drillDownJurisdiction('${escapeHtml(h.district)}')" style="background: ${confColor}; border:none; padding: 4px 8px; border-radius: 4px; color: #000; font-weight: 700; font-size: 10px; cursor: pointer;">
                        Inspect in Triage
                    </button>
                </div>
            `);

            mapMarkers.push(circle);

            // Add to sidebar list
            listHtml += `
                <div class="jurisdiction-card" onclick="panToDistrict(${h.lat}, ${h.lon})">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                        <strong style="color: #fff; font-size: 12px;">${escapeHtml(h.district)}</strong>
                        <span class="badge" style="background: ${confColor}; color: #000; font-weight: 800;">${h.avg_confusion}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; font-size: 11px; color: var(--text-muted); font-family: var(--font-mono);">
                        <span>${h.post_count} signals</span>
                        <span>${escapeHtml(h.primary_category.replace(/_/g, ' '))}</span>
                    </div>
                </div>
            `;
        });

        if (listElem) {
            listElem.innerHTML = listHtml || `<div class="empty-state">No localized hotspots detected.</div>`;
        }

    } catch (err) {
        console.error("Failed to load geospatial data:", err);
    }
}

function panToDistrict(lat, lon) {
    if (leafletMap) {
        leafletMap.flyTo([lat, lon], 7, { duration: 1.2 });
    }
}

function drillDownJurisdiction(district) {
    switchTab('triage');
    const searchInput = document.getElementById('triage-search');
    if (searchInput) {
        searchInput.value = district;
        loadTriagePosts();
    }
}
