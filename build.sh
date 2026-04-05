#!/bin/bash
# PyInstaller 打包脚本

set -e

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Building executable..."
pyinstaller --onefile \
    --name github-collector \
    --add-data "config.yaml:." \
    src/main.py

echo "Build complete!"
echo "Executable: dist/github-collector"
