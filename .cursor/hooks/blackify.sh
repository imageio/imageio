#!/bin/bash

# Read JSON input from stdin
json_input=$(cat)

# Extract the file path that was edited
file_path=$(echo "$json_input" | jq -r '.file_path // empty')

# Format the modified file with black (only Python files)
if [ -n "$file_path" ] && ([[ $file_path == *.py ]] || [[ $file_path == *.pyi ]]); then
    uv run black "$file_path" 2>/dev/null
fi

exit 0
