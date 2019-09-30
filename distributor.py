import asyncio
import json

from io import StringIO

class Distributor:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.reader, self.writer = reader, writer
        self.address = writer.get_extra_info('peername')
        self.players = {}

        # TODO wait for event and start externally
        self.listening_task = asyncio.create_task(self.listen())
        self.new_player_queue = asyncio.Queue()

    async def listen(self):
        while True:  # TODO proper loop
            try:
                raw = await self.reader.readuntil()
                data = json.loads(raw)

                if data['type'] == 'register':
                    await self.new_player_queue.put(data)
                    continue

                player_id = data['id']
                # TODO check for errors
                player = self.players[player_id]
                await player.queue.put(data['payload'])

            except KeyError:
                raise

            except asyncio.streams.IncompleteReadError:
                break

            except json.JSONDecodeError:
                raise  # Jaja funkt nicht und so TODO

    async def send(self, data: dict):
        raw = json.dumps(data).encode('ascii')
        self.writer.write(raw)
        await self.writer.drain()

    async def new_players(self):
        while True:
            request = await self.new_player_queue.get()
            player_id = request['id']  # TODO assign yourself
            player = Player(player_id, self)
            self.players[player_id] = player
            self.new_player_queue.task_done()
            yield player


class PlayerSocket:
    def __init__(self, player_id: str, distributor: Distributor):
        self.player_id = player_id  # TODO rename to id
        self.distributor = distributor
        self.address = distributor.address  # spaghet

        self.queue = asyncio.Queue()

    async def send(self, data: dict):  # TODO custom data class
        await self.distributor.send({
            'id': self.player_id,
            'data': data
        })

    async def receive(self) -> dict:
        payload = await self.queue.get()
        self.queue.task_done()
        return payload

class Player(PlayerSocket):
    def __init__(self, player_id: str, distributor: Distributor):
        super().__init__(player_id, distributor)

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
