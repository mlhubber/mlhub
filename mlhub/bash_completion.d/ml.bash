# References
# ----------
# [1] https://github.com/syncany/syncany/blob/master/gradle/bash/syncany.bash-completion

# Gets the first non-option word of the command line, except the program name.
_mlhub_get_firstword() {
    local firstword i

    firstword=
    for ((i = 1; i < ${#COMP_WORDS[@]}; ++i)); do
	if [[ ${COMP_WORDS[i]} != -* ]]; then
	    firstword=${COMP_WORDS[i]}
	    break
	fi
    done

    echo $firstword
}

# Gets the last non-option word of the command line.
_mlhub_get_lastword() {
	local lastword i

	lastword=
	for ((i = 1; i < ${#COMP_WORDS[@]}; ++i)); do
	    if [[ ${COMP_WORDS[i]} != -* ]] &&
	       [[ -n ${COMP_WORDS[i]} ]] &&
               [[ ${COMP_WORDS[i]} != $cur ]]; then
	        lastword=${COMP_WORDS[i]}
	    fi
	done

	echo $lastword
}

_mlhub() {
    local cur prev firstword lastword
    local complete_words    # possible completion list for current word
    local complete_options  # possible completion list for current option

    local global_commands   # list of available global commands
    local global_options    # list of available global options 

    local available_options
    local clean_options
    local installed_options
    local commands_options
    local configure_options
    local install_options
    local readme_options
    local remove_options

    cur=${COMP_WORDS[COMP_CWORD]}      # current parameter
    prev=${COMP_WORDS[COMP_CWORD-1]}   # previous parameter
    firstword=$(_mlhub_get_firstword)  # first non-option parameter
    lastword=$(_mlhub_get_lastword)    # last non-option parameter

    # available global commands
    global_commands="\
    	available\
	clean\
        installed\
	commands\
	configure\
	install\
	readme\
	remove\
        "

    # available global options
    global_options="\
	--debug\
   	-h --help\
	--quiet\
	--init-dir\
	--mlhub\
	--cmd\
      	"

    available_options="\
	-h --help\
        --name-only\
	"

    clean_options="\
	-h --help\
	"

    installed_options="\
	-h --help\
        --name-only\
	"

    commands_options="\
	-h --help\
	"

    configure_options="\
	-h --help\
	"

    install_options="\
	-h --help\
	"

    readme_options="\
	-h --help\
	"

    remove_options="\
	-h --help\
	"

    # Determines possible completions for the command (${firstword})
    case "${firstword}" in
	# Commands do not reqire a model name
	available)
	    complete_options="${available_options}"
            ;;
	clean)
	    complete_options="${clean_options}"
	    ;;
	installed)
	    complete_options="${installed_options}"
	    ;;

	# Commands requires a model name
	commands)
	    complete_options="${commands_options}"

	    local installed_model=$(ml installed --name-only)

	    # Only one model name is allowed
	    local typed=0
	    for model in ${installed_model}; do
		if [[ "$model" == "$lastword" ]]; then
		    typed=1
		fi
	    done

	    if [[ $typed == 0 ]]; then
		complete_words=("${installed_model}")
	    fi
	    ;;
	configure)
	    complete_options="${configure_options}"
	    local installed_model=$(ml installed --name-only)
	    complete_words=("${installed_model}")
	    ;;
	install)
	    complete_options="${install_options}"
	    local available_model=$(ml available --name-only)
	    complete_words=("${available_model}")
	    ;;
	readme)
	    complete_options="${readme_options}"
	    local installed_model=$(ml installed --name-only)
	    complete_words=("${installed_model}")
	    ;;
	remove)
	    complete_options="${remove_options}"
	    local installed_model=$(ml installed --name-only)
	    complete_words=("${installed_model}")
	    ;;
	*)
	    complete_words="${global_commands}"
	    complete_options="${global_options}"
	    ;;
    esac

    # Either display words or options, depending on the user input
    if [[ $cur == -* ]]; then
	COMPREPLY=($(compgen -W "$complete_options" -- $cur))
    else
	COMPREPLY=($(compgen -W "$complete_words" -- $cur))
    fi
}

# Hook completion function to ml
complete -F _mlhub ml
