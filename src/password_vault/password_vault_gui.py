from collections import OrderedDict
import datetime
import enum
from enum import Enum
from functools import partial
import json
import logging
import os
import time
import tkinter as tk
import tkinter.font
import tkinter.filedialog
import tkinter.messagebox
import tkinter.scrolledtext
import tkinter.simpledialog
import traceback

from fsm.enum_fsm import EnumFsm
from password_vault.password_vault import PasswordVault


logger = logging.getLogger(__name__)


class FsmState(Enum):
    ENTRANCE = enum.auto()
    LOAD_METADATA = enum.auto()
    MANAGE_DATA_REPLICA_DIRECTORIES = enum.auto()
    ADD_DATA_REPLICA_DIRECTORY = enum.auto()
    DELETE_DATA_REPLICA_DIRECTORY = enum.auto()
    ASK_MAIN_PASSWORD = enum.auto()
    MAIN_MENU = enum.auto()
    SEARCH_ACCOUNT = enum.auto()
    CHANGE_PASSWORD = enum.auto()
    MANAGE_ACCOUNT = enum.auto()
    EXIT = enum.auto()


class PasswordVaultGui:
    CACHES_DIRECTORY = "caches"
    METADATA_FILE_NAME = "metadata.json"
    DATA_REPLICA_DIRECTORIES_FIELD = "directories"
    STRING_ENCODING = "utf-8"
    CONSOLE_MAX_LINES = 200
    ACCOUNT_NAMES_VIEW_N_CANDIDATES = 64
    MAX_IDLING_TIME = 300

    def __init__(self):
        self._metadata_file_path: str = os.path.join(
            self.CACHES_DIRECTORY, self.METADATA_FILE_NAME
        )
        self._metadata: dict = {}
        self._intra_state_variables: dict = {}
        self._inter_state_variables: dict = {}

        os.makedirs(self.CACHES_DIRECTORY, exist_ok=True)

        self._is_fsm_ready: bool = False
        self._init_fsm()
        self._is_tkinter_ready: bool = False
        self._init_tkinter()

    def loop(self):
        is_exited = False
        prev_fsm_state = FsmState.ENTRANCE
        prev_fsm_state_start_time = time.time()

        def on_closing_window():
            nonlocal is_exited
            is_exited = True

        def check_and_handle_idling():
            nonlocal prev_fsm_state, prev_fsm_state_start_time
            current_state = self._fsm.current_state
            if current_state == prev_fsm_state:
                if (
                    time.time() - prev_fsm_state_start_time
                    > self.MAX_IDLING_TIME
                ):
                    on_closing_window()
            else:
                prev_fsm_state = current_state
                prev_fsm_state_start_time = time.time()

        self._root.protocol("WM_DELETE_WINDOW", on_closing_window)
        try:
            while is_exited is False:
                is_exited = self._fsm.update()
                self._root.update_idletasks()
                self._root.update()
                check_and_handle_idling()
        except Exception as e:
            logger.info("{}: {}".format(type(e).__name__, e))
            traceback.print_exc()
        finally:
            logger.info("Bye")
            self._root.quit()

    def _init_fsm(self):
        self._fsm = EnumFsm(
            start_state=FsmState.ENTRANCE,
            exit_state=FsmState.EXIT,
            on_state_changed=self._on_fsm_state_changed,
        )
        self._fsm.add_state(
            state=FsmState.ENTRANCE,
            stay_callback=self._entrance_state_stay_callback,
        )
        self._fsm.add_state(
            state=FsmState.LOAD_METADATA,
            stay_callback=self._load_metadata_state_stay_callback,
        )
        self._fsm.add_state(
            state=FsmState.MANAGE_DATA_REPLICA_DIRECTORIES,
            enter_callback=self._manage_data_replica_directories_state_enter_callback,
            stay_callback=self._manage_data_replica_directories_state_stay_callback,
            exit_callback=self._manage_data_replica_directories_state_exit_callback,
        )
        self._fsm.add_state(
            state=FsmState.ADD_DATA_REPLICA_DIRECTORY,
            stay_callback=self._add_data_replica_directory_state_stay_callback,
        )
        self._fsm.add_state(
            state=FsmState.DELETE_DATA_REPLICA_DIRECTORY,
            enter_callback=self._delete_data_replica_directory_state_enter_callback,
            stay_callback=self._delete_data_replica_directory_state_stay_callback,
        )
        self._fsm.add_state(
            state=FsmState.ASK_MAIN_PASSWORD,
            enter_callback=self._ask_main_password_state_enter_callback,
            stay_callback=self._ask_main_password_state_stay_callback,
        )
        self._fsm.add_state(
            state=FsmState.MAIN_MENU,
            enter_callback=self._main_menu_state_enter_callback,
            stay_callback=self._main_menu_state_stay_callback,
            exit_callback=self._main_menu_state_exit_callback,
        )
        self._fsm.add_state(
            state=FsmState.SEARCH_ACCOUNT,
            enter_callback=self._search_accounts_state_enter_callback,
            stay_callback=self._search_accounts_state_stay_callback,
            exit_callback=self._search_accounts_state_exit_callback,
        )
        self._fsm.add_state(
            state=FsmState.CHANGE_PASSWORD,
            stay_callback=self._change_password_state_stay_callback,
        )
        self._fsm.add_state(
            state=FsmState.MANAGE_ACCOUNT,
            enter_callback=self._manage_account_state_enter_callback,
            stay_callback=self._manage_account_state_stay_callback,
            exit_callback=self._manage_account_state_exit_callback,
        )
        self._fsm.add_state(
            state=FsmState.EXIT, stay_callback=self._exit_state_stay_callback
        )

        self._fsm.start()
        self._is_fsm_ready = True

    def _init_tkinter(self):
        ## initialize top level widget
        self._root = tk.Tk()
        self._root.geometry("1280x720")
        self._root.title("Password Vault")
        self._root.minsize(320, 240)

        ## initialize fonts
        self._title_font = tkinter.font.Font(family="System", size=16)
        self._normal_font = tkinter.font.Font(family="System", size=12)
        self._account_names_view_font = tkinter.font.Font(
            family="System", size=36
        )
        self._account_details_account_name_label_font = tkinter.font.Font(
            family="System", size=18
        )

        ## initialize widgets
        self._title_label = tk.Label(self._root, font=self._title_font)

        info_frame = tk.Frame(self._root)
        self._console = tkinter.scrolledtext.ScrolledText(
            info_frame, wrap="word", font=self._normal_font, spacing3=4
        )
        self._account_names_list_box = tk.Listbox(
            info_frame, bd=0, highlightthickness=0, selectmode="browse"
        )
        self._account_names_scroll_bar = tk.Scrollbar(info_frame)
        self._account_names_list_box.config(
            yscrollcommand=self._account_names_scroll_bar.set,
            font=self._account_names_view_font,
        )
        self._account_names_scroll_bar.config(
            command=self._account_names_list_box.yview
        )

        ## \[[Dis](https://stackoverflow.com/a/40539365)\] Vertical scrollbar for frame in Tkinter, Python
        ## \[[Dis](https://stackoverflow.com/a/3092341)\] Adding a scrollbar to a group of widgets in Tkinter
        ## \[[Dis](https://stackoverflow.com/a/4311134)\] How do I remove the light grey border around my Canvas widget?
        self._account_frame = tk.Frame(info_frame)
        self._account_canvas = tk.Canvas(
            self._account_frame, bd=0, highlightthickness=0
        )
        self._account_scroll_bar = tk.Scrollbar(
            self._account_frame,
            orient="vertical",
            command=self._account_canvas.yview,
        )
        self._account_canvas.configure(
            yscrollcommand=self._account_scroll_bar.set
        )

        user_input_frame = tk.Frame(self._root)
        user_input_label = tk.Label(
            user_input_frame, text=">", font=self._normal_font
        )
        self._user_input_field = tk.StringVar()
        self._input_entry = tk.Entry(
            user_input_frame,
            textvariable=self._user_input_field,
            font=self._title_font,
        )

        command_buttons_frame = tk.Frame(self._root)
        self._command_buttons = [
            tk.Button(
                command_buttons_frame,
                font=self._normal_font,
                relief="groove",
                command=partial(
                    self._command_button_pressed_callback, button_idx=i
                ),
            )
            for i in range(3)
        ]

        ## Pack widgets
        # \[[Dis](https://stackoverflow.com/a/42075343)\] Avoid the status bar (footer) from disappearing in a GUI when reducing the size of the screen
        command_buttons_frame.pack(side="bottom", fill="x", padx=4)
        for btn in self._command_buttons:
            btn.pack(side="left", fill="both", expand=True, ipady=8)

        user_input_frame.pack(side="bottom", fill="x", padx=4, pady=4, ipady=4)
        user_input_label.pack(side="left", fill="y", padx=4)
        self._input_entry.pack(side="left", fill="both", expand=True, padx=4)
        self._input_entry.focus()

        self._title_label.pack(side="top", fill="x", pady=4)

        info_frame.pack(side="top", fill="both", expand=True, padx=4)
        self._activate_console_view()

        ## Set up widget callbacks
        self._user_input_field.trace_add(
            mode="write", callback=self._on_user_input_changed
        )
        self._root.bind("<Delete>", self._on_delete_button_pressed)
        self._root.bind("<Escape>", self._on_escape_button_pressed)
        self._root.bind("<Return>", self._on_confirm_input)
        self._root.bind("<Tab>", self._on_tab_button_pressed)
        self._account_names_list_box.bind(
            "<<ListboxSelect>>", self._on_account_names_list_box_selected
        )

        ## \[[Dis](https://stackoverflow.com/a/34881659)\] Tkinter - Listbox that follows cursor?
        def highlight_account_name_by_cursor_pointing_location(
            event: tk.Event,
        ):
            self._account_names_list_box.selection_clear(0, tk.END)
            self._account_names_list_box.selection_set(
                self._account_names_list_box.nearest(event.y)
            )

        self._account_names_list_box.bind(
            "<Enter>", highlight_account_name_by_cursor_pointing_location
        )
        self._account_names_list_box.bind(
            "<Motion>", highlight_account_name_by_cursor_pointing_location
        )
        self._account_names_list_box.bind(
            "<Leave>",
            lambda _: self._account_names_list_box.select_clear(0, tk.END),
        )

        self._is_tkinter_ready = True

    def _command_button_pressed_callback(self, button_idx: int):
        command_button_pressed = self._command_buttons[button_idx]["text"]
        self._intra_state_variables[
            "command_button_pressed"
        ] = command_button_pressed.lower()
        logger.debug("Button: {}".format(command_button_pressed))

    def _on_user_input_changed(self, name, index, mode):
        self._intra_state_variables[
            "user_input"
        ] = self._user_input_field.get()

    def _on_confirm_input(self, *args):
        confirmed_input = self._user_input_field.get()
        self._intra_state_variables["confirmed_input"] = confirmed_input
        self._user_input_field.set("")
        self._input_entry.focus()
        logger.debug("User Input: {}".format(confirmed_input))

    def _on_delete_button_pressed(self, *args):
        self._intra_state_variables["delete_button_pressed"] = True
        logger.debug("Keyboard: \"delete\" button pressed")

    def _on_escape_button_pressed(self, *args):
        self._intra_state_variables["escape_button_pressed"] = True
        logger.debug("Keyboard: \"escape\" button pressed")

    def _on_tab_button_pressed(self, *args):
        self._intra_state_variables["tab_button_pressed"] = True
        logger.debug("Keyboard: \"tab\" button pressed")

    def _on_account_names_list_box_selected(self, event):
        selections = self._account_names_list_box.curselection()
        if len(selections):
            account_name = self._account_names_list_box.get(selections[0])
            self._intra_state_variables["account_name_selected"] = account_name
            logger.debug("Account name selected: {}".format(account_name))
        else:
            self._intra_state_variables.pop("account_name_selected", None)

    def _activate_console_view(self):
        self._deactivate_account_names_list_box_view()
        self._deactivate_account_view()
        self._console.pack(side="top", fill="both", expand=True)

    def _deactivate_console_view(self):
        self._console.pack_forget()

    def _activate_account_names_list_box_view(self):
        self._deactivate_console_view()
        self._deactivate_account_view()
        self._account_names_list_box.pack(
            side="left", fill="both", expand=True
        )
        self._account_names_scroll_bar.pack(side="right", fill="both")

    def _deactivate_account_names_list_box_view(self):
        self._account_names_list_box.delete(0, "end")
        self._account_names_list_box.pack_forget()
        self._account_names_scroll_bar.pack_forget()

    def _activate_account_view(self) -> tk.Frame:
        self._deactivate_console_view()
        self._deactivate_account_names_list_box_view()
        self._account_frame.pack(side="top", fill="both", expand=True)
        self._account_canvas.pack(side="left", fill="both", expand=True)
        self._account_scroll_bar.pack(
            before=self._account_canvas, side="right", fill="y"
        )
        account_contents_frame = tk.Frame(self._account_canvas)
        account_contents_frame.bind(
            "<Configure>",
            lambda e: self._account_canvas.configure(
                scrollregion=self._account_canvas.bbox('all')
            ),
        )
        accountCanvas_contentsWindow = self._account_canvas.create_window(
            (0, 0), window=account_contents_frame, anchor="nw"
        )
        ## \[[Dis](https://stackoverflow.com/a/29322445)\] Tkinter: How to get frame in canvas window to expand to the size of the canvas?
        self._account_canvas.bind(
            "<Configure>",
            lambda e: self._account_canvas.itemconfig(
                accountCanvas_contentsWindow, width=e.width
            ),
        )
        self._account_canvas.itemconfig(
            accountCanvas_contentsWindow,
            width=self._account_canvas.winfo_width(),
        )
        return account_contents_frame

    def _deactivate_account_view(self):
        self._account_canvas.unbind("<Configure>")
        for widget in self._account_canvas.winfo_children():
            widget.destroy()
        self._account_frame.pack_forget()
        self._account_canvas.pack_forget()
        self._account_scroll_bar.pack_forget()

    def _entrance_state_stay_callback(self) -> FsmState:
        self._console_print(text="Welcome to the password vault.")
        return FsmState.LOAD_METADATA

    def _load_metadata_state_stay_callback(self) -> FsmState:
        if os.path.isfile(self._metadata_file_path):
            self._metadata = json.load(open(self._metadata_file_path, "r"))
        else:
            self._metadata = {self.DATA_REPLICA_DIRECTORIES_FIELD: []}
            self._save_metadata()
        return FsmState.MANAGE_DATA_REPLICA_DIRECTORIES

    def _manage_data_replica_directories_state_enter_callback(self):
        print_content = (
            "Password vault data replica directories:\n"
            + "\n".join(
                [
                    f"{i + 1}) {d}"
                    for i, d in enumerate(
                        self._metadata[self.DATA_REPLICA_DIRECTORIES_FIELD]
                    )
                ]
            )
            + "\n"
            + (
                "Choose an operation:\n"
                "1) Add a directory\n"
                "2) Delete a directory\n"
                "Pass an empty input to go to the next step."
            )
        )
        self._console_print(text=print_content)
        self._configure_common_buttons(
            texts=["Next", "Add", "Delete"],
            states=["normal", "normal", "normal"],
        )

    def _manage_data_replica_directories_state_stay_callback(self) -> FsmState:
        command = self._intra_state_variables.pop("confirmed_input", None)
        if command is not None:
            if command == "":
                command = "next"
            elif command == "1":
                command = "add"
            elif command == "2":
                command = "delete"
            else:
                self._console_print("Invalid input: \"{}\"".format(command))
                return FsmState.MANAGE_DATA_REPLICA_DIRECTORIES
        else:
            command = self._intra_state_variables.pop(
                "command_button_pressed", None
            )
        if command == "next":
            if len(self._metadata[self.DATA_REPLICA_DIRECTORIES_FIELD]) == 0:
                self._console_print(
                    "Must specify at least one directory to store the account data."
                )
                return FsmState.MANAGE_DATA_REPLICA_DIRECTORIES
            self._save_metadata()
            return FsmState.ASK_MAIN_PASSWORD
        elif command == "add":
            return FsmState.ADD_DATA_REPLICA_DIRECTORY
        elif command == "delete":
            return FsmState.DELETE_DATA_REPLICA_DIRECTORY
        return FsmState.MANAGE_DATA_REPLICA_DIRECTORIES

    def _manage_data_replica_directories_state_exit_callback(self):
        self._configure_common_buttons(
            texts=["", "", ""], states=["disabled", "disabled", "disabled"]
        )

    def _add_data_replica_directory_state_stay_callback(self) -> FsmState:
        data_replica_directory = tkinter.filedialog.askdirectory(
            parent=self._root,
            initialdir=os.path.expanduser("~"),
            title="Add data replica directory",
        )
        if data_replica_directory != "":
            self._metadata[self.DATA_REPLICA_DIRECTORIES_FIELD].append(
                os.path.normpath(data_replica_directory)
            )
        return FsmState.MANAGE_DATA_REPLICA_DIRECTORIES

    def _delete_data_replica_directory_state_enter_callback(self):
        self._console_print("Enter the index of the directory to delete it.")

    def _delete_data_replica_directory_state_stay_callback(self) -> FsmState:
        command = self._intra_state_variables.pop("confirmed_input", None)
        if command is None:
            return FsmState.DELETE_DATA_REPLICA_DIRECTORY
        is_command_valid = command.isdecimal()
        is_command_valid &= int(command) > 0 and int(command) <= len(
            self._metadata[self.DATA_REPLICA_DIRECTORIES_FIELD]
        )
        if not is_command_valid:
            self._console_print("Invalid input: \"{}\"".format(command))
            return FsmState.MANAGE_DATA_REPLICA_DIRECTORIES
        deleted_directory = self._metadata[
            self.DATA_REPLICA_DIRECTORIES_FIELD
        ].pop(int(command) - 1)
        self._console_print("Deleted directory: {}".format(deleted_directory))
        return FsmState.MANAGE_DATA_REPLICA_DIRECTORIES

    def _ask_main_password_state_enter_callback(self):
        self._console_print(
            "Enter the main password. This password will be used to "
            "encrypt the vault. It should be different from any other "
            "passwords you have used. If you forget this password, you will "
            "lose access to this password vault. However, you should not "
            "write this password down, or disclose it to anyone."
        )

    def _ask_main_password_state_stay_callback(self) -> FsmState:
        pw = tkinter.simpledialog.askstring(
            "Password", "Enter the main password:", show="*"
        )
        if pw is None or pw == "":
            self._console_print("Password cannot be empty.")
            return FsmState.EXIT
        logger.info("Wait until the password vault is initialized.")
        try:
            self._password_vault = PasswordVault(
                directories=self._metadata[
                    self.DATA_REPLICA_DIRECTORIES_FIELD
                ],
                main_password=pw,
            )
        except ValueError as e:
            self._console_print(text=str(e))
            return FsmState.ASK_MAIN_PASSWORD
        return FsmState.MAIN_MENU

    def _main_menu_state_enter_callback(self):
        self._activate_console_view()
        self._title_label.config(text="Main Menu")
        self._console_print(
            "Choose an operation:\n"
            "1) Search to add / delete / modify / view an account\n"
            "2) Change password\n"
            "Passing an empty input has the same effect as selecting option 1."
        )
        self._configure_common_buttons(
            texts=["Search", "Change Password", ""],
            states=["normal", "normal", "disabled"],
        )

    def _main_menu_state_stay_callback(self) -> FsmState:
        command = self._intra_state_variables.pop("confirmed_input", None)
        if command is not None:
            if command == "" or command == "1":
                command = "search"
            elif command == "2":
                command = "change password"
            else:
                self._console_print("Invalid input: \"{}\".".format(command))
                return FsmState.MAIN_MENU
        else:
            command = self._intra_state_variables.pop(
                "command_button_pressed", None
            )
        if command == "search":
            return FsmState.SEARCH_ACCOUNT
        elif command == "change password":
            return FsmState.CHANGE_PASSWORD
        return FsmState.MAIN_MENU

    def _main_menu_state_exit_callback(self):
        self._title_label.config(text="")
        self._configure_common_buttons(
            texts=["", "", ""], states=["disabled", "disabled", "disabled"]
        )

    def _search_accounts_state_enter_callback(self):
        self._title_label.config(text="Account Searching")
        self._configure_common_buttons(
            texts=["", "Cancel", ""], states=["disabled", "normal", "disabled"]
        )
        self._intra_state_variables["account_candidates"] = []
        self._activate_account_names_list_box_view()

    def _search_accounts_state_stay_callback(self) -> FsmState:
        command = None
        if (
            self._intra_state_variables.pop("escape_button_pressed", False)
            is True
        ):
            command = "cancel"
        else:
            command = self._intra_state_variables.pop(
                "command_button_pressed", None
            )
        if command == "cancel":
            return FsmState.MAIN_MENU

        account_selected = self._intra_state_variables.pop(
            "confirmed_input", ""
        )
        if account_selected == "":
            account_selected = self._intra_state_variables.get(
                "account_name_selected", ""
            )
        if account_selected != "":
            self._inter_state_variables["account_name"] = account_selected
            return FsmState.MANAGE_ACCOUNT

        tab_button_pressed = self._intra_state_variables.pop(
            "tab_button_pressed", None
        )
        if tab_button_pressed is not None:
            candidates = self._intra_state_variables["account_candidates"]
            if len(candidates) > 0:
                self._user_input_field.set(candidates[0])
                self._input_entry.focus()

        user_input = self._intra_state_variables.pop("user_input", None)
        if user_input is not None:
            account_candidates = self._password_vault.search_account_name(
                account_name=user_input,
                n_candidates=self.ACCOUNT_NAMES_VIEW_N_CANDIDATES,
            )
            self._intra_state_variables[
                "account_candidates"
            ] = account_candidates
            self._account_names_list_box.delete(0, "end")
            for account_name in account_candidates:
                self._account_names_list_box.insert("end", account_name)
        return FsmState.SEARCH_ACCOUNT

    def _search_accounts_state_exit_callback(self):
        self._title_label.config(text="")

    def _change_password_state_stay_callback(self) -> FsmState:
        self._console_print(
            "Select the directory for storing the the archive of the existing password vault."
        )
        archive_directory = tkinter.filedialog.askdirectory(
            parent=self._root,
            initialdir=".",
            title="Directory of the archive",
        )
        if archive_directory == "":
            self._console_print(
                "Archive of the existing password vault will NOT be created."
            )
        else:
            current_datetime_str = datetime.datetime.now().strftime(
                "%Y%m%d_%H%M%S"
            )
            archive_file_name = f"password_vault_{current_datetime_str}.zip"
            archive_file_path = os.path.join(
                archive_directory, archive_file_name
            )
            self._password_vault.create_archive(
                archive_file_path=archive_file_path
            )
            self._console_print(
                "Archive of the existing password vault created."
            )
        pw = tkinter.simpledialog.askstring(
            "New Password", "Enter the new password:", show="*"
        )
        if pw is None or pw == "":
            self._console_print("Password cannot be empty.")
            return FsmState.MAIN_MENU
        self._password_vault.change_password(new_main_password=pw)
        self._console_print("Password changed successfully.")
        return FsmState.MAIN_MENU

    def _manage_account_state_enter_callback(self):
        def on_delete_row(
            frame: tk.Frame, account_fields: OrderedDict, idx: int
        ):
            field_key = account_fields[idx][0].get()
            response = tkinter.messagebox.askyesno(
                title="Delete Row",
                message=f"Are you sure you want to delete this row: \"{field_key}\"?",
            )
            if response is not True:
                return
            del account_fields[idx]
            frame.destroy()

        def append_row(frame: tk.Frame, account_fields: OrderedDict):
            new_row_idx = len(account_fields)
            new_row_frame = tk.Frame(frame)
            field_key_entry = tk.Entry(
                new_row_frame, exportselection=False, font=self._normal_font
            )
            field_value_entry = tk.Entry(
                new_row_frame,
                show="*",
                exportselection=False,
                font=self._normal_font,
            )
            field_value_visibility_toggle = tk.Button(
                new_row_frame,
                text="*",
                font=self._normal_font,
                command=lambda: field_value_entry.configure(
                    show="" if field_value_entry["show"] == "*" else "*"
                ),
            )
            delete_row_button = tk.Button(
                new_row_frame,
                text="X",
                font=self._normal_font,
                command=lambda: on_delete_row(
                    frame=new_row_frame,
                    account_fields=account_fields,
                    idx=new_row_idx,
                ),
            )

            account_fields[new_row_idx] = (field_key_entry, field_value_entry)

            new_row_frame.pack(side="top", fill="x", padx=8, pady=4, ipady=4)
            field_key_entry.pack(side="left", fill="both", expand=True, padx=4)
            field_value_entry.pack(
                side="right", fill="both", expand=True, padx=4
            )
            field_value_visibility_toggle.pack(
                side="right", fill="y", ipadx=8, padx=4
            )
            delete_row_button.pack(side="right", fill="y", ipadx=8, padx=4)
            return new_row_frame, field_key_entry, field_value_entry

        def on_append_row_button_pressed(
            frame: tk.Frame, canvas: tk.Canvas, account_fields: OrderedDict
        ):
            append_row(frame=frame, account_fields=account_fields)
            canvas.yview_moveto(1.0)

        self._title_label.config(text="Account Details")
        self._configure_common_buttons(
            texts=["Confirm", "Cancel", "Delete"],
            states=["normal", "normal", "normal"],
        )

        account_details_frame = self._activate_account_view()
        account_name = self._inter_state_variables.get("account_name", None)
        if not isinstance(account_name, str) or account_name == "":
            logger.error(
                "\"account_name\" not in attribute \"_inter_state_variables\""
            )
            return FsmState.EXIT
        account_name_label = tk.Label(
            account_details_frame,
            text=account_name,
            font=self._account_details_account_name_label_font,
        )
        header_frame = tk.Frame(account_details_frame)
        field_key_label = tk.Label(
            header_frame, text="Field", font=self._normal_font
        )
        field_value_label = tk.Label(
            header_frame, text="Value", font=self._normal_font
        )

        account_name_label.pack(side="top", fill="x", pady=4, ipady=4)
        header_frame.pack(side="top", fill="x", pady=4, ipady=4)
        field_key_label.pack(side="left", fill="both", padx=4, expand=True)
        field_value_label.pack(side="left", fill="both", padx=4, expand=True)

        if account_name in self._password_vault:
            account_details = self._password_vault.get_account(
                account_name=account_name
            )
        else:
            account_details = self._password_vault.get_blank_account()
            account_details[PasswordVault.ACCOUNT_NAME_TAG] = account_name

        default_visible_fields = [
            PasswordVault.ACCOUNT_NAME_TAG,
            PasswordVault.ACCOUNT_MODIFICATION_DATE_TAG,
            PasswordVault.ACCOUNT_UUID_TAG,
        ]
        self._intra_state_variables["account_fields"] = OrderedDict()
        for k, v in account_details.items():
            _, field_key_entry, field_value_entry = append_row(
                frame=account_details_frame,
                account_fields=self._intra_state_variables["account_fields"],
            )
            field_key_entry.insert(0, k)
            field_value_entry.insert(0, v)
            if k in default_visible_fields:
                field_value_entry.configure(show="")
        append_field_button = tk.Button(
            account_details_frame,
            relief="groove",
            text="Add Field",
            font=self._normal_font,
            command=partial(
                on_append_row_button_pressed,
                frame=account_details_frame,
                canvas=self._account_canvas,
                account_fields=self._intra_state_variables["account_fields"],
            ),
        )
        footer_label = tk.Label(
            account_details_frame, text="", font=self._normal_font
        )

        append_field_button.pack(
            side="bottom", fill="x", padx=16, pady=4, ipady=4
        )
        footer_label.pack(
            before=append_field_button,
            side="bottom",
            fill="x",
            pady=8,
            ipady=4,
        )

    def _manage_account_state_stay_callback(self) -> FsmState:
        command = None
        if (
            self._intra_state_variables.pop("escape_button_pressed", False)
            is True
        ):
            command = "cancel"
        elif (
            self._intra_state_variables.pop("delete_button_pressed", False)
            is True
        ):
            command = "delete"
        elif self._intra_state_variables.pop("confirmed_input", None) == "":
            command = "confirm"
        else:
            command = self._intra_state_variables.pop(
                "command_button_pressed", None
            )
        if command is None:
            return FsmState.MANAGE_ACCOUNT

        account_name = self._inter_state_variables.get("account_name", None)
        if not isinstance(account_name, str) or account_name == "":
            logger.error(
                "\"account_name\" not in attribute \"_inter_state_variables\""
            )
            return FsmState.EXIT
        if command == "confirm":
            account_fields = self._intra_state_variables["account_fields"]
            updated_account_details = OrderedDict()
            for field_key_entry, field_value_entry in account_fields.values():
                key = field_key_entry.get()
                value = field_value_entry.get()
                if len(key) == 0:
                    tkinter.messagebox.showerror(
                        title="Invalid Field",
                        message="Field cannot have an empty identifier",
                    )
                    return FsmState.MANAGE_ACCOUNT
                if key in updated_account_details:
                    tkinter.messagebox.showerror(
                        title="Invalid Field",
                        message="Field identifiers must be unique",
                    )
                    return FsmState.MANAGE_ACCOUNT
                updated_account_details[key] = value
            if PasswordVault.ACCOUNT_NAME_TAG not in updated_account_details:
                tkinter.messagebox.showerror(
                    title="Invalid Field",
                    message=f"Key \"{PasswordVault.ACCOUNT_NAME_TAG}\" is compulsory",
                )
                return FsmState.MANAGE_ACCOUNT
            new_account_name = updated_account_details[
                PasswordVault.ACCOUNT_NAME_TAG
            ]
            if new_account_name == "":
                tkinter.messagebox.showerror(
                    title="Invalid Value",
                    message=f"\"{PasswordVault.ACCOUNT_NAME_TAG}\" cannot be empty",
                )
                return FsmState.MANAGE_ACCOUNT
            if new_account_name == account_name:
                self._password_vault.update_account(
                    details=updated_account_details
                )
                logger.info(f"Updated account:\"{account_name}\"")
            else:
                r = tkinter.messagebox.askyesno(
                    title="Rename Account",
                    message=(
                        "Are you sure you want to rename this account from "
                        f"\"{account_name}\" to \"{new_account_name}\"?"
                    ),
                )
                if r is False:
                    return FsmState.MANAGE_ACCOUNT
                if new_account_name in self._password_vault:
                    tkinter.messagebox.showerror(
                        title="Invalid Value",
                        message=(
                            f"Modified \"{PasswordVault.ACCOUNT_NAME_TAG}\": "
                            f"\"{new_account_name}\" already exists"
                        ),
                    )
                    return FsmState.MANAGE_ACCOUNT
                else:
                    self._password_vault.update_account(
                        details=updated_account_details
                    )
                    try:
                        self._password_vault.delete_account(
                            account_name=account_name
                        )
                    except ValueError:
                        logger.warning(
                            f"Failed to delete account: \"{account_name}\""
                        )
                logger.info(
                    "Updated account and changed account name from "
                    f"\"{account_name}\" to \"{new_account_name}\""
                )
            return FsmState.SEARCH_ACCOUNT
        elif command == "cancel":
            return FsmState.SEARCH_ACCOUNT
        elif command == "delete":
            r = tkinter.messagebox.askyesno(
                title="Delete Account",
                message="Are you sure you want to delete this account?",
            )
            if r is False:
                return FsmState.MANAGE_ACCOUNT
            try:
                self._password_vault.delete_account(account_name=account_name)
                logger.info(f"Deleted account:\"{account_name}\"")
            except ValueError:
                logger.warning(f"Failed to delete account: \"{account_name}\"")
            return FsmState.SEARCH_ACCOUNT
        logger.error("Unknown command")
        return FsmState.EXIT

    def _manage_account_state_exit_callback(self):
        self._title_label.config(text="")
        self._inter_state_variables.pop("account_name", None)

    def _exit_state_stay_callback(self) -> FsmState:
        return FsmState.EXIT

    def _console_print(
        self,
        text: str,
        prefix: str = "",
        suffix: str = "",
        use_default_prefix: bool = True,
        use_default_suffix: bool = True,
    ):
        if use_default_prefix is True:
            prefix = f"[{time.process_time():.2f}] "
        if use_default_suffix is True:
            suffix = "\n"
        print_content = f"{prefix}{text}{suffix}"
        logger.debug(print_content)
        self._console.configure(state="normal")
        self._console.insert(tk.END, print_content)
        self._console.configure(state="disabled")
        self._console.see(tk.END)
        self._console_remove_obsolete_lines()

    def _console_remove_obsolete_lines(self):
        n_lines = int(self._console.index("end").split(".")[0]) - 1
        if n_lines > self.CONSOLE_MAX_LINES:
            del_n = n_lines - self.CONSOLE_MAX_LINES
            self._console.configure(state="normal")
            self._console.delete("1.0", f"{del_n + 1}.0")
            self._console.configure(state="disabled")

    def _console_clear(self):
        self._console.configure(state="normal")
        self._console.delete("1.0", tk.END)
        self._console.configure(state="disabled")

    def _configure_common_buttons(self, texts: list, states: list):
        assert len(self._command_buttons) == len(texts) and len(texts) == len(
            states
        )
        for i, (t, s) in enumerate(zip(texts, states)):
            self._command_buttons[i]["text"] = t
            self._command_buttons[i]["state"] = s

    def _on_fsm_state_changed(self, current_state: Enum, next_state: Enum):
        logger.debug("{} -> {}".format(current_state, next_state))
        self._intra_state_variables.clear()
        self._user_input_field.set("")
        self._input_entry.focus()

    def _save_metadata(self):
        json.dump(
            self._metadata, open(self._metadata_file_path, "w"), indent=4
        )
