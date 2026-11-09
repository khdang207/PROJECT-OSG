#!/bin/bash
# Cai dat moi truong chay cho du an AI Backup (Linux).
# Tao venv roi cai requirements.txt. Chay xong thi dung:
#   source venv/bin/activate
set -e
cd "$(dirname "$0")"
python3 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt
echo "Xong. Chay: source venv/bin/activate"
