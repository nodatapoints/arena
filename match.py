import asyncio

from distributor import Player
from game import Game

class Match:  # TODO inherit from Game
    def __init__(self, *players):
        self.players = players
        self.running = False
        self.end_event = asyncio.Event()

        for p in players:
            p.match = self

    async def get_move(self, player: Player, was_invalid: bool):
        await player.send({
            'type': 'get_move',
            'repeat': was_invalid})
        return await player.receive()
    
    def valid(self, player, move) -> bool:
        return True

    async def poll_valid_move(self, player) -> dict:
        was_invalid = False
        while True:  # TODO timeout
            move = await self.get_move(player, was_invalid=was_invalid)
            if self.valid(player, move):
                return move

            was_invalid = True

    async def poll_moves(self):
        #breakpoint()
        return await asyncio.gather(*(
            self.poll_valid_move(p) for p in self.players))

    async def broadcast(self, message):
        await asyncio.gather(*(p.send(message) for p in self.players))

    async def carry_out(self):  # TODO better name
        if self.running:
            await self.end_event.wait()
            return
        self.running = True

        await self.broadcast({'type': 'playerinfo', 'content': [p.player_id for p in self.players]})
        for _ in range(5):
            moves = await self.poll_moves()
            #breakpoint()
            await self.broadcast({'moves': moves})

        await self.broadcast({'type': 'end', 'comment':'l8r bitches'})

        self.end_event.set()

class Matchmaker:
    def __init__(self):
        self.candidates = []
        self.matches = []
        self.global_lock = asyncio.Lock()

    def match_approved(self, a: Player, b: Player) -> bool:
        return True  # a.address != b.address

    async def get_match(self, player: Player) -> Match:
        async with self.global_lock:
            for opponent in self.candidates:
                if self.match_approved(player, opponent):
                    self.candidates.remove(opponent)

                    match = Match(player, opponent)
                    self.matches.append(match)
                    return match

            else:
                self.candidates.append(player)

        return await player.match
