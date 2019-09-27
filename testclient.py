#!/usr/bin/python3.7

import asyncio
import sys
import json
import random

async def send(writer, data: dict):
    raw = json.dumps(data).encode()

    print(raw)
    writer.write(raw+b'\n')
    await writer.drain()

async def client():
    reader, writer = await asyncio.open_connection('127.0.0.1', 5054)

    id = '{:05d}'.format(random.randint(100000)) 

    await send(writer,
        {'type': 'register', 'id': id}
    )
    await send(writer,
        {'type': 'register', 'id': id+'2'}
    )

    for message in messages:
        id, payload = message.split()
        data = {
            'id': id,
            'type': 'message',
            'payload': payload
        }
        await send(writer, data)
        # await asyncio.sleep(1)
    writer.close()

asyncio.run(client())
