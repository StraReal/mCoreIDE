import serial
import threading

board = serial.Serial("COM3", 57600, timeout=1)
print(f"Connected to {board.name}. Type commands to send, Ctrl+C to quit.\n")

print_raw_and_hex = False

def read_loop():
    while True:
        line = board.readline()
        if line:
            if print_raw_and_hex:
                print(f"[RAW] {line}")
                print(f"[HEX] {line.hex()}")
            print(f"[STR] {line.decode(errors='ignore').strip()}")

def write_loop():
    while True:
        cmd = input()
        board.write((cmd + '\n').encode())

read_thread = threading.Thread(target=read_loop, daemon=True)
read_thread.start()

try:
    write_loop()
except KeyboardInterrupt:
    print("\nDisconnected.")
    board.close()