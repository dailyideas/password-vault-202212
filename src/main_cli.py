import argparse
from collections import OrderedDict
import enum
from enum import Enum
import getpass
import itertools
import json
import os
import traceback

import colorama
from colorama import Fore


#### #### #### ####
#### global
#### #### #### ####
## constant
SCRIPT_NAME = os.path.basename(__file__).split(".")[0]
SCRIPT_PATH = os.path.abspath(__file__)
SCRIPT_DIRECTORY = os.path.dirname(SCRIPT_PATH)
APP_DIRECTORY = SCRIPT_DIRECTORY
SCRIPT_RELATIVE_DIRECTORY = os.path.relpath(SCRIPT_DIRECTORY, APP_DIRECTORY)
## import
from input_manipulation.input_helper import InputHelper
from password_vault.password_vault import PasswordVault

## colorama
colorama.just_fix_windows_console()
colorama.init(autoreset=True)


#### #### #### ####
#### class
#### #### #### ####
class FsmState(Enum):
    ENTRANCE = enum.auto()
    SHOW_DIRECTORIES = enum.auto()
    ADD_DIRECTORY = enum.auto()
    DELETE_DIRTORY = enum.auto()
    ASK_MAIN_PASSWORD = enum.auto()
    SHOW_ACCOUNT_OPERATIONS = enum.auto()
    SEARCH_ACCOUNT = enum.auto()
    UPDATE_ACCOUNT = enum.auto()
    DELETE_ACCOUNT = enum.auto()
    CHANGE_PASSWORDS = enum.auto()
    ACCOUNT_ADD_FIELD = enum.auto()
    ACCOUNT_MODIFY_FIELD = enum.auto()
    ACCOUNT_DELETE_FIELD = enum.auto()
    EXIT = enum.auto()


