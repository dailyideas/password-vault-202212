import hashlib
import os
import pathlib
import sys
import time


#### #### #### ####
#### global
#### #### #### ####
## constant
SCRIPT_NAME = os.path.basename(__file__).split(".")[0]
SCRIPT_PATH = os.path.abspath(__file__)
SCRIPT_DIRECTORY = os.path.dirname(SCRIPT_PATH)
APP_DIRECTORY = pathlib.Path(SCRIPT_DIRECTORY).parent.absolute()
SCRIPT_RELATIVE_DIRECTORY = os.path.relpath(SCRIPT_DIRECTORY, APP_DIRECTORY)
## import
sys.path.insert(1, str(APP_DIRECTORY))
from file_manipulation.directory_handler import DirectoryHandler
from file_manipulation.directory_handler_with_encryption import (
    DirectoryHandlerWithEncryption,
)


#### #### #### ####
#### class
#### #### #### ####
class DirectoryHandlerWithReplication:
    REPLICA_ID_FILE_NAME = "replica_id"

    def __init__(self, directories: list, key: bytes):
        assert len(directories) > 0
        self._directories = directories
        directories_uid = []
        for d in self._directories:
            handler = DirectoryHandler(directory=d)
            replica_id = handler.read_metadata(
                file_name=self.REPLICA_ID_FILE_NAME
            )
            if replica_id is None:
                replica_id = self._generate_replica_id()
                handler.write_metadata(
                    file_name=self.REPLICA_ID_FILE_NAME, data=replica_id
                )
            directories_uid.append(replica_id)
        self._directory_handlers = [
            DirectoryHandlerWithEncryption(
                directory=d, key=hashlib.sha256(key + replica_id).digest()
            )
            for d, replica_id in zip(self._directories, directories_uid)
        ]
        self._directory_handlers.sort(
            key=lambda handler: handler.modified, reverse=True
        )
        self.cleanup()
        self.recover()

    def __contains__(self, file_name: str) -> bool:
        return self.file_exists(file_name=file_name)

    @property
    def directories(self) -> list:
        return self._directories

    def file_exists(self, file_name: str) -> bool:
        return file_name in self._directory_handlers[0]

    def write_to_file(self, file_name: str, data: bytes):
        for handler in self._directory_handlers:
            handler.write_to_file(file_name=file_name, data=data)

    def read_from_file(self, file_name: str) -> bytes:
        problematic_handlers = []
        data = None
        for handler in self._directory_handlers:
            try:
                data = handler.read_from_file(file_name=file_name)
            except AssertionError:
                problematic_handlers.append(handler)
                continue
            else:
                break
        if data is None:
            raise AssertionError(
                f"File {file_name} is not found/invalid in all directories"
            )
        for handler in problematic_handlers:
            handler.write_to_file(file_name=file_name, data=data)
        return data

    def delete_file(self, file_name: str):
        for handler in self._directory_handlers:
            try:
                handler.delete_file(file_name=file_name)
            except AssertionError:
                continue

    def cleanup(self):
        for handler in self._directory_handlers:
            handler.cleanup()

    def recover(self):
        gathered_files_name = {}
        for handler_index, handler in enumerate(self._directory_handlers):
            files_name = handler.get_all_files_name()
            for file_name in files_name:
                if file_name not in gathered_files_name:
                    gathered_files_name[file_name] = [handler_index]
                else:
                    gathered_files_name[file_name].append(handler_index)
        for file_name, handler_indices in gathered_files_name.items():
            reference_data = None
            if len(handler_indices) != len(self._directory_handlers):
                if reference_data is None:
                    reference_data = self._directory_handlers[
                        handler_indices[0]
                    ].read_from_file(file_name=file_name)
                for i in range(len(self._directory_handlers)):
                    if i not in handler_indices:
                        self._directory_handlers[i].write_to_file(
                            file_name=file_name, data=reference_data
                        )
            reference_hash = self._directory_handlers[
                handler_indices[0]
            ].get_file_hash(file_name=file_name)
            for handler in self._directory_handlers[1:]:
                if (
                    handler.get_file_hash(file_name=file_name)
                    == reference_hash
                ):
                    continue
                if reference_data is None:
                    reference_data = self._directory_handlers[
                        0
                    ].read_from_file(file_name=file_name)
                handler.write_to_file(file_name=file_name, data=reference_data)

    def change_key(self, new_key: bytes):
        for handler in self._directory_handlers:
            replica_id = handler.read_metadata(
                file_name=self.REPLICA_ID_FILE_NAME
            )
            if replica_id is None:
                replica_id = self._generate_replica_id()
                handler.write_metadata(
                    file_name=self.REPLICA_ID_FILE_NAME, data=replica_id
                )
            handler.change_key(
                new_key=hashlib.sha256(new_key + replica_id).digest()
            )

    def get_all_files_name(self) -> set:
        return self._directory_handlers[0].get_all_files_name()

    def search_file_name(
        self, target_name: str, n_candidates: int = 9
    ) -> list:
        return self._directory_handlers[0].search_file_name(
            target_name=target_name, n_candidates=n_candidates
        )

    def _generate_replica_id(self) -> bytes:
        return hashlib.sha256(time.time_ns().to_bytes(8, "big")).digest()
