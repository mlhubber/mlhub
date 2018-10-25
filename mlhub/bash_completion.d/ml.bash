# References
# ----------
# [1] https://github.com/syncany/syncany/blob/master/gradle/bash/syncany.bash-completion

# Gets the first non-option word of the command line, except the program name.
# If none, the index would be the last word, and the first word would be empty.
_mlhub_get_firstword() {
    local firstword i

    for ((i = 1; i < ${#COMP_WORDS[@]}; ++i)); do
	if [[ ${COMP_WORDS[i]} != -* ]] &&
	       [[ -n ${COMP_WORDS[i]} ]]; then
	    firstword=${COMP_WORDS[i]}
	    break
	fi
    done

    echo $i $firstword
}

# Gets the last non-option word of the command line,
# except the program name and current word.
# If none, the index would be zero, and the last word would be empty.
_mlhub_get_lastword() {
    local lastword i

    for ((i = ${#COMP_WORDS[@]}; i > 0; i=i-1)); do
	if [[ ${COMP_WORDS[i]} != -* ]] &&
               [[ -n ${COMP_WORDS[i]} ]] &&
	       [[ ${COMP_WORDS[i]} != ${cur} ]]; then
	    lastword=${COMP_WORDS[i]}
	    break
	fi
    done

    echo $i $lastword
}

# Searches for available commands for all installed models.
_mlhub_model_commands() {
    local model_commands
    local installed_models=$(ml installed --name-only)
    for model in ${installed_models}; do
	for cmd in $(ml commands --name-only ${model}); do
	    model_commands+="${cmd} "
	done
    done

    echo $model_commands
}

# Return the completion words cached in $1
_mlhub_cached_completion_words() {
    local words=$(python -c "\
import mlhub;\
mlhub.utils.get_completion_list(mlhub.constants.$1)\
    ")

    echo ${words}
}

_mlhub() {
    local cur prev firstword i_firstword lastword i_lastword
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

    read i_firstword firstword < <(_mlhub_get_firstword) # first non-option parameter
    read i_lastword lastword < <(_mlhub_get_lastword)    # last non-option parameter

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
        --version\
        -v
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
        --name-only\
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

	    local installed_models=$(ml installed --name-only)

	    # Only one model name is allowed
	    local typed=0
	    for model in ${installed_models}; do
		if [[ "$model" == "$lastword" ]]; then
		    typed=1
		fi
	    done

	    if [[ $typed == 0 ]]; then
		complete_words=("${installed_models}")
	    fi
	    ;;
	configure)
	    complete_options="${configure_options}"
	    local installed_models=$(ml installed --name-only)
	    complete_words=("${installed_models}")
	    ;;
	install)
	    complete_options="${install_options}"
	    complete_words=("$(_mlhub_cached_completion_words COMPLETION_MODELS)")
	    ;;
	readme)
	    complete_options="${readme_options}"
	    local installed_models=$(ml installed --name-only)
	    complete_words=("${installed_models}")
	    ;;
	remove)
	    complete_options="${remove_options}"
	    local installed_models=$(ml installed --name-only)
	    complete_words=("${installed_models}")
	    ;;
	*)
	    if [[ ${COMP_CWORD} -le ${i_firstword} ]]; then

		# For completion cases:
		#   ml [TAB] firstword lastword
		#   ml [TAB] firstword
		#   ml first[TAB]word
		#   ml [TAB]

		complete_words="${global_commands}"
		complete_words+=" $(_mlhub_cached_completion_words COMPLETION_COMMANDS)"
		complete_words+=" $(_mlhub_cached_completion_words COMPLETION_MODELS)"
		complete_options="${global_options}"
	    elif [[ ${i_lastword} -ge ${COMP_CWORD} ]] ||
		     [[ ${i_firstword} -eq ${i_lastword} ]]; then

		# For completion cases:
		#   ml firstword [TAB] lastword
		#   ml firstword [TAB]
		#   ml first[TAB]word

		local installed_models=$(ml installed --name-only)
		complete_words=("${installed_models}")
	    fi
            ;;
    esac

    # Either display words or options, depending on the user input
    if [[ $cur == -* ]]; then
	COMPREPLY=($(compgen -W "$complete_options" -- $cur))
    else
	COMPREPLY=($(compgen -W "$complete_words" -- $cur))
    fi
}

# Hook completion function to ml.
# 
# -o bashdefault -o default is used for `ml score dogs-cats [TAB]` to
# complete directory names or file names.
complete -F _mlhub -o bashdefault -o default ml
