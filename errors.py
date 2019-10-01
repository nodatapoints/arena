class BaseError(Exception):
    """Base error for every exception that will be transported to the client"""
    def __init__(self, exception: Exception=None, **kwargs):
        super().__init__(self.__class__.__doc__)
        self.description = self.__class__.__doc__
        self.additional_args = kwargs
        if exception is not None:
            original_arg, = exception.args  # FIXME might break
            self.description += ': '+original_arg

    @property
    def code(self):
        raise NotImplementedError(f'No code found for exception {type(self)}')

    @property
    def json(self) -> dict:
        return {
            "type": "err",
            "code": self.code,
            "description": self.description,
            "additional_info": self.additional_args
        }

class JSONSyntaxError(BaseError):
    """Invalid JSON Syntax"""
    code = 301
