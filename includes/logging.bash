#!/usr/bin/env bash
#
# Logging helpers for bin scripts
#
# Requires SCRIPT_NAME to be set by the caller before sourcing.
# Sources colors.bash automatically.
#
# Functions:
#   success — prints a green bold prefixed success message to stdout
#   info    — prints a blue bold prefixed message to stdout
#   debug   — prints a gray prefixed debug message to stderr; silent unless DEBUG=1
#   warn    — prints a yellow bold prefixed warning to stderr
#   err     — prints a red bold prefixed error message to stderr
#   fatal   — prints an error message and exits with status 1

[[ -n "${_LOGGING_BASH_LOADED:-}" ]] && return
_LOGGING_BASH_LOADED=1

# shellcheck source=colors.bash
source "$(dirname "$(realpath "${BASH_SOURCE[0]}")")/colors.bash"

success() { printf "${Bold}${Green}%s:${Color_Off} %s\n" "${SCRIPT_NAME}" "$*"; }
info()    { printf "${Bold}${Blue}%s:${Color_Off} %s\n" "${SCRIPT_NAME}" "$*"; }
debug()   { [[ -n "${DEBUG:-}" ]] && printf "${IBlack}%s: debug:${Color_Off} %s\n" "${SCRIPT_NAME}" "$*" >&2 || true; }
warn()    { printf "${Bold}${Yellow}%s: warn:${Color_Off} %s\n" "${SCRIPT_NAME}" "$*" >&2; }
err()     { printf "${Bold}${Red}%s: error:${Color_Off} %s\n" "${SCRIPT_NAME}" "$*" >&2; }
fatal()   { err "$*"; exit 1; }
