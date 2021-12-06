"""
Utilities for handling pdf files.

https://lwd.atlassian.net/wiki/spaces/EMPLOYER/pages/2014904367/Process+PDF+file+uploads+to+fit+within+FINEOS+size+limit
Context is provided in the referenced spec regarding settings and configurations used here.
"""

import os
import subprocess
from typing import IO, Any, Dict, Optional, Union

import massgov.pfml.util.logging as logging

logger = logging.get_logger(__name__)

PDF_SETTINGS = "/screen"
SUCCESS_MESSAGE = "PDF successfully compressed"
ERROR_MESSAGE = "PDF could not be compressed"


class PDFUtilError(RuntimeError):
    """A base PDF utility error."""

    method_name: Optional[str]
    message: str


class PDFCompressionError(PDFUtilError):
    """An exception occurred while attempting to compress a PDF."""


class PDFSizeError(PDFUtilError):
    """Size was not reduced while attempting to compress a PDF."""


def pdf_compression_attrs(original_size: int, resulting_size: int) -> Dict[str, Union[str, int]]:
    space = 1 - (resulting_size / original_size) if original_size > 0 else 0
    return {
        "original_size": original_size,
        "resulting_size": resulting_size,
        "space_saving": f"{space:.0%}",
    }


def get_file_size(f: IO[Any]) -> int:
    f.seek(0, os.SEEK_END)
    return f.tell()


def compress_pdf(source_file: IO[Any], dest_file: IO[Any]) -> int:
    gs_cli_command = [
        "gs",
        "-sDEVICE=pdfwrite",
        f"-dPDFSETTINGS={PDF_SETTINGS}",
        "-dSAFER",
        "-dNOPAUSE",
        "-dQUIET",
        "-dBATCH",
        "-sOutputFile=%stdout",
        "-q",
        "-_",
    ]

    source_file.seek(0)
    dest_file.seek(0)

    proc = subprocess.run(
        gs_cli_command, stdin=source_file, stdout=dest_file, stderr=subprocess.PIPE
    )
    if proc.returncode != 0:
        error_message = str(proc.stderr).strip()
        logger.warning(error_message)
        raise PDFCompressionError(error_message)

    original_size = get_file_size(source_file)
    resulting_size = get_file_size(dest_file)
    if resulting_size >= original_size:
        logger.info(ERROR_MESSAGE, extra={**pdf_compression_attrs(original_size, resulting_size)})
        raise PDFSizeError(ERROR_MESSAGE)

    logger.info(SUCCESS_MESSAGE, extra={**pdf_compression_attrs(original_size, resulting_size)})

    return resulting_size
