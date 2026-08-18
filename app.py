import os
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import db_manager

PORT = 8000

class AnalyticsRequestHandler(SimpleHTTPRequestHandler):
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200, "ok")
        self.end_headers()
        
    def send_json(self, data, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
        
    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        if path == '/api/analytics':
            query_components = parse_qs(parsed_url.query)
            filters = {k: v[0] for k, v in query_components.items()}
            
            success, data = db_manager.get_analytics_data(filters)
            if success:
                self.send_json({"status": "success", "data": data})
            else:
                self.send_json({"status": "error", "message": data}, 500)
                
        elif path == '/api/schema':
            success, data = db_manager.get_schema_summary()
            if success:
                self.send_json({"status": "success", "data": data})
            else:
                self.send_json({"status": "error", "message": data}, 500)
                
        elif path == '/api/filters':
            success, data = db_manager.get_filter_options()
            if success:
                self.send_json({"status": "success", "data": data})
            else:
                self.send_json({"status": "error", "message": data}, 500)
                
        elif path == '/api/playground_queries':
            queries = db_manager.get_playground_queries()
            self.send_json({"status": "success", "data": queries})
            
        else:
            # Serve static files for all other GET requests
            super().do_GET()

    def do_POST(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        if path == '/api/query':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                payload = json.loads(post_data.decode('utf-8'))
                sql = payload.get('sql', '')
                
                success, data = db_manager.run_playground_query(sql)
                if success:
                    self.send_json({"status": "success", "data": data})
                else:
                    self.send_json({"status": "error", "message": data}, 400)
            except Exception as e:
                self.send_json({"status": "error", "message": str(e)}, 400)
                
        elif path == '/api/upload':
            # Handle raw file upload
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self.send_json({"status": "error", "message": "No file content"}, 400)
                return
                
            file_data = self.rfile.read(content_length)
            upload_path = os.path.join(os.getcwd(), 'uploaded_dataset.csv')
            with open(upload_path, 'wb') as f:
                f.write(file_data)
                
            # Re-initialize the DB with the new file
            success, msg = db_manager.init_db(upload_path)
            if success:
                self.send_json({"status": "success", "message": "Dataset uploaded and DB rebuilt."})
            else:
                self.send_json({"status": "error", "message": f"Failed to rebuild DB: {msg}"}, 500)
                
        elif path == '/api/reset':
            # Reset to default Zomato_Orders.csv
            success, msg = db_manager.init_db(db_manager.DEFAULT_CSV)
            if success:
                self.send_json({"status": "success", "message": "Reset to default dataset."})
            else:
                self.send_json({"status": "error", "message": f"Failed to reset: {msg}"}, 500)
                
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    # Change working directory to static so that simple requests serve index.html naturally, 
    # but since our backend is in the root, it's better to just run from root and let static/ be served.
    # We will map "/" to serve "static/index.html"
    class CustomHandler(AnalyticsRequestHandler):
        def translate_path(self, path):
            if path == "/":
                return os.path.join(os.getcwd(), "static", "index.html")
            elif path.startswith("/static/"):
                return os.path.join(os.getcwd(), path[1:])
            else:
                # default fallback
                return os.path.join(os.getcwd(), "static", path[1:])

    server_address = ('', PORT)
    httpd = HTTPServer(server_address, CustomHandler)
    print(f"Starting server on http://localhost:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    print("Stopping server.")
    httpd.server_close()
