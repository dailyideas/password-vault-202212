import base64
from collections import OrderedDict
import datetime
import hashlib
import os
import pathlib
import sys
import uuid


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
from bytes_manipulation.dict_helper import DictHelper
from file_manipulation.directory_handler_with_replication import (
    DirectoryHandlerWithReplication,
)


#### #### #### ####
#### class
#### #### #### ####
class PasswordVault:
    STRING_ENCODING = "utf-8"
    DEFAULT_AUX_PASSWORD_FILE_NAME = "password_vault_aux_password.txt"
    AUX_PASSWORD_LENGTH = 8

    ACCOUNT_NAME_TAG = "account_name"
    ACCOUNT_MODIFICATION_DATE_TAG = "account_modification_date"
    ACCOUNT_UUID_TAG = "account_uuid"

    def __init__(
        self,
        directories: list,
        main_password: str,
        aux_password_file_path: str = "",
    ):
        self._aux_password_file_path = aux_password_file_path
        if self._aux_password_file_path == "":
            self._aux_password_file_path = os.path.join(
                SCRIPT_DIRECTORY, self.DEFAULT_AUX_PASSWORD_FILE_NAME
            )
        main_password_bytes = main_password.encode(self.STRING_ENCODING)
        if os.path.isfile(self._aux_password_file_path) is True:
            aux_password = open(self._aux_password_file_path, "r").read()
        else:
            aux_password = self._generate_aux_password()
            open(self._aux_password_file_path, "w").write(aux_password)
        assert len(aux_password) == self.AUX_PASSWORD_LENGTH
        aux_password_bytes = aux_password.encode(self.STRING_ENCODING)
        key = hashlib.sha256(main_password_bytes + aux_password_bytes).digest()
        self._directory_handler = DirectoryHandlerWithReplication(
            directories=directories, key=key
        )

    def __contains__(self, file_name: str) -> bool:
        return self._directory_handler.file_exists(file_name=file_name)

    def get_all_accounts_name(self) -> set:
        return self._directory_handler.get_all_files_name()

    def search_account_name(
        self, account_name: str, n_candidates: int = 9
    ) -> list:
        return self._directory_handler.search_file_name(
            target_name=account_name, n_candidates=n_candidates
        )

    def update_account(self, details: OrderedDict):
        account_name = details[self.ACCOUNT_NAME_TAG]
        details[
            self.ACCOUNT_MODIFICATION_DATE_TAG
        ] = datetime.date.today().isoformat()
        details_serialized = DictHelper.to_bytes(data=details)
        self._directory_handler.write_to_file(
            file_name=account_name, data=details_serialized
        )

    def delete_account(self, account_name: str):
        self._assert_account_exists(account_name=account_name)
        self._directory_handler.delete_file(file_name=account_name)

    def get_account(self, account_name: str) -> OrderedDict:
        self._assert_account_exists(account_name=account_name)
        details_serialized = self._directory_handler.read_from_file(
            file_name=account_name
        )
        return DictHelper.from_bytes(data=details_serialized)

    def get_blank_account(self) -> OrderedDict:
        return OrderedDict(
            {
                self.ACCOUNT_NAME_TAG: "",
                self.ACCOUNT_MODIFICATION_DATE_TAG: datetime.date.today().isoformat(),
                self.ACCOUNT_UUID_TAG: uuid.uuid4().hex,
            }
        )

    def change_password(self, new_main_password: str):
        new_main_password_bytes = new_main_password.encode(
            self.STRING_ENCODING
        )
        aux_password = self._generate_aux_password()
        aux_password_bytes = aux_password.encode(self.STRING_ENCODING)
        aux_password_file_future_path = (
            self._aux_password_file_path + ".future"
        )
        open(aux_password_file_future_path, "w").write(aux_password)
        new_key = hashlib.sha256(
            new_main_password_bytes + aux_password_bytes
        ).digest()
        self._directory_handler.change_key(new_key=new_key)
        os.replace(aux_password_file_future_path, self._aux_password_file_path)

    def _assert_account_exists(self, account_name: str):
        assert (
            self._directory_handler.file_exists(file_name=account_name) is True
        ), f"Account name \"{account_name}\" does not exist"

    @classmethod
    def _generate_aux_password(cls) -> str:
        assert cls.AUX_PASSWORD_LENGTH % 4 == 0
        return base64.b64encode(
            os.urandom(cls.AUX_PASSWORD_LENGTH // 4 * 3)
        ).decode(cls.STRING_ENCODING)
