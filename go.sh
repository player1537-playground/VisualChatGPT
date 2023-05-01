#!/usr/bin/env bash

die() { printf $'Error: %s\n' "$*" >&2; exit 1; }
root=$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)
project=${root##*/}


#---

llmerick() {
    exec python3 "${root:?}/llmerick.py" \
        "$@" \
        ##
}

go-Summarize() {
    for arg in "${@:2}"; do
        preprocess=${root:?}/summarize/preprocess.jsonnet \
        encode=${root:?}/summarize/encode.jsonnet \
        decode=${root:?}/summarize/decode.jsonnet \
        postprocess=${root:?}/summarize/postprocess.jsonnet \
        suffix=${1:?} \
        input=${root:?}/summarize/input${suffix:?}.txt \
        inputs=${root:?}/summarize/inputs${suffix:?}.json \
        requests=${root:?}/summarize/requests${suffix:?}.json \
        responses=${root:?}/summarize/responses${suffix:?}.json \
        outputs=${root:?}/summarize/outputs${suffix:?}.json \
        output=${root:?}/summarize/output${suffix:?}.txt \
        "${FUNCNAME[0]:?}-${arg:?}" \
        || die "Failed to run step: ${arg:?}"
    done
}

go-Summarize-Preprocess() {
    <"${input:?}" \
    llmerick \
        --preprocess-file "${preprocess:?}" \
    | tee "${inputs:?}"
}

go-Summarize-Encode() {
    <"${inputs:?}" \
    llmerick \
        --encode-file "${encode:?}" \
    | tee "${requests:?}"
}

go-Summarize-Execute() {
    <"${requests:?}" \
    llmerick \
        --execute \
    | tee "${responses:?}"
}

go-Summarize-Decode() {
    <"${responses:?}" \
    llmerick \
        --decode-file "${decode:?}" \
    | tee "${outputs:?}"
}

go-Summarize-Postprocess() {
    <"${outputs:?}" \
    llmerick \
        --postprocess-file "${postprocess:?}" \
    | tee "${output:?}"
}


#---

test -f "${root:?}/env.sh" && source "${_:?}"
go-"$@"
