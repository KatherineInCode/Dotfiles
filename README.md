# My Dotfiles

This repository contains my dotfiles and other configuration scripts for setting up a development environment, particularly around the command line. Right now, I work almost exclusively on macOS, so these are geared entirely in that direction.

This repository, as dotfiles repositories are apt to be, under constant construction.

## Prerequisites

- Clone this repository into `~/.df`
- Install homebrew (`/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`)
- Install Vundle (`git clone https://github.com/VundleVim/Vundle.vim.git dotfiles/.vim/bundle/Vundle.vim`)

## Update script

The `update.sh` script should take care of updating and installing necessary things, along with using `stow` to manage dotfiles.

## Other Configuration

There are various other things I like to do to set up my environment.

### Shell

To use the homebrew version of zsh:

```
echo /opt/homebrew/bin/zsh >> /etc/shells
chsh -s /opt/homebrew/bin/zsh
```

### Terminal Theme

I use the theme called "Iridium" in the `files` folder. I'm not sure where exactly it comes from—and I've tweaked it a bit here and there.

### Keyboard Settings

Set Key Repeat to the fasted, and Delay Until Repeat to the second-shortest.

Re-map `Caps Lock` to `Escape`. This can be done by System Preferences -> Keyboard -> Keyboard -> Modifier Keys -> Re-map `Caps Lock` to `Escape`.

Turn off "correct spelling automatically" in the Text tab.

In the Shortcuts tab, turn off the Mission Control keyboard shortcuts for moving left/right a space, because it interferes with Xcode.

Input Source is U.S.

Put `files/DefaultKeyBinding.dict` in the `~/Library/KeyBindings`.

### Better Touch Tool

I have a set of custom gestures from BetterTouchTool in the `files` directory; just import them into the app.
