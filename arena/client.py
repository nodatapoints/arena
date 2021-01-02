from functools import wraps
from asyncio.streams import StreamReader, StreamWriter, open_connection

from .packet import *
from . import PORT


class ClientProxy:
    def __init__(self, ip):
        self.reader, self.writer = None, None
        self.id = None
        self.ip = ip
    async def __aenter__(self):
        self.reader, self.writer = await open_connection(self.ip, PORT)
        await self.sync()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self.writer.close()
        print('waiting for close')
        await self.writer.wait_closed()

    async def send(self, pkg: Packet):
        self.writer.write(pkg.tojson())
        await self.writer.drain()

    async def sync(self):
        await self.send(SyncPacket())
        reply = await self.receive(SyncReplyPacket)
        self.id = reply.id
        return reply

    async def receive(self, pkg_class=None):
        json = await self.reader.readuntil()
        if pkg_class is None:
            return Packet.fromjson(json)

        return pkg_class.fromjson(json)


def game_client(gen):
    @wraps(gen)
    def wrapped(address):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server = address, PORT
            sock.connect(server)

            fobj = sock.makefile('rb')
            def recv(pkg_class=None):
                json = fobj.readline()
                if not json:
                    return None

            def send(pkg):
                sock.sendall(pkg.tojson())

            send(SyncPacket())
            sync = recv(SyncReplyPacket)

            first_pkg = recv()
            beginning = first_pkg.typ is PacketType.GET

            client = gen(sync.id, beginning)
            move = next(client)
            if beginning:
                send(MovePacket(move))

            else:
                move = client.send(first_pkg.update)

            next(client)

            while True:
                packet = recv()
                if packet is None:
                    break

                if packet.typ is PacketType.END:
                    print('ended', packet.status)

                elif packet.typ is PacketType.ERROR:
                    print('error', packet)
                
                elif packet.typ is PacketType.UPDATE:
                    move = client.send(packet.update)
                    next(client)

                elif packet.typ is PacketType.GET:
                    send(MovePacket(move))

                else:
                    print('dont know what to do with', packet)
                    break

        except:
            raise

        finally:
            sock.close()

    return wrapped
