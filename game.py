from enum import Enum
from typing import Tuple

Tile = Enum('Tile', 'EMPTY A B')

class Grid:
    def __init__(self, width: int, height: int):
        self.width, self.height = width, height
        self.data = [[Tile.EMPTY for _ in range(width)] for _ in range(height)]

    def __getitem__(self, pos: Tuple[int, int]) -> Tile:
        x, y = pos
        return self.data[y % self.height][x % self.width]

    def __setitem__(self, pos: Tuple[int, int], value: Tile) -> Tile:
        x, y = pos
        self.data[y % self.height][x % self.width] = value

class Game(Grid):
    width, height = 100, 100
    def __init__(self):
        super().__init__(self, Game.width, Game.height)

    def valid(self, player, change) -> bool:
        return True

    def apply(self, moves):
        pass
