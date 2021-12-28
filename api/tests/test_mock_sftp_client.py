import os
import tempfile


def test_get_dir(mock_sftp_client):
    with tempfile.TemporaryDirectory() as directory:
        with open(f"{directory}/file1", "w") as f1:
            f1.write("test1")
        with open(f"{directory}/file2", "w") as f1:
            f1.write("test2")

        mock_sftp_client.put(directory, "tempdir", confirm=False)
        assert len(mock_sftp_client._dirs) == 1
        assert len(mock_sftp_client.files) == 2

        mock_sftp_client.get("tempdir", f"{directory}/copydir")
        files = os.listdir(f"{directory}/copydir")
        assert len(files) == 2


def test_put_dir(mock_sftp_client):
    with tempfile.TemporaryDirectory() as directory:
        with open(f"{directory}/file1", "w") as f1:
            f1.write("test1")
        with open(f"{directory}/file2", "w") as f1:
            f1.write("test2")

        mock_sftp_client.put(directory, "tempdir", confirm=False)
        put_files = mock_sftp_client.listdir("tempdir")
        assert len(put_files) == 2
        assert "file1" in put_files
        assert "file2" in put_files


def test_remove_dir(mock_sftp_client):
    with tempfile.TemporaryDirectory() as directory:
        with open(f"{directory}/file1", "w") as f1:
            f1.write("test1")
        with open(f"{directory}/file2", "w") as f1:
            f1.write("test2")

        mock_sftp_client.put(directory, "tempdir", confirm=False)
        assert len(mock_sftp_client._dirs) == 1
        assert len(mock_sftp_client.files) == 2

        mock_sftp_client.remove("tempdir")
        assert len(mock_sftp_client._dirs) == 0
        assert len(mock_sftp_client.files) == 0


def test_rename_dir(mock_sftp_client):
    with tempfile.TemporaryDirectory() as directory:
        with open(f"{directory}/file1", "w") as f1:
            f1.write("test1")
        with open(f"{directory}/file2", "w") as f1:
            f1.write("test2")

        mock_sftp_client.put(directory, "tempdir", confirm=False)
        assert len(mock_sftp_client._dirs) == 1
        assert len(mock_sftp_client.files) == 2

        mock_sftp_client.rename("tempdir", "renamed")
        assert len(mock_sftp_client._dirs) == 1
        assert len(mock_sftp_client.files) == 2

        assert "renamed" in mock_sftp_client._dirs
        renamed_dir_files = mock_sftp_client.listdir("renamed")
        assert len(renamed_dir_files) == 2

        assert "tempdir" not in mock_sftp_client._dirs
        original_files = mock_sftp_client.listdir("tempdir")
        assert len(original_files) == 0
