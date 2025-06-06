#!/bin/bash

missing=0
while read -r requirement; do
    pkg=$(echo "$requirement" | cut -d'=' -f1 | cut -d'>' -f1 | cut -d'<' -f1)
    if ! pip show "$pkg" > /dev/null 2>&1; then
        missing=1
        break
    fi
done < requirements.txt

if [ $missing -eq 1 ]; then
    pip install -r requirements.txt
fi

python main.py
