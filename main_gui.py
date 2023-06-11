import logging
import logging.config
import os

from password_vault.password_vault_gui import PasswordVaultGui


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        level=logging.DEBUG if os.environ.get("DEBUG") else logging.INFO,
    )

    password_vault = PasswordVaultGui()
    password_vault.loop()
