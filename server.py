#!/usr/bin/python3.7

import asyncio
from arena.game import AlternatingGame

class TestGame(AlternatingGame):
    def __init__(self):
        self._running = False

    def valid(self, player, move) -> bool:
        return True

    @property
    def running(self):
        return self._running

    @property
    def end_status(self):
        return "blooop"

    def play(self):
        self._running = True
        for _ in range(5):
            move = yield
            print('got', move)
            yield move
            print('yielded', move)

        self._running = False


asyncio.run(TestGame.run_server('localhost'))
