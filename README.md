# password-vault-202212

# Table of Contents
- [About](#about)
- [Get started](#get-started)

# About
This project provides a tool to encrypt and store the details of accounts. It is not as feature rich as popular password managers like NordPass and 1Password, but it should provide the same level of security.

This password vault does not have features like auto-login, auto-save and browser add-ons. If every thing is implemented correctly, including the Python packages that this project uses, it only guarantees that the stored account will be equally safe when comparing with NordPass and any other password managers that also utilize ChaCha20 as the encryption algorithm. Yes, so there is no reason to use this tool, except that I could save the money for a few lunch over a year... and a bit of self-satisfaction.

Accounts will be encrypted and stored in individual files under a directory you specified. You could specify multiple directories to store the files. They will act as the replicas. It prevents data loss when there is data corruption in some of the directories. The data recovery process is automatic.

## File descriptions

The main logics of this project are implemented in the folder "src/file_manipulation". Class `DirectoryHandler` implements a simple file read write handler within a directory. Class `DirectoryHandlerWithFileHash`, child class of `DirectoryHandler`, extends the functionality by storing the hash of each file in the directory. It helps to discover possible file corruptions. Class `DirectoryHandlerWithEncryption`, child class of `DirectoryHandlerWithFileHash`, further extends the functionality by encrypting the file contents. Changing the encryption key is also supported. Lastly, `DirectoryHandlerWithReplication` is a standalone class which maintains multiple `DirectoryHandlerWithEncryption` instances. These `DirectoryHandlerWithEncryption` instances will be the replicas to one another. Therefore, when one instance found a file corrupted, the content could be recovered from the replica.

`CipherHelper` in "src/data_encryption" is the helper class which specifies how data are encrypted and decrypted. It utilizes the `ChaCha20` module provided by [PyCryptodome](https://www.pycryptodome.org/). Files in "src/bytes_manipulation" and "src/input_manipulation" are some other helper classes. Class `PasswordVault` in "src\password_vault" is a thin wrapper of `DirectoryHandlerWithReplication`. It exposes APIs so that account details could be updated and saved via the JSON data structure.

Lastly, "src/main_cli.py" is the entry point of the tool. It guides users to use the `PasswordVault` by implementing an FSM. The tool works on the command line interface only. Having a GUI will be more element and user-friendly, but it will take some time to implement.

# Get Started
This tool could be used by running the source code via a Python interpreter, or by directly executing the exported program.

## Run the Source Code
1. Ensure Python with version >= 3.10 installed.
1. Clone this repository to the target directory.
1. At the project directory, run `python src\main_cli.py` along with optional arguments. Details of the arguments could be found [here](#optional-arguments-for-main_clipy)

## Directly executing the exported program
Todo...

## Running main_cli.py
The first step is to specifies the folders to be used as the storage space for the password vault. To add or remove a directory, enter the corresponding operation index and press enter. Noting that deleting a directory here does not delete the files in the file system.

# Optional Arguments for main_cli.py
- -d METADATA_DIRECTORY, --metadata-directory METADATA_DIRECTORY
  - The directory where metadata are stored. Default to the directory where the script is located.
- -n N_CANDIDATES, --n_candidates N_CANDIDATES
  - Number of candidates to display when searching for an account.
