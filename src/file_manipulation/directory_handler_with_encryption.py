from __future__ import annotations
import binascii
import dataclasses
import datetime
import os

from data_encryption.cipher_helper import CipherHelper
from file_manipulation.directory_handler_with_file_hash import (
    DirectoryHandlerWithFileHash,
)


@dataclasses.dataclass
class DirectoryInfo:
    BYTE_ORDER = "big"
    VERSION = 1
    VERSION_BYTE = VERSION.to_bytes(1, byteorder=BYTE_ORDER, signed=False)
    modified: datetime.datetime
    next_nonce: int
    key_changed: bool

    def serialized(self) -> bytes:
        b0 = self.VERSION_BYTE
        b1 = int(self.modified.timestamp()).to_bytes(
            8, byteorder=self.BYTE_ORDER, signed=False
        )
        b2 = self.next_nonce.to_bytes(
            12, byteorder=self.BYTE_ORDER, signed=False
        )
        b3 = int(self.key_changed).to_bytes(
            1, byteorder=self.BYTE_ORDER, signed=False
        )
        b0_to_b3 = b0 + b1 + b2 + b3
        checksum = binascii.crc32(b0_to_b3).to_bytes(
            4, byteorder=self.BYTE_ORDER, signed=False
        )
        return b0_to_b3 + checksum

    @classmethod
    def deserialized(cls, data: bytes) -> DirectoryInfo:
        b0 = data[:1]
        b1 = data[1:9]
        b2 = data[9:21]
        b3 = data[21:22]
        stored_checksum = data[22:26]
        calculated_checksum = binascii.crc32(data[:22]).to_bytes(
            4, byteorder=cls.BYTE_ORDER, signed=False
        )
        if stored_checksum != calculated_checksum:
            raise ValueError(
                "Checksum does not match. Data may have been corrupted."
            )
        version = int.from_bytes(b0, byteorder=cls.BYTE_ORDER, signed=False)
        if version != cls.VERSION:
            (b0, b1, b2, b3) = cls._upgrade_data(data=data)
        modified = datetime.datetime.fromtimestamp(
            int.from_bytes(b1, byteorder=cls.BYTE_ORDER, signed=False),
            tz=datetime.timezone.utc,
        )
        next_nonce = int.from_bytes(b2, byteorder=cls.BYTE_ORDER, signed=False)
        key_changed = bool(
            int.from_bytes(b3, byteorder=cls.BYTE_ORDER, signed=False)
        )
        return DirectoryInfo(
            modified=modified, next_nonce=next_nonce, key_changed=key_changed
        )

    @classmethod
    def _upgrade_data(cls, data: bytes) -> tuple[bytes, bytes, bytes, bytes]:
        version = int.from_bytes(
            data[:1], byteorder=cls.BYTE_ORDER, signed=False
        )
        raise NotImplementedError(
            f"Cannot upgrade {cls.__name__} v{version} to v{cls.VERSION}."
        )


