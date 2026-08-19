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
    id_cols = [col for col, meta in schema.items() if meta['role'] == 'id']
    
    selects = ["COUNT(*) as total_records"]
    for id_c in id_cols:
        selects.append(f"COUNT(DISTINCT {id_c}) as distinct_{id_c}")
        
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

def build_top_items_by_quantity(schema, filters, item_col, qty_col, table_name="dataset"):
    valid_columns = list(schema.keys())
    f_clause, f_params = build_filter_clause(filters, valid_columns)
    query = f"""
        SELECT {item_col} as item, SUM({qty_col}) as total_quantity
        FROM {table_name}
        WHERE 1=1 {f_clause} AND {item_col} IS NOT NULL
        GROUP BY {item_col}
        ORDER BY total_quantity DESC
        LIMIT 10
    """
    return query, f_params

def build_top_items_by_frequency(schema, filters, item_col, id_col, table_name="dataset"):
    valid_columns = list(schema.keys())
    f_clause, f_params = build_filter_clause(filters, valid_columns)
    query = f"""
        SELECT {item_col} as item, COUNT(DISTINCT {id_col}) as order_frequency
        FROM {table_name}
        WHERE 1=1 {f_clause} AND {item_col} IS NOT NULL
        GROUP BY {item_col}
        ORDER BY order_frequency DESC
        LIMIT 10
    """
    return query, f_params

def build_most_profitable_dishes(schema, filters, item_col, profit_col, revenue_col, table_name="dataset"):
    valid_columns = list(schema.keys())
    f_clause, f_params = build_filter_clause(filters, valid_columns)
    
    if revenue_col:
        margin_sql = f"ROUND(SUM({profit_col}) * 100.0 / NULLIF(SUM(SUM({revenue_col})) OVER(), 0), 1) AS margin_pct"
    else:
        margin_sql = "0 AS margin_pct"
        
    query = f"""
        SELECT 
            {item_col} as item, 
            SUM({profit_col}) AS profit, 
            {margin_sql}
        FROM {table_name}
        WHERE 1=1 {f_clause} AND {item_col} IS NOT NULL
        GROUP BY {item_col}
        ORDER BY profit DESC
        LIMIT 10
    """
    return query, f_params

def build_best_combos_query(schema, filters, item_col, id_col, table_name="dataset"):
    valid_columns = list(schema.keys())
    f_clause, f_params = build_filter_clause(filters, valid_columns, prefix="a.")
    
    query = f"""
        SELECT 
            a.{item_col} AS item_a, 
            b.{item_col} AS item_b, 
            COUNT(*) AS times_together 
        FROM {table_name} a 
        JOIN {table_name} b 
            ON a.{id_col} = b.{id_col} 
            AND a.{item_col} < b.{item_col} 
        WHERE 1=1 {f_clause}
        GROUP BY a.{item_col}, b.{item_col} 
        ORDER BY times_together DESC 
        LIMIT 10
    """
    return query, f_params

def build_rfm_query(schema, filters, cust_id_col, date_col, revenue_col, table_name="dataset"):
    valid_columns = list(schema.keys())
    f_clause, f_params = build_filter_clause(filters, valid_columns)
    
    # Calculate Max Date in dataset for Recency calculation
    # Since we can't easily do variables in single sqlite pass, we use scalar subquery
    
    query = f"""
        WITH customer_stats AS (
            SELECT 
                {cust_id_col},
                MAX({date_col}) as last_order_date,
                COUNT(DISTINCT {date_col}) as frequency,
                SUM({revenue_col}) as monetary,
                (SELECT MAX({date_col}) FROM {table_name}) as max_db_date
            FROM {table_name}
            WHERE 1=1 {f_clause} AND {cust_id_col} IS NOT NULL
            GROUP BY {cust_id_col}
        ),
        rfm_calc AS (
            SELECT 
                {cust_id_col},
                CAST(julianday(max_db_date) - julianday(last_order_date) AS INTEGER) as recency,
                frequency,
                monetary
            FROM customer_stats
        ),
        rfm_scores AS (
            SELECT 
                *,
                NTILE(5) OVER (ORDER BY recency DESC) AS r_score,
                NTILE(5) OVER (ORDER BY frequency ASC) AS f_score,
                NTILE(5) OVER (ORDER BY monetary ASC) AS m_score
            FROM rfm_calc
        ),
        segments AS (
            SELECT 
                *,
                (r_score + f_score + m_score) / 3.0 as avg_score,
                CASE 
                    WHEN (r_score + f_score + m_score) / 3.0 >= 4 THEN 'Champions'
                    WHEN (r_score + f_score + m_score) / 3.0 >= 3 THEN 'Loyal'
                    WHEN (r_score + f_score + m_score) / 3.0 >= 2 THEN 'At Risk'
                    ELSE 'Lost'
                END as segment
            FROM rfm_scores
        )
        SELECT 
            segment, 
            COUNT(*) as customer_count,
            ROUND(AVG(monetary), 2) as avg_monetary
        FROM segments
        GROUP BY segment
        ORDER BY avg_monetary DESC
    """
    
    # Top 10 customers by monetary
    top_cust_query = f"""
        SELECT 
            {cust_id_col} as customer_id,
            SUM({revenue_col}) as monetary
        FROM {table_name}
        WHERE 1=1 {f_clause} AND {cust_id_col} IS NOT NULL
        GROUP BY {cust_id_col}
        ORDER BY monetary DESC
        LIMIT 10
    """
    
    return query, top_cust_query, f_params, f_params

def build_churn_query(schema, filters, cust_id_col, date_col, location_col, table_name="dataset"):
    valid_columns = list(schema.keys())
    f_clause, f_params = build_filter_clause(filters, valid_columns)
    
    # Threshold is 60 days
    query = f"""
        WITH customer_last_order AS (
            SELECT 
                {cust_id_col},
                {location_col if location_col else "'Unknown'"} as location,
                MAX({date_col}) as last_order_date,
                (SELECT MAX({date_col}) FROM {table_name}) as max_db_date
            FROM {table_name}
            WHERE 1=1 {f_clause} AND {cust_id_col} IS NOT NULL
            GROUP BY {cust_id_col}, {location_col if location_col else "'Unknown'"}
        ),
        churn_status AS (
            SELECT 
                {cust_id_col},
                location,
                CASE 
                    WHEN CAST(julianday(max_db_date) - julianday(last_order_date) AS INTEGER) > 60 THEN 'Churned'
                    ELSE 'Active'
                END as status
            FROM customer_last_order
        )
        SELECT 
            location,
            status,
            COUNT(*) as customer_count
        FROM churn_status
        GROUP BY location, status
        ORDER BY location, status
    """
    return query, f_params

def build_heatmap_query(schema, filters, location_col, table_name="dataset"):
    valid_columns = list(schema.keys())
    f_clause, f_params = build_filter_clause(filters, valid_columns)
    
    # Simple count by location
    query = f"""
        SELECT 
            {location_col} as location,
            COUNT(*) as order_density
        FROM {table_name}
        WHERE 1=1 {f_clause} AND {location_col} IS NOT NULL
        GROUP BY {location_col}
        ORDER BY order_density DESC
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
