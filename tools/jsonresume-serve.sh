#! /usr/bin/env bash

set -eu
set -x

yaml_file=resume.yaml
#cmd_args=("${@}")
#declare -p cmd_args
#script_name="${cmd_args[0]}"
script_name="${0}"

json_file () {
    local yaml_file="${1}"
    echo "$(basename "${yaml_file}" .yaml).json"
}

yaml_to_json () {
    local filename="${1}"
    local out="$(json_file "${filename}")"
    local mid="${out}.mid"
    yq -ojson "${filename}">"${mid}"
    cp "${mid}" "${out}"
}

watch_yaml_to_json () {
    inotifywait --monitor --include "${yaml_file}" -e CLOSE_WRITE "${PWD}" | \
        while read -r dir action filename; do
            echo "$(date) -- dir: ${dir}; filename: ${filename}; action: ${action}"
            yaml_to_json "${filename}"
            if [[ -n ${server_pid:-} ]] && [[ -f /proc/$server_pid/cmdline ]] && grep -q 'resume serve' /proc/$server_pid/cmdline; then
                kill $server_pid
            fi
        done
}

serve () {
    theme="$(jq --raw-output '""+.meta.theme' resume.json)";
    THEME="${THEME:-$theme}"
    if [[ -n ${THEME:-} ]]; then
        resume serve --theme "${THEME}"
    else
        resume serve
    fi
}

serve_loop () {
    while true; do
        $script_name serve &
        server_pid=$!
        fg
        read -rp 'another loop?'
    done
}

cycle () {
        (
                ${BASH_SOURCE[0]} serve | tee out1.txt
                grep ono < out1.txt | tee ono2.js
        ) &
        firefox 'http://localhost:4000'
        sleep 10
        ps w | awk '/[n]ode .*resume / {print $1}' | xargs kill
        cat ono2.js
}


main () {
    yaml_to_json "$yaml_file"
    watch_yaml_to_json &
    #serve_loop
    serve
}

"$@"
