import json
import logging
import logging.config
import os


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
from password_vault.password_vault_gui import PasswordVaultGui


#### #### #### ####
#### main
#### #### #### ####
if __name__ == "__main__":
    logging.config.dictConfig(
        json.load(
            open(os.path.join(APP_DIRECTORY, "config", "python_logging.json"))
        )
    )

    password_vault = PasswordVaultGui()
    password_vault.loop()
