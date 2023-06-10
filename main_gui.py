import json
import logging
import logging.config
import os

from password_vault.password_vault_gui import PasswordVaultGui


if __name__ == "__main__":
    logging.config.dictConfig(
        json.load(open(os.path.join("configs", "python_logging.json")))
    )

    password_vault = PasswordVaultGui()
    password_vault.loop()
