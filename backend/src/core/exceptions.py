"""
Custom exceptions for the Material Test Processor application.

This module defines a hierarchy of exceptions for consistent error handling
across the application. All custom exceptions inherit from AppError.
"""


class AppError(Exception):
    """Base exception for all application errors.

    Attributes:
        message: Human-readable error description.
        details: Optional additional context or data about the error.
    """

    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class ValidationError(AppError):
    """Raised when input validation fails.

    Examples:
        - Invalid dimension values (negative, zero, out of range)
        - Missing required fields
        - Invalid data types
    """

    pass


class ProcessingError(AppError):
    """Raised when data processing or calculations fail.

    Examples:
        - Division by zero in formula evaluation
        - Missing required columns during processing
        - Calculation overflow or invalid results
    """

    pass


class FileFormatError(AppError):
    """Raised when file parsing or format validation fails.

    Examples:
        - Invalid CSV structure
        - Missing header rows
        - Unsupported file encoding
    """

    pass


class FormulaError(AppError):
    """Raised when formula evaluation fails.

    Examples:
        - Invalid formula syntax
        - Unknown variable references
        - Circular dependencies
    """

    pass


class ConfigurationError(AppError):
    """Raised when application configuration is invalid.

    Examples:
        - Invalid column mapping
        - Missing required configuration
        - Incompatible settings
    """

    pass
