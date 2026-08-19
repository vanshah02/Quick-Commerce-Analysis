import os
import json
from flask import Flask, request, jsonify, session, redirect, url_for, send_from_directory
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
import pandas as pd
import db_manager

load_dotenv()

app = Flask(__name__, static_folder='static', static_url_path='')
app.secret_key = os.getenv('SECRET_KEY', 'dev_secret_key_12345')

oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID', 'DUMMY_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET', 'DUMMY_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)

def is_logged_in():
    return 'user' in session

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/login')
def login():
    redirect_uri = url_for('auth', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/auth/callback')
def auth():
    token = google.authorize_access_token()
    user = google.parse_id_token(token, nonce=None)
    if user:
        session['user'] = user
    return redirect('/')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

@app.route('/api/auth_status')
def auth_status():
    if is_logged_in():
        return jsonify({"logged_in": True, "user": session['user']})
    return jsonify({"logged_in": False})

@app.route('/api/analytics', methods=['GET'])
def analytics():
    if not is_logged_in():
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    
    filters = request.args.to_dict()
    success, data = db_manager.get_analytics_data(filters)
    if success:
        return jsonify({"status": "success", "data": data})
    else:
        return jsonify({"status": "error", "message": data}), 500

@app.route('/api/schema', methods=['GET'])
def schema():
    if not is_logged_in():
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    
    success, data = db_manager.get_schema_summary()
    if success:
        return jsonify({"status": "success", "data": data})
    else:
        return jsonify({"status": "error", "message": data}), 500

@app.route('/api/filters', methods=['GET'])
def filters():
    if not is_logged_in():
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
        
    success, data = db_manager.get_filter_options()
    if success:
        return jsonify({"status": "success", "data": data})
    else:
        return jsonify({"status": "error", "message": data}), 500

@app.route('/api/playground_queries', methods=['GET'])
def playground_queries():
    if not is_logged_in():
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
        
    queries = db_manager.get_playground_queries()
    return jsonify({"status": "success", "data": queries})

@app.route('/api/query', methods=['POST'])
def query():
    if not is_logged_in():
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
        
    data = request.json
    sql = data.get('sql', '')
    success, res = db_manager.run_playground_query(sql)
    if success:
        return jsonify({"status": "success", "data": res})
    else:
        return jsonify({"status": "error", "message": res}), 400

@app.route('/api/upload', methods=['POST'])
def upload():
    if not is_logged_in():
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
        
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file part"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No selected file"}), 400
        
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ['.csv', '.xls', '.xlsx']:
        return jsonify({"status": "error", "message": "Unsupported file format"}), 400
        
    upload_path = os.path.join(os.getcwd(), 'uploaded_dataset' + ext)
    file.save(upload_path)
    
    sheet_name = request.form.get('sheet_name', None)
    
    if ext in ['.xls', '.xlsx'] and sheet_name is None:
        try:
            xl = pd.ExcelFile(upload_path)
            if len(xl.sheet_names) > 1:
                return jsonify({
                    "status": "multiple_sheets",
                    "sheets": xl.sheet_names,
                    "filename": file.filename
                })
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 400
            
    success, msg = db_manager.init_db(upload_path, sheet_name=sheet_name)
    if success:
        return jsonify({"status": "success", "message": "Dataset uploaded and DB rebuilt."})
    else:
        return jsonify({"status": "error", "message": f"Failed to rebuild DB: {msg}"}), 500

@app.route('/api/upload_sheet', methods=['POST'])
def upload_sheet():
    if not is_logged_in():
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
        
    sheet_name = request.json.get('sheet_name')
    filename = request.json.get('filename')
    ext = os.path.splitext(filename)[1].lower()
    upload_path = os.path.join(os.getcwd(), 'uploaded_dataset' + ext)
    
    success, msg = db_manager.init_db(upload_path, sheet_name=sheet_name)
    if success:
        return jsonify({"status": "success", "message": "Sheet loaded and DB rebuilt."})
    else:
        return jsonify({"status": "error", "message": f"Failed to rebuild DB: {msg}"}), 500

@app.route('/api/reset', methods=['POST'])
def reset():
    if not is_logged_in():
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
        
    success, msg = db_manager.init_db(db_manager.DEFAULT_CSV)
    if success:
        return jsonify({"status": "success", "message": "Reset to default dataset."})
    else:
        return jsonify({"status": "error", "message": f"Failed to reset: {msg}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
