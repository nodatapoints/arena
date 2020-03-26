#!/usr/bin/python3.7
from arena.client import game_client

@game_client
def client(id, begins):
    print('got id', id)

    if begins:
        print('beginning')
        print('move', 5)
        yield 5

    for i in range(10, 20):
        update = yield
        print('update', update)
        yield i
        print('move', i)


if __name__ == '__main__':
    client('localhost')
