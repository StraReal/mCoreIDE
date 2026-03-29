import serial
import threading
import pygame
import sys

board = serial.Serial("COM3", 57600, timeout=1)
print(f"Connected to {board.name}. Type commands to send, Ctrl+C to quit.\n")

print_raw_and_hex = False

move_direction = None

def read_loop():
    while True:
        line = board.readline()
        if line:
            if print_raw_and_hex:
                print(f"[RAW] {line}")
                print(f"[HEX] {line.hex()}")
            print(f"[STR] {line.decode(errors='ignore').strip()}")

def write_loop():
    global move_direction
    while True:
        cmd = input()
        if cmd == "/livemove":
            print("Entering live move mode. Press WASD to move, ESC to exit.")
            live_move_mode()
        else:
            board.write((cmd + '\n').encode())

def live_move_mode():
    global move_direction
    pygame.init()
    screen = pygame.display.set_mode((300, 100))
    pygame.display.set_caption("Live Move Control")
    clock = pygame.time.Clock()
    print(f"Window caption set to: {pygame.display.get_caption()}")
    running = True
    color = (0,0,0)
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_w:
                    move_direction = 1
                    color = (127, 0, 0)
                elif event.key == pygame.K_s:
                    move_direction = 2
                    color = (0, 0, 127)
                elif event.key == pygame.K_a:
                    move_direction = 3
                    color = (127, 64, 0)
                elif event.key == pygame.K_d:
                    move_direction = 4
                    color = (10, 127, 0)
                if move_direction:
                    board.write(f"/move {move_direction} 50\n".encode())
            elif event.type == pygame.KEYUP:
                if event.key in [pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d]:
                    color = (0, 0, 0)
                    board.write(f"/move 1 0\n".encode())



        screen.fill(color)
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()

read_thread = threading.Thread(target=read_loop, daemon=True)
read_thread.start()

try:
    write_loop()
except KeyboardInterrupt:
    print("\nDisconnected.")
    board.close()
