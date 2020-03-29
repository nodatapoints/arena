import asyncio
from contextlib import asynccontextmanager
from itertools import cycle
from abc import ABCMeta, abstractmethod

from .player import Party

from .packet import *
from .errors import *


class BasicMatch(metaclass=ABCMeta):
    def __init__(self, game, *players):
        self.players = players
        self.running = False
        self.end_event = asyncio.Event()
        self.game = game

        for p in players:
            p.match = self

    async def get_move(self, player: Party, was_invalid: bool):
        pkg = GetMovePacket(repeat=was_invalid)
        await player.send(pkg)
        return await player.receive(MovePacket)
    
    async def poll_valid_move(self, player) -> dict:
        was_invalid = False
        while True:  # TODO timeout
            move = await self.get_move(player, was_invalid=was_invalid)
            if self.game.valid(player, move.move):
                return move

            was_invalid = True

    async def broadcast(self, message, ignore_fail=False):
        await asyncio.gather(*(p.send(message, ignore_fail) for p in self.players))
    async def send_to(self, player, message, ignore_fail=False):
        await player.send(message, ignore_fail)

    @abstractmethod
    async def play(self):
        pass

class SynchronousMatch(BasicMatch):
    async def poll_moves(self):
        return await asyncio.gather(*(
            self.poll_valid_move(p) for p in self.players))

    async def play(self):
        if self.running:
            await self.end_event.wait()
            return

        self.running = True

        try:
            match_gen = self.game.play()
            next(match_gen)
            while True:
                match_gen.send(await self.poll_moves())
                update = next(match_gen)
    
                await self.broadcast(update)

        except StopIteration:
            await self.broadcast(EndPacket(self.game.end_status))

        except TerminalError as e:
            await self.broadcast(e.packet, ignore_fail=True)

        finally:
            self.end_event.set()


class AlternatingMatch(BasicMatch):
    async def play(self):
        if self.running:
            await self.end_event.wait()

        self.running = True

        try:
            player_gen = cycle(self.players)
            player = next(player_gen)

            while self.game.running:
                other = player
                player = next(player_gen)

                move = await self.poll_valid_move(player)
                self.game.apply(player, move.move)

                await self.send_to(other, UpdatePacket(move.move))
                
            await self.broadcast(EndPacket(self.game.end_status), ignore_fail=True)

        except TerminalError as e:
            await self.broadcast(e.packet, ignore_fail=True)

        except:
            e = InternalServerError()
            await self.broadcast(e.packet, ignore_fail=True)
            raise

        finally:
            self.end_event.set()


class Matchmaker:
    def __init__(self, game_factory, match_cls=AlternatingMatch):
        self.candidates = []  # Make Queue
        self.matches = set()
        self.global_lock = asyncio.Lock()
        self.game_factory = game_factory
        self.match_cls = match_cls

    def match_approved(self, a: Party, b: Party) -> bool:
        return True

    async def get_match(self, player: Party) -> BasicMatch:
        async with self.global_lock:
            for opponent in self.candidates:
                if self.match_approved(player, opponent):
                    self.candidates.remove(opponent)

                    match = self.match_cls(self.game_factory(), player, opponent)
                    return match

            else:
                self.candidates.append(player)

        return await player.match

    @asynccontextmanager
    async def create_match(self, player: Party):
        match = await self.get_match(player)
        self.matches.add(match)
        yield match
        self.matches.discard(match)

