#!/bin/bash
#
# Environment variables for all the colors

# Enable colors in OSX terminal
export CLICOLOR=1

# Reset
export Color_Off='\e[0m'       # Text Reset
export Bold='\e[1m'            # Generic Bold
export Underline='\e[4m'       # Underline

# Foreground
export Black='\e[30m'        # Black
export Red='\e[31m'          # Red
export Green='\e[32m'        # Green
export Yellow='\e[33m'       # Yellow
export Blue='\e[34m'         # Blue
export Purple='\e[35m'       # Purple
export Cyan='\e[36m'         # Cyan
export White='\e[37m'        # White

# Background
export On_Black='\e[40m'       # Black
export On_Red='\e[41m'         # Red
export On_Green='\e[42m'       # Green
export On_Yellow='\e[43m'      # Yellow
export On_Blue='\e[44m'        # Blue
export On_Purple='\e[45m'      # Purple
export On_Cyan='\e[46m'        # Cyan
export On_White='\e[47m'       # White

# High Intensity Foreground
export IBlack='\e[90m'       # Black
export IRed='\e[91m'         # Red
export IGreen='\e[92m'       # Green
export IYellow='\e[93m'      # Yellow
export IBlue='\e[94m'        # Blue
export IPurple='\e[95m'      # Purple
export ICyan='\e[96m'        # Cyan
export IWhite='\e[97m'       # White

# High Intensity Background
export On_IBlack='\e[100m'   # Black
export On_IRed='\e[101m'     # Red
export On_IGreen='\e[102m'   # Green
export On_IYellow='\e[103m'  # Yellow
export On_IBlue='\e[104m'    # Blue
export On_IPurple='\e[105m'  # Purple
export On_ICyan='\e[106m'    # Cyan
export On_IWhite='\e[107m'   # White

all_colors() {
	for x in 0 1 2 4 7 8; do
		for i in `seq 30 37`; do
			for a in `seq 40 47`; do
				echo -ne "\e[$x;$i;$a""m\\\e[$x;$i;$a""m\e[0;39;49m ";
			done;
			echo;
		done;
		echo ;
	done;
}
