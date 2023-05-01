#!/usr/bin/env python3
"""

"""

from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass
import json
import sys
from io import StringIO
from typing import NewType, TextIO, Dict, List, Any
import pprint

import requests
import tiktoken
import _jsonnet


#--- Types

Text = NewType('Text', str)
Code = NewType('Code', TextIO)
Request = NewType('Request', Dict[str, Any])
Response = NewType('Response', Dict[str, Any])


#--- Config

ROOT = Path(__file__).resolve().parent
URL = 'https://api.openai.com/v1/chat/completions'
MODEL = 'gpt-3.5-turbo'
OPENAI_API_KEY = (Path.home() / '.openai_api_key').read_text().strip()
PRICING = 0.002 / 1000  # dollars/token


#--- Utils

@dataclass
class Split:
    new_tokens: int
    old_tokens: int

    def __call__(self, document: str) -> List[str]:
        encoding = tiktoken.encoding_for_model(MODEL)
        encode = encoding.encode_ordinary
        decode = encoding.decode

        fragments = []

        tokens = encode(document)
        i = 0
        while i < len(tokens):
            chunk = tokens[i:i+self.new_tokens+self.old_tokens+1]
            fragment = decode(chunk)
            fragments.append(fragment)
            
            i += self.new_tokens

        return fragments


def jsonnet(context: json, filename: str, source: str):
    native_callbacks = {}
    native_callbacks['split'] = (
        ('document', 'new_tokens', 'old_tokens'),
        lambda document, new_tokens, old_tokens: Split(int(new_tokens, 10), int(old_tokens, 10))(document),
    )

    ext_codes = {}
    for k, v in context.items():
        ext_codes[k] = json.dumps(v)

    output = _jsonnet.evaluate_snippet(
        filename,
        source,
        native_callbacks=native_callbacks,
        ext_codes=ext_codes,
    )

    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return output


#--- Functional Layer

def do_preprocess(context, code: Code) -> List[Text]:
    return jsonnet(context, code.name, code.read())


def do_encode(context, code: Code) -> List[Request]:
    return jsonnet(context, code.name, code.read())


def do_execute(context) -> List[Response]:
    context.setdefault('responses', [])
    for i, request in enumerate(context['requests']):
        print(f'Execute: Request {i}/{len(context["requests"])}', file=sys.stderr)
        with requests.post(
            url=URL,
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {OPENAI_API_KEY}',
            },
            json={
                'model': MODEL,
                'messages': [
                    {
                        'role': message['role'],
                        'content': message['content'],
                    }
                    for message in request['messages']
                ],
            },
        ) as r:
            response = r.json()

        context['responses'].append(response)

    return context


def do_decode(context, code: Code) -> List[Text]:
    return jsonnet(context, code.name, code.read())


def do_postprocess(context, code: Code) -> Text:
    return jsonnet(context, code.name, code.read())


def main(reader, writer, preprocess, encode, execute, decode, postprocess, pretty):
    context = reader.read()
    
    try:
        context = json.loads(context)
    except json.JSONDecodeError:
        context = { 'input': context }

    if preprocess:
        context |= do_preprocess(context, preprocess)
    
    if encode:
        context |= do_encode(context, encode)

    if execute:
        context |= do_execute(context)

    if decode:
        context |= do_decode(context, decode)

    if postprocess:
        context |= do_postprocess(context, postprocess)

    try:
        context = context['output']
    except KeyError:
        if pretty:
            context = pprint.pformat(context, width=120, compact=True, sort_dicts=False)
        else:
            context = json.dumps(context)

    writer.write(context)


def cli():
    import argparse, sys

    parser = argparse.ArgumentParser()
    parser.add_argument('--input', '-i', dest='reader', type=argparse.FileType('rt'), default=sys.stdin)
    parser.add_argument('--output', '-o', dest='writer', type=argparse.FileType('wt'), default=sys.stdout)
    def add_code_argument(parser, dest):
        parser.add_argument(f'--{dest}-code', dest=dest, type=StringIO)
        parser.add_argument(f'--{dest}-file', dest=dest, type=argparse.FileType('rt'))
    add_code_argument(parser, dest='preprocess')
    add_code_argument(parser, dest='encode')
    parser.add_argument('--execute', action='store_true')
    add_code_argument(parser, dest='decode')
    add_code_argument(parser, dest='postprocess')
    parser.add_argument('--pretty', action='store_true')
    args = vars(parser.parse_args())

    main(**args)


if __name__ == '__main__':
    cli()
