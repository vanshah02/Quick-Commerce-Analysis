# Quick Commerce Analytics & SQL Intelligence Platform

A dynamic analytics dashboard for exploring and analyzing quick-commerce order data using **Python, Pandas, SQLite, SQL, HTML, CSS and JavaScript**.

The main goal of this project is to take a CSV dataset and automatically generate useful business insights instead of creating a dashboard that only works for one fixed dataset.

## Features

* Upload and analyze CSV datasets
* Automatic dataset/schema detection
* Dynamic filters based on available columns
* Revenue and order analysis
* Top-performing products
* Product/category performance
* Peak activity analysis
* Frequently purchased product combinations
* Business insights from the available data
* Interactive charts and dashboard
* SQL query viewer for individual analyses
* SQL Studio for running custom queries
* Export SQL query results as CSV
* SQLite database integration

## How It Works

The application first reads the uploaded CSV and checks its columns and data types.

Based on the dataset, it identifies useful fields such as:

* IDs
* Categories
* Numeric columns
* Date/time columns
* Product/item fields

The data is then loaded into SQLite and used to generate the required SQL queries for the dashboard.

This makes the dashboard flexible enough to work with different datasets without manually changing every chart and filter.

## Analytics Included

### Overview

The dashboard provides important KPIs such as:

* Total records/orders
* Total revenue
* Total quantity
* Average values
* Other relevant metrics depending on the dataset

### Product Analysis

The application can identify:

* Top products by quantity
* Most frequently ordered products
* Best-performing categories
* Revenue contribution
* Profit-related metrics when available

### Peak Activity

If the dataset contains a date/time column, the application can analyze activity across different hours or time periods to identify peak demand.

### Product Combinations

The application uses order-level data to find products that are commonly purchased together.

This can be useful for:

* Combo offers
* Cross-selling
* Product recommendations
* Understanding customer buying patterns

## Dynamic Filters

Filters are not completely hardcoded.

The application checks the uploaded dataset and generates filters based on the categorical fields available in that dataset.

For example, one dataset may provide:

* City
* Category
* Cuisine

while another may provide:

* Region
* Department
* Product Type

The dashboard adjusts accordingly.

## Business Use Cases

The dashboard can help answer questions such as:

* Which products generate the most revenue?
* Which products are ordered most frequently?
* Which categories perform the best?
* What are the busiest ordering periods?
* Which locations contribute the most?
* Which products are commonly purchased together?
* Where can combo offers or cross-selling be introduced?

## SQL Analysis

SQL is used extensively throughout the project for data analysis.

Some of the SQL concepts used include:

* `SELECT`
* `WHERE`
* `GROUP BY`
* `ORDER BY`
* `COUNT`
* `SUM`
* `AVG`
* `DISTINCT`
* CTEs
* Window functions
* Self joins
* Ranking
* Date/time based analysis

The **View SQL** option allows users to see the query used for a particular analysis.

## SQL Studio

The project also includes an SQL Studio where users can write and execute their own analytical queries.

Example:

```sql
SELECT
    category,
    SUM(revenue) AS total_revenue
FROM orders
GROUP BY category
ORDER BY total_revenue DESC;
```

Query results can also be exported as CSV.

## Tech Stack

**Frontend**

* HTML
* CSS
* JavaScript
* Chart.js

**Backend**

* Python
* Pandas
* SQLite
* REST API

**Database**

* SQLite

**Data Analysis**

* SQL
* Pandas

## Project Structure

```text
Quick-Commerce-Analysis/
│
├── app.py
├── db_manager.py
├── query_builder.py
├── schema_inspector.py
├── sql_queries.py
├── requirements.txt
│
├── static/
│   ├── index.html
│   ├── css/
│   └── js/
│
├── datasets/
│
└── README.md
```

## Installation

Clone the repository:

```bash
git clone <your-repository-url>
cd Quick-Commerce-Analysis
```

Create a virtual environment:

```bash
python3 -m venv .venv
```

Activate it:

### macOS / Linux

```bash
source .venv/bin/activate
```

### Windows

```bash
.venv\Scripts\activate
```

Install the required packages:

```bash
pip install -r requirements.txt
```

## Run the Project

Start the application:

```bash
python3 app.py
```

Then open the local URL shown by the application in your browser.

## Dataset

The project can be used with the included quick-commerce/order dataset or with another CSV containing suitable transactional data.

For the best results, the dataset should contain fields such as:

* Order ID
* Product/Item
* Category
* Quantity
* Revenue/Sales
* Date/Time
* Location

The application will use whatever relevant fields are available rather than requiring an exact column structure.


## Future Improvements

Some possible additions to the project are:

* AI-generated business insights
* Sales forecasting
* Customer segmentation
* RFM analysis
* Recommendation system
* Advanced market basket analysis
* Anomaly detection
* PDF/Excel report generation
* User authentication
* Cloud database support

## Author

**Vansh Shah**

B.Tech Information Technology

---

### Project Focus

**Turning raw order data into useful business insights using Python, SQL and interactive analytics.**
