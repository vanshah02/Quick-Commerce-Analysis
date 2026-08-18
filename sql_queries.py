# Repository of all SQL queries used in the dashboard

QUERIES = {
    "kpis": """
        SELECT 
            SUM(line_revenue) as total_revenue,
            COUNT(DISTINCT order_id) as total_orders,
            SUM(quantity) as total_items_sold,
            SUM(line_profit) as net_profit,
            ROUND(100.0 * SUM(line_profit) / SUM(line_revenue), 2) as profit_margin,
            ROUND(AVG(line_revenue * 1.0 / basket_size), 2) as aov,
            ROUND(AVG(delivery_time_mins), 1) as avg_delivery_time,
            ROUND(AVG(rating), 2) as avg_rating
        FROM zomato_orders
        WHERE 1=1 {filters}
    """,

    "most_ordered_items": """
        SELECT 
            item,
            category,
            cuisine,
            SUM(quantity) AS total_quantity,
            COUNT(DISTINCT order_id) AS order_appearances,
            SUM(line_revenue) AS total_revenue
        FROM zomato_orders
        WHERE 1=1 {filters}
        GROUP BY item, category, cuisine
        ORDER BY total_quantity DESC
        LIMIT 10
    """,

    "most_profitable_dishes": """
        SELECT 
            item,
            category,
            SUM(line_revenue) AS total_revenue,
            ROUND(SUM(line_profit), 2) AS total_profit,
            ROUND(100.0 * SUM(line_profit) / SUM(line_revenue), 2) AS profit_margin_pct,
            SUM(quantity) AS total_qty
        FROM zomato_orders
        WHERE 1=1 {filters}
        GROUP BY item, category
        ORDER BY total_profit DESC
        LIMIT 10
    """,

    "regional_sales_contribution": """
        WITH city_sales AS (
            SELECT 
                city,
                COUNT(DISTINCT order_id) as total_orders,
                SUM(line_revenue) as city_revenue
            FROM zomato_orders
            WHERE 1=1 {filters}
            GROUP BY city
        )
        SELECT 
            city,
            total_orders,
            city_revenue,
            ROUND(100.0 * city_revenue / SUM(city_revenue) OVER(), 2) as pct_contribution
        FROM city_sales
        ORDER BY city_revenue DESC
    """,
    
    "peak_hours_heatmap": """
        SELECT 
            city,
            CAST(strftime('%H', timestamp) AS INTEGER) as hour_of_day,
            COUNT(DISTINCT order_id) as order_count,
            SUM(line_revenue) as hourly_revenue
        FROM zomato_orders
        WHERE 1=1 {filters}
        GROUP BY city, hour_of_day
        ORDER BY city, hour_of_day
    """,

    "delivery_latency_by_city": """
        SELECT 
            city,
            ROUND(AVG(delivery_time_mins), 1) AS avg_delivery_time,
            ROUND(MIN(delivery_time_mins), 1) AS min_delivery_time,
            ROUND(MAX(delivery_time_mins), 1) AS max_delivery_time,
            ROUND(AVG(rating), 2) AS avg_rating,
            COUNT(DISTINCT order_id) AS total_orders
        FROM zomato_orders
        WHERE 1=1 {filters}
        GROUP BY city
        ORDER BY avg_delivery_time ASC
    """,
    
    "best_combos": """
        WITH order_pairs AS (
            SELECT 
                a.item AS item_a,
                b.item AS item_b,
                COUNT(DISTINCT a.order_id) AS combo_orders,
                ROUND(AVG(a.unit_price + b.unit_price), 2) AS combined_price
            FROM zomato_orders a
            JOIN zomato_orders b 
                ON a.order_id = b.order_id 
                AND a.item < b.item
            WHERE 1=1 {filters_a}
            GROUP BY a.item, b.item
        )
        SELECT 
            item_a,
            item_b,
            combo_orders,
            combined_price
        FROM order_pairs
        ORDER BY combo_orders DESC
        LIMIT 10
    """,

    "filter_options": """
        SELECT DISTINCT {column} FROM zomato_orders WHERE {column} IS NOT NULL ORDER BY {column}
    """
}

# Example queries for the SQL Playground
PLAYGROUND_QUERIES = [
    {
        "title": "Top 3 Most Profitable Dishes by City (Window Function)",
        "sql": """WITH ranked_dishes AS (
    SELECT 
        city,
        item,
        SUM(line_profit) as total_profit,
        DENSE_RANK() OVER(PARTITION BY city ORDER BY SUM(line_profit) DESC) as rank
    FROM zomato_orders
    GROUP BY city, item
)
SELECT city, item, ROUND(total_profit, 2) as profit, rank
FROM ranked_dishes
WHERE rank <= 3;"""
    },
    {
        "title": "Sales Contribution % by Time of Day",
        "sql": """WITH time_sales AS (
    SELECT 
        CASE 
            WHEN CAST(strftime('%H', timestamp) AS INTEGER) BETWEEN 6 AND 11 THEN 'Breakfast (06-11)'
            WHEN CAST(strftime('%H', timestamp) AS INTEGER) BETWEEN 12 AND 16 THEN 'Lunch (12-16)'
            WHEN CAST(strftime('%H', timestamp) AS INTEGER) BETWEEN 17 AND 21 THEN 'Dinner Peak (17-21)'
            ELSE 'Late Night (22-05)'
        END AS time_bucket,
        SUM(line_revenue) as bucket_revenue
    FROM zomato_orders
    GROUP BY time_bucket
)
SELECT 
    time_bucket, 
    bucket_revenue,
    ROUND(100.0 * bucket_revenue / SUM(bucket_revenue) OVER(), 2) as pct_of_total_sales
FROM time_sales
ORDER BY bucket_revenue DESC;"""
    },
    {
        "title": "Delivery Delay Impact on Ratings",
        "sql": """SELECT 
    CASE 
        WHEN delivery_time_mins < 25 THEN '1. Super Fast (<25m)'
        WHEN delivery_time_mins BETWEEN 25 AND 35 THEN '2. Standard (25-35m)'
        WHEN delivery_time_mins BETWEEN 36 AND 45 THEN '3. Delayed (36-45m)'
        ELSE '4. Very Late (>45m)'
    END as delivery_speed,
    COUNT(DISTINCT order_id) as total_orders,
    ROUND(AVG(rating), 2) as avg_rating
FROM zomato_orders
GROUP BY delivery_speed
ORDER BY delivery_speed;"""
    }
]
