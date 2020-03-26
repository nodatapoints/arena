from dataclasses import dataclass, asdict, field, fields
from typing import ClassVar
from enum import Enum
from functools import wraps
import json

class PacketType(Enum):
    SYNC = 'sync'
    SYNC_REPLY = 'sync.reply'

    START = 'game.start'
    MOVE = 'game.move'
    GET = 'game.get'
    UPDATE = 'game.update'
    END = 'game.end'

    ERROR = 'error'

@dataclass
class DataDict:
    def asdict(self):
        return asdict(self)

    def tojson(self):
        raw = json.dumps(self.asdict()).encode('ascii')
        assert b'\n' not in raw
        return raw + b'\n'

    def __post_init__(self):
        for f in fields(self):
            if issubclass(f.type, DataDict):
                value = getattr(self, f.name)
                setattr(self, f.name, f.type(**value))


@dataclass
class Packet(DataDict):
    _type: ClassVar[str]
    registry: ClassVar[dict] = {}
    type: str = field(init=False)

    @staticmethod
    def packet(t):
        def decorator(cls):
            cls = dataclass(cls)
            cls._type = t.value
            Packet.registry[t.value] = cls
            return cls

        return decorator
    @classmethod
    def fromdict(cls, d: dict):
        try:
            typ = d.pop('type')
            if cls is Packet:
                cls = Packet.registry[typ]

            elif typ != cls._type:
                raise InvalidPacketType("expected package type " \
                    f"'{cls._type}', got '{type}'")

            return cls(**d)

        except KeyError:
            raise NoPacketTypeError()

        except AttributeError:
            raise InvalidDataFormat(f"expected 'dict', got '{d.__class__.__name__}'")

        except TypeError as e:
            raise UnknownKeyError(*e.args)

    @classmethod
    def fromjson(cls, buf):
        return cls.fromdict(json.loads(buf, encoding='ascii'))

    def __post_init__(self):
        DataDict.__post_init__(self)
        self.type = self._type
    
    @property
    def typ(self):
        return PacketType(self.type)


@Packet.packet(PacketType.SYNC)
class SyncPacket(Packet):
    pass


@Packet.packet(PacketType.SYNC_REPLY)
class SyncReplyPacket(Packet):
    id: int


@Packet.packet(PacketType.GET)
class GetMovePacket(Packet):
    repeat: bool


@Packet.packet(PacketType.MOVE)
class MovePacket(Packet):
    move: int


@Packet.packet(PacketType.UPDATE)
class UpdatePacket(Packet):
    update: int


@Packet.packet(PacketType.ERROR)
class ErrorPacket(Packet):
    code: int
    description: str
    additional_args: str


@Packet.packet(PacketType.END)
class EndPacket(Packet):
    status: str

# cyclic imports kill me

class ErrorMessage(Exception):
    """Base error for every exception that will be transported to the client"""
    def __init__(self, *args, **kwargs):
        self.description = self.__class__.__doc__
        self.additional_args = kwargs
        self.description += ': '+' '.join(args)

    @property
    def code(self):
        raise NotImplementedError(f'No code found for exception {type(self)}')

    @property
    def packet(self) -> ErrorPacket:
        return ErrorPacket(self.code, self.description, self.additional_args)

class ClientErrorMessage(ErrorMessage):
    pass

class InvalidPacketType(ClientErrorMessage):
    """Unexpected package received"""
    code = 302

class NoPacketTypeError(ClientErrorMessage):
    """No package type specified"""
    code = 303

class InvalidDataFormat(ClientErrorMessage):
    """Invalid packet format"""
    code = 304

class UnknownKeyError(ClientErrorMessage):
    """Invalid packet format"""
    code = 305

