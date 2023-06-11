# password-vault-202212

# Table of Contents
- [About](#about)
- [Get started](#get-started)
  - Run the app via source code
  - Run the app via executable
  - GUI explanation

# About
A password vault program with a simple GUI. Just like a Python dictionary mapping a key (e.g. google.com), to another dictionary which contains the details of the key (e.g. the gmail account and its password). No other feature at all. It serves as a DIY project to consolidate the usage of inheritance in OOP, and FSM.

This password vault utilizes the `ChaCha20` module provided by [PyCryptodome](https://www.pycryptodome.org/) as the encryption algorithm.

# Get Started

## Run the app via source code
1. Ensure Python with version >= 3.10 installed.
1. Clone this repository to the target directory.
1. At the project directory, run `python src\main_gui.py`.

## Run the app via executable
1. Download the zip file from the release page.
1. Unzip and run `password-vault\password-vault.exe`.

## GUI explanation
1. The program will begin with waiting you to specify the directories where account data are stored. You can add and/or delete the directories. Each directory will be a replica of each other to provide redundancy.
  - ![002.png](assets/002.png)
1. Next, the program will ask for your password. If your data directories are empty, it will be the password to encrypt the account data. Else, it will check whether it is the correct password to decrypt existing data in the directories.
  - ![003.png](assets/003.png)
1. Afterwards, it is the main menu listing the operations that you can perform on the password vault. You can make your choice by entering the index in the input bar and then press the "enter" button, or click the buttons at the bottom.
1. In the account searching view, it is blank before you enter any character. If you want to add an account, enter the custom name for the account and press the "enter" button. If you want to delete or modify an existing account, enter its name and press the "enter" button. The console will list the best matched candidates when you change the input. You can use the "tab" button for auto-complete, which will fill the input bar with the name of the first row in the list.
  - ![004.png](assets/004.png)
1. By entering the account details view, we can add, delete or modify the fields of the account details using the GUI. We can also delete the account by clicking the "delete" button. By clicking the "confirm" button, the updated account details will be stored.
  - ![005.png](assets/005.png)
