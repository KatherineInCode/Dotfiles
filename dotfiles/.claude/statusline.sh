#!/bin/bash

# Source colors from dotfiles
source ~/.df/includes/colors.bash

# Read JSON input from stdin
input=$(cat)

# Extract relevant information
model=$(echo "$input" | jq -r '.model.display_name')
cwd=$(echo "$input" | jq -r '.workspace.current_dir')
remaining=$(echo "$input" | jq -r '.context_window.remaining_percentage // empty')

# Build status line
status="$model | $(basename "$cwd")"

# Add context remaining if available
if [ -n "$remaining" ]; then
  status="$status | ${remaining}%"
fi

echo "$status"
