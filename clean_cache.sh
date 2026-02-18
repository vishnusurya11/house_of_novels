#!/bin/bash
# Clean all Python bytecode cache files

echo "Cleaning Python bytecode cache..."
find . -type f -name "*.pyc" -delete 2>/dev/null
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find .venv -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
echo "Cache cleaned!"
