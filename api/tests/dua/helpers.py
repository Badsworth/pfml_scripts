import os

from massgov.pfml.db.models.employees import ReferenceFile


def get_mock_reference_file(file_name: str) -> ReferenceFile:
    return ReferenceFile(
        file_location=os.path.join(os.path.dirname(__file__), "test_files", file_name)
    )
