import asyncio
import json

import websockets


async def main() -> None:
    async with websockets.connect("ws://127.0.0.1:8741/ws") as w:
        hello = json.loads(await w.recv())
        assert hello["type"] == "hello" and hello["user_id"] == 1, hello
        await w.send(json.dumps({"ping": 1}))
        echo = json.loads(await w.recv())
        assert echo["type"] == "echo" and echo["data"] == {"ping": 1}, echo
        print("WS OK: hello + echo round-trip")


asyncio.run(main())
