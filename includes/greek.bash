#!/usr/bin/env bash
#
# Greek alphabet arrays for worktree scripts

[[ -n "$_GREEK_BASH_LOADED" ]] && return
_GREEK_BASH_LOADED=1

# Parallel arrays mapping Greek letter names to Unicode characters.
#
# GREEK_NAMES — lowercase English names (alpha, beta, …, omega)
# GREEK_CHARS — corresponding Unicode characters (α, β, …, ω)
GREEK_NAMES=(
    alpha beta gamma delta epsilon zeta eta theta iota kappa
    lambda mu nu xi omicron pi rho sigma tau upsilon phi chi psi omega
)
GREEK_CHARS=(
    $'\u03B1' $'\u03B2' $'\u03B3' $'\u03B4' $'\u03B5' $'\u03B6' $'\u03B7' $'\u03B8' $'\u03B9' $'\u03BA'
    $'\u03BB' $'\u03BC' $'\u03BD' $'\u03BE' $'\u03BF' $'\u03C0' $'\u03C1' $'\u03C3' $'\u03C4' $'\u03C5'
    $'\u03C6' $'\u03C7' $'\u03C8' $'\u03C9'
)
