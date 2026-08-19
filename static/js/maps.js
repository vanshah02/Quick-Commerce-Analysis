let leafletMap = null;
let heatLayer = null;

const CITY_COORDS = {
    'mumbai': [19.0760, 72.8777],
    'delhi': [28.7041, 77.1025],
    'bangalore': [12.9716, 77.5946],
    'bengaluru': [12.9716, 77.5946],
    'hyderabad': [17.3850, 78.4867],
    'ahmedabad': [23.0225, 72.5714],
    'chennai': [13.0827, 80.2707],
    'kolkata': [22.5726, 88.3639],
    'surat': [21.1702, 72.8311],
    'pune': [18.5204, 73.8567],
    'jaipur': [26.9124, 75.7873],
    'lucknow': [26.8467, 80.9462],
    'kanpur': [26.4499, 80.3319],
    'nagpur': [21.1458, 79.0882],
    'indore': [22.7196, 75.8577],
    'thane': [19.2183, 72.9781],
    'bhopal': [23.2599, 77.4126],
    'visakhapatnam': [17.6868, 83.2185],
    'pimpri-chinchwad': [18.6298, 73.7997],
    'patna': [25.5941, 85.1376],
    'vadodara': [22.3072, 73.1812],
    'ghaziabad': [28.6692, 77.4538],
    'ludhiana': [30.9010, 75.8573],
    'agra': [27.1767, 78.0081],
    'nashik': [20.0110, 73.7903],
    'faridabad': [28.4089, 77.3178],
    'meerut': [28.9845, 77.7064],
    'rajkot': [22.3039, 70.8022],
    'kalyan-dombivli': [19.2403, 73.1305],
    'vasai-virar': [19.3919, 72.8397],
    'varanasi': [25.3176, 82.9739],
    'srinagar': [34.0837, 74.7973],
    'aurangabad': [19.8762, 75.3433],
    'dhanbad': [23.7957, 86.4304],
    'amritsar': [31.6340, 74.8723],
    'navi mumbai': [19.0330, 73.0297],
    'allahabad': [25.4358, 81.8463],
    'howrah': [22.5958, 88.2636],
    'ranchi': [23.3441, 85.3096],
    'gwalior': [26.2124, 78.1772],
    'jabalpur': [23.1815, 79.9864],
    'coimbatore': [11.0168, 76.9558],
    'vijayawada': [16.5062, 80.6480],
    'jodhpur': [26.2389, 73.0243],
    'madurai': [9.9252, 78.1198],
    'raipur': [21.2514, 81.6296],
    'kota': [25.2138, 75.8648],
    'chandigarh': [30.7333, 76.7794],
    'guwahati': [26.1445, 91.7362],
    'solapur': [17.6599, 75.9064],
    'hubli-dharwad': [15.3647, 75.1240],
    'bareilly': [28.3670, 79.4304]
};

function renderHeatmap(dataRows) {
    if (!document.getElementById('map-container')) return;
    
    // Initialize map if not done
    if (!leafletMap) {
        leafletMap = L.map('map-container').setView([20.5937, 78.9629], 5); // Center of India
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(leafletMap);
    }

    // Clear previous heat layer
    if (heatLayer) {
        leafletMap.removeLayer(heatLayer);
    }

    const heatPoints = [];
    let maxDensity = 0;

    // Build data points
    dataRows.forEach(row => {
        if (!row.location) return;
        const locName = row.location.toLowerCase().trim();
        const coords = CITY_COORDS[locName];
        
        if (coords) {
            const density = parseInt(row.order_density) || 0;
            if (density > maxDensity) maxDensity = density;
            heatPoints.push([coords[0], coords[1], density]);
        } else {
            // Pseudo-random cluster near the center for unknown locations just to show something
            // Wait, maybe we just ignore unknown locations.
        }
    });

    if (heatPoints.length > 0) {
        // Adjust bounds to fit points
        const bounds = L.latLngBounds(heatPoints.map(p => [p[0], p[1]]));
        leafletMap.fitBounds(bounds, { padding: [50, 50], maxZoom: 12 });

        heatLayer = L.heatLayer(heatPoints, {
            radius: 25,
            blur: 15,
            maxZoom: 12,
            max: maxDensity > 0 ? maxDensity : 1.0,
            gradient: {0.4: 'blue', 0.6: 'cyan', 0.7: 'lime', 0.8: 'yellow', 1.0: 'red'}
        }).addTo(leafletMap);
        
        // Timeout to fix leaflet sizing issues when unhidden
        setTimeout(() => {
            leafletMap.invalidateSize();
        }, 100);
    } else {
        // Reset view to India if no points match
        leafletMap.setView([20.5937, 78.9629], 5);
        setTimeout(() => {
            leafletMap.invalidateSize();
        }, 100);
    }
}
