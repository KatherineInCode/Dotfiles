#!/usr/bin/env bash

cleandd() {
    rm -rf ~/Library/Developer/Xcode/DerivedData
    echo "Removed all derived data."
}

alias cleardd=cleandd

function openws {
    for f in ./*.xcworkspace; do
        open "${f}"
        break;
    done
}
