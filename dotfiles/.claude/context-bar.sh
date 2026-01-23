#!/bin/bash

# Build a context usage progress bar with partial fill and color coding
#
# Arguments:
#   $1 - used_percentage (0-100)
#
# Output:
#   Formatted progress bar string with color codes, or empty if no percentage
#
# Dependencies:
#   Requires color variables (IRed, IYellow, IGreen, IBlue, Color_Off) to be set

build_context_bar() {
    local used_percentage="$1"

    if [ -z "$used_percentage" ]; then
        return
    fi

    # Build a 10-character progress bar with partial fill
    local bar_width=10
    local scaled=$(( used_percentage * bar_width ))
    local filled=$(( scaled / 100 ))
    local remainder=$(( scaled % 100 ))

    # Determine partial character based on remainder (0-99)
    # Empty (0-33%), ▒ medium (34-66%), ▓ dark (67-99%)
    local partial_char=""
    if [ "$filled" -lt "$bar_width" ]; then
        if [ "$remainder" -ge 67 ]; then
            partial_char="▓"
        elif [ "$remainder" -ge 34 ]; then
            partial_char="▒"
        fi
    fi

    # Calculate empty slots
    local has_partial=0
    if [ -n "$partial_char" ]; then has_partial=1; fi
    local empty=$(( bar_width - filled - has_partial ))

    # Choose color based on usage: blue < 20%, green 20-49%, yellow 50-79%, red >= 80%
    local bar_color
    if [ "$used_percentage" -ge 80 ]; then
        bar_color="${IRed}"
    elif [ "$used_percentage" -ge 50 ]; then
        bar_color="${IYellow}"
    elif [ "$used_percentage" -ge 20 ]; then
        bar_color="${IGreen}"
    else
        bar_color="${IBlue}"
    fi

    # Use block characters for the graph: █ full, ▓▒ partial shades, ░ empty
    local bar=""
    local i
    for ((i=0; i<filled; i++)); do bar+="█"; done
    bar+="$partial_char"
    for ((i=0; i<empty; i++)); do bar+="░"; done

    printf " : ${bar_color}%s${Color_Off} %s%%" "$bar" "$used_percentage"
}