class DirectoryHandlerWithEncryption(DirectoryHandlerWithFileHash):
    DIRECTORY_INFO_FILE_NAME = "directory_info"
    FILES_USING_NEW_KEY_CACHE_SUBDIRECTORY = ".files_using_new_key_cache"
    STRING_ENCODING = "utf-8"

    def __init__(self, directory: str, key: bytes):
        super().__init__(directory=directory)
        os.makedirs(
            os.path.join(
                self._directory, self.FILES_USING_NEW_KEY_CACHE_SUBDIRECTORY
            ),
            exist_ok=True,
        )
        self._key = key
        directory_info_path = os.path.join(
            self._directory,
            self.METADATA_SUBDIRECTORY,
            self.DIRECTORY_INFO_FILE_NAME,
        )
        is_directory_info_present = os.path.isfile(directory_info_path)
        if is_directory_info_present is True:
            info_encrypted = open(directory_info_path, "rb").read()
            info_bytes = CipherHelper.unpack_and_decrypt(
                packed_data=info_encrypted, key=self._key
            )
            try:
                self._directory_info = DirectoryInfo.deserialized(
                    data=info_bytes
                )
            except ValueError:
                raise ValueError(
                    f"Key is incorrect, or data is corrupted in directory \"{self._directory}\"."
                )
        else:
            self._directory_info = DirectoryInfo(
                modified=datetime.datetime.fromtimestamp(
                    0, tz=datetime.timezone.utc
                ),
                next_nonce=0,
                key_changed=False,
            )
        if self._directory_info.key_changed is True:
            self._recover()

    @property
    def modified(self) -> datetime.datetime:
        return self._directory_info.modified

    def write_to_file(self, file_name: str, data: bytes):
        self._write_file_hash(file_name=file_name, data=data)
        nonce = self._get_nonce()
        self._save_directory_info()
        data_encrypted = CipherHelper.encrypt_and_pack(
            data=data, key=self._key, nonce=nonce
        )
        open(os.path.join(self._directory, file_name), "wb").write(
            data_encrypted
        )
        self._files.add(file_name)

    def read_from_file(self, file_name: str) -> bytes:
        data_encrypted = super(
            DirectoryHandlerWithFileHash, self
        ).read_from_file(file_name=file_name)
        data = CipherHelper.unpack_and_decrypt(
            packed_data=data_encrypted, key=self._key
        )
        assert self._check_file_hash(
            file_name=file_name, data=data
        ), "File hash does not match."
        return data

    def change_key(self, new_key: bytes):
        self.cleanup()
        files_name = self.get_all_files_name()
        new_nonce = 0
        files_using_new_key_cache_abs_path = os.path.join(
            self._directory, self.FILES_USING_NEW_KEY_CACHE_SUBDIRECTORY
        )
        for file_name in files_name:
            try:
                data = self.read_from_file(file_name=file_name)
            except AssertionError:
                self.delete_file(file_name=file_name)
                continue
            data_encrypted = CipherHelper.encrypt_and_pack(
                data=data, key=new_key, nonce=new_nonce
            )
            open(
                os.path.join(files_using_new_key_cache_abs_path, file_name),
                "wb",
            ).write(data_encrypted)
            new_nonce += 1

        self._key = new_key
        self._directory_info.modified = datetime.datetime.now(
            tz=datetime.timezone.utc
        )
        self._directory_info.next_nonce = new_nonce
        self._directory_info.key_changed = True
        self._save_directory_info()

        self._move_files(
            src=files_using_new_key_cache_abs_path, dst=self._directory
        )

        self._directory_info.modified = datetime.datetime.now(
            tz=datetime.timezone.utc
        )
        self._directory_info.key_changed = False
        self._save_directory_info()

    def _get_nonce(self):
        nonce = self._directory_info.next_nonce
        self._directory_info.next_nonce += 1
        return nonce

    def _save_directory_info(self):
        nonce = self._get_nonce()
        self._directory_info.modified = datetime.datetime.now(
            tz=datetime.timezone.utc
        )
        info_serialized = self._directory_info.serialized()
        info_encrypted = CipherHelper.encrypt_and_pack(
            data=info_serialized, key=self._key, nonce=nonce
        )
        os.makedirs(
            os.path.join(self._directory, self.METADATA_SUBDIRECTORY),
            exist_ok=True,
        )
        open(
            os.path.join(
                self._directory,
                self.METADATA_SUBDIRECTORY,
                self.DIRECTORY_INFO_FILE_NAME,
            ),
            "wb",
        ).write(info_encrypted)

    def _delete_files_using_new_key_cache(self):
        files_using_new_key_cache_abs_path = os.path.join(
            self._directory, self.FILES_USING_NEW_KEY_CACHE_SUBDIRECTORY
        )
        for file_name in os.listdir(files_using_new_key_cache_abs_path):
            try:
                os.unlink(
                    os.path.join(files_using_new_key_cache_abs_path, file_name)
                )
            except:
                continue

    def _recover(self):
        files_using_new_key_cache_abs_path = os.path.join(
            self._directory, self.FILES_USING_NEW_KEY_CACHE_SUBDIRECTORY
        )
        os.makedirs(files_using_new_key_cache_abs_path, exist_ok=True)
        if self._directory_info.key_changed is False:
            self._delete_files_using_new_key_cache()
            return
        self._move_files(
            src=files_using_new_key_cache_abs_path, dst=self._directory
        )
        self._directory_info.modified = datetime.datetime.now(
            tz=datetime.timezone.utc
        )
        self._directory_info.key_changed = False
        self._save_directory_info()

    @classmethod
    def _move_files(cls, src: str, dst: str):
        assert os.path.isdir(src), "Source is not a directory."
        assert os.path.isdir(dst), "Destination is not a directory."
        source_files_name = [
            f for f in os.listdir(src) if os.path.isfile(os.path.join(src, f))
        ]
        for file_name in source_files_name:
            os.replace(
                os.path.join(src, file_name), os.path.join(dst, file_name)
            )
