#! /usr/bin/env bash
set -eu

#yaml_file=resume.yaml
yaml_file=src/bruno.bronosky.resume.yaml
#cmd_args=("${@}")
#declare -p cmd_args
#script_name="${cmd_args[0]}"
script_name="${0}"

json_filename () {
    local yaml_file="${1}"
    local type="${2:-json}"
    echo "build/$(basename "${yaml_file}" .yaml).${type}"
}

json_file="$(json_filename "${yaml_file}")"

yaml_to_json () {
    local filename="${1:-$yaml_file}"
    local out="$(json_filename "${filename}")"
    local mid="${out}.mid"
    yq -ojson 'select(.basics)' "${filename}">"${mid}"
    mv "${mid}" "${out}"
}

watch_yaml_to_json () {
    inotifywait --monitor --include "${yaml_file}" -e CLOSE_WRITE "${PWD}" | \
        while read -r dir action watched_file; do
            echo "$(date) inotify event -- dir: ${dir}; watched_file: ${watched_file}; action: ${action}"
            yaml_to_json "${watched_file}"
            if [[ -n "${server_pid:-}" ]] \
            && [[ -f "/proc/$server_pid/cmdline" ]] \
            && grep -q 'resume serve' "/proc/$server_pid/cmdline"; \
            then
                kill "$server_pid"
            fi
        done
}

serve () {
    src_file="${1:-$json_file}"
    theme="$(yq -ot '""+.meta.theme' "$src_file")";
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
    src_file="${2:-$json_file}"
    dst_file="${src_file%.*}.$format"
    which -a yq; yq -V
    resume export --resume "$src_file" $dst_file --theme $(yq -ot '""+.meta.theme' $src_file)
}

html () {
    src_file="${1:-$json_file}"
    render html "$src_file"
}

pdf () {
    src_file="${1:-$json_file}"
    render pdf "$src_file"
}

build () {
    yaml_to_json
    html
    pdf
}

main () {
    yaml_to_json
    watch_yaml_to_json &
    #serve_loop
    serve
}

default_function=("help")
#"$@"
source $(PATH=.:$PATH which BOILERPLATE.sh)
