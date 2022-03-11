import tempfile
from pathlib import Path
from unittest import mock

import pytest

import massgov.pfml.util.pdf as pdf_util

PROCESS_ERROR = "process error"


@pytest.fixture
def pdf_doc_string():
    return b"""%!
    /Helvetica findfont 20 scalefont setfont
    50 50 moveto
    (Hello World) show
    showpage
    quit
    """


@pytest.fixture
def test_pdf_path(request):
    test_files = {
        "small_pdf": "test_files/certHealthCondition.pdf",
        "large_pdf": "test_files/marsEv2.pdf",
    }
    return Path(__file__).parent / test_files[request.param]


def test_get_file_size(pdf_doc_string):
    with tempfile.SpooledTemporaryFile(mode="xb") as temp_pdf:
        temp_pdf.write(pdf_doc_string)
        assert len(pdf_doc_string) == pdf_util.get_file_size(temp_pdf)


# TODO:
# PORTAL-1349
# add large_pdf to the list of parametrized fixtures in this test
# once the pdf compression performance has improved enough
@pytest.mark.parametrize("test_pdf_path", ["small_pdf"], indirect=True)
def test_compress_pdf(test_pdf_path):
    with test_pdf_path.open("rb") as test_pdf, tempfile.SpooledTemporaryFile(
        mode="xb"
    ) as output_pdf:
        resulting_size = pdf_util.compress_pdf(test_pdf, output_pdf)

        assert resulting_size > 0
        assert resulting_size < pdf_util.get_file_size(test_pdf)


@pytest.mark.parametrize("test_pdf_path", ["small_pdf", "large_pdf"], indirect=True)
def test_compress_pdf_timeout(test_pdf_path):
    with test_pdf_path.open("rb") as test_pdf, tempfile.SpooledTemporaryFile(
        mode="xb"
    ) as output_pdf:
        with pytest.raises(pdf_util.PDFCompressionError) as e:
            pdf_util.compress_pdf(test_pdf, output_pdf, timeout=0)

        assert pdf_util.TIMEOUT_ERROR_MESSAGE in str(e.value)


@mock.patch("massgov.pfml.util.pdf.subprocess.run")
def test_compress_pdf_fails_on_subprocess_fail(mock_run, pdf_doc_string):
    mock_proc = mock.Mock()
    mock_proc.configure_mock(**{"returncode": 1, "stderr": PROCESS_ERROR})
    mock_run.return_value = mock_proc

    with tempfile.SpooledTemporaryFile(mode="xb") as input_pdf, tempfile.SpooledTemporaryFile(
        mode="xb"
    ) as output_pdf:
        input_pdf.write(pdf_doc_string)
        with pytest.raises(pdf_util.PDFCompressionError) as e:
            pdf_util.compress_pdf(input_pdf, output_pdf)

        assert PROCESS_ERROR in str(e.value)


@mock.patch("massgov.pfml.util.pdf.subprocess.run")
def test_compress_pdf_fails_on_larger_output(mock_run, pdf_doc_string):
    mock_proc = mock.Mock()
    mock_proc.configure_mock(**{"returncode": 0, "stdout": pdf_doc_string, "stderr": ""})
    mock_run.return_value = mock_proc

    with tempfile.SpooledTemporaryFile(mode="xb") as input_pdf, tempfile.SpooledTemporaryFile(
        mode="xb"
    ) as output_pdf:
        with pytest.raises(pdf_util.PDFSizeError) as e:
            pdf_util.compress_pdf(input_pdf, output_pdf)

        assert pdf_util.ERROR_MESSAGE in str(e.value)
