# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a personal dotfiles repository for macOS development environment configuration. It lives at `~/.df` and uses GNU Stow to symlink dotfiles into the home directory.

## Common Commands

```bash
# Full environment update (pulls repo, updates brew, stows dotfiles, updates vim plugins, updates rust)
./update.sh

# Stow dotfiles manually (restow to refresh symlinks)
stow --verbose --restow --dir ~/.df/ --target ~/ --ignore=\.DS_Store dotfiles

# Install/update homebrew packages
brew bundle --file=~/.df/Brewfile

# Run a git command across all nested git repos (e.g., Vundle submodule)
git distribute <command>
```

## Architecture

### Directory Structure

- **dotfiles/**: Files to be symlinked into `~/` via Stow. The directory structure mirrors the home directory layout.
- **includes/**: Bash configuration modules (`.bash` files) sourced by `.bashrc` in a specific order: `path.bash` files first, then all others.
- **bin/**: Custom git subcommands (`git-distribute`, `git-sha`, `git-commit-count`) that extend git functionality.
- **files/**: Configuration files that need manual installation (Terminal theme, key bindings).

### Bash Loading Order

The `.bashrc` sources all `.bash` files from the repository:

1. Sources `~/.secrets` and `~/.local.bash_profile` if they exist (for machine-specific config)
2. Sources all `path.bash` files first (to set up PATH)
3. Sources remaining `.bash` files from `includes/`

### Custom Git Commands

Scripts in `bin/` are automatically available as git subcommands:

- `git distribute <cmd>`: Runs a git command in all nested git repositories (useful for updating submodules)
- `git sha`: Returns the short SHA of HEAD
- `git commit-count`: Returns the number of commits

## Linting

- Shell scripts should pass `shellcheck`.
- Markdown files should pass `markdownlint`.
