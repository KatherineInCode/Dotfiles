#!/usr/bin/env bash
#
# Logging helpers for bin scripts
#
# Requires SCRIPT_NAME to be set by the caller before sourcing.
# Sources colors.bash automatically.
#
# Functions:
#   info  — prints a blue bold prefixed message to stdout
#   err   — prints a red bold prefixed error message to stderr
#   fatal — prints an error message and exits with status 1

[[ -n "${_LOGGING_BASH_LOADED:-}" ]] && return
_LOGGING_BASH_LOADED=1

# shellcheck source=colors.bash
source "$(dirname "$(realpath "${BASH_SOURCE[0]}")")/colors.bash"

info()  { printf "${Bold}${Blue}%s:${Color_Off} %s\n" "${SCRIPT_NAME}" "$*"; }
err()   { printf "${Bold}${Red}%s: error:${Color_Off} %s\n" "${SCRIPT_NAME}" "$*" >&2; }
fatal() { err "$*"; exit 1; }
