from functools import wraps
from .packet import *
from . import PORT

import socket
from io import BytesIO

BUFFER = 1024

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
                print(json)

                if pkg_class is None:
                    return Packet.fromjson(json)

                return pkg_class.fromjson(json)

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
