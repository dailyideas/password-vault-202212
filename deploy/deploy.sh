#!/bin/bash

pyinstaller deploy/main_gui.spec
mkdir dist/password-vault/data/
exports_directory="exports/"`date +"%Y-%m-%d_%H%M%S"`
mkdir -p $exports_directory
zip "$exports_directory/password-vault.zip" dist/password-vault/
