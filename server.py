#!/usr/bin/python3.7

import asyncio
from distributor import Distributor, Player
from match import Matchmaker

mm = Matchmaker()

async def handle_player(player):
    match = await mm.get_match(player)
    await match.carry_out()

async def handle_connection(reader, writer):
    dist = Distributor(reader, writer)

    async for player in dist.new_players():
        asyncio.create_task(handle_player(player))

async def main():
    server = await asyncio.start_server(handle_connection,
        '25.58.122.144', 5054)

    async with server:
        await server.serve_forever()

asyncio.run(main())
