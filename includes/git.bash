#!/usr/bin/env bash

alias gs='git status -sb'
alias gd='git diff --no-ext-diff'
alias gadd='git add -A && git status -sb'

source /opt/homebrew/etc/bash_completion.d/git-prompt.sh
source /opt/homebrew/etc/bash_completion.d/git-completion.bash
