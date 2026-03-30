import asyncio
import websockets

connected = set()

async def handler(websocket):
    connected.add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        connected.remove(websocket)

async def input_loop():
    while True:
        key = await asyncio.get_event_loop().run_in_executor(None, input, "")
        if key == "g":
            msg = "target"
        elif key == "r":
            msg = "enemy"
        else:
            continue
        for ws in connected:
            await ws.send(msg)

async def main():
    async with websockets.serve(handler, "localhost", 8765):
        print("WebSocket server running on ws://localhost:8765")
        await input_loop()

asyncio.run(main())