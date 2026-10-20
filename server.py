
import socket
import threading
import os
import json
import hashlib

HOST = "0.0.0.0"
PORT = 5000
SAVE_DIR = os.path.expanduser("~/LANshare/received_files")
CHUNK_SIZE = 4096


def read_header(conn):
    data = b""
    while b"\n" not in data:
        chunk = conn.recv(1)
        if not chunk:
            raise ConnectionError("Connection closed")
        data += chunk
        if len(data) > 65536:
            raise ValueError("Header too large")
    return json.loads(data.split(b"\n", 1)[0].decode())


def send_json(conn, data):
    conn.sendall(json.dumps(data).encode() + b"\n")


def unique_path(directory, filename):
    filename = os.path.basename(filename)
    name, ext = os.path.splitext(filename)
    counter = 0

    while True:
        candidate = filename if counter == 0 else f"{name} ({counter}){ext}"
        path = os.path.join(directory, candidate)

        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            return path, candidate, fd
        except FileExistsError:
            counter += 1


def handle_client(conn, addr):
    filepath = None

    try:
        request = read_header(conn)
        action = request.get("action")

        if action == "list":
            files = []
            for name in sorted(os.listdir(SAVE_DIR)):
                path = os.path.join(SAVE_DIR, name)
                if os.path.isfile(path):
                    files.append({
                        "name": name,
                        "size": os.path.getsize(path)
                    })

            send_json(conn, {"status": "success", "files": files})

        elif action == "upload":
            filename = os.path.basename(request["filename"])
            filesize = int(request["filesize"])
            expected_hash = request["sha256"]

            if not filename or filename in (".", "..") or filesize < 0:
                raise ValueError("Invalid file metadata")

            filepath, saved_name, fd = unique_path(SAVE_DIR, filename)
            received = 0
            digest = hashlib.sha256()

            with os.fdopen(fd, "wb") as file:
                while received < filesize:
                    chunk = conn.recv(min(CHUNK_SIZE, filesize - received))
                    if not chunk:
                        raise ConnectionError("Transfer interrupted")
                    file.write(chunk)
                    digest.update(chunk)
                    received += len(chunk)

            if digest.hexdigest() == expected_hash:
                send_json(conn, {"status": "success", "filename": saved_name})
                print(f"Uploaded: {saved_name} from {addr}")
                print("SHA-256 verification: PASSED")
            else:
                os.remove(filepath)
                filepath = None
                send_json(conn, {"status": "error", "message": "Checksum mismatch"})

        elif action == "download":
            filename = os.path.basename(request["filename"])
            path = os.path.join(SAVE_DIR, filename)

            if not os.path.isfile(path):
                send_json(conn, {"status": "error", "message": "File not found"})
                return

            filesize = os.path.getsize(path)
            digest = hashlib.sha256()

            with open(path, "rb") as file:
                while True:
                    chunk = file.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    digest.update(chunk)

            send_json(conn, {
                "status": "success",
                "filename": filename,
                "filesize": filesize,
                "sha256": digest.hexdigest()
            })

            with open(path, "rb") as file:
                while True:
                    chunk = file.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    conn.sendall(chunk)

            print(f"Downloaded: {filename} sent to {addr}")

        else:
            send_json(conn, {"status": "error", "message": "Unknown action"})

    except Exception as e:
        print(f"Error with {addr}: {e}")
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError:
                pass
    finally:
        conn.close()


def start_server():
    os.makedirs(SAVE_DIR, exist_ok=True)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen()
        print(f"LANshare server running on port {PORT}")

        while True:
            conn, addr = server.accept()
            threading.Thread(
                target=handle_client,
                args=(conn, addr),
                daemon=True
            ).start()


if __name__ == "__main__":
    start_server()
