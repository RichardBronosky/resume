#! /usr/bin/env bash

_env_meta(){
    # Perform env setup here

    # ctrl chars for terminal colorizing
    all_off="$(tput sgr0)"
    bold="${all_off}$(tput bold)"
    blue="${bold}$(tput setaf 4)"
    yellow="${bold}$(tput setaf 3)"

    DEBUG_TRAP="${DEBUG_TRAP:-0}"
    DEBUG_XTRACE="${DEBUG_XTRACE:-0}"
    DEBUG_SETUP="${DEBUG_SETUP:-}"
    [[ ${DEBUG_TRAP}   -gt 0 ]] && _trap_set   ||:
    [[ ${DEBUG_XTRACE} -gt 0 ]] && _xtrace_set ||:
    [[ -n ${DEBUG_SETUP}     ]] && "${DEBUG_SETUP[@]}" ||:
    SCRIPT_PATH="$(_path_to_this_script)"
    SCRIPT_DIR="$(dirname ${SCRIPT_PATH})"
    SCRIPT_NAME="$(basename ${SCRIPT_PATH})"
    FORCE_SOURCE='' \
        _is_sourced || default_function=("_source_boilerplate")
    _is_function _env && _env ||true
}

tput(){
    command tput "$@" 2>/dev/null ||:
}

# Use an array so that arguments can be included ("ls" "-l")
#default_function=("help")
unset default_function_takes_file

#### BEGIN BOILER''PLATE

_has_main_function(){
    declare -F | grep -qE '\<main$';
}

if [[ -z ${default_function:-} ]]; then
    if _has_main_function; then
        default_function=("main")
    else
        default_function=("help")
    fi
fi

_source_boilerplate(){
  echo 'source $''(PATH=.:$''PATH which BOILER''PLATE.sh)'
}

_usage(){
    pad='s/^/       /'
    /usr/bin/less -EXS<<USAGE
$SCRIPT_NAME

Usage:
       $SCRIPT_NAME [-h | help] SUBCOMMAND [ ARGUMENT [ | ARGUMENT ] ... ]
$(if [[ -n "${default_function:-}" ]]; then
if [[ -z "${default_function_takes_file:-}" ]]; then
    cat <<NON_FILE_ARG
       $SCRIPT_NAME [$default_function] ARGUMENT
NON_FILE_ARG
else
    cat <<FILE_ARG
       $SCRIPT_NAME [$default_function] FILE
       $SCRIPT_NAME [$default_function] < FILE
FILE_ARG
fi
fi)

Subcommands:
$(
_funcs | sed "$pad"
)

Note:
       The help  subcommand accepts a subcommand  as a argument and  will show
       the the source  code for the subcommand to help  you understand what it
       does and how it may be useful.

Example:
$(
{
echo "$ $0 help help"
help help
} | sed "$pad"
)

USAGE
}

_section(){
    echo -e "\n""## $* ##"
}

_tee_stderr(){
    tee >(cat >&2)
}

_is_function(){
    [[ "$(type -t "$1" 2>/dev/null)" == *function* ]]
}

_funcs(){
    [[ ${1:-} == "--all" ]] && prefix="" || prefix="[^_]"
    declare -F | awk '$2=="-f" && $3~/^'"$prefix"'/{print $3}'
}

_path_to_this_script(){
    local dir; dir="$(cd "$(dirname "$(realpath "${BASH_SOURCE[${#BASH_SOURCE[@]}-1]}")")" && pwd -P)"
    if [[ ${1:-} == "cd" ]]; then
        echo cd "$dir"
        cd "$dir"
    else
        echo "$dir/$(basename "${BASH_SOURCE[${#BASH_SOURCE[@]}-1]}")"
    fi
}

_fd(){(
    check_what="$1"
    check_for="$2"
    case $check_what in
        stdin  | in  | 0 )
            case $check_for in
                tty )
                    [[ -t 0 ]]
                ;;
                pipe )
                    [[ -p /dev/stdin ]]
                ;;
                redirect | pipelike )
                    _fd 0 pipe || ! _fd 0 tty
                ;;
                * )
                    echo "Checking '$check_what' fd for '$check_for' is not implemented"
                    return 255
                ;;
            esac
        ;;
        stdout | out | 1 )
            case $check_for in
                tty )
                    [[ -t 1 ]]
                ;;
                pipe )
                    echo -e \
"Checking  'stdout'  fd for  'pipe'  is  not  implemented because  bash  cannot""\n" \
"distinguish  between piping  to another  command and  redirecting output  to a""\n" \
"file. Consider checking for 'pipelike'""\n"
                    return 255
                ;;
                redirect | pipelike )
                    ! _fd 1 tty
                ;;
                * )
                    echo "Checking '$check_what' fd for '$check_for' is not implemented"
                    return 255
                ;;
            esac
        ;;
        * )
            echo "Checking '$check_what' fd is not implemented"
            return 255
        ;;
    esac
)}

