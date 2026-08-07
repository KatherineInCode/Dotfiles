#!/usr/bin/env bash

# Read JSON input from stdin
input=$(cat)

# Resolve script directory (following symlinks) for sourcing relative files
script_path="${BASH_SOURCE[0]}"
while [ -L "$script_path" ]; do
    script_dir="$(cd -P "$(dirname "$script_path")" && pwd)"
    script_path="$(readlink "$script_path")"
    [[ $script_path != /* ]] && script_path="$script_dir/$script_path"
done
script_dir="$(cd -P "$(dirname "$script_path")" && pwd)"

# Use the same color variables as other dotfiles
# shellcheck source=../../includes/colors.bash
source "$script_dir/../../includes/colors.bash"

# Source the progress bar function
# shellcheck source=../../bin/progress-bar
source "$script_dir/../../bin/progress-bar"

# Time
current_time=$(date +%H:%M) # Like \A in PS1

# User
current_user=$(whoami) # Like \u in PS1

# Host (underlined if remote)
current_host=$(hostname -s) # Like \h in PS1

if [ -n "$SSH_CLIENT" ] || [ -n "$SSH_TTY" ]; then
    host_format="${Underline}${IPurple}%s${Color_Off}"
else
    host_format="${IPurple}%s${Color_Off}"
fi

base=$(printf "${IBlack}%s${Color_Off} ${IBlue}%s${Color_Off} @ $host_format" "$current_time" "$current_user" "$current_host")

# Current directory name only
current_dir=$(echo "$input" | jq -r '.workspace.current_dir')
display_dir=$(basename "$current_dir")
dir_info=$(printf " : ${IYellow}%s${Color_Off}" "$display_dir")

# Change to working directory
# cspell:ignore statusline
cd "$current_dir" 2>/dev/null || echo "statusline: could not cd to $current_dir" >&2

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

# Git prompt settings
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

# Build git info using __git_ps1
git_info=""
if git rev-parse --git-dir > /dev/null 2>&1; then
    git_info=$(printf " : ${IRed}%s %s${Color_Off}" "$(git_sha)" "$(__git_ps1 "%s")")
fi

# Model name
model_name=$(echo "$input" | jq -r '.model.display_name')
model_info=$(printf " : ${IBlue}%s${Color_Off}" "$model_name")

# Effort level, colored by tier (low->max) on the same blue/green/yellow/red
# heat scale progress-bar/color_tokens use. Tier names and their model
# support are still shifting (xhigh is newer and not universally supported),
# so a tier not in this list falls back to uncolored rather than erroring.
EFFORT_LEVELS=(low medium high xhigh max)
EFFORT_COLORS=("${IBlue}" "${IGreen}" "${IYellow}" "${IRed}" "${Bold}${IRed}")

effort_level=$(echo "$input" | jq -r '.effort.level // empty')
effort_info=""
if [ -n "$effort_level" ]; then
    effort_color=""
    for i in "${!EFFORT_LEVELS[@]}"; do
        if [ "${EFFORT_LEVELS[$i]}" = "$effort_level" ]; then
            effort_color="${EFFORT_COLORS[$i]}"
            break
        fi
    done
    effort_info=$(printf " : ${effort_color}%s${Color_Off}" "${effort_level^}")
fi

# Context window used percentage
used_percentage=$(echo "$input" | jq -r '.context_window.used_percentage // empty')

# Context usage graph
context_info=$(print_progress_bar "$used_percentage")
if [ -n "$context_info" ]; then
    context_info=" : $context_info"
fi

# Session cost
cost_usd=$(echo "$input" | jq -r '.cost.total_cost_usd // empty')
cost_info=""
if [ -n "$cost_usd" ]; then
    cost_info=$(printf " : ${IGreen}\$%.2f${Color_Off}" "$cost_usd")
fi

# Output the status line
# time user @ host : dir : git : model : effort : context : cost
printf "%s%s%s%s%s%s%s\n" "$base" "$dir_info" "$git_info" "$model_info" "$effort_info" "$context_info" "$cost_info"
