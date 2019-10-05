import asyncio
import json

from errors import *

class Distributor:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.reader, self.writer = reader, writer
        self.address = writer.get_extra_info('peername')
        self.players = {}

        # TODO wait for event and start externally
        self.listening_task = asyncio.create_task(self.listen())
        self.new_player_queue = asyncio.Queue()

    async def handle_incoming_message(self):
        try:
            raw = await self.reader.readuntil()
            data = json.loads(raw)

            if data['type'] == 'register':
                await self.new_player_queue.put(data)
                return

            player_id = data['id']
            # TODO check for errors
            player = self.players[player_id]
            await player.queue.put(data['payload'])

        except KeyError:
            raise

        except asyncio.streams.IncompleteReadError:
            raise

        except json.JSONDecodeError as e:
            raise JSONSyntaxError(e)

    async def listen(self):
        while True:
            try:
                await self.handle_incoming_message()

            except ClientError as e:
                await self.send(e.json)

    async def send(self, data: dict):
        raw = json.dumps(data).encode('ascii')
        self.writer.write(raw)
        await self.writer.drain()

    async def new_players(self):
        while True:
            request = await self.new_player_queue.get()
            player = Party(self)
            self.players[player.id] = player
            self.new_player_queue.task_done()
            yield player


class PartyProxy:
    id = 0

    def __init__(self, distributor: Distributor):
        self.id = PartyProxy.id
        PartyProxy.id += 1

        self.distributor = distributor
        self.address = distributor.address  # spaghet

        self.queue = asyncio.Queue()

    async def send(self, data: dict):  # TODO custom data class
        await self.distributor.send({
            'gameid': self.id,
            **data
        })

    async def receive(self) -> dict:
        payload = await self.queue.get()
        self.queue.task_done()
        return payload

class Party(PartyProxy):
    def __init__(self, distributor: Distributor):
        super().__init__(distributor)

        loop = asyncio.get_event_loop()
        self.matched_fut = loop.create_future()

    @property
    def match(self):
        if self.matched_fut.done():
            return self.matched_fut.result()

        return self.matched_fut

    @match.setter
    def match(self, value):
        self.matched_fut.set_result(value)
