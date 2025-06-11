import os
import os.path
import uuid
from glob import glob
from datetime import datetime
import urllib.parse

class HttpServer:
    def __init__(self):
        self.sessions = {}
        self.types = {}
        self.types['.pdf'] = 'application/pdf'
        self.types['.jpg'] = 'image/jpeg'
        self.types['.png'] = 'image/png'
        self.types['.txt'] = 'text/plain'
        self.types['.html'] = 'text/html'
        self.upload_dir = './uploads'
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)

    def response(self, code=404, message='Not Found', body=b'', headers={}):
        date_str = datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
        if not isinstance(body, bytes):
            body = body.encode('utf-8')

        resp = []
        resp.append(f"HTTP/1.1 {code} {message}\r\n")
        resp.append(f"Date: {date_str}\r\n")
        resp.append("Connection: close\r\n")
        resp.append("Server: MyEnhancedServer/1.0\r\n")
        resp.append(f"Content-Length: {len(body)}\r\n")
        for key, value in headers.items():
            resp.append(f"{key}: {value}\r\n")
        resp.append("\r\n")

        response_headers = "".join(resp)
        return response_headers.encode('utf-8') + body

    def parse_request(self, data):
        parts = data.split(b'\r\n\r\n', 1)
        header_part = parts[0]
        body = parts[1] if len(parts) > 1 else b''

        header_lines = header_part.split(b'\r\n')
        request_line = header_lines[0].decode('utf-8').strip()
        
        try:
            method, path, _ = request_line.split(' ')
        except ValueError:
            return None, None, None, None

        headers = {}
        for line in header_lines[1:]:
            line_str = line.decode('utf-8').strip()
            if ':' in line_str:
                key, value = line_str.split(':', 1)
                headers[key.strip()] = value.strip()
        
        return method.upper(), path, headers, body

    def process(self, data):
        method, path, headers, body = self.parse_request(data)

        if not method:
            return self.response(400, 'Bad Request', 'Invalid request line')

        print("\n--- Received Headers ---")
        for key, value in headers.items():
            print(f"{key}: {value}")
        print("------------------------")
        path = urllib.parse.unquote(path)

        if method == 'GET':
            return self.http_get(path, headers)
        elif method == 'POST':
            return self.http_post(path, headers, body)
        elif method == 'DELETE':
            return self.http_delete(path, headers)
        else:
            return self.response(405, 'Method Not Allowed', f"Method {method} is not supported.")

    def http_get(self, path, headers):
        """
        Handles GET requests.
        - /: Returns a welcome message.
        - /list: Returns an HTML page listing files.
        - /<filename>: Returns the requested file.
        """
        if path == '/':
            return self.response(200, 'OK', 'Welcome to the Enhanced File Server!', {'Content-Type': 'text/plain'})

        if path == '/list':
            try:
                files = os.listdir(self.upload_dir)
                html_body = "<html><head><title>File Listing</title></head><body><h1>Files in /uploads/</h1><ul>"
                for f in files:
                    html_body += f"<li>{f}</li>"
                html_body += "</ul></body></html>"
                return self.response(200, 'OK', html_body, {'Content-Type': 'text/html'})
            except Exception as e:
                return self.response(500, 'Internal Server Error', f"Could not list directory: {e}")

        safe_path = os.path.normpath(os.path.join(self.upload_dir, path.lstrip('/')))
        
        if not safe_path.startswith(os.path.abspath(self.upload_dir)):
            return self.response(403, 'Forbidden', 'Access denied.')

        if not os.path.exists(safe_path) or os.path.isdir(safe_path):
            return self.response(404, 'Not Found', f'File not found: {path}')

        try:
            with open(safe_path, 'rb') as fp:
                file_content = fp.read()
            
            _, fext = os.path.splitext(safe_path)
            content_type = self.types.get(fext.lower(), 'application/octet-stream')
            
            return self.response(200, 'OK', file_content, {'Content-Type': content_type})
        except Exception as e:
            return self.response(500, 'Internal Server Error', f"Could not read file: {e}")

    def http_post(self, path, headers, body):
        if path != '/upload':
            return self.response(400, 'Bad Request', "POST requests are only for '/upload'.")

        filename = headers.get('X-File-Name')
        if not filename:
            return self.response(400, 'Bad Request', "Header 'X-File-Name' is required for upload.")

        if '..' in filename or '/' in filename or '\\' in filename:
             return self.response(400, 'Bad Request', 'Invalid filename.')

        file_path = os.path.join(self.upload_dir, filename)
        
        try:
            with open(file_path, 'wb') as f:
                f.write(body)
            print(f"File '{filename}' uploaded successfully.")
            return self.response(201, 'Created', f"File '{filename}' created.")
        except Exception as e:
            print(f"Error uploading file: {e}")
            return self.response(500, 'Internal Server Error', f"Could not save file: {e}")

    def http_delete(self, path, headers):
        """
        Handles DELETE requests to remove a file from the uploads directory.
        """
        filename = path.lstrip('/')
        
        if not filename or '..' in filename or '/' in filename or '\\' in filename:
             return self.response(400, 'Bad Request', 'Invalid filename for deletion.')
        
        file_path = os.path.join(self.upload_dir, filename)

        if not os.path.exists(file_path):
            return self.response(404, 'Not Found', f"File '{filename}' not found.")
        
        if os.path.isdir(file_path):
            return self.response(400, 'Bad Request', "Cannot delete a directory.")

        try:
            os.remove(file_path)
            print(f"File '{filename}' deleted successfully.")
            return self.response(200, 'OK', f"File '{filename}' deleted.")
        except Exception as e:
            print(f"Error deleting file: {e}")
            return self.response(500, 'Internal Server Error', f"Could not delete file: {e}")
