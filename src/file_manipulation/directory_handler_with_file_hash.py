import hashlib
import os

from file_manipulation.directory_handler import DirectoryHandler


class DirectoryHandlerWithFileHash(DirectoryHandler):
    HASHES_SUBDIRECTORY = ".hashes"
    HASH_FILE_EXTENSION = "hash"

    def write_to_file(self, file_name: str, data: bytes):
        self._write_file_hash(file_name=file_name, data=data)
        super().write_to_file(file_name=file_name, data=data)

    def read_from_file(self, file_name: str) -> bytes:
        self._ensure_file_exists(file_name=file_name)
        data = super().read_from_file(file_name=file_name)
        if not self._check_file_hash(file_name=file_name, data=data):
            raise ValueError("File hash does not match")
        return data

    def get_file_hash(self, file_name: str) -> bytes:
        self._ensure_file_exists(file_name)
        with open(
            os.path.join(
                self._directory,
                self.HASHES_SUBDIRECTORY,
                f"{file_name}.{self.HASH_FILE_EXTENSION}",
            ),
            "rb",
        ) as f:
            return f.read()

    def delete_file(self, file_name: str):
        self._ensure_file_exists(file_name=file_name)
        super().delete_file(file_name=file_name)
        self._delete_hash(file_name=file_name)

    def cleanup(self):
        hash_directory_abs_path = os.path.join(
            self._directory, self.HASHES_SUBDIRECTORY
        )
        os.makedirs(hash_directory_abs_path, exist_ok=True)
        hash_files = [
            f
            for f in os.listdir(hash_directory_abs_path)
            if os.path.isfile(os.path.join(hash_directory_abs_path, f))
        ]
        for f in self._files:
            try:
                hash_files.remove(f"{f}.{self.HASH_FILE_EXTENSION}")
            except ValueError:
                ## Case: hash file does not exist
                self.delete_file(file_name=f)
        for f in hash_files:
            ## Case: hash file exists but file does not
            os.remove(os.path.join(hash_directory_abs_path, f))

    def _get_hash_file_path(self, file_name: str) -> str:
        hash_directory_abs_path = os.path.join(
            self._directory, self.HASHES_SUBDIRECTORY
        )
        os.makedirs(hash_directory_abs_path, exist_ok=True)
        return os.path.join(
            hash_directory_abs_path, f"{file_name}.{self.HASH_FILE_EXTENSION}"
        )

    def _write_file_hash(self, file_name: str, data: bytes):
        data_hash = self._get_hash(data=data)
        hash_path = self._get_hash_file_path(file_name=file_name)
        open(hash_path, "wb").write(data_hash)

    def _check_file_hash(self, file_name: str, data: bytes) -> bool:
        data_hash = self._get_hash(data=data)
        hash_path = self._get_hash_file_path(file_name=file_name)
        return data_hash == open(hash_path, "rb").read()

    def _delete_hash(self, file_name: str):
        hash_path = self._get_hash_file_path(file_name=file_name)
        if os.path.isfile(hash_path):
            os.remove(hash_path)

    @classmethod
    def _get_hash(cls, data: bytes) -> bytes:
        """
        Calculate the hash of bytes.

        Parameters
        ----
        data : bytes
            Data to be hashed.
        """
        m = hashlib.sha256()
        m.update(data)
        return m.digest()
