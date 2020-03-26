import asyncio
from abc import ABCMeta, abstractmethod
from . import PORT
from .match import AlternatingMatch, SynchronousMatch, Matchmaker
from arena.player import Party

__all__ = 'SynchronousGame', 'AlternatingGame'

class Game(metaclass=ABCMeta):
    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def valid(self, player, move) -> bool:
        pass

    @abstractmethod
    def play(self):
        pass

    @property
    @abstractmethod
    def running(self) -> bool:
        pass

    @property
    @abstractmethod
    def end_status(self) -> bool:
        pass

    @classmethod
    async def run_server(cls, ip):
        mm = Matchmaker(cls, match_cls=cls.match_factory)

        async def handle_connection(reader, writer):
            async with Party(reader, writer) as player:
                match = await mm.get_match(player)
                await match.play()

        server = await asyncio.start_server(handle_connection, ip, PORT)

        async with server:
            await server.serve_forever()


class AlternatingGame(Game):
    match_factory = AlternatingMatch

class SynchronousGame(Game):
    match_factory = SynchronousMatch
