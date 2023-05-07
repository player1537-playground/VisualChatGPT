#!/usr/bin/env python3
"""

"""

from __future__ import annotations
from tkinter import *
from tkinter.scrolledtext import *
from tkinter.filedialog import *
from tkinter.ttk import *
from pathlib import Path
from dataclasses import dataclass
import json
import sys

from PIL import Image
from PIL.ImageTk import PhotoImage
import requests
import tiktoken
import _jsonnet


DEFAULT_URL = 'https://api.openai.com/v1/chat/completions'
DEFAULT_MODEL = 'gpt-3.5-turbo'
OPENAI_API_KEY = (Path.home() / '.openai_api_key').read_text().strip()
PRICING = 0.002 / 1000  # dollars/token


def run(func):
    return func()


def _configure_text_defaults(text: Text):
    def callback(event):
        text.tag_add(SEL, '1.0', END)
        text.mark_set(INSERT, '1.0')
        text.see(INSERT)
        return 'break'
    text.bind('<Control-KeyRelease-a>', callback)
    def callback(event):
        text.insert(INSERT, "  ")
        return 'break'
    text.bind('<Tab>', callback)


class TextRedirector(object):
    def __init__(self, fileobj, widget, tag="stdout"):
        self.fileobj = fileobj
        self.widget = widget
        self.tag = tag

    def write(self, str):
        self.widget.configure(state="normal")
        self.widget.insert("end", str, (self.tag,))
        self.widget.see('end')
        self.widget.configure(state="disabled")
        self.fileobj.write(str)
    
    def flush(self):
        self.fileobj.flush()


class Editor(Frame):
    def __init__(self, master: Widget, *, value=None):
        super().__init__(master)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._value = \
        value = value or ''

        self._var = \
        var = StringVar()
        var.set(self.value)
        def callback(name, index, mode):
            self._value = var.get()
        var.trace('w', callback)

        self._text = \
        text = ScrolledText(self, exportselection=False)
        text.grid(row=0, column=0, sticky='nsew')
        _configure_text_defaults(text)
        text.insert(END, var.get())
        def callback(event):
            var.set(text.get('1.0', END))
            text.edit_modified(0)
        text.bind('<<Modified>>', callback)
        def callback(event):
            def count(text, index, *, default=0):
                x = text.count('1.0', index, '-chars')
                if x is None:
                    x = default
                else:
                    x = x[0]
                return x

            value = self._value
            left = right = count(text, f'@{event.x},{event.y}')
            # print(f'{left = !r}')
            # print(f'{right = !r}')
            # if ranges := text.tag_ranges(SEL):
            #     left = count(text, SEL_FIRST, default=0)
            #     right = count(text, SEL_LAST, default=len(value))
            
            left = value.rfind('##', 0, left)
            if left < 0:
                left = 0
            else:
                nl = value.find('\n', left)
                if nl >= 0:
                    left = nl + 1
            
            right = value.find('##', right)
            if right < 0:
                right = len(value)
            
            text.tag_remove(SEL, '1.0', END)
            text.tag_add(SEL, f'1.0+{left} chars', f'1.0+{right} chars')
        text.bind('<Control-Button-1>', callback)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._var.set(value)

    @property
    def text(self):
        return self._text


def _llmerick_split(document, *, new_tokens, old_tokens=0, model=DEFAULT_MODEL):
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


def _llmerick_fetch(request):
    with requests.post(
        url=request.get('url', DEFAULT_URL),
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {OPENAI_API_KEY}',
        },
        json={
            'model': request.get('model', DEFAULT_MODEL),
            'messages': [
                {
                    'role': message['role'],
                    'content': message['content'],
                }
                for message in request['messages']
            ],
        },
        proxies={
            'http': '',
            'https': '',
        },
    ) as r:
        return r.json()


def _llmerick_re_find_all(needle: str, haystack: str) -> List[str]:
    ret = []
    for match in re.findall(needle, haystack):
        ret.append(match)
    return ret


def llmerick(*, input: str, code: str) -> str:
    try:
        input = json.loads(input)
    except json.JSONDecodeError:
        pass
    finally:
        input = json.dumps(input)

    native_callbacks = {}
    ext_codes = {}

    ext_codes['_llmerick_input'] = input

    def split(document, new_tokens, old_tokens) -> List[str]:
        return _llmerick_split(document, new_tokens=new_tokens, old_tokens=old_tokens)
    ext_codes['_llmerick_split_encode'] = (
        r'''function(document, new_tokens, old_tokens=0)'''
        r'''  std.manifestJsonMinified({'''
        r'''    document: document,'''
        r'''    new_tokens: new_tokens,'''
        r'''    old_tokens: old_tokens,'''
        r'''  })'''
    )
    native_callbacks['_llmerick_split'] = (('args',), lambda args: split(**json.loads(args)))
    ext_codes['_llmerick_split_decode'] = (
        r'''function(fragments)'''
        r'''  fragments'''
    )

    def fetch(input) -> Response:
        input = json.loads(input)
        request = input['request']
        response = _llmerick_fetch(
            request=input['request'],
        )
        output = { 'response': response }
        output = json.dumps(output)
        return output
    ext_codes['_llmerick_fetch_encode'] = (
        r'''function(request)'''
        r'''  std.manifestJsonMinified({'''
        r'''    request: request,'''
        r'''  })'''
    )
    native_callbacks['_llmerick_fetch'] = (('input',), fetch)
    ext_codes['_llmerick_fetch_decode'] = (
        r'''function(output)'''
        r'''  std.parseJson(output).response'''
    )

    def re_find_all(needle: str, haystack: str) -> List[str]:
        return _llmerick_re_find_all(needle, haystack)
    ext_codes['_llmerick_re_find_all_encode'] = (
        r'''function(needle, haystack)'''
        r'''  std.manifestJsonMinified({'''
        r'''    needle: needle,'''
        r'''    haystack: haystack,'''
        r'''  })'''
    )
    native_callbacks['_llmerick_re_find_all'] = (('needle', 'haystack'), lambda args: re_find_all(**json.loads(args)))
    ext_codes['_llmerick_re_find_all_decode'] = (
        r'''function(matches)'''
        r'''  matches'''
    )

    try:
        output = _jsonnet.evaluate_snippet(
            '<code>',
            code,
            native_callbacks=native_callbacks,
            ext_codes=ext_codes,
        )
        # print(f'{output = !r}')
    except:
        # print(_add_line_numbers(source))
        raise
    
    output = json.loads(output)

    if not isinstance(output, str):
        output = json.dumps(output, indent=2)
    
    return output


