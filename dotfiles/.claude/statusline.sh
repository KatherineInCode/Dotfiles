#!/bin/bash

# Use the same color variables as other dotfiles
source ../../includes/colors.bash

# Get local variables
current_time=$(date +%H:%M) # Like \A in PS1
current_user=$(whoami) # Like \u in PS1
current_host=$(hostname -s) # Like \h in PS1

# Read JSON input from stdin
input=$(cat)

# Extract prompt-relevant information from JSON input
current_dir=$(echo "$input" | jq -r '.workspace.current_dir')
model_name=$(echo "$input" | jq -r '.model.display_name')
used_percentage=$(echo "$input" | jq -r '.context_window.used_percentage // empty')

# Display path with ~ for home directory (like \w in PS1)
display_dir="${current_dir/#$HOME/~}"

# Source git-prompt.sh for __git_ps1
if [ -f /opt/homebrew/etc/bash_completion.d/git-prompt.sh ]; then
    # shellcheck source=/dev/null
    source /opt/homebrew/etc/bash_completion.d/git-prompt.sh
elif [ -f /usr/local/etc/bash_completion.d/git-prompt.sh ]; then
    # shellcheck source=/dev/null
    source /usr/local/etc/bash_completion.d/git-prompt.sh
elif [ -f /usr/share/git-core/contrib/completion/git-prompt.sh ]; then
    # shellcheck source=/dev/null
    source /usr/share/git-core/contrib/completion/git-prompt.sh
fi

# Git prompt settings (matching prompt.bash)
git_sha() {
    git rev-parse --short HEAD 2>/dev/null
}

# cspell:disable
# shellcheck disable=SC2034
GIT_PS1_SHOWDIRTYSTATE=1
# shellcheck disable=SC2034
GIT_PS1_SHOWUNTRACKEDFILES=1
# shellcheck disable=SC2034
GIT_PS1_SHOWSTASHSTATE=1
# shellcheck disable=SC2034
GIT_PS1_SHOWUPSTREAM="verbose"
# cspell:enable

# Change to working directory
# cspell:ignore statusline
cd "$current_dir" 2>/dev/null || echo "statusline: could not cd to $current_dir" >&2

# Build git info using __git_ps1
git_info=""
if git rev-parse --git-dir > /dev/null 2>&1; then
    git_info=$(printf " ${IRed}%s %s ${Color_Off}:" "$(git_sha)" "$(__git_ps1 "%s")")
fi

# Build context info with graph
context_info=""
if [ -n "$used_percentage" ]; then
    # Build a 10-character progress bar
    bar_width=10
    filled=$(( used_percentage * bar_width / 100 ))
    empty=$(( bar_width - filled ))

    # Use block characters for the graph
    bar=""
    for ((i=0; i<filled; i++)); do bar+="█"; done
    for ((i=0; i<empty; i++)); do bar+="░"; done

    context_info=$(printf " : ${IPurple}%s${Color_Off} %s%%" "$bar" "$used_percentage")
fi

# Check if SSH session (underline hostname if so)
if [ -n "$SSH_CLIENT" ] || [ -n "$SSH_TTY" ]; then
    host_format="${Underline}${IPurple}%s${Color_Off}"
else
    host_format="${IPurple}%s${Color_Off}"
fi

# Output the status line
# time user @ host : git : dir : model : context
printf "${IBlack}%s${Color_Off} ${IBlue}%s${Color_Off} @ $host_format :%s ${IYellow}%s${Color_Off} : ${IBlue}%s${Color_Off}%s\n" "$current_time" "$current_user" "$current_host" "$git_info" "$display_dir" "$model_name" "$context_info"
