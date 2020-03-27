#!/usr/bin/python3.7

import asyncio
from arena.game import AlternatingGame

class TestGame(AlternatingGame):
    def valid(self, player, move) -> bool:
        return True

    @property
    def end_status(self):
        return "blooop"

    def play(self):
        for _ in range(5):
            move = yield
            print('got', move)
            yield move
            print('yielded', move)


asyncio.run(TestGame.run_server('localhost'))
