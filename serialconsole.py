import serial
import threading
import pygame
import asyncio
from bleak import BleakScanner, BleakClient, BleakGATTCharacteristic

async def live_move_mode(mode=0, client = None):
    global move_direction
    pygame.init()
    screen = pygame.display.set_mode((300, 100))
    pygame.display.set_caption("Live Move Control")
    clock = pygame.time.Clock()
    print(f"Window caption set to: {pygame.display.get_caption()}")
    running = True
    color = (0, 0, 0)
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
                    if mode:
                        data = bytearray(f"/move {move_direction} 70\n".encode())
                        await client.write_gatt_char(WRITE_UUID, data, response=False)
                    else:
                        board.write(f"/move {move_direction} 70\n".encode())
            elif event.type == pygame.KEYUP:
                if event.key in [pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d]:
                    color = (0, 0, 0)
                    if mode:
                        data = bytearray("/move 1 0\n".encode())
                        await client.write_gatt_char(WRITE_UUID, data, response=False)
                    else:
                        board.write("/move 1 0\n".encode())

        screen.fill(color)
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()

connect_type = input("Connect with Bluetooth or Serial? (B/S): ").lower().strip()

async def serial_main():
    global board
    board = serial.Serial("COM3", 115200, timeout=1)
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

    async def write_loop():
        global move_direction
        while True:
            cmd = input()
            if cmd == "/livemove":
                print("Entering live move mode. Press WASD to move, ESC to exit.")
                await live_move_mode()
            else:
                board.write((cmd + '\n').encode())

    read_thread = threading.Thread(target=read_loop, daemon=True)
    read_thread.start()

    try:
        await write_loop()
    except KeyboardInterrupt:
        print("\nDisconnected.")
        board.close()

if connect_type in ("b", "bluetooth"):
    WRITE_UUID = "0000ffe3-0000-1000-8000-00805f9b34fb"
    NOTIFY_UUID = "0000ffe2-0000-1000-8000-00805f9b34fb"
    buffer = ""

    def notification_handler(characteristic: BleakGATTCharacteristic, data: bytearray):
        global buffer
        buffer += data.decode('utf-8', errors='replace')
        if '\n' in buffer:
            lines = buffer.split('\n')
            for line in lines[:-1]:
                print(f"[STR]: {line.strip()}")
            buffer = lines[-1]

    async def input_loop(client: BleakClient):
        loop = asyncio.get_event_loop()
        live_move_task = None
        while True:
            text = await loop.run_in_executor(None, input, "")
            if text == "/livemove":
                if live_move_task is None or live_move_task.done():
                    print("Entering live move mode. Press WASD to move, ESC to exit.")
                    live_move_task = asyncio.create_task(live_move_mode(1, client))
                else:
                    print("Live move mode already running!")
            else:
                data = bytearray((text + '\n').encode())
                await client.write_gatt_char(WRITE_UUID, data, response=False)

    async def main():
        print("Scanning for mBot...")
        devices = await BleakScanner.discover(timeout=5)

        mbot = None
        for device in devices:
            if device.name and "Makeblock" in device.name:
                mbot = device
                break

        if not mbot:
            print("mBot not found!")
            return

        print(f"Connecting to {mbot.name}...")
        async with BleakClient(mbot.address) as client:
            print("Connected! Type to send, received data will print automatically.")

            await client.start_notify(NOTIFY_UUID, notification_handler)

            await input_loop(client)
    asyncio.run(main())

elif connect_type in ("s", "serial"):
    asyncio.run(serial_main())