class FSM:
    METADATA_FILE_NAME = "metadata.json"
    METADATA_KEY_DIRECTORIES = "directories"
    METADATA_KEY_AUX_PASSWORD_FILE_PATH = "aux_password_file_path"

    def __init__(self, metadata_directory: str, n_candidates: int = 9):
        assert os.path.isdir(metadata_directory)
        self._metadata_directory = metadata_directory
        self._n_candidates = n_candidates
        self._metadata_file_path = os.path.join(
            metadata_directory, self.METADATA_FILE_NAME
        )
        if os.path.isfile(self._metadata_file_path):
            self._metadata = self._load_metadata(self._metadata_file_path)
        else:
            self._metadata = {
                self.METADATA_KEY_DIRECTORIES: [],
                self.METADATA_KEY_AUX_PASSWORD_FILE_PATH: os.path.join(
                    self._metadata_directory, "aux_password.txt"
                ),
            }
            json.dump(
                self._metadata, open(self._metadata_file_path, "w"), indent=4
            )
        self._main_state = FsmState.ENTRANCE
        self._password_vault = None
        self._account_details = None
        self._is_account_details_updated = False

    def start(self):
        try:
            while self._main_state != FsmState.EXIT:
                if self._main_state == FsmState.ENTRANCE:
                    self._main_state = self._at_state_entrance()
                elif self._main_state == FsmState.SHOW_DIRECTORIES:
                    self._main_state = self._at_state_show_directories()
                elif self._main_state == FsmState.ADD_DIRECTORY:
                    self._main_state = self._at_state_add_directory()
                elif self._main_state == FsmState.DELETE_DIRTORY:
                    self._main_state = self._at_state_delete_directory()
                elif self._main_state == FsmState.ASK_MAIN_PASSWORD:
                    self._main_state = self._at_state_ask_main_password()
                elif self._main_state == FsmState.SHOW_ACCOUNT_OPERATIONS:
                    self._main_state = self._at_state_show_account_operations()
                elif self._main_state == FsmState.SEARCH_ACCOUNT:
                    self._main_state = self._at_state_search_account()
                elif self._main_state == FsmState.UPDATE_ACCOUNT:
                    self._main_state = self._at_state_update_account()
                elif self._main_state == FsmState.DELETE_ACCOUNT:
                    self._main_state = self._at_state_delete_account()
                elif self._main_state == FsmState.CHANGE_PASSWORDS:
                    self._main_state = self._at_state_change_passwords()
                elif self._main_state == FsmState.ACCOUNT_ADD_FIELD:
                    self._main_state = self._at_state_account_add_field()
                elif self._main_state == FsmState.ACCOUNT_MODIFY_FIELD:
                    self._main_state = self._at_state_account_modify_field()
                elif self._main_state == FsmState.ACCOUNT_DELETE_FIELD:
                    self._main_state = self._at_state_account_delete_field()
                else:
                    raise ValueError(
                        Fore.RED + f"Invalid state: {self._main_state}"
                    )
        except Exception as e:
            print(Fore.RED + "An error occurred.")
            print(f"{type(e).__name__}: {e}")
            traceback.print_exc()
        finally:
            print(Fore.CYAN + "Bye.")

    def _at_state_entrance(self):
        print(
            "Welcome to password vault.\n"
            "Legend: "
            f"{Fore.CYAN}Information{Fore.RESET} "
            f"{Fore.GREEN}Success{Fore.RESET} "
            f"{Fore.RED}Failure{Fore.RESET}"
        )
        return FsmState.SHOW_DIRECTORIES

    def _at_state_show_directories(self):
        print(Fore.CYAN + "Password vault directories:")
        for i, d in enumerate(self._metadata[self.METADATA_KEY_DIRECTORIES]):
            print(f"{i + 1}) {d}")
        print(Fore.CYAN + "Choose an operation:")
        print("1) Add a directory")
        print("2) Delete a directory")
        print("0) Exit")
        print("Pass an empty input to go to next step.")
        r = self._get_input()
        if r == "":
            if len(self._metadata[self.METADATA_KEY_DIRECTORIES]) == 0:
                print(Fore.RED + "At least one directory must be provided.")
                return FsmState.SHOW_DIRECTORIES
            json.dump(
                self._metadata, open(self._metadata_file_path, "w"), indent=4
            )
            return FsmState.ASK_MAIN_PASSWORD
        elif r == "1":
            return FsmState.ADD_DIRECTORY
        elif r == "2":
            return FsmState.DELETE_DIRTORY
        elif r == "0":
            return FsmState.EXIT
        print(Fore.RED + "Invalid input.")
        return self._main_state

    def _at_state_add_directory(self):
        print(
            "Enter the absolute path of the directory. Make sure the "
            "directory do not contain irrelevant files as they could be "
            "deleted by this program."
        )
        i = self._get_input()
        if os.path.isabs(i) is False:
            print(Fore.RED + "Input must be an absolute path.")
        elif os.path.isdir(i) is False:
            print(Fore.RED + "Input must be an existing directory.")
        elif i in self._metadata[self.METADATA_KEY_DIRECTORIES]:
            print(Fore.RED + "Directory already exists.")
        else:
            self._metadata[self.METADATA_KEY_DIRECTORIES].append(i)
        return FsmState.SHOW_DIRECTORIES

    def _at_state_delete_directory(self):
        print("Enter the index of the directory to delete it.")
        i = self._get_input()
        if i.isdigit() is False:
            print(Fore.RED + "Invalid input.")
            return FsmState.SHOW_DIRECTORIES
        i = int(i)
        if i < 1 or i > len(self._metadata[self.METADATA_KEY_DIRECTORIES]):
            print(Fore.RED + "Invalid input.")
            return FsmState.SHOW_DIRECTORIES
        self._metadata[self.METADATA_KEY_DIRECTORIES].pop(int(i) - 1)
        return FsmState.SHOW_DIRECTORIES

    def _at_state_ask_main_password(self):
        print(
            "Enter the main password. This password will be used to "
            "encrypt the vault. It should be different from any other "
            "passwords you have used. If you forget this password, you will "
            "lose access to this password vault. However, you should not "
            "written this password down, or disclose it to anyone."
        )
        p = getpass.getpass("Main password: ")
        if len(p) == 0:
            print(Fore.RED + "Password cannot be empty.")
            return FsmState.EXIT
        self._password_vault = PasswordVault(
            directories=self._metadata[self.METADATA_KEY_DIRECTORIES],
            main_password=p,
            aux_password_file_path=self._metadata[
                self.METADATA_KEY_AUX_PASSWORD_FILE_PATH
            ],
        )
        print(
            "An auxiliary password is generated and stored at "
            f"\"{self._metadata[self.METADATA_KEY_AUX_PASSWORD_FILE_PATH]}\". "
            "The password vault can only be decrypted by providing both the "
            "main and auxiliary passwords. You should make multiple copies of "
            "this file in safe places. If you lose this auxiliary password, "
            "you will lose access to this password vault. "
        )
        return FsmState.SHOW_ACCOUNT_OPERATIONS

    def _at_state_show_account_operations(self):
        assert isinstance(self._password_vault, PasswordVault)
        self._account_details = None
        self._is_account_details_updated = False
        print(Fore.CYAN + "Choose an operation:")
        print("1) Search an account")
        print("2) Add an account")
        print("3) Delete an account")
        print("4) Change passwords")
        print("0) Exit")
        i = self._get_input()
        if i == "1":
            return FsmState.SEARCH_ACCOUNT
        elif i == "2":
            print("Enter the name of the account.")
            account_name = self._get_input()
            if account_name in self._password_vault:
                print(
                    Fore.RED + "An account with the same name already exists."
                )
                return self._main_state
            if len(account_name) == 0:
                print(Fore.RED + "Account name cannot be empty.")
                return self._main_state
            self._account_details = self._password_vault.get_blank_account()
            self._account_details[
                PasswordVault.ACCOUNT_NAME_TAG
            ] = account_name
            self._is_account_details_updated = True
            return FsmState.UPDATE_ACCOUNT
        elif i == "3":
            return FsmState.DELETE_ACCOUNT
        elif i == "4":
            return FsmState.CHANGE_PASSWORDS
        elif i == "0":
            return FsmState.EXIT
        print(Fore.RED + "Invalid input.")
        return self._main_state

    def _at_state_search_account(self):
        target_name = self._search_account()
        assert isinstance(self._password_vault, PasswordVault)
        if target_name not in self._password_vault:
            print(Fore.RED + "No such account.")
            return FsmState.SHOW_ACCOUNT_OPERATIONS
        self._account_details = self._password_vault.get_account(
            account_name=target_name
        )
        return FsmState.UPDATE_ACCOUNT

    def _at_state_update_account(self):
        assert isinstance(self._password_vault, PasswordVault)
        assert isinstance(self._account_details, OrderedDict)
        print(Fore.CYAN + "Details of the account:")
        for i, (k, v) in enumerate(self._account_details.items()):
            print(f"{i + 1}) {k}: {v}")
        print(Fore.CYAN + "Choose an operation:")
        print("1) Add a field")
        print("2) Modify a field")
        print("3) Delete a field")
        print("Pass an empty input to complete the update.")
        i = self._get_input()
        if i == "":
            if self._is_account_details_updated:
                self._password_vault.update_account(
                    details=self._account_details
                )
                print(Fore.GREEN + "Account updated.")
            return FsmState.SHOW_ACCOUNT_OPERATIONS
        elif i == "1":
            return FsmState.ACCOUNT_ADD_FIELD
        elif i == "2":
            return FsmState.ACCOUNT_MODIFY_FIELD
        elif i == "3":
            return FsmState.ACCOUNT_DELETE_FIELD
        print(Fore.RED + "Invalid input.")
        return self._main_state

    def _at_state_delete_account(self):
        target_name = self._search_account()
        assert isinstance(self._password_vault, PasswordVault)
        if target_name not in self._password_vault:
            print(Fore.RED + "No such account.")
            return FsmState.SHOW_ACCOUNT_OPERATIONS
        self._password_vault.delete_account(account_name=target_name)
        print(Fore.GREEN + "Account deleted.")
        return FsmState.SHOW_ACCOUNT_OPERATIONS

    def _at_state_change_passwords(self):
        p = getpass.getpass("Enter the new password:")
        if len(p) == 0:
            print(Fore.RED + "Password cannot be empty.")
            return FsmState.SHOW_ACCOUNT_OPERATIONS
        p_repeated = getpass.getpass("Repeat the password:")
        if p != p_repeated:
            print(Fore.RED + "The passwords do not match.")
            return FsmState.SHOW_ACCOUNT_OPERATIONS
        assert isinstance(self._password_vault, PasswordVault)
        self._password_vault.change_password(new_main_password=p)
        print(Fore.GREEN + "Password changed.")
        return FsmState.SHOW_ACCOUNT_OPERATIONS

    def _at_state_account_add_field(self):
        assert isinstance(self._password_vault, PasswordVault)
        assert isinstance(self._account_details, OrderedDict)
        print("Enter the name of the field. Pass an empty input to cancel.")
        field_key = self._get_input()
        if field_key == "":
            return FsmState.UPDATE_ACCOUNT
        elif field_key in self._account_details:
            print(Fore.RED + "The field already exists.")
            return self._main_state
        print(
            f"Enter the value of the field \"{field_key}\". "
            "Pass an empty input to cancel."
        )
        field_value = self._get_input()
        if field_value == "":
            return FsmState.UPDATE_ACCOUNT
        self._account_details[field_key] = field_value
        print(Fore.GREEN + "The field has been added.")
        self._is_account_details_updated = True
        return FsmState.UPDATE_ACCOUNT

    def _at_state_account_modify_field(self):
        assert isinstance(self._account_details, OrderedDict)
        print("Enter the index of the field. Pass an empty input to cancel.")
        field_index = self._get_input()
        if field_index == "":
            return FsmState.UPDATE_ACCOUNT
        field_key = self._get_field_key_from_index(field_index=field_index)
        if field_key is None:
            print(Fore.RED + "Invalid input.")
            return self._main_state
        print(
            f"Enter the value of the field \"{field_key}\". "
            "Pass an empty input to cancel."
        )
        field_value = self._get_input()
        if field_value == "":
            return FsmState.UPDATE_ACCOUNT
        self._account_details[field_key] = field_value
        print(Fore.GREEN + f"The field \"{field_key}\" has been modified.")
        self._is_account_details_updated = True
        return FsmState.UPDATE_ACCOUNT

    def _at_state_account_delete_field(self):
        assert isinstance(self._password_vault, PasswordVault)
        assert isinstance(self._account_details, OrderedDict)
        print("Enter the index of the field. Pass an empty input to cancel.")
        field_index = self._get_input()
        if field_index == "":
            return FsmState.UPDATE_ACCOUNT
        field_key = self._get_field_key_from_index(field_index=field_index)
        if field_key is None:
            print(Fore.RED + "Invalid input.")
            return self._main_state
        del self._account_details[field_key]
        print(Fore.GREEN + f"The field \"{field_key}\" has been deleted.")
        self._is_account_details_updated = True
        return FsmState.UPDATE_ACCOUNT

    def _get_field_key_from_index(self, field_index: str | int) -> str | None:
        assert isinstance(self._account_details, OrderedDict)
        if isinstance(field_index, str) and not field_index.isdigit():
            return None
        field_index = int(field_index)
        if field_index - 1 >= len(self._account_details):
            return None
        field_key = next(
            itertools.islice(self._account_details, int(field_index) - 1, None)
        )
        if field_key in [
            PasswordVault.ACCOUNT_NAME_TAG,
            PasswordVault.ACCOUNT_MODIFICATION_DATE_TAG,
            PasswordVault.ACCOUNT_UUID_TAG,
        ]:
            return None
        return field_key

    def _search_account(self) -> str:
        assert isinstance(self._password_vault, PasswordVault)
        print("Enter the name of the account.")
        target_name = ""
        possible_names = []
        i = InputHelper.getch()
        while i != "\n" and i != "\r":
            if i == "\t":
                target_name = (
                    possible_names[0] if len(possible_names) else target_name
                )
            elif i == "\b":
                target_name = target_name[:-1]
            else:
                target_name += i
            possible_names = self._password_vault.search_account_name(
                account_name=target_name, n_candidates=self._n_candidates
            )
            print(f"{target_name}: {possible_names}")
            i = InputHelper.getch()
        return target_name

    @classmethod
    def _load_metadata(cls, metadata_file_path: str) -> dict:
        assert os.path.isfile(metadata_file_path)
        d = json.load(open(metadata_file_path, "r"))
        assert "directories" in d
        return d

    @classmethod
    def _get_input(cls) -> str:
        return input(">")


#### #### #### ####
#### main
#### #### #### ####
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A simple password vault.")
    parser.add_argument(
        "-d",
        "--metadata-directory",
        type=str,
        default=SCRIPT_DIRECTORY,
        help="The directory where metadata are stored. Default to the directory where the script is located.",
    )
    parser.add_argument(
        "-n",
        "--n_candidates",
        type=int,
        default=9,
        help="Number of candidates to display when searching for an account.",
    )
    args = parser.parse_args()

    fsm = FSM(
        metadata_directory=args.metadata_directory,
        n_candidates=args.n_candidates,
    )
    fsm.start()
