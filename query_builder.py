import schema_inspector

def build_filter_clause(filters, valid_columns, prefix=""):
    clause = ""
    params = []
    if not filters:
        return clause, params
        
    for key, val in filters.items():
        if key in valid_columns and val and val != "All":
            col = f"{prefix}{key}" if prefix else key
            clause += f" AND {col} = ?"
            params.append(val)
            
    return clause, params

def build_kpi_query(schema, filters, table_name="dataset"):
    valid_columns = list(schema.keys())
    f_clause, f_params = build_filter_clause(filters, valid_columns)
    
    measures = schema_inspector.get_measures(schema)
    id_col = schema_inspector.get_id_column(schema)
    
    selects = ["COUNT(*) as total_records"]
    if id_col:
        selects.append(f"COUNT(DISTINCT {id_col}) as distinct_{id_col}")
        
    for m in measures:
        selects.append(f"SUM({m}) as sum_{m}")
        selects.append(f"ROUND(AVG({m}), 2) as avg_{m}")
        
    query = f"SELECT {', '.join(selects)} FROM {table_name} WHERE 1=1 {f_clause}"
    return query, f_params

def build_group_contribution_query(schema, dimension, measure, filters, table_name="dataset"):
    valid_columns = list(schema.keys())
    f_clause, f_params = build_filter_clause(filters, valid_columns)
    
    query = f"""
        WITH grouped AS (
            SELECT 
                {dimension},
                COUNT(*) as record_count,
                SUM({measure}) as group_total
            FROM {table_name}
            WHERE 1=1 {f_clause} AND {dimension} IS NOT NULL
            GROUP BY {dimension}
        )
        SELECT 
            {dimension},
            record_count,
            group_total,
            ROUND(100.0 * group_total / SUM(group_total) OVER(), 2) as pct_contribution
        FROM grouped
        ORDER BY group_total DESC
    """
    return query, f_params

def build_time_series_query(schema, date_col, measure, secondary_dim, filters, table_name="dataset"):
    valid_columns = list(schema.keys())
    f_clause, f_params = build_filter_clause(filters, valid_columns)
    
    # Extract hour. SQLite specific.
    group_cols = f"CAST(strftime('%H', {date_col}) AS INTEGER)"
    select_cols = f"{group_cols} as hour_of_day, SUM({measure}) as total_{measure}"
    
    if secondary_dim:
        select_cols = f"{secondary_dim}, " + select_cols
        group_cols = f"{secondary_dim}, " + group_cols
        
    query = f"""
        SELECT 
            {select_cols}
        FROM {table_name}
        WHERE 1=1 {f_clause} AND {date_col} IS NOT NULL
        GROUP BY {group_cols}
        ORDER BY {group_cols}
    """
    return query, f_params

def build_top_items_by_quantity(schema, filters, table_name="dataset"):
    valid_columns = list(schema.keys())
    f_clause, f_params = build_filter_clause(filters, valid_columns)
    query = f"""
        SELECT item, SUM(quantity) as total_quantity
        FROM {table_name}
        WHERE 1=1 {f_clause} AND item IS NOT NULL
        GROUP BY item
        ORDER BY total_quantity DESC
        LIMIT 10
    """
    return query, f_params

def build_top_items_by_frequency(schema, filters, table_name="dataset"):
    valid_columns = list(schema.keys())
    f_clause, f_params = build_filter_clause(filters, valid_columns)
    query = f"""
        SELECT item, COUNT(DISTINCT order_id) as order_frequency
        FROM {table_name}
        WHERE 1=1 {f_clause} AND item IS NOT NULL
        GROUP BY item
        ORDER BY order_frequency DESC
        LIMIT 10
    """
    return query, f_params

def build_most_profitable_dishes(schema, filters, table_name="dataset"):
    valid_columns = list(schema.keys())
    f_clause, f_params = build_filter_clause(filters, valid_columns)
    query = f"""
        SELECT 
            item, 
            SUM(line_profit) AS profit, 
            ROUND(SUM(line_profit) * 100.0 / SUM(line_revenue), 1) AS margin_pct
        FROM {table_name}
        WHERE 1=1 {f_clause} AND item IS NOT NULL
        GROUP BY item
        ORDER BY profit DESC
        LIMIT 10
    """
    return query, f_params

def build_best_combos_query(schema, filters, table_name="dataset"):
    valid_columns = list(schema.keys())
    f_clause, f_params = build_filter_clause(filters, valid_columns, prefix="a.")
    
    query = f"""
        SELECT 
            a.item AS item_a, 
            b.item AS item_b, 
            COUNT(*) AS times_together 
        FROM {table_name} a 
        JOIN {table_name} b 
            ON a.order_id = b.order_id 
            AND a.item < b.item 
        WHERE 1=1 {f_clause}
        GROUP BY a.item, b.item 
        ORDER BY times_together DESC 
        LIMIT 10
    """
    return query, f_params

def generate_playground_queries(schema, table_name="dataset"):
    queries = []
    
    dims = schema_inspector.get_dimensions(schema)
    measures = schema_inspector.get_measures(schema)
    date_col = schema_inspector.get_datetime_column(schema)
    
    if len(dims) >= 2 and measures:
        d1, d2 = dims[0], dims[1]
        m1 = measures[0]
        queries.append({
            "title": f"Top 3 {d2} by {d1} (Window Function)",
            "sql": f"""WITH ranked_data AS (
    SELECT 
        {d1},
        {d2},
        SUM({m1}) as total,
        DENSE_RANK() OVER(PARTITION BY {d1} ORDER BY SUM({m1}) DESC) as rank
    FROM {table_name}
    GROUP BY {d1}, {d2}
)
SELECT {d1}, {d2}, ROUND(total, 2) as {m1}_total, rank
FROM ranked_data
WHERE rank <= 3;"""
        })
        
    if date_col and measures:
        m1 = measures[0]
        queries.append({
            "title": "Sales Contribution % by Time of Day",
            "sql": f"""WITH time_sales AS (
    SELECT 
        CASE 
            WHEN CAST(strftime('%H', {date_col}) AS INTEGER) BETWEEN 6 AND 11 THEN 'Breakfast (06-11)'
            WHEN CAST(strftime('%H', {date_col}) AS INTEGER) BETWEEN 12 AND 16 THEN 'Lunch (12-16)'
            WHEN CAST(strftime('%H', {date_col}) AS INTEGER) BETWEEN 17 AND 21 THEN 'Dinner Peak (17-21)'
            ELSE 'Late Night (22-05)'
        END AS time_bucket,
        SUM({m1}) as bucket_total
    FROM {table_name}
    GROUP BY time_bucket
)
SELECT 
    time_bucket, 
    bucket_total,
    ROUND(100.0 * bucket_total / SUM(bucket_total) OVER(), 2) as pct_of_total
FROM time_sales
ORDER BY bucket_total DESC;"""
        })
        
    if measures:
        m1 = measures[0]
        queries.append({
            "title": f"Overall Distribution of {m1}",
            "sql": f"""SELECT 
    MIN({m1}) as min_val,
    MAX({m1}) as max_val,
    ROUND(AVG({m1}), 2) as avg_val,
    SUM({m1}) as total_val
FROM {table_name};"""
        })
        
    return queries
