import requests
import argparse
import os
from html.parser import HTMLParser

BASE_URL = "http://127.0.0.1:8888"

class MyHTMLParser(HTMLParser):
    def handle_data(self, data):
        if data.strip():
            print(data)
            
def list_files():
    try:
        response = requests.get(f"{BASE_URL}/list")
        print("--- Server File List ---")
        if response.headers.get('Content-Type') == 'text/html':
             print("Received HTML response. To view, save to a file and open in a browser.")
             parser = MyHTMLParser()
             parser.feed(response.text)
        else:
             print(response.text)
        print("------------------------")
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error listing files: {e}")

def upload_file(local_path, remote_name):
    if not os.path.exists(local_path):
        print(f"Error: Local file '{local_path}' not found.")
        return

    try:
        with open(local_path, 'rb') as f:
            file_data = f.read()

        headers = {'X-File-Name': remote_name}
        url = f"{BASE_URL}/upload"
        
        print(f"Uploading '{local_path}' as '{remote_name}'...")
        response = requests.post(url, data=file_data, headers=headers)
        
        print(f"Server response ({response.status_code}):")
        print(response.text)
        response.raise_for_status()
        print("Upload successful!")

    except requests.exceptions.RequestException as e:
        print(f"Error uploading file: {e}")

def delete_file(remote_name):
    try:
        url = f"{BASE_URL}/{remote_name}"
        print(f"Requesting to delete '{remote_name}'...")
        response = requests.delete(url)
        
        print(f"Server response ({response.status_code}):")
        print(response.text)
        response.raise_for_status()
        print("Delete request sent successfully.")

    except requests.exceptions.RequestException as e:
        print(f"Error deleting file: {e}")

def main():
    parser = argparse.ArgumentParser(description="Client for the Enhanced HTTP Server.")
    subparsers = parser.add_subparsers(dest='command', required=True, help='sub-command help')

    parser_list = subparsers.add_parser('list', help='List files on the server')
    
    parser_upload = subparsers.add_parser('upload', help='Upload a file to the server')
    parser_upload.add_argument('local_path', help='The path to the local file to upload')
    parser_upload.add_argument('remote_name', help='The name the file will have on the server')
    
    parser_delete = subparsers.add_parser('delete', help='Delete a file from the server')
    parser_delete.add_argument('remote_name', help='The name of the file to delete on the server')

    args = parser.parse_args()

    if args.command == 'list':
        list_files()
    elif args.command == 'upload':
        upload_file(args.local_path, args.remote_name)
    elif args.command == 'delete':
        delete_file(args.remote_name)

if __name__ == "__main__":
    main()
