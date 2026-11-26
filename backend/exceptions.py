from fastapi import status


class AppError(Exception):
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, message: str):
        self.message = message or "App error"
        super().__init__(self.message)


class NotFound(AppError):
    status_code = status.HTTP_404_NOT_FOUND


class ConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT


class InvalidInput(AppError):
    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
