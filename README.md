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

To use the homebrew version of bash:

```
echo /opt/homebrew/bin/bash >> /etc/shells
chsh -s /opt/homebrew/bin/bash
```

### Terminal Theme

I use the theme called "Iridium" in the `files` folder. This is my tweaked version of [Hybrid](https://github.com/w0ng/vim-hybrid).

### Key Bindings

Put `files/DefaultKeyBinding.dict` in the folder `~/Library/KeyBindings/`.

### Better Touch Tool

I have a set of custom gestures from BetterTouchTool in the `files` directory; just import them into the app.

## System Settings

A rundown of how I adjust things in System Settings to my liking. This section exists mostly for documentation purposes.

### Appearance

I always use light mode on my professional machines, and dark mode on my personal machines. Multicolor accent color.

### Accessibility

Under "Zoom", I turn on "Use scroll gesture with modifier keys to zoom", with a modifier of "Control", a zoom style of "Full Screen", and under "Advanced", I turn off "Smooth images". This lets me zoom in easily on simulators to check pixel alignment and things like that.

### Control Center

I set "Sound" to "Always Show in Menu Bar".

I set "Spotlight" to "Don't Show in Menu Bar".

### Desktop and Dock

I use a `defaults write` command to keep the Dock from resizing: `defaults write com.apple.Dock size-immutable -bool true`.

I set "Minimize windows using" to "Scale Effect". I turn on "Minimize windows into application icon". I turn off "Show suggested and recent apps in Dock".

I set "Click wallpaper to reveal desktop" to "Only in Stage Manager".

I turn off "Close windows when quitting an application".

I turn off "Automaticall rearrange Spaces based on most recent use" and turn on "When switching to an application, switch to a Space with open windows for the application".

#### Hot Corners

I set the lower-right to "Start Screen Saver".

### Wallpaper

On my professional machines I use one of the colorful non-landscape system wallpapers. I turn off "Show as screen saver".

### Screen Saver

I use "Shuffle All" under "Shuffle Aerials", and I shuffle "Continuously".

### Lock Screen

Unless corporate policy is otherwise, I set my "Start Screen Saver when inactive" to "5 minutes", "Turn display off on battery when inactive" to "10 minutes", "Turn display off on power adapter when inactive" to "1 hour", and "Require password after screen saver begins or display is turned off" to "5 seconds".

### Keyboard

I set "Key repeat rate" to the fastest and "Delay until repeat" to the second-shortest.

I set "Press 🌐 key to" to "Do nothing".

#### Keyboard Shortcuts

Under "Mission Control", I turn off the move left/right key combinations, because they interfere with Xcode.

Under "Splotlight", I turn off "Show Finder search window".

Under "Modifier Keys", I set "Caps Lock" to "Escape".

#### Text Input

Under "Text Input", I turn off "Correct spelling automatically", "Capitalize words automatically", "Show inline predictive text", and "Add period with double-space".

### Trackpad

I set "Look up & data detectors" to "Tap with Three Fingers".

I set "Swipe between full-screen applications" to "Swipe Left or Right with Four Fingers", because I use BetterTouchTool to make a three-finger swipe change tabs.

I set "App Exposé" to "Swipe Down with Three Fingers".