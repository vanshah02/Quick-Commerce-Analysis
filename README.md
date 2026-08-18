# Quick Analyser & SQL Portfolio Platform

A comprehensive Data Analyst portfolio project simulating a real-world analytics dashboard for diverse datasets.  

This project goes beyond a simple frontend by embedding a **fully functional Python + SQLite backend**. It dynamically parses raw CSV transaction data into a relational database, executes complex SQL aggregations (including CTEs, window functions, and self-joins), and serves the insights via a REST API to a custom-built, Zomato-themed dashboard.

## Features

1.  **Zero-Dependency Backend**: Built entirely with Python's standard library (`http.server` & `sqlite3`) and `pandas` for ETL. Runs anywhere instantly.
2.  **Relational SQL Engine**: Ingests flat CSVs and processes analytics using advanced SQL.
3.  **Interactive Executive Dashboard**: 
    -   Key Performance Indicators (Revenue, Orders, Margins, AOV).
    -   **Regional Contribution**: Tracks percentage of total sales per region using SQL Window functions.
    -   **Most Profitable Items**: Margin analysis and volume tracking.
    -   **Peak Activity Hours**: Temporal heatmap analysis.
    -   **Market Basket Analysis**: SQL Self-Joins to discover the most frequent item combinations.
4.  **SQL Query Inspector**: Every KPI and Chart has a "View SQL" button that reveals the exact query executed behind the scenes.
5.  **Live SQL Studio**: An embedded interactive SQL playground with a gallery of interview-grade SQL questions. Run raw queries against the dataset and export the results to CSV!
6.  **Dynamic Dataset Upload**: Drag-and-drop a new CSV file to instantly rebuild the database and refresh the dashboard.

## Setup & Running

1.  Ensure you have Python 3 installed.
2.  Install requirements:
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: The only external requirement is `pandas` and `numpy` for parsing the CSV).*
3.  Run the application:
    ```bash
    python3 app.py
    ```
4.  Open your browser and navigate to `http://localhost:8000/`.

## Resume Bullet Points

If you are using this project for your resume, here are a few ways to describe your work:

*   **Data Architecture**: Architected a local SQLite data warehouse to ingest and normalize flat food delivery transaction records, enabling high-performance analytical queries.
*   **SQL & Business Intelligence**: Authored advanced SQL scripts utilizing CTEs, Window Functions (e.g., `SUM() OVER(PARTITION BY...)`), and Self-Joins to compute regional sales contributions, delivery latencies, and market basket combinations.
*   **Full-Stack Analytics**: Developed a custom REST API using Python and built an interactive dashboard leveraging Vanilla CSS and Chart.js to visualize KPIs, margin analysis, and temporal heatmaps.
*   **Data Tooling**: Implemented an interactive "SQL Studio" within the application, allowing real-time query execution, syntax highlighting, and CSV export capabilities for ad-hoc analysis.

*Styled with a custom modern executive theme (Red, Black, and White).*
