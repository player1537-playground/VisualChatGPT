#!/usr/bin/env python3
"""

"""

from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass, field
import json
import sys
from io import StringIO
from typing import NewType, TextIO, Dict, List, Any
import pprint
import re

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
OPENAI_API_KEY = (Path.home() / '.openai_api_key').read_text().strip()
PRICING = 0.002 / 1000  # dollars/token


@dataclass
class Application:
    pretty: bool
    url: str
    model: str

    reader: TextIO
    writer: TextIO

    preprocess_enable: bool
    preprocess_file: TextIO

    encode_enable: bool
    encode_file: TextIO

    execute_enable: bool
    execute_file: TextIO

    execute_enable: bool
    execute_file: TextIO

    decode_enable: bool
    decode_file: TextIO

    postprocess_enable: bool
    postprocess_file: TextIO

    context: json


    #--- Utilities

    def _jsonnet(self, context: json, filename: str, source: str):
        native_callbacks = {}

        def split(document: str, new_tokens: str, old_tokens: str) -> List[str]:
            new_tokens = int(new_tokens)
            old_tokens = int(old_tokens)
            return self._split(document, new_tokens=new_tokens, old_tokens=old_tokens)
        native_callbacks['split'] = (('document', 'new_tokens', 'old_tokens'), split)

        def fetch(request: str) -> Response:
            request = json.loads(request)
            print(f'{request = !r}', file=sys.stderr)
            return self._fetch(request)
        native_callbacks['fetch'] = (('request',), fetch)

        def re_find_all(needle: str, haystack: str) -> List[str]:
            return self._re_find_all(needle, haystack)
        native_callbacks['re_find_all'] = (('needle', 'haystack'), re_find_all)

        ext_codes = {}
        for k, v in context.items():
            ext_codes[k] = json.dumps(v)

        def _add_line_numbers(source):
            lines = []
            for i, line in enumerate(source.split("\n"), 1):
                lines.append(f"{i:3d} {line}")

            return "\n".join(lines)

        try:
            output = _jsonnet.evaluate_snippet(
                filename,
                source,
                native_callbacks=native_callbacks,
                ext_codes=ext_codes,
            )
        except:
            print(_add_line_numbers(source))
            raise

        try:
            return json.loads(output)
        except json.JSONDecodeError:
            return output

    def _split(self, document, *, new_tokens, old_tokens=0):
        encoding = tiktoken.encoding_for_model(MODEL)
        encode = encoding.encode_ordinary
        decode = encoding.decode

        fragments = []

        tokens = encode(document)
        for i in range(0, len(tokens), new_tokens):
            lo = i - old_tokens
            lo = max(0, lo)
            hi = i + new_tokens + 1
            hi = min(len(tokens), hi)
            chunk = tokens[lo:hi]
            fragment = decode(chunk)
            fragments.append(fragment)

        return fragments

    def _fetch(self, request: Request) -> Response:
        with requests.post(
            url=request.get('url', self.url),
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {OPENAI_API_KEY}',
            },
            json={
                'model': request.get('model', self.model),
                'messages': [
                    {
                        'role': message['role'],
                        'content': message['content'],
                    }
                    for message in request['messages']
                ],
            },
        ) as r:
            return r.json()

    def _re_find_all(self, needle: str, haystack: str) -> List[str]:
        ret = []
        for match in re.findall(needle, haystack):
            ret.append(match)
        return ret


    #--- Functional

    def preprocess(self, context, code: Code) -> List[Text]:
        assert self.preprocess_enable
        print(f'{code = !r}')
        return self._jsonnet(context, code.name, code.read())

    def encode(self, context, code: Code) -> List[Request]:
        assert self.encode_enable
        return self._jsonnet(context, code.name, code.read())

    def execute(self, context, code: Code) -> List[Response]:
        assert self.execute_enable
        return self._jsonnet(context, code.name, code.read())

    def decode(self, context, code: Code) -> List[Text]:
        assert self.decode_enable
        return self._jsonnet(context, code.name, code.read())

    def postprocess(self, context, code: Code) -> Text:
        assert self.postprocess_enable
        return self._jsonnet(context, code.name, code.read())


    #--- Main

    def __call__(self):
        context = self.reader.read()
        
        try:
            context = json.loads(context)
        except json.JSONDecodeError:
            context = { 'input': context }

        if self.preprocess_enable:
            context |= self.preprocess(context, self.preprocess_file)
        
        if self.encode_enable:
            context |= self.encode(context, self.encode_file)

        if self.execute_enable:
            context |= self.execute(context, self.execute_file)

        if self.decode_enable:
            context |= self.decode(context, self.decode_file)

        if self.postprocess_enable:
            context |= self.postprocess(context, self.postprocess_file)

        try:
            context = context['output']
        except KeyError:
            if self.pretty:
                context = pprint.pformat(context, width=120, compact=True, sort_dicts=False)
            else:
                context = json.dumps(context)

        self.writer.write(context)


def cli():
    def fakefile(s, name='StringIO'):
        s = StringIO(s)
        s.name = name
        return s

    import argparse, sys

    parser = argparse.ArgumentParser()
    parser.add_argument('--url', dest='url', default='https://api.openai.com/v1/chat/completions')
    parser.add_argument('--model', dest='model', default='gpt-3.5-turbo')
    parser.add_argument('--input', '-i', dest='reader', type=argparse.FileType('rt'), default=sys.stdin)
    parser.add_argument('--output', '-o', dest='writer', type=argparse.FileType('wt'), default=sys.stdout)
    def add_code_argument(parser, *, flag, dest):
        if dest != 'combined':
            parser.add_argument(f'{flag}', dest=f'{dest}_enable', action='store_true')
        parser.add_argument(f'{flag}-code', dest=f'{dest}_file', type=lambda s: fakefile(s, f"<{flag}>"))
        parser.add_argument(f'{flag}-file', dest=f'{dest}_file', type=argparse.FileType('rt'))
    add_code_argument(parser, flag='--combined', dest='combined')
    add_code_argument(parser, flag='--preprocess', dest='preprocess')
    add_code_argument(parser, flag='--encode', dest='encode')
    add_code_argument(parser, flag='--execute', dest='execute')
    add_code_argument(parser, flag='--decode', dest='decode')
    add_code_argument(parser, flag='--postprocess', dest='postprocess')
    parser.add_argument('--pretty', action='store_true')
    args = vars(parser.parse_args())

    combined_file = args.pop('combined_file')
    if combined_file is not None:
        sections = ['preprocess', 'encode', 'execute', 'decode', 'postprocess']

        combined_parts = {}
        combined_parts[section := None] = []

        for line in combined_file:
            line = line.removesuffix("\n")
            if line.startswith('##'):
                section = line[len('##'):]
                section = section.strip()
                if section not in sections:
                    raise ValueError(f'Section {section!r} not recognized: {line}')
                combined_parts[section] = []
                continue

            combined_parts[section].append(line)

        for section in sections:
            if section not in combined_parts:
                continue

            if args[f'{section}_file'] is not None:
                continue

            args[f'{section}_file'] = fakefile("\n".join(sum([
                combined_parts[None],
                combined_parts[section],
            ], [])), f"<##{section}>")

    app = Application(**args, context={})
    app()


if __name__ == '__main__':
    cli()
