const CHART_COLORS = [
    '#E23744', '#1E293B', '#F8FAFC', '#94A3B8', '#64748B', '#CBD5E1', '#F1F5F9'
];

let instances = {};

function getOrCreateChart(canvasId, config) {
    if (instances[canvasId]) {
        instances[canvasId].destroy();
    }
    const ctx = document.getElementById(canvasId).getContext('2d');
    instances[canvasId] = new Chart(ctx, config);
    return instances[canvasId];
}

function renderGroupContributionChart(canvasId, wdata) {
    const dim = wdata.dimension;
    const labels = wdata.rows.map(d => d[dim] || 'Unknown');
    const data = wdata.rows.map(d => parseFloat(d.pct_contribution));

    const config = {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: CHART_COLORS,
                borderWidth: 1,
                borderColor: '#ffffff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'right' },
                tooltip: {
                    callbacks: {
                        label: (ctx) => ` ${ctx.label}: ${ctx.raw}%`
                    }
                }
            }
        }
    };
    
    getOrCreateChart(canvasId, config);
}

function renderTimeSeriesChart(canvasId, wdata) {
    const measureCol = 'total_' + wdata.measure;
    
    // Check if secondary dim exists
    if (!wdata.secondary_dim) {
        // Simple line chart
        const labels = wdata.rows.map(d => d.hour_of_day + ':00');
        const data = wdata.rows.map(d => d[measureCol]);
        
        getOrCreateChart(canvasId, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: wdata.measure,
                    data: data,
                    borderColor: CHART_COLORS[0],
                    backgroundColor: CHART_COLORS[0] + '20',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });
        return;
    }
    
    // Grouped by secondary dim
    const hours = [...new Set(wdata.rows.map(d => d.hour_of_day))].sort((a,b)=>a-b);
    const groups = [...new Set(wdata.rows.map(d => d[wdata.secondary_dim]))];
    
    const datasets = groups.map((g, i) => {
        const color = CHART_COLORS[i % CHART_COLORS.length];
        const gData = wdata.rows.filter(d => d[wdata.secondary_dim] === g);
        
        const dataPoints = hours.map(h => {
            const match = gData.find(d => d.hour_of_day === h);
            return match ? match[measureCol] : 0;
        });
        
        return {
            label: g,
            data: dataPoints,
            borderColor: color,
            backgroundColor: color,
            tension: 0.4
        };
    });

    const config = {
        type: 'line',
        data: {
            labels: hours.map(h => h + ':00'),
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: { legend: { position: 'top' } }
        }
    };
    
    getOrCreateChart(canvasId, config);
}
