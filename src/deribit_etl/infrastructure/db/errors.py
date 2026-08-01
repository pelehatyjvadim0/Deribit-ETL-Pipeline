"""Database adapter errors exposed to infrastructure entry points."""


class DatabaseOperationError(Exception):
    """A database operation failed after entering the database adapter."""
