#!/usr/bin/env bash
#
# Shared helpers for Greek-letter iOS worktree scripts (nwt, park)
#
# Requires SCRIPT_NAME to be set and logging.bash sourced by the caller.
#
# Variables:
#   DEVELOPER — path to ~/Developer
#   MAIN_REPO — path to the main iOS repo checkout
#
# Functions:
#   fetch_and_rebase_onto_main — fetches origin/main and rebases a worktree onto
#                                it, aborting and exiting 1 on rebase failure

[[ -n "${_WORKTREE_HELPERS_BASH_LOADED:-}" ]] && return
_WORKTREE_HELPERS_BASH_LOADED=1

DEVELOPER="${HOME}/Developer"
MAIN_REPO="${DEVELOPER}/ios/main"

# Fetches origin/main into MAIN_REPO, then rebases the given worktree onto it.
# Aborts the rebase and exits the script with status 1 on conflict/failure.
#
# Args:
#   $1 - dir: path to the worktree to rebase.
#   $2 - branch_label: human-readable branch name for log messages (e.g.
#        "alpha-parked").
fetch_and_rebase_onto_main() {
    local dir="$1"
    local branch_label="$2"

    info "fetching origin/main..."
    git -C "$MAIN_REPO" fetch origin main

    info "rebasing ${branch_label} onto origin/main..."
    if ! git -C "$dir" rebase origin/main; then
        err "rebase failed; aborting"
        git -C "$dir" rebase --abort 2>/dev/null || true
        exit 1
    fi
}
