let currentSqlData = {};
let uploadedFileName = '';

document.addEventListener('DOMContentLoaded', async () => {
    // Check auth status first
    const authRes = await fetch('/api/auth_status');
    const authData = await authRes.json();
    
    if (!authData.logged_in) {
        document.getElementById('login-overlay').style.display = 'flex';
        return; // Stop initialization until logged in
    } else {
        document.getElementById('login-overlay').style.display = 'none';
        document.getElementById('user-profile').style.display = 'flex';
        document.getElementById('user-name').textContent = authData.user.name;
        document.getElementById('user-avatar').src = authData.user.picture;
    }

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
        
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const res = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            const data = await res.json();
            
            if(data.status === 'multiple_sheets') {
                statusEl.innerHTML = '';
                document.getElementById('sheet-selector-container').style.display = 'block';
                document.getElementById('btn-upload-submit').style.display = 'none';
                
                const sel = document.getElementById('sheet-selector');
                sel.innerHTML = '';
                data.sheets.forEach(s => {
                    const opt = document.createElement('option');
                    opt.value = s;
                    opt.textContent = s;
                    sel.appendChild(opt);
                });
                uploadedFileName = data.filename;
            } else if(data.status === 'success') {
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
    
    document.getElementById('btn-load-sheet').addEventListener('click', async () => {
        const sheet = document.getElementById('sheet-selector').value;
        const statusEl = document.getElementById('upload-status');
        statusEl.innerHTML = '<span style="color: #64748b;">Loading sheet...</span>';
        
        try {
            const res = await fetch('/api/upload_sheet', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ sheet_name: sheet, filename: uploadedFileName })
            });
            const data = await res.json();
            if(data.status === 'success') {
                statusEl.innerHTML = '<span style="color: #10b981;">' + data.message + '</span>';
                document.getElementById('current-db').textContent = uploadedFileName + ' (' + sheet + ')';
                setTimeout(async () => {
                    closeModal('modal-upload');
                    statusEl.innerHTML = '';
                    document.getElementById('sheet-selector-container').style.display = 'none';
                    document.getElementById('btn-upload-submit').style.display = 'inline-block';
                    await initSchemaAndFilters();
                    fetchAnalytics();
                }, 1500);
            } else {
                statusEl.innerHTML = '<span style="color: #ef4444;">' + data.message + '</span>';
            }
        } catch (e) {
            statusEl.innerHTML = '<span style="color: #ef4444;">Error loading sheet.</span>';
        }
    });
});

