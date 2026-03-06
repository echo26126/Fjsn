from enum import Enum
from fastapi import HTTPException
from typing import Optional, Any

class ErrorCode(int, Enum):
    SUCCESS = 200
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    SERVER_ERROR = 500
    VALIDATION_ERROR = 422
    
    # Business Errors
    DATA_NOT_FOUND = 1001
    INVALID_PARAM = 1002
    OPERATION_FAILED = 1003

class APIException(HTTPException):
    def __init__(
        self,
        code: int = ErrorCode.SERVER_ERROR,
        msg: str = "Internal Server Error",
        detail: Any = None,
        headers: Optional[dict[str, str]] = None,
    ) -> None:
        self.code = code
        self.msg = msg
        super().__init__(status_code=code, detail=msg, headers=headers)
