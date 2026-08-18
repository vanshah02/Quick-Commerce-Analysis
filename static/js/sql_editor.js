let currentStudioData = null;

async function loadStudioQueries() {
    try {
        const res = await fetch('/api/playground_queries');
        const { data } = await res.json();
        
        const list = document.getElementById('query-library');
        list.innerHTML = '';
        
        data.forEach(q => {
            const li = document.createElement('li');
            li.textContent = q.title;
            li.addEventListener('click', () => {
                document.getElementById('sql-editor').value = q.sql;
            });
            list.appendChild(li);
        });
    } catch(e) {
        console.error("Failed to load studio queries", e);
    }
}

async function executeStudioQuery() {
    const sql = document.getElementById('sql-editor').value;
    if (!sql.trim()) return;
    
    const statusEl = document.getElementById('studio-status');
    statusEl.textContent = 'Running...';
    statusEl.style.color = 'inherit';
    
    const startTime = performance.now();
    
    try {
        const res = await fetch('/api/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sql })
        });
        
        const data = await res.json();
        const duration = (performance.now() - startTime).toFixed(1);
        
        if (data.status === 'success') {
            currentStudioData = data.data;
            statusEl.textContent = `Success: ${currentStudioData.length} rows returned in ${duration}ms`;
            statusEl.style.color = '#10b981';
            renderStudioTable(currentStudioData);
        } else {
            currentStudioData = null;
            statusEl.textContent = `Error: ${data.message}`;
            statusEl.style.color = '#ef4444';
            renderStudioTable([]);
        }
    } catch(e) {
        currentStudioData = null;
        statusEl.textContent = `Execution failed`;
        statusEl.style.color = '#ef4444';
        renderStudioTable([]);
    }
}

function renderStudioTable(data) {
    const thead = document.querySelector('#table-studio thead');
    const tbody = document.querySelector('#table-studio tbody');
    
    thead.innerHTML = '';
    tbody.innerHTML = '';
    
    if (!data || data.length === 0) return;
    
    // Headers
    const keys = Object.keys(data[0]);
    const trHead = document.createElement('tr');
    keys.forEach(k => {
        const th = document.createElement('th');
        th.textContent = k;
        trHead.appendChild(th);
    });
    thead.appendChild(trHead);
    
    // Rows
    data.forEach(row => {
        const tr = document.createElement('tr');
        keys.forEach(k => {
            const td = document.createElement('td');
            td.textContent = row[k] !== null ? row[k] : 'NULL';
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
    });
}

function exportStudioResults() {
    if (!currentStudioData || currentStudioData.length === 0) {
        alert("No results to export!");
        return;
    }
    
    const keys = Object.keys(currentStudioData[0]);
    let csvContent = "data:text/csv;charset=utf-8,";
    
    // Header
    csvContent += keys.join(",") + "\r\n";
    
    // Rows
    currentStudioData.forEach(row => {
        const values = keys.map(k => {
            let val = row[k] !== null ? row[k] : '';
            // Escape quotes
            if (typeof val === 'string') {
                val = '"' + val.replace(/"/g, '""') + '"';
            }
            return val;
        });
        csvContent += values.join(",") + "\r\n";
    });
    
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "sql_results.csv");
    document.body.appendChild(link); // Required for FF
    
    link.click();
    document.body.removeChild(link);
}
