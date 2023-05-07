#!/usr/bin/env python3
"""

"""

from __future__ import annotations
from pathlib import Path
import json

import tiktoken


#--- Config

MODEL = 'gpt-3.5-turbo'
PRICING = 0.002 / 1000  # dollars/token


def print_requests_cost(context):
    encoding = tiktoken.encoding_for_model(MODEL)
    encode = encoding.encode

    total_tokens = 0
    for i, request in enumerate(context['requests'], 1):
        request_tokens = 0
        for message in request['messages']:
            message_tokens = len(encode(message['content']))

            request_tokens += message_tokens
        
        # print(f'  Request {i}: {request_tokens} (${PRICING*request_tokens:0.03f})')

        total_tokens += request_tokens

    print(f'Total Requests Cost: # = {i}, {total_tokens} tokens (${PRICING*total_tokens:0.03f})')


def print_responses_cost(context):
    encoding = tiktoken.encoding_for_model(MODEL)
    encode = encoding.encode

    total_tokens = 0
    for i, response in enumerate(context['responses'], 1):
        response_tokens = response['usage']['total_tokens']

        total_tokens += response_tokens

    print(f'Total Responses Cost: # = {i}, {total_tokens} tokens (${PRICING*total_tokens:0.03f})')


def main(reader, writer):
    context = json.load(reader)

    print_requests_cost(context)
    print_responses_cost(context)


def cli():
    import argparse, sys

    parser = argparse.ArgumentParser()
    parser.add_argument('--input', '-i', dest='reader', type=argparse.FileType('rt'), default=sys.stdin)
    parser.add_argument('--output', '-o', dest='writer', type=argparse.FileType('wt'), default=sys.stdout)
    args = vars(parser.parse_args())

    main(**args)


if __name__ == '__main__':
    cli()
