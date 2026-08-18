let currentSqlData = {};

document.addEventListener('DOMContentLoaded', async () => {
    // 1. Fetch schema and init filters
    await initSchemaAndFilters();
    
    // 2. Fetch analytics
    fetchAnalytics();
    
    document.getElementById('apply-filters').addEventListener('click', fetchAnalytics);
    
    document.getElementById('btn-upload').addEventListener('click', () => {
        document.getElementById('modal-upload').style.display = 'flex';
    });
    
    document.getElementById('btn-reset').addEventListener('click', async () => {
        if(confirm("Are you sure you want to reset the database to the default dataset?")) {
            try {
                const res = await fetch('/api/reset', { method: 'POST' });
                const data = await res.json();
                if(data.status === 'success') {
                    alert('Database reset successfully!');
                    document.getElementById('current-db').textContent = 'Zomato_Orders.csv';
                    await initSchemaAndFilters();
                    fetchAnalytics();
                } else {
                    alert('Error: ' + data.message);
                }
            } catch(e) {
                console.error(e);
            }
        }
    });

    document.getElementById('upload-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const fileInput = document.getElementById('csv-file');
        if(!fileInput.files.length) return;
        
        const file = fileInput.files[0];
        
        const statusEl = document.getElementById('upload-status');
        statusEl.innerHTML = '<span style="color: #64748b;">Uploading and rebuilding database...</span>';
        
        try {
            const res = await fetch('/api/upload', {
                method: 'POST',
                headers: { 'Content-Type': 'application/octet-stream' },
                body: file
            });
            const data = await res.json();
            if(data.status === 'success') {
                statusEl.innerHTML = '<span style="color: #10b981;">' + data.message + '</span>';
                document.getElementById('current-db').textContent = file.name;
                setTimeout(async () => {
                    closeModal('modal-upload');
                    statusEl.innerHTML = '';
                    await initSchemaAndFilters();
                    fetchAnalytics();
                }, 1500);
            } else {
                statusEl.innerHTML = '<span style="color: #ef4444;">' + data.message + '</span>';
            }
        } catch(e) {
            statusEl.innerHTML = '<span style="color: #ef4444;">Error uploading file.</span>';
        }
    });
});

async function initSchemaAndFilters() {
    try {
        const res = await fetch('/api/filters');
        const { data } = await res.json();
        
        const container = document.getElementById('dynamic-filters');
        container.innerHTML = '';
        
        for (const [col, details] of Object.entries(data)) {
            const div = document.createElement('div');
            div.className = 'filter-group';
            div.innerHTML = `
                <label for="filter-${col}">${details.label}</label>
                <select id="filter-${col}" data-col="${col}">
                    <option value="All">All ${details.label}s</option>
                </select>
            `;
            container.appendChild(div);
            
            const select = document.getElementById(`filter-${col}`);
            details.values.forEach(val => {
                const opt = document.createElement('option');
                opt.value = val;
                opt.textContent = val;
                select.appendChild(opt);
            });
        }
    } catch(e) {
        console.error("Failed to load filters", e);
    }
}

function getFilters() {
    const params = new URLSearchParams();
    const selects = document.querySelectorAll('#dynamic-filters select');
    selects.forEach(sel => {
        if (sel.value && sel.value !== "All") {
            params.append(sel.dataset.col, sel.value);
        }
    });
    return params.toString();
}

