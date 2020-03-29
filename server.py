#!/usr/bin/python3.7

import asyncio
from arena.game import AlternatingGame

class TestGame(AlternatingGame):
    def __init__(self):
        self._running = False

    def valid(self, player, move) -> bool:
        return True

    @property
    def end_status(self):
        return "blooop"

    @property
    def running(self):
        return True

    def apply(self, player, move):
        pass

asyncio.run(TestGame.run_server('localhost'))
