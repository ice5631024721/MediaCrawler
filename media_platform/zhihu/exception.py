from httpx import RequestError


class DataFetchError(RequestError):
    """something error when fetch"""