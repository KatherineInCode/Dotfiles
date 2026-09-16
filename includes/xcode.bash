#!/usr/bin/env bash

cleandd() {
    if [[ -d build/DerivedData ]]; then
        echo "Removing ./build/DerivedData ($(du -sh build/DerivedData | cut -f1))..."
        rm -rf build/DerivedData
    fi

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

alias sbsw="sbs && openws"
alias csbsw="cleardd && sbs && openws"
alias ccsbsw="cleardd && clearsims && sbs && openws"
