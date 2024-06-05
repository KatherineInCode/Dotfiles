#!/usr/bin/env bash

set -e

# Git

git distribute pull

# Homebrew

brew update
brew upgrade
brew bundle --file=~/.df/Brewfile --no-lock
brew cleanup

# Stow the actual dotfiles

stow --verbose --restow --dir ~/.df/ --target ~/ --ignore=\.DS_Store dotfiles

# Vim plugins

vim +PluginInstall +qall

# Ruby

# Python

#pip3 install --quiet --upgrade pip
#pip3 install --quiet --user --upgrade -r ~/.df/Pipfile

# Rust

rustup update

./cargo.sh
