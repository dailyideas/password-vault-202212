import os
import pathlib
import shutil
import sys

import pytest


#### #### #### ####
#### global
#### #### #### ####
## constant
SCRIPT_NAME = os.path.basename(__file__).split(".")[0]
SCRIPT_PATH = os.path.abspath(__file__)
SCRIPT_DIRECTORY = os.path.dirname(SCRIPT_PATH)
APP_DIRECTORY = pathlib.Path(SCRIPT_DIRECTORY).parent.absolute()
SCRIPT_RELATIVE_DIRECTORY = os.path.relpath(SCRIPT_DIRECTORY, APP_DIRECTORY)
PROJECT_DIRECTORY = pathlib.Path(APP_DIRECTORY).parent.absolute()
## import
sys.path.insert(1, str(PROJECT_DIRECTORY))
from src.file_manipulation.directory_handler_with_replication import (
    DirectoryHandlerWithReplication,
)


#### #### #### ####
#### class
#### #### #### ####
class TestDirectoryHandlerWithReplication:
    DATA_DIRECTORIES = [
        os.path.join(SCRIPT_DIRECTORY, "data0"),
        os.path.join(SCRIPT_DIRECTORY, "data1"),
        os.path.join(SCRIPT_DIRECTORY, "data2"),
    ]

    def setup_method(self):
        for d in self.DATA_DIRECTORIES:
            os.makedirs(d)

    def teardown_method(self):
        for d in self.DATA_DIRECTORIES:
            shutil.rmtree(d)

    def test_file_rw(self):
        key = b"01234567890123456789012345678901"
        file_name = "0.txt"
        data = b"0123"

        directory_handler = DirectoryHandlerWithReplication(
            directories=self.DATA_DIRECTORIES, key=key
        )
        directory_handler.write_to_file(file_name=file_name, data=data)
        result = directory_handler.read_from_file(file_name=file_name)
        assert result == data

        directory_handler = DirectoryHandlerWithReplication(
            directories=self.DATA_DIRECTORIES, key=key
        )
        result = directory_handler.read_from_file(file_name=file_name)
        assert result == data

    def test_directory_handler_with_incorrect_password(self):
        key = b"01234567890123456789012345678901"
        incorrect_key = b"01234567890123456789012345678902"

        directory_handler = DirectoryHandlerWithReplication(
            directories=self.DATA_DIRECTORIES, key=key
        )
        directory_handler.write_to_file(file_name="0.txt", data=b"0123")

        with pytest.raises(ValueError):
            directory_handler = DirectoryHandlerWithReplication(
                directories=self.DATA_DIRECTORIES, key=incorrect_key
            )

    def test_delete_file(self):
        key = b"01234567890123456789012345678901"
        file_name = "0.txt"
        data = b"0123"

        directory_handler = DirectoryHandlerWithReplication(
            directories=self.DATA_DIRECTORIES, key=key
        )
        directory_handler.write_to_file(file_name=file_name, data=data)
        assert len(directory_handler.get_all_files_name()) == 1
        directory_handler.delete_file(file_name=file_name)
        assert len(directory_handler.get_all_files_name()) == 0

    # def test_change_key(self):
    #     key = b"01234567890123456789012345678901"
    #     file_name = "0.txt"
    #     data = b"0123"
    #     new_key = b"01234567890123456789012345678902"

    #     directory_handler = DirectoryHandlerWithEncryption(
    #         directory=self.DATA_DIRECTORY, key=key
    #     )
    #     directory_handler.write_to_file(file_name=file_name, data=data)

    #     directory_handler.change_key(new_key=new_key)
    #     result = directory_handler.read_from_file(file_name=file_name)
    #     assert result == data

    #     directory_handler = DirectoryHandlerWithEncryption(
    #         directory=self.DATA_DIRECTORY, key=new_key
    #     )
    #     result = directory_handler.read_from_file(file_name=file_name)
    #     assert result == data
