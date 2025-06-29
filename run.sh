#!/usr/bin/env sh

echo "=== Starting program ==="

# Install lark
pip install lark
# Might need this or use in a virtual environment
# pip install lark --break-system-packages

# Clone repository
# Es publico
echo "=== Cloning repository ==="
git clone git@github.com:swpiergo121/compiladores_lab_20.git

echo "=== Moving to directory ==="
cd compiladores_lab_20

echo "=== Running code ==="
python3 main.py

echo "=== Done ==="
