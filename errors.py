class BaseError(Exception):
    """Base error for every exception that will be transported to the client"""
    def __init__(self, exception: Exception, **kwargs):
        super().__init__(self.__class__.__doc__)
        self.info, = exception.args  # FIXME might break
        self.additional_args = kwargs

    @property
    def code(self):
        raise NotImplementedError(f'No code found for exception {type(self)}')

    @property
    def json(self) -> dict:
        return {
            "type": "err",
            "code": self.code,
            "description": self.__class__.__doc__ + ': ' + self.info,
            "additional_info": self.additional_args
        }

class JSONSyntaxError(BaseError):
    """Invalid JSON Syntax"""
    code = 301
