from .packet import ErrorPacket, ErrorMessage, ClientErrorMessage

class JSONSyntaxError(ClientErrorMessage):
    """Invalid JSON Syntax"""
    code = 301

class TerminalError(ErrorMessage):
    pass

class InternalServerError(ErrorMessage):
    """this was not supposed to happen"""
    code = 500

class ConnectionError(TerminalError):
    """Connection broke"""
    code = 100


class TimeoutError(TerminalError):
    """Client timed out"""
    code = 101
