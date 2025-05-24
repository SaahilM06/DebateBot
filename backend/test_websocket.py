import asyncio
import websockets

async def test_client():
    uri = "ws://localhost:8771"
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected!")
            greeting = await websocket.recv()
            print(f"Server says: {greeting}")
            
            # Listen for transcriptions
            while True:
                message = await websocket.recv()
                print(f"Transcription: {message}")
    except Exception as e:
        print(f"Connection failed: {e}")

asyncio.run(test_client())