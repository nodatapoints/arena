import asyncio
import json
from typing import Type

from .errors import *
from .packet import *

class Party:
    id_count = 0
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.reader, self.writer = reader, writer
        self.address = writer.get_extra_info('peername')
        self.id = self.id_count
        Party.id_count += 1

        loop = asyncio.get_event_loop()
        self.matched_fut = loop.create_future()

    async def __aenter__(self):
        await self.perform_sync()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self.writer.close()
        try:
            await self.writer.wait_closed()

        except BrokenPipeError:
            print('broken pipe')  # TODO

    @property
    def match(self):
        if self.matched_fut.done():
            return self.matched_fut.result()

        return self.matched_fut

    @match.setter
    def match(self, value):
        self.matched_fut.set_result(value)

    async def perform_sync(self):
        await self.receive(SyncPacket)
        await self.send(SyncReplyPacket(id=self.id)) 

    async def send(self, packet: Packet, ignore_fail=False):
        raw = packet.tojson()
        try:
            self.writer.write(raw)
            await self.writer.drain()

        except (ConnectionResetError, BrokenPipeError):
            if not ignore_fail:
                raise ConnectionError
        
    # Type[Packet] does not handle subclassing well
    async def _receive(self, parse_type: Type=None) -> Packet:
        while True:
            try:
                raw = await self.reader.readuntil()
                print(raw)
                data = json.loads(raw)
                if parse_type is None:
                    return data
                
                return parse_type.fromdict(data)

            except json.JSONDecodeError as e:
                e = JSONSyntaxError(*e.args)
                await self.send(e.packet)

            except ClientErrorMessage as e:
                await self.send(e.packet)

            except asyncio.IncompleteReadError:
                raise ConnectionError

    async def receive(self, parse_type: Type=None, timeout: float=None, ignore_timeout=False) -> Packet:
        try:
            return await asyncio.wait_for(self._receive(parse_type), timeout=timeout)
        except asyncio.TimeoutError:
            if not ignore_timeout:
                raise TimeoutError
