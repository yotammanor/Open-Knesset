class APIException(Exception):
    """
    Base class for Api exceptions. copied from REST framework
    Subclasses should provide `.status_code` and `.default_detail` properties.
    """
    status_code = 500
    default_detail = ''

    def __init__(self, detail=None):
        self.detail = detail or self.default_detail

    def __str__(self):
        return self.detail


class HttpBadRequest(APIException):
    status_code = 500
    detail = 'The provided data was invalid'
