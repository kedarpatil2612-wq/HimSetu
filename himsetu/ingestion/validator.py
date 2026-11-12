"""File validator for HIMSETU ingestion pipeline.

Validates that a file exists, is readable, and is non-empty before
any metadata extraction is attempted.
"""

from __future__ import annotations

from pathlib import Path

from himsetu.ingestion.models import ValidationResult, ValidationStatus


class FileValidator:
    """Performs basic file-level validation before ingestion.

    Checks:
      - File path exists.
      - Path points to a file (not a directory).
      - File is non-empty.

    Does not read or parse file contents; that is the handler's job.
    """

    def validate(self, path: Path) -> ValidationResult:
        """Validate that a file exists and is readable.

        Args:
            path: Path to the file to validate.

        Returns:
            ValidationResult with status and any diagnostic notes.
        """
        notes: list[str] = []

        if not path.exists():
            return ValidationResult(
                status=ValidationStatus.INVALID,
                notes=[f"File does not exist: {path}"],
                file_size_bytes=None,
            )

        if not path.is_file():
            return ValidationResult(
                status=ValidationStatus.INVALID,
                notes=[f"Path is not a file: {path}"],
                file_size_bytes=None,
            )

        size = path.stat().st_size

        if size == 0:
            return ValidationResult(
                status=ValidationStatus.INVALID,
                notes=["File is empty (0 bytes)."],
                file_size_bytes=0,
            )

        if size < 10:
            notes.append(f"File is very small ({size} bytes); may be incomplete.")
            return ValidationResult(
                status=ValidationStatus.WARNING,
                notes=notes,
                file_size_bytes=size,
            )

        return ValidationResult(
            status=ValidationStatus.VALID,
            notes=notes,
            file_size_bytes=size,
        )
