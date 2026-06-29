from fastapi import HTTPException, status


class APIException(HTTPException):
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)


class EntityNotFoundException(APIException):
    def __init__(self, entity_name: str, identifier: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{entity_name} identified by {identifier} was not found.",
        )


# Map common status codes to custom HTTP exceptions
class UnauthorizedException(APIException):
    def __init__(self, detail: str = "Could not authenticate credentials"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)
