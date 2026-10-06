from fastapi import HTTPException, status

class PolicyRAGException(Exception):
    def __init__(self, message: str, status_code: int = 500, details: dict = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}

class PolicyNotFoundException(PolicyRAGException):
    def __init__(self, policy_id: int):
        super().__init__(f"Policy with ID {policy_id} not found", status_code=404)

class PolicyConflictException(PolicyRAGException):
    def __init__(self, message: str, conflicting_policies: list = None):
        super().__init__(message, status_code=409, details={"conflicts": conflicting_policies or []})

class UnanswerableQueryException(PolicyRAGException):
    def __init__(self, query: str, reason: str = "No sufficient policy evidence found"):
        super().__init__(reason, status_code=200, details={"query": query, "answerable": False})

class InvalidCredentialsException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

class InsufficientPermissionsException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have required permissions",
        )
