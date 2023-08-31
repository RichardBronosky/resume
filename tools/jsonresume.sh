#! /usr/bin/env bash
set -eu

#yaml_file=resume.yaml
yaml_file=bruno.bronosky.resume.yaml
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
    src_file="${1:-$(json_file "$yaml_file")}"
    theme="$(yq -ot '""+.meta.theme' $src_file)";
    THEME="${THEME:-$theme}"
    if [[ -n ${THEME:-} ]]; then
        resume serve --resume "$src_file" --theme "${THEME}"
    else
        resume serve --resume "$src_file"
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

render () {
    format="$1"
    src_file="${2:-$(json_file "$yaml_file")}"
    dst_file="${src_file%.*}.$format"
    which -a yq; yq -V
    resume export --resume "$src_file" $dst_file --theme $(yq -ot '""+.meta.theme' $src_file)
}

html () {
    src_file="${1:-$(json_file "$yaml_file")}"
    render html "$src_file"
}

pdf () {
    src_file="${1:-$(json_file "$yaml_file")}"
    render pdf "$src_file"
}

main () {
    yaml_to_json "$yaml_file"
    watch_yaml_to_json &
    #serve_loop
    serve
}

default_function=("help")
#"$@"
source $(PATH=.:$PATH which BOILERPLATE.sh)