async function fetchAnalytics() {
    try {
        const qs = getFilters();
        const res = await fetch('/api/analytics?' + qs);
        const { data } = await res.json();
        
        currentSqlData = data.sql_used || {};
        const activeWidgets = data.available_widgets || [];
        
        // Render KPIs dynamically
        const kpiRibbon = document.getElementById('kpi-ribbon');
        kpiRibbon.innerHTML = '';
        if (activeWidgets.includes('kpis') && data.kpis) {
            const btn = `<button class="btn-view-sql" onclick="viewSql('kpis')" style="position:absolute; top: 1rem; right: 1rem; padding: 2px 8px; font-size: 0.7rem; background: #e2e8f0; border: none; border-radius: 4px; cursor: pointer; z-index: 10;">View SQL</button>`;
            let isFirst = true;
            for (const [key, val] of Object.entries(data.kpis)) {
                // Formatting heuristics
                let formatted = val;
                if (key.includes('sum_') || key.includes('avg_') || key.includes('total_')) {
                    if (key.includes('price') || key.includes('revenue') || key.includes('profit') || key.includes('amount')) {
                        formatted = '₹' + Number(val).toLocaleString(undefined, {minimumFractionDigits: 0, maximumFractionDigits: 2});
                    } else if (Number.isFinite(val)) {
                        formatted = Number(val).toLocaleString();
                    }
                }
                const title = key.replace(/_/g, ' ').toUpperCase();
                
                kpiRibbon.innerHTML += `
                    <div class="kpi-card" style="position:relative;">
                        ${isFirst ? btn : ''}
                        <div class="kpi-title">${title}</div>
                        <div class="kpi-value">${formatted}</div>
                    </div>
                `;
                isFirst = false;
            }
        }
        
        // Helper to toggle visibility
        const toggleWidget = (id, show) => {
            document.getElementById(id).style.display = show ? 'block' : 'none';
        };

        // Render Group Contribution
        if (activeWidgets.includes('group_contribution')) {
            toggleWidget('card-group-contribution', true);
            const wdata = data.group_contribution;
            document.getElementById('title-group-contribution').textContent = `${wdata.measure.replace(/_/g, ' ')} by ${wdata.dimension.replace(/_/g, ' ')} (Window Function)`;
            try { renderGroupContributionChart('chart-group-contribution', wdata); } catch(e) { console.error(e); }
        } else { toggleWidget('card-group-contribution', false); }

        // Render Top Items by Quantity
        if (activeWidgets.includes('top_items_qty')) {
            toggleWidget('card-top-items-qty', true);
            const wdata = data.top_items_qty.rows;
            const tbody = document.querySelector('#table-top-items-qty tbody');
            tbody.innerHTML = wdata.map(row => `
                <tr>
                    <td>${row.item}</td>
                    <td>${Number(row.total_quantity).toLocaleString()}</td>
                </tr>
            `).join('');
        } else { toggleWidget('card-top-items-qty', false); }

        // Render Top Items by Frequency
        if (activeWidgets.includes('top_items_freq')) {
            toggleWidget('card-top-items-freq', true);
            const wdata = data.top_items_freq.rows;
            const tbody = document.querySelector('#table-top-items-freq tbody');
            tbody.innerHTML = wdata.map(row => `
                <tr>
                    <td>${row.item}</td>
                    <td>${Number(row.order_frequency).toLocaleString()}</td>
                </tr>
            `).join('');
        } else { toggleWidget('card-top-items-freq', false); }

        // Render Most Profitable Dishes
        if (activeWidgets.includes('top_items_profit')) {
            toggleWidget('card-top-items-profit', true);
            const wdata = data.top_items_profit.rows;
            const tbody = document.querySelector('#table-top-items-profit tbody');
            tbody.innerHTML = wdata.map((row, idx) => `
                <tr>
                    <td>${idx + 1}</td>
                    <td>${row.item}</td>
                    <td>₹${Number(row.profit).toLocaleString('en-IN', {maximumFractionDigits: 0})}</td>
                    <td>${Number(row.margin_pct).toFixed(1)}%</td>
                </tr>
            `).join('');
        } else { toggleWidget('card-top-items-profit', false); }
        
        // Render Time Series
        if (activeWidgets.includes('time_series')) {
            toggleWidget('card-time-series', true);
            const wdata = data.time_series;
            document.getElementById('title-time-series').textContent = `Peak Activity Hours (${wdata.measure})`;
            try { renderTimeSeriesChart('chart-time-series', wdata); } catch(e) { console.error(e); }
        } else { toggleWidget('card-time-series', false); }

        // Render Best Combos
        if (activeWidgets.includes('best_combos')) {
            toggleWidget('card-best-combos', true);
            const wdata = data.best_combos.rows;
            
            const tbody = document.querySelector('#table-best-combos tbody');
            tbody.innerHTML = wdata.map((row, idx) => `
                <tr>
                    <td>${idx + 1}</td>
                    <td>${row.item_a} + ${row.item_b}</td>
                    <td>${row.times_together}</td>
                </tr>
            `).join('');
        } else { toggleWidget('card-best-combos', false); }

    } catch(e) {
        console.error("Failed to load analytics", e);
    }
}

function viewSql(key) {
    const sql = currentSqlData[key];
    if (sql) {
        document.getElementById('sql-code-block').textContent = sql;
        document.getElementById('modal-sql').style.display = 'flex';
    } else {
        alert("SQL not available for this widget.");
    }
}

function closeModal(id) {
    document.getElementById(id).style.display = 'none';
}
