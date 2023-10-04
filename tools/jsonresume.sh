#! /usr/bin/env bash
set -eu

#  temporary solution until my changes are accepted upstream
export PATH=~/src/resume-cli/build:$PATH

#yaml_file=resume.yaml
yaml_file=src/bruno.bronosky.resume.yaml
#cmd_args=("${@}")
#declare -p cmd_args
#script_name="${cmd_args[0]}"
script_name="${0}"

json_filename () {
    local src_file="${1:-$yaml_file}"
    local type="${2:-json}"
    echo "build/$(basename "${src_file}" .yaml).${type}"
}

json_file="$(json_filename "${yaml_file}")"

_y () {
    local format="${1}"
    local query="${2:-.}"
    local filename="${3:-$yaml_file}"
    yq --output-format="$format" "$query" "$filename"
}

_yy () { _y yaml "$@"; }

_yj () { _y json "$@"; }

_yt () { _y t "$@"; }

main_document () {
    _yy 'select(.basics)' "$@"
}

json_from_yaml () {
    main_document "$@" | _yj . -
}

yaml_file_to_json_file () {
    local out="$(json_filename "$@")"
    local mid="${out}.mid"
    json_from_yaml > "${mid}"
    mv "${mid}" "${out}"
}

get_package_repo_url () {
    #package_json='node_modules/resume-cli/package.json'
    package_json="$1"
    _yt '.repository.url' "$package_json"
}

resolve_module () {
    local module="$1"
    node --eval "console.log(require.resolve('$module'))"
}

resolve_package_json () {
    local module="$1"
    node --eval "console.log(require.resolve('$module/package.json'))"
}

get_theme () {
    src_file="${1:-$yaml_file}"
    _yt '""+.meta.theme' "$src_file"
}

clone_theme () {
    local json="$(resolve_package_json "jsonresume-theme-$(get_theme)")"
    local url="$(get_package_repo_url "$json")"
    git clone $url
}

watch_do () {
    local watch="$1"
    shift
    local cmd=("$@")
    inotifywait --monitor --include "$watch" --event CLOSE_WRITE --recursive "${PWD}" | \
        while read -r dir action watched_file; do
            xarg_pipe="${dir%%/}/$watched_file"
            _yy -P <(echo "[{'inotify event': {'date':'$(date)', 'pwd':'$PWD', 'dir':'$dir', 'watched_file':'$watched_file', 'action':'$action', 'xarg_{}':'$xarg_pipe'}}]")
            echo "${cmd[*]}"$'\n'
            xargs -I '{}' bash -c "${cmd[*]}" <<<"$xarg_pipe"
        done
}

watch_yaml_to_json () {
    inotifywait --monitor --include "${yaml_file}" -e CLOSE_WRITE "${PWD}" | \
        while read -r dir action watched_file; do
            echo "$(date) inotify event -- dir: ${dir}; watched_file: ${watched_file}; action: ${action}"
            yaml_file_to_json_file "${watched_file}"
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
    theme="$(get_theme "$src_file")";
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
    src_file="${2:-}"
    if [[ -n "${src_file:-}" ]]; then
        dst_file="${3:-$src_file}"
    else
        dst_file="${json_file}"
        src_file=/tmp/resume.json
        json_from_yaml $yaml_file > "$src_file"
    fi
    dst_file="${dst_file%.*}.$format"
    resume export --resume "$src_file" "$dst_file" --theme $(get_theme "$src_file")
    if [[ $format == "pdf" ]] && which qpdf > /dev/null; then
        pdf_meta build/bruno.bronosky.resume.pdf src/pdf_properties.json
    fi
}

pdf_meta () {
    src_file="${1}"
    meta_file="${2}"
    dst_file="${3:-${src_file%.*}.pdf}"
    mid_file="${dst_file%.*}.ascii.pdf"
    qpdf --qdf --object-streams=disable "$src_file" "$mid_file"
    qpdf --update-from-json="$meta_file" "$mid_file"  "$dst_file"
}

html_preload () {
    RENDER_TEMPLATE='/preloading.template' ./tools/jsonresume.sh html build/bruno.bronosky.resume.json build/preloading.html
}

html () {
    src_file="${1:-}"
    dst_file="${2:-${json_file%.*}.html}"
    render html "$src_file" "$dst_file"
}

pdf () {
    src_file="${1:-}"
    dst_file="${2:-${json_file%.*}.pdf}"
    render pdf "$src_file" "$dst_file"
}

build () {
    yaml_file_to_json_file
    html
    pdf
}

main () {
    yaml_file_to_json_file
    watch_yaml_to_json &
    #serve_loop
    serve
}

default_function=("help")
#"$@"
source $(PATH=.:$PATH which BOILERPLATE.sh)
