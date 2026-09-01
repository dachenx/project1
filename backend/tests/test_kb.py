import pytest
from fastapi import HTTPException

from app.routers.kb import _validate_file_signature


def test_valid_pdf():
    _validate_file_signature(".pdf", b"%PDF-1.7 ...")


def test_invalid_pdf_raises():
    with pytest.raises(HTTPException):
        _validate_file_signature(".pdf", b"not a pdf")


def test_valid_docx():
    _validate_file_signature(".docx", b"PK\x03\x04 ...")


def test_invalid_docx_raises():
    with pytest.raises(HTTPException):
        _validate_file_signature(".docx", b"plain text")


def test_text_with_null_bytes_raises():
    with pytest.raises(HTTPException):
        _validate_file_signature(".txt", b"hello\x00world")


def test_text_without_null_bytes_ok():
    _validate_file_signature(".txt", b"plain text no null")
