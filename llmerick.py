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

    code: Code


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

    #--- Main

    def __call__(self):
        context = self.reader.read()
        
        try:
            context = json.loads(context)
        except json.JSONDecodeError:
            context = { 'input': context }

        context = self._jsonnet(context, self.code.name, self.code.read())

        try:
            context = context['output']
        except (KeyError, TypeError):
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
        parser.add_argument(f'{flag}', dest=f'{dest}', type=argparse.FileType('rt'))
        parser.add_argument(f'{flag}-str', dest=f'{dest}', type=lambda s: fakefile(s, f"<{flag}>"))
    add_code_argument(parser, flag='--code', dest='code')
    parser.add_argument('--pretty', action='store_true')
    args = vars(parser.parse_args())

    app = Application(**args)
    app()


if __name__ == '__main__':
    cli()