async function initSchemaAndFilters() {
    try {
        const res = await fetch('/api/filters');
        const { data } = await res.json();
        
        const container = document.getElementById('dynamic-filters');
        container.innerHTML = '';
        
        if (!data) return;
        
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
        if (res.status === 401) {
            window.location.reload();
            return;
        }
        
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
        
        const toggleWidget = (id, show) => {
            document.getElementById(id).style.display = show ? 'block' : 'none';
        };

        // Render Group Contribution
        if (activeWidgets.includes('group_contribution')) {
            toggleWidget('card-group-contribution', true);
            const wdata = data.group_contribution;
            document.getElementById('title-group-contribution').textContent = `${wdata.measure.replace(/_/g, ' ')} by ${wdata.dimension.replace(/_/g, ' ')}`;
            try { renderGroupContributionChart('chart-group-contribution', wdata); } catch(e) {}
        } else { toggleWidget('card-group-contribution', false); }

        // Render RFM Analysis
        if (activeWidgets.includes('rfm')) {
            toggleWidget('card-rfm', true);
            document.getElementById('table-rfm').style.display = 'table';
            document.getElementById('table-rfm-top').style.display = 'table';
            document.getElementById('msg-rfm').style.display = 'none';
            const wdata = data.rfm;
            document.getElementById('title-rfm').textContent = wdata.title;
            
            const thead = document.querySelector('#table-rfm thead');
            thead.innerHTML = '<tr>' + wdata.headers.map(h => `<th>${h}</th>`).join('') + '</tr>';
            const tbody = document.querySelector('#table-rfm tbody');
            tbody.innerHTML = wdata.rows.map(row => `
                <tr>
                    <td>${row.segment}</td>
                    <td>${Number(row.customer_count).toLocaleString()}</td>
                    <td>₹${Number(row.avg_monetary).toLocaleString('en-IN', {maximumFractionDigits: 0})}</td>
                </tr>
            `).join('');
            
            const tophead = document.querySelector('#table-rfm-top thead');
            tophead.innerHTML = '<tr>' + wdata.top_headers.map(h => `<th>${h}</th>`).join('') + '</tr>';
            const toptbody = document.querySelector('#table-rfm-top tbody');
            toptbody.innerHTML = wdata.top_rows.map(row => `
                <tr>
                    <td>${row.customer_id}</td>
                    <td>₹${Number(row.monetary).toLocaleString('en-IN', {maximumFractionDigits: 0})}</td>
                </tr>
            `).join('');
            
        } else { 
            toggleWidget('card-rfm', true);
            document.getElementById('table-rfm').style.display = 'none';
            document.getElementById('table-rfm-top').style.display = 'none';
            const msg = document.getElementById('msg-rfm');
            msg.style.display = 'block';
            msg.textContent = 'RFM analysis requires a customer ID and date column — not available in this dataset.';
        }

        // Render Churn
        if (activeWidgets.includes('churn')) {
            toggleWidget('card-churn', true);
            document.getElementById('table-churn').style.display = 'table';
            document.getElementById('msg-churn').style.display = 'none';
            const wdata = data.churn;
            document.getElementById('title-churn').textContent = wdata.title;
            
            const thead = document.querySelector('#table-churn thead');
            thead.innerHTML = '<tr>' + wdata.headers.map(h => `<th>${h}</th>`).join('') + '</tr>';
            const tbody = document.querySelector('#table-churn tbody');
            tbody.innerHTML = wdata.rows.map(row => `
                <tr>
                    <td>${row.location}</td>
                    <td>${row.status}</td>
                    <td>${Number(row.customer_count).toLocaleString()}</td>
                </tr>
            `).join('');
        } else {
            toggleWidget('card-churn', true);
            document.getElementById('table-churn').style.display = 'none';
            const msg = document.getElementById('msg-churn');
            msg.style.display = 'block';
            msg.textContent = 'Churn analysis requires a customer ID and date column — not available in this dataset.';
        }

        // Render Heatmap
        if (activeWidgets.includes('heatmap')) {
            toggleWidget('card-heatmap', true);
            document.getElementById('map-container').style.display = 'block';
            document.getElementById('msg-heatmap').style.display = 'none';
            const wdata = data.heatmap;
            document.getElementById('title-heatmap').textContent = wdata.title;
            try { 
                if (typeof renderHeatmap === 'function') renderHeatmap(wdata.rows); 
            } catch(e) { console.error(e); }
        } else {
            toggleWidget('card-heatmap', true);
            document.getElementById('map-container').style.display = 'none';
            const msg = document.getElementById('msg-heatmap');
            msg.style.display = 'block';
            msg.textContent = 'Delivery Hotspots requires a location column (city/area) — not available in this dataset.';
        }

        // Render Top Items by Quantity
        if (activeWidgets.includes('top_items_qty')) {
            toggleWidget('card-top-items-qty', true);
            const wdata = data.top_items_qty;
            document.getElementById('title-top-items-qty').textContent = wdata.title;
            const thead = document.querySelector('#table-top-items-qty thead tr');
            thead.innerHTML = wdata.headers.map(h => `<th>${h}</th>`).join('');
            
            const tbody = document.querySelector('#table-top-items-qty tbody');
            tbody.innerHTML = wdata.rows.map(row => `
                <tr>
                    <td>${row.item}</td>
                    <td>${Number(row.total_quantity).toLocaleString()}</td>
                </tr>
            `).join('');
        } else { toggleWidget('card-top-items-qty', false); }

        // Render Top Items by Frequency
        if (activeWidgets.includes('top_items_freq')) {
            toggleWidget('card-top-items-freq', true);
            const wdata = data.top_items_freq;
            document.getElementById('title-top-items-freq').textContent = wdata.title;
            const thead = document.querySelector('#table-top-items-freq thead tr');
            thead.innerHTML = wdata.headers.map(h => `<th>${h}</th>`).join('');
            
            const tbody = document.querySelector('#table-top-items-freq tbody');
            tbody.innerHTML = wdata.rows.map(row => `
                <tr>
                    <td>${row.item}</td>
                    <td>${Number(row.order_frequency).toLocaleString()}</td>
                </tr>
            `).join('');
        } else { toggleWidget('card-top-items-freq', false); }

        // Render Most Profitable Dishes
        if (activeWidgets.includes('top_items_profit')) {
            toggleWidget('card-top-items-profit', true);
            const wdata = data.top_items_profit;
            document.getElementById('title-top-items-profit').textContent = wdata.title;
            const thead = document.querySelector('#table-top-items-profit thead tr');
            thead.innerHTML = wdata.headers.map(h => `<th>${h}</th>`).join('');
            
            const tbody = document.querySelector('#table-top-items-profit tbody');
            tbody.innerHTML = wdata.rows.map((row, idx) => `
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
            try { renderTimeSeriesChart('chart-time-series', wdata); } catch(e) {}
        } else { toggleWidget('card-time-series', false); }

        // Render Best Combos
        if (activeWidgets.includes('best_combos')) {
            toggleWidget('card-best-combos', true);
            const wdata = data.best_combos;
            document.getElementById('title-best-combos').textContent = wdata.title;
            const thead = document.querySelector('#table-best-combos thead tr');
            thead.innerHTML = wdata.headers.map(h => `<th>${h}</th>`).join('');
            
            const tbody = document.querySelector('#table-best-combos tbody');
            tbody.innerHTML = wdata.rows.map((row, idx) => `
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
