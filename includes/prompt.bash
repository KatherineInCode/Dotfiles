git_sha() {
    git rev-parse --short HEAD 2>/dev/null
}

GIT_PS1_SHOWDIRTYSTATE=1
# GIT_PS1_SHOWCOLORHINTS=1
GIT_PS1_SHOWUNTRACKEDFILES=1
GIT_PS1_SHOWSTASHSTATE=1
GIT_PS1_SHOWUPSTREAM="verbose"

if [ -n "$SSH_CLIENT" ] || [ -n "$SSH_TTY" ]; then
    hostPart="${Underline}${IPurple}\h${Color_Off}"
else
    hostPart="${IPurple}\h${Color_Off}"
fi

export PS1="${IBlack}\A${Color_Off} ${IBlue}\u${Color_Off} @ ${hostPart} :${IRed}\$(__git_ps1 \" \$(git_sha) %s ${Color_Off}:\") ${IYellow}\w${Color_Off}\n> "

unset hostPart
