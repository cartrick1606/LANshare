# LANshare
# LANshare: TCP File Transfer System

LANshare is a Python-based client-server application that enables file transfers over a TCP connection. It provides a simple way to upload, list, and download files while verifying file integrity using SHA-256 checksums.

## Features

- **TCP communication:** Reliable client-server communication using Python sockets.
- **File upload:** Transfer files from a client to the server.
- **File download:** Retrieve files stored on the server.
- **File listing:** View files available on the server.
- **Progress tracking:** Display transfer progress and speed.
- **Integrity verification:** Use SHA-256 hashing to verify transferred files.
- **Overwrite protection:** Automatically generate unique filenames to preserve existing files.
- **Multithreading:** Handle multiple client connections using Python's threading module.

## Technologies Used

- Python 3
- `socket` for TCP networking
- `threading` for concurrent client handling
- `hashlib` for SHA-256 checksums
- `json` for exchanging file metadata
- `os` for file and directory management

## Project Structure

```text
LANshare/
├── client.py
├── server.py
├── README.md
└── .gitignore
```

## Requirements

- Python 3 installed on the client and server machines.
- A local network connection when transferring between separate computers.
- No third-party Python packages are required.

## Getting Started

### 1. Start the server

Navigate to the directory containing `server.py` and run:

```bash
python3 server.py
```

The server listens on TCP port `5000`.

### 2. Start the client

On the client machine, run:

```bash
python client.py
```

Enter the server's IP address when prompted. Use `127.0.0.1` for local testing when the client and server can communicate through localhost.

### 3. Choose an operation

The client provides the following menu:

1. Upload a file
2. List files on the server
3. Download a file
4. Exit

Downloaded files are saved in the client's `downloads/` directory. Uploaded files are stored in the server's `received_files/` directory.

## How It Works

1. The client establishes a TCP connection with the server.
2. JSON metadata communicates the requested operation and relevant file information.
3. Files are transferred in chunks to avoid loading entire files into memory.
4. SHA-256 checksums verify file integrity.
5. The server handles incoming client connections using threads.

## Testing

The project has been tested locally using Windows and Windows Subsystem for Linux (WSL).

The initial file-transfer test successfully transferred a 10 MB test file. Progress tracking and SHA-256 verification were also tested.

File listing and downloading should be tested separately before treating those features as fully verified.

## Limitations

- The application does not currently implement client authentication or encrypted transfers.
- It is intended for educational use on trusted networks.
- Network configuration and firewall rules may affect connections between separate computers.

## Future Improvements

- Graphical user interface using Tkinter.
- Client authentication and encrypted communication.
- Improved transfer error recovery.
- Transfer history and logging.

## Author

Karthik

## License

No license has been added yet. All rights are reserved by default until a license is selected.
