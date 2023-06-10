import json
import logging
import logging.config
import os
import sys

from password_vault.password_vault_gui import PasswordVaultGui


if __name__ == "__main__":
    logging_config_file_path = os.path.join("configs", "python_logging.json")
    if hasattr(sys, "_MEIPASS"):
        logging_config_file_path = os.path.join(
            sys._MEIPASS, logging_config_file_path
        )
    logging.config.dictConfig(json.load(open(logging_config_file_path)))

    password_vault = PasswordVaultGui()
    password_vault.loop()
