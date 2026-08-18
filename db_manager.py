import sqlite3
import pandas as pd
import os
import schema_inspector
import query_builder

DB_PATH = "zomato_analytics.db"
DEFAULT_CSV = "Zomato_Orders.csv"
TABLE_NAME = "dataset"

def init_db(csv_path=DEFAULT_CSV):
    """Initializes the SQLite database from a CSV file using dynamic schema detection."""
    if not os.path.exists(csv_path):
        return False, f"CSV file not found: {csv_path}"
    
    try:
        # Load CSV
        df = pd.read_csv(csv_path)
        
        # Normalize column names (lowercase, strip whitespace)
        df.columns = df.columns.str.lower().str.strip()
        
        # Detect Schema
        schema = schema_inspector.detect_schema(df)
        
        # Coerce numeric measures safely to avoid mixed-type DB crashes
        measures = schema_inspector.get_measures(schema)
        for m in measures:
            df[m] = pd.to_numeric(df[m], errors='coerce')
        
        # Connect to SQLite
        conn = sqlite3.connect(DB_PATH)
        
        # Write to SQLite exactly as-is
        df.to_sql(TABLE_NAME, conn, index=False, if_exists='replace')
        
        # Save schema for the backend to use
        schema_inspector.save_schema(schema)
        
        conn.commit()
        conn.close()
        return True, "Database initialized successfully."
    except Exception as e:
        return False, str(e)

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def execute_query(query, params=()):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(query, params)
        rows = cur.fetchall()
        return True, [dict(row) for row in rows]
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def get_schema_summary():
    schema = schema_inspector.load_schema()
    if not schema:
        return False, "Schema not found. Please reset or upload a dataset."
        
    summary = {
        "columns": schema,
        "measures": schema_inspector.get_measures(schema),
        "dimensions": schema_inspector.get_dimensions(schema),
        "datetime_col": schema_inspector.get_datetime_column(schema),
        "id_col": schema_inspector.get_id_column(schema)
    }
    return True, summary

def get_analytics_data(filters=None):
    if filters is None:
        filters = {}
        
    schema = schema_inspector.load_schema()
    if not schema:
        return False, "Schema not initialized"
        
    data = {}
    sql_used = {}
    available_widgets = []
    
    # 1. KPIs
    query_kpis, params_kpis = query_builder.build_kpi_query(schema, filters, TABLE_NAME)
    success, res = execute_query(query_kpis, params_kpis)
    if success and res:
        data["kpis"] = res[0]
        sql_used["kpis"] = query_kpis.strip()
        available_widgets.append("kpis")
        
    dims = schema_inspector.get_dimensions(schema)
    measures = schema_inspector.get_measures(schema)
    date_col = schema_inspector.get_datetime_column(schema)
    id_col = schema_inspector.get_id_column(schema)
    
    # Check what we can build
    if dims and measures:
        # Sort dimensions by cardinality descending (e.g. item=100, city=10, zone=4)
        dims_desc = sorted(dims, key=lambda d: schema[d]['cardinality'], reverse=True)
        high_card_dim = dims_desc[0]
        low_card_dim = dims_desc[-1]
        
        # Pick best measures
        revenue_measure = next((m for m in measures if 'revenue' in m.lower() or 'total' in m.lower()), measures[0])
        
        # 3. Group Contribution (Low cardinality, e.g. Regions/Categories)
        q, p = query_builder.build_group_contribution_query(schema, low_card_dim, revenue_measure, filters, TABLE_NAME)
        success, res = execute_query(q, p)
        if success:
            data["group_contribution"] = {
                "dimension": low_card_dim,
                "measure": revenue_measure,
                "rows": res
            }
            sql_used["group_contribution"] = q.strip()
            available_widgets.append("group_contribution")
            
    # 4. Time Series
    if date_col and measures:
        secondary_dim = next((d for d in dims if schema[d]['cardinality'] <= 10), None)
        m = measures[0]
        q, p = query_builder.build_time_series_query(schema, date_col, m, secondary_dim, filters, TABLE_NAME)
        success, res = execute_query(q, p)
        if success:
            data["time_series"] = {
                "date_col": date_col,
                "measure": m,
                "secondary_dim": secondary_dim,
                "rows": res
            }
            sql_used["time_series"] = q.strip()
            available_widgets.append("time_series")
            
    # Explicit Food Analytics Panels
    # A. Top items by quantity
    q, p = query_builder.build_top_items_by_quantity(schema, filters, TABLE_NAME)
    success, res = execute_query(q, p)
    if success:
        data["top_items_qty"] = {"rows": res}
        sql_used["top_items_qty"] = q.strip()
        available_widgets.append("top_items_qty")

    # B. Top items by order frequency
    q, p = query_builder.build_top_items_by_frequency(schema, filters, TABLE_NAME)
    success, res = execute_query(q, p)
    if success:
        data["top_items_freq"] = {"rows": res}
        sql_used["top_items_freq"] = q.strip()
        available_widgets.append("top_items_freq")

    # C. Most profitable dishes
    q, p = query_builder.build_most_profitable_dishes(schema, filters, TABLE_NAME)
    success, res = execute_query(q, p)
    if success:
        data["top_items_profit"] = {"rows": res}
        sql_used["top_items_profit"] = q.strip()
        available_widgets.append("top_items_profit")

    # D. Best combos
    q, p = query_builder.build_best_combos_query(schema, filters, TABLE_NAME)
    success, res = execute_query(q, p)
    if success:
        data["best_combos"] = {"rows": res}
        sql_used["best_combos"] = q.strip()
        available_widgets.append("best_combos")
    
    data["sql_used"] = sql_used
    data["available_widgets"] = available_widgets
    
    return True, data

def get_filter_options():
    """Reads schema_meta.json and dynamically fetches dimension options."""
    schema = schema_inspector.load_schema()
    if not schema:
        return False, "Schema not initialized"
        
    dimensions = schema_inspector.get_dimensions(schema)
    options = {}
    
    for col in dimensions[:6]: # Limit to top 6 dimensions to avoid UI overload
        # Exclude nulls
        query = f"SELECT DISTINCT {col} FROM {TABLE_NAME} WHERE {col} IS NOT NULL ORDER BY {col} LIMIT 100"
        success, res = execute_query(query)
        if success:
            options[col] = {
                "label": col.replace('_', ' ').title(),
                "values": [r[col] for r in res]
            }
            
    return True, options

def get_playground_queries():
    schema = schema_inspector.load_schema()
    if not schema:
        return []
    return query_builder.generate_playground_queries(schema, TABLE_NAME)

def run_playground_query(sql):
    if not sql.strip().upper().startswith("SELECT") and not sql.strip().upper().startswith("WITH"):
        return False, "Only SELECT / WITH queries are allowed in the playground."
        
    success, res = execute_query(sql)
    if not success:
        return False, res
        
    return True, res

if not os.path.exists(DB_PATH) or not os.path.exists("schema_meta.json"):
    init_db()
