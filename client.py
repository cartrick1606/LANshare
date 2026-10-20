
import socket
import os
import json
import hashlib
import time

PORT = 5000
CHUNK_SIZE = 4096
DOWNLOAD_DIR = "downloads"


def send_json(sock, data):
    sock.sendall(json.dumps(data).encode() + b"\n")


def read_header(sock):
    data = b""
    while b"\n" not in data:
        chunk = sock.recv(1)
        if not chunk:
            raise ConnectionError("Connection closed")
        data += chunk
        if len(data) > 65536:
            raise ValueError("Header too large")
    return json.loads(data.split(b"\n", 1)[0].decode())


def file_hash(path):
    digest = hashlib.sha256()
    with open(path, "rb") as file:
        for chunk in iter(lambda: file.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def show_progress(done, total, start):
    elapsed = max(time.time() - start, 0.001)
    speed = done / elapsed / (1024 * 1024)
    percent = done / total * 100 if total else 100
    print(
        f"\rProgress: {percent:.1f}% | {done}/{total} bytes | "
        f"Speed: {speed:.2f} MB/s",
        end="",
        flush=True
    )


def upload(sock):
    path = input("File path to upload: ").strip().strip('"')

    if not os.path.isfile(path):
        print("File not found!")
        return

    size = os.path.getsize(path)
    digest = file_hash(path)

    send_json(sock, {
        "action": "upload",
        "filename": os.path.basename(path),
        "filesize": size,
        "sha256": digest
    })

    sent = 0
    start = time.time()

    with open(path, "rb") as file:
        while True:
            chunk = file.read(CHUNK_SIZE)
            if not chunk:
                break
            sock.sendall(chunk)
            sent += len(chunk)
            show_progress(sent, size, start)

    print()
    response = read_header(sock)

    if response.get("status") == "success":
        print("Upload successful!")
        print("SHA-256 verification: PASSED")
        print("Server filename:", response["filename"])
    else:
        print("Upload failed:", response.get("message"))


def list_files(sock):
    send_json(sock, {"action": "list"})
    response = read_header(sock)

    if response.get("status") != "success":
        print("Could not list server files.")
        return

    files = response["files"]
    if not files:
        print("No files on server.")
        return

    print("\nFiles available on server:")
    for item in files:
        print(f"  {item['name']} ({item['size']} bytes)")


def download(sock):
    filename = input("Exact filename on server: ").strip()

    send_json(sock, {"action": "download", "filename": filename})
    response = read_header(sock)

    if response.get("status") != "success":
        print("Download failed:", response.get("message"))
        return

    filename = os.path.basename(response["filename"])
    size = int(response["filesize"])
    expected_hash = response["sha256"]

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    name, ext = os.path.splitext(filename)
    destination = os.path.join(DOWNLOAD_DIR, filename)
    counter = 1

    while os.path.exists(destination):
        destination = os.path.join(DOWNLOAD_DIR, f"{name} ({counter}){ext}")
        counter += 1

    received = 0
    digest = hashlib.sha256()
    start = time.time()

    try:
        with open(destination, "xb") as file:
            while received < size:
                chunk = sock.recv(min(CHUNK_SIZE, size - received))
                if not chunk:
                    raise ConnectionError("Download interrupted")
                file.write(chunk)
                digest.update(chunk)
                received += len(chunk)
                show_progress(received, size, start)

        print()

        if digest.hexdigest() == expected_hash:
            print("Download successful!")
            print("SHA-256 verification: PASSED")
            print("Saved to:", os.path.abspath(destination))
        else:
            os.remove(destination)
            print("Checksum mismatch! Invalid download deleted.")

    except Exception:
        if os.path.exists(destination):
            os.remove(destination)
        raise


def main():
    host = input("Server IP (127.0.0.1 for local testing): ").strip()

    while True:
        print("\n=== LANshare ===")
        print("1. Upload file")
        print("2. List server files")
        print("3. Download file")
        print("4. Exit")

        choice = input("Choose: ").strip()

        if choice == "4":
            break

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((host, PORT))

                if choice == "1":
                    upload(sock)
                elif choice == "2":
                    list_files(sock)
                elif choice == "3":
                    download(sock)
                else:
                    print("Invalid choice.")

        except (OSError, ValueError, ConnectionError) as e:
            print("Error:", e)


if __name__ == "__main__":
    main()
