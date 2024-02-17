#!/usr/bin/env bash
#
# This file is only executed for login shells. That means it gets executed when logging in over SSH or logging into KDE, but not when a new macOS terminal window is opened

# All of my settings are in bashrc, so just use that

if [ -f ~/.bashrc ]; then
  # shellcheck source=/dev/null
  source ~/.bashrc
fi
