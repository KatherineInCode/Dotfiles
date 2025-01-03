#!/usr/bin/env bash

cleandd() {
    rm -rf ~/Library/Developer/Xcode/DerivedData
    echo "Removed all derived data."
}

alias cleardd=cleandd

cleansims() {
    xcrun simctl --set previews delete all
    echo "Deleted all cached previews."
}

alias clearsims=cleansims

function openws {
    for f in ./*.xcworkspace; do
        open "${f}"
        break;
    done
}

alias sbs="Scripts/bootstrap.sh"
alias csbs="cleardd && sbs"
alias ccsbs="cleardd && clearsims && sbs"