def main(
    title: str,
    icon: Path,
    left: Path,
    right: Path,
    code: Path,
    lib: Path,
):
    #/tk
    tk = Tk()
    tk.title(title)
    tk.geometry('640x480')
    tk.attributes('-zoomed', True)
    tk.grid_rowconfigure(0, weight=1)
    tk.grid_columnconfigure(0, weight=1)

    icon = icon
    icon = Image.open(icon)
    icon = PhotoImage(icon)
    tk.wm_iconphoto(True, icon)

    style = Style(tk)
    style.configure('stacked.TNotebook', tabposition='nw', tabplacement='nw')

    def _generic_run_code(*, input_editor, output_editor):
        def getselection(text, *, name):
            if ranges := text.tag_ranges(SEL):
                return text.get(*ranges)
            else:
                raise ValueError(f'Nothing selected in {name} editor')

        input_text = getselection(input_editor.text, name='input')
        lib_text = getselection(lib_editor.text, name='lib')
        code_text = getselection(code_editor.text, name='code')

        output_text = llmerick(input=input_text, code=lib_text + code_text)
        output_editor.text.mark_set(INSERT, END)
        output_editor.text.see(INSERT)
        output_editor.text.insert(INSERT, '\n##\n' + output_text)

    menu = Menu(tk)
    def callback():
        _generic_run_code(
            input_editor=left_editor,
            output_editor=right_editor,
        )
    menu.add_command(label='Left-to-Right', command=callback)
    def callback():
        _generic_run_code(
            input_editor=right_editor,
            output_editor=left_editor,
        )
    menu.add_command(label='Right-to-Left', command=callback)
    tk.config(menu=menu)

    #/tk/topbot
    topbot = \
    frame = Frame(tk)
    frame.grid(row=0, column=0, sticky='nsew')
    frame.grid_rowconfigure(0, weight=1)
    frame.grid_rowconfigure(1, weight=0)
    frame.grid_columnconfigure(0, weight=1)

    #/tk/topbot/top
    top = \
    frame = Frame(topbot)
    frame.grid(row=0, column=0, sticky='nsew')
    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_columnconfigure(1, weight=1)
    frame.grid_columnconfigure(2, weight=1)
    
    #/tk/topbot/bot
    bot = \
    frame = Frame(topbot, height=128)
    frame.grid(row=1, column=0, sticky='sew')
    frame.grid_propagate(False)
    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=1)

    #/tk/topbot/top/left_editor
    left_editor = \
    editor = Editor(top, value=left.read_text())
    editor.grid(row=0, column=0, sticky='nsew')

    #/tk/topbot/top/center
    center = \
    frame = Frame(top)
    frame.grid(row=0, column=1, sticky='nsew')
    frame.grid_rowconfigure(0, weight=1, uniform='center')
    frame.grid_rowconfigure(1, weight=3, uniform='center')
    frame.grid_columnconfigure(0, weight=1, uniform='center')

    #/tk/topbot/top/center/lib_editor
    lib_editor = \
    editor = Editor(center, value=lib.read_text())
    editor.grid(row=0, column=0, sticky='new')

    #/tk/topbot/top/center/code_editor
    code_editor = \
    editor = Editor(center, value=code.read_text())
    editor.grid(row=1, column=0, sticky='sew')

    #/tk/topbot/top/right_editor
    right_editor = \
    editor = Editor(top, value=right.read_text())
    editor.grid(row=0, column=2, sticky='nsew')

    #/tk/topbot/bot/bot_text
    bot_text = \
    text = ScrolledText(bot)
    text.grid(row=0, column=0, sticky='nsew')
    _configure_text_defaults(text)
    text.tag_configure('stderr', foreground='#b22222')
    sys.stdout = TextRedirector(sys.stdout, text, 'stdout')
    sys.stderr = TextRedirector(sys.stderr, text, 'stderr')

    tk.mainloop()


def cli():
    def icon(s) -> Path:
        if isinstance(s, str):
            s = Path.home() / '.local' / 'share' / 'icons' / f'{s}.ico'
        else:
            s = Path(s)

        return s
        
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--title', default='VisualLLMerick', type=lambda s: f'VisualLLMerick - {s}')
    parser.add_argument('--left', type=Path, default=Path('/dev/null'))
    parser.add_argument('--lib', type=Path, default=Path('/dev/null'))
    parser.add_argument('--code', type=Path, default=Path('/dev/null'))
    parser.add_argument('--right', type=Path, default=Path('/dev/null'))
    parser.add_argument('--icon', type=icon, default=icon('VL'))
    args = vars(parser.parse_args())

    main(**args)


if __name__ == '__main__':
    cli()
