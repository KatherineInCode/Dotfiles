#!/bin/bash
#
# Based on https://github.com/holman/dotfiles/blob/master/zsh/zshrc.symlink

# shellcheck source=/dev/null

DF=$HOME/.df

if [ -f ~/.secrets ]; then
  source ~/.secrets
fi

if [ -f ~/.local.bash_profile ]; then
  source ~/.local.bash_profile
fi

all_files=("$DF"/**/*.bash)

# Source all of the path ones first
for file in "${all_files[@]}"
do
  if [[ $file != */path.bash ]]; then
    continue
  fi
  source "$file"
done  

# Then source all .bash files that are not path or completion
for file in "${all_files[@]}"
do
  if [[ $file == */path.bash ]]; then
    continue
  fi
  source "$file"
done

unset DF
unset all_files

# I prefer vi mode for command-line editing
set -o vi
export EDITOR=vim