_main(){
    _env_meta
    (
        cmd=("help")
        if [[ -n "${default_function:-}" ]]; then
            if [[ -z "${default_function_takes_file:-}" && -n "${1:-}" ]] && ! _is_function "$1"; then
                cmd=("${default_function[@]}")
            else
                if [[ -f "${1:-}" ]]; then
                    cmd=("${default_function[@]}" "$@")
                elif _fd stdin pipelike; then
                    ## TODO: Fix this!!!
                    #cmd=("${default_function[@]}" "/dev/stdin")
                    :
                else
                    cmd=("${default_function[@]}")
                fi
            fi
        fi
        if [[ "${cmd[0]}" == "help" && -n "${1:-}" ]]; then
            # Use and array so that arguments can be included ("ls" "-l")
            cmd=("$1")
            # Map alternate subcommands
            [[ $cmd == -h ]]     && cmd="help"
            [[ $cmd == -help ]]  && cmd="help"
            [[ $cmd == --help ]] && cmd="help"
            # Do not shift the arguments until last
            shift
        fi
        "${cmd[@]}" "$@"
    )
}

_is_sourced(){
    local stack_depth=${1:-0}
    [[ -z ${FORCE_SOURCE:-} ]] || return
    [[ "X${BASH_SOURCE:-}X"      != "XX" ]] && [[ "${BASH_SOURCE[$stack_depth]}" != "$0"          ]] && return
    [[ "X${ZSH_EVAL_CONTEXT:-}X" != "XX" ]] && [[ $ZSH_EVAL_CONTEXT   == *file:shfunc* ]] && return
    return
}

_vars(){
    set \
        | awk '
            /^[a-zA-Z_]+ \(\)/{exit}
            /^(ALAC|CSF_|DBUS|DEBUGINFOD_URLS|DOCKER_HOST|DRAW|GPG|GTK|HOST|INVO|KUBE|M[AMO])/{next}
            /^(OLD|_?P9|PY|SS|TERM|TMUX|WIN|XAUTH|XDG)/{next}
            {print}'
}

_trap_fn(){
    [[ ${DEBUG_TRAP_SKIP:-} ]] && unset DEBUG_TRAP_SKIP && return 0
    if [[ ${DEBUG_TRAP:-0} -gt 0 && $BASH_COMMAND != "unset DEBUG_TRAP" && "${FUNCNAME[1]}" != *_is_function* ]]; then
        printf "${yellow:-}[%s:%5s %-${length_longest_func}s${all_off:-} %s\n" \
            "${BASH_SOURCE[1]}" \
            "${BASH_LINENO[0]}" \
            "${FUNCNAME[1]}()]" \
            "${BASH_COMMAND}" >&2
            #"$({ sed -n l | sed 's,\\,\\\\\\\\,g' }<<<"XX${BASH_COMMAND}XX")" >&2
    fi
    if _is_function ${BASH_COMMAND%% *}; then DEBUG_TRAP_SKIP=1; fi
    return 0 # do not block execution in extdebug mode
}

_trap_set(){
    length_longest_func="$(_funcs --all | sed 's/././g' | sort | tail -n1 | wc -c)"
    set -o functrace
    trap _trap_fn DEBUG
}

_xtrace_set(){
    length_longest_func="$(_funcs --all | sed 's/././g' | sort | tail -n1 | wc -c)"
    PS4='$(_ps4)'
    set -x
}

_ps4(){
    printf "${yellow:-}[%s:%5s %-${length_longest_func}s ${all_off:-}" \
        "${BASH_SOURCE[1]}" \
        "${BASH_LINENO[0]}" \
        "${FUNCNAME[1]}()]"
}

_entrypoint(){
    if _is_sourced -1; then
        _env_meta
    else
        _main "$@"
    fi
}

# Explicitly use the (implied) function keyword to prevent conflict with common aliases
function help(){
    local funcs="$@"
    if [[ -z "${funcs[@]}" ]]; then
        for func in usage _usage _funcs; do _is_function $func && { $func; return; }; done
    else
        for func in "${funcs[@]}"; do
            declare -f "$func"
        done
    fi
}

# Avoid having your interactive shell close if you source this script and get an
# error caught by set -eu (set -o errexit; set -o nounset)
(
    # EVERY SHELL SCRIPT SHOULD HAVE: set -eu
    # Use ||true after commands that should be fault tolerant
    # e: Exit immediately if a command exits with a non-zero status
    # u: Unset variables treated as an error when substituting
    set -eu
   _entrypoint "$@"
)
#### END BOILER''PLATE
