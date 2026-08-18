import pandas as pd
import json
import os

def detect_schema(df):
    schema = {}
    row_count = len(df)
    
    for col in df.columns:
        # Calculate distinct count and null percentage
        cardinality = df[col].nunique(dropna=True)
        null_count = df[col].isnull().sum()
        null_pct = null_count / row_count if row_count > 0 else 0
        
        # Determine SQL Type
        sql_type = "TEXT"
        if pd.api.types.is_numeric_dtype(df[col]):
            sql_type = "REAL" if pd.api.types.is_float_dtype(df[col]) else "INTEGER"
            
        # Determine Role
        role = "text"
        col_lower = str(col).lower()
        
        is_datetime = False
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            is_datetime = True
        elif df[col].dtype == 'object' or pd.api.types.is_string_dtype(df[col]):
            # Fast heuristic check for datetime string on a sample
            sample = df[col].dropna().head(50)
            if len(sample) > 0:
                try:
                    parsed = pd.to_datetime(sample, errors='coerce')
                    if parsed.notnull().mean() > 0.9:
                        is_datetime = True
                except:
                    pass

                    
        if is_datetime:
            role = "datetime"
            sql_type = "TEXT" # Store ISO strings in sqlite
        elif 'id' in col_lower or cardinality == row_count:
            role = "id"
        elif pd.api.types.is_numeric_dtype(df[col]):
            # If it's a float or has many values, or is named like a measure
            if pd.api.types.is_float_dtype(df[col]) or cardinality > 10 or any(w in col_lower for w in ['qty', 'quantity', 'price', 'revenue', 'profit', 'cost', 'amount']):
                role = "numeric_measure"
            else:
                role = "categorical" # e.g., rating, binary flags
        else: # Object/String type
            if cardinality <= row_count * 0.8: # Allow up to 80% uniqueness for items/products
                role = "categorical"
            else:
                role = "text"
                
        schema[col] = {
            "name": col,
            "sql_type": sql_type,
            "role": role,
            "cardinality": int(cardinality),
            "null_pct": float(null_pct),
            "null_count": int(null_count)
        }
        
    return schema

def get_measures(schema):
    return [col for col, meta in schema.items() if meta['role'] == 'numeric_measure']

def get_dimensions(schema):
    return [col for col, meta in schema.items() if meta['role'] == 'categorical']

def get_datetime_column(schema):
    for col, meta in schema.items():
        if meta['role'] == 'datetime':
            return col
    return None

def get_id_column(schema):
    for col, meta in schema.items():
        if meta['role'] == 'id':
            return col
    return None

def save_schema(schema, filepath="schema_meta.json"):
    with open(filepath, 'w') as f:
        json.dump(schema, f, indent=2)

def load_schema(filepath="schema_meta.json"):
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)
    return {}
