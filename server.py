import socket
import argparse
import socketserver
from multiprocessing import Pool
from httpserver import HttpServer

HOST, PORT = "127.0.0.1", 8888
http_server_instance = HttpServer()

class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
    def handle(self):
        try:
            data = self.request.recv(65535).strip()
            if not data:
                return
            
            print(f"Thread-{self.request.fileno()}: Received request")
            response = http_server_instance.process(data)

            self.request.sendall(response)
        except Exception as e:
            print(f"Error in request handler thread: {e}")

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

def run_thread_pool_server():
    print(f"Starting THREAD POOL server on {HOST}:{PORT}")
    
    socketserver.TCPServer.allow_reuse_address = True
    server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)
    print("Server loop running in thread pool.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down thread pool server.")
        server.shutdown()
        server.server_close()

def handle_connection_for_process(connection):
    """
    Worker function for the process pool. Handles a single client connection.
    """
    try:
        data = connection.recv(65535).strip()
        if not data:
            connection.close()
            return
            
        print("Process worker: Received request")
        response = http_server_instance.process(data)
        
        connection.sendall(response)
        connection.close()
    except Exception as e:
        print(f"Error in process worker: {e}")
    finally:
        connection.close()


def run_process_pool_server():
    """Starts the server using a process pool."""
    print(f"Starting PROCESS POOL server on {HOST}:{PORT}")
    num_processes = 4 
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen(5)
        print(f"Server listening. Process pool size: {num_processes}")
        
        with Pool(processes=num_processes) as pool:
            try:
                while True:
                    conn, addr = server_socket.accept()
                    print(f"Accepted connection from {addr}")
                    pool.apply_async(handle_connection_for_process, (conn,))
            except KeyboardInterrupt:
                print("\nShutting down process pool server.")
                pool.close()
                pool.join()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a concurrent HTTP server.")
    parser.add_argument(
        '--mode',
        choices=['thread', 'process'],
        required=True,
        help="Concurrency mode: 'thread' for thread pool, 'process' for process pool."
    )
    args = parser.parse_args()

    if args.mode == 'thread':
        run_thread_pool_server()
    elif args.mode == 'process':
        run_process_pool_server()
