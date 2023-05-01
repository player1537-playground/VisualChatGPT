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


ROOT = Path(__file__).resolve().parent
URL = 'https://api.openai.com/v1/chat/completions'
MODEL = 'gpt-3.5-turbo'
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


@dataclass
class Message:
    role: str
    content: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Message:
        return cls(
            role=data['role'],
            content=data['content'],
        )

    def tk(self, master: Widget) -> Widget:
        frame = Frame(master)
        frame.grid_rowconfigure(0, weight=0)
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        role_var = StringVar()
        role_var.set(self.role)
        def callback(name, index, mode):
            self.role = role_var.get()
        role_var.trace('w', callback)

        content_var = StringVar()
        content_var.set(self.content)
        def callback(name, index, mode):
            self.content = content_var.get()
        content_var.trace('w', callback)

        role_entry = Entry(frame, textvariable=role_var)
        role_entry.grid(row=0, column=0, sticky='nsew')

        content_text = ScrolledText(frame)
        _configure_text_defaults(content_text)
        content_text.insert(END, content_var.get())
        def callback(event):
            content_var.set(content_text.get('1.0', END))
        content_text.bind('<<Modified>>', callback)
        content_text.grid(row=1, column=0, sticky='nsew')

        return frame


@dataclass
class Request:
    messages: List[Message]

    def tk(self, master: Widget) -> Widget:
        frame = Frame(master)
        frame.grid_columnconfigure(0, weight=1)

        for i, message in enumerate(self.messages):
            frame.grid_rowconfigure(i, weight=1)

            message = message.tk(frame)
            message.grid(row=i, column=0, sticky='nsew')

        return frame


@dataclass
class Requests:
    requests: List[Request]
    
    def report(self):
        encoding = tiktoken.encoding_for_model(MODEL)
        encode = encoding.encode_ordinary
        decode = encoding.decode
        
        total_prompt_tokens = 0
        for i, request in enumerate(self.requests):
            request_prompt_tokens = 0
            for message in request.messages:
                message_prompt_tokens = len(encode(message.content))
                
                request_prompt_tokens += message_prompt_tokens
            
            print(f'Request {i}: prompt_tokens = {request_prompt_tokens!r}; cost = ${request_prompt_tokens * PRICING:0.3f}')
            
            total_prompt_tokens += request_prompt_tokens

        print(f'Requests: prompt_tokens = {total_prompt_tokens!r}; cost = ${total_prompt_tokens * PRICING:0.2f}')

    def tk(self, master: Widget) -> Widget:
        notebook = Notebook(master)
        notebook.pack(fill='both', expand=True)

        for i, request in enumerate(self.requests):
            request = request.tk(notebook)
            request.pack(fill='both', expand=True)
            notebook.add(request, text=f'Request {i}')

        return notebook


@dataclass
class Response:
    usage_prompt_tokens: int
    usage_completion_tokens: int
    usage_total_tokens: int
    message: Message

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Response:
        return cls(
            usage_prompt_tokens=data['usage']['prompt_tokens'],
            usage_completion_tokens=data['usage']['completion_tokens'],
            usage_total_tokens=data['usage']['total_tokens'],
            message=Message.from_dict(data['choices'][0]['message'])
        )
    
    def tk(self, master: Widget) -> Widget:
        return self.message.tk(master)


@dataclass
class Responses:
    responses: List[Response]
    
    def report(self):
        total_response_tokens = 0
        for i, response in enumerate(self.responses):
            response_tokens = response.usage_total_tokens
            
            print(f'Response {i}: tokens = {response_tokens!r}; cost = ${PRICING * response_tokens:0.3f}')
            
            total_response_tokens += response_tokens

        print(f'Responses: tokens = {total_response_tokens!r}; cost = ${PRICING * total_response_tokens:0.2f}')

    def tk(self, master: Widget) -> Widget:
        frame = Frame(master)

        for i, response in enumerate(self.responses):
            response = response.tk(frame)
            response.grid(row=i, column=0, stick='nsew')
            frame.grid_rowconfigure(i, weight=1)
            frame.grid_columnconfigure(0, weight=1)

        return frame


@dataclass
class Split:
    new_tokens: int
    old_tokens: int

    def __post_init__(self):
        # Jsonnet seems to make all of these variables floats instead of ints.
        # Let's coerce them to integers.
        self.new_tokens = int(self.new_tokens)
        self.old_tokens = int(self.old_tokens)

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


@dataclass
class Code:
    name: str
    source: str

    @classmethod
    def from_path(cls, path: Path) -> Code:
        path = Path(path)
        return cls(
            name=path.name,
            source=path.read_text(),
        )

    def tk(self, master: Widget) -> Widget:
        var = StringVar()
        var.set(self.source)
        def callback(name, index, mode):
            self.source = var.get()
        var.trace('w', callback)

        text = ScrolledText(master)
        _configure_text_defaults(text)
        text.insert(END, var.get())
        def callback(event):
            var.set(text.get('1.0', END))
            text.edit_modified(0)
        text.bind('<<Modified>>', callback)

        return text


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
        text = ScrolledText(self)
        text.grid(0, 0, sticky='nsew')
        _configure_text_defaults(text)
        text.insert(END, var.get())
        def callback(event):
            var.set(text.get('1.0', END))
            text.edit_modified(0)
        text.bind('<<Modified>>', callback)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._var.set(value)


class Editors(Frame):
    def __init__(self, master: Widget, *, value=None):
        if value is None:
            value = []

        super().__init__(master)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._notebook = \
        notebook = Notebook(self)
        notebook.grid(row=0, column=0, sticky='nsew')

        self._notebook_editors = []

        self.value = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        for _ in self._notebook_editors:
            self._notebook.forget(0)

        self._notebook_editors = [None] * len(value)

        self._value = value



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


TEXT = NewType('TEXT', str)
CODE = NewType('CODE', str)


@dataclass
class Application:
    input: TEXT
    preprocess: CODE
    inputs: List[TEXT]
    encoder: CODE
    requests: List[Request]
    responses: List[Response]
    decoder: CODE
    outputs: List[TEXT]
    postprocess: CODE
    output: TEXT

    def compile(self):
        data = json.loads(_jsonnet.evaluate_snippet(
            self.code.name,
            self.code.source,
            native_callbacks={
                'split': (('document', 'new_tokens', 'old_tokens'), lambda document, new_tokens, old_tokens: Split(new_tokens, old_tokens)(document)),
            },
            ext_vars={
                'document': self.document.text,
            },
        ))

        print(f'Here! {len(data["requests"]) = !r}')

        self.requests.requests = [
            Request(
                messages=[
                    Message.from_dict(message)
                    for message in request['messages']
                ],
            )
            for request in data['requests']
        ]
        
        self.requests.report()
    
    def execute(self):
        responses = []
        for i, request in enumerate(self.requests.requests):
            with requests.post(
                url=self.url,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {OPENAI_API_KEY}',
                },
                json={
                    'model': MODEL,
                    'messages': [
                        {
                            'role': message.role,
                            'content': message.content,
                        }
                        for message in request.messages
                    ],
                },
            ) as r:
                response = r.json()
            
            response = Response.from_dict(response)
            responses.append(response)
        
        self.responses.responses = responses
        self.responses.report()

    def tk(self, master: Widget) -> Widget:
        menu = Menu(master)
        master.config(menu=menu)

        notebook = Notebook(master)
        notebook.grid(row=0, column=0, stick='nsew')
        notebook.grid_rowconfigure(0, weight=1)
        notebook.grid_columnconfigure(0, weight=1)

        

        document = self.document.tk(notebook)
        notebook.add(document, text=f'1 Document', underline=0)
        
        code = self.code.tk(notebook)
        notebook.add(code, text=f'2 Code', underline=0)

        requests = None

        responses = None

        notebook.enable_traversal()

        return frame


def main(
    title: str,
    url: str,
    input: TEXT,
    preprocess: CODE,
    inputs: List[TEXT],
    encoder: CODE,
    requests: List[Request],
    responses: List[Response],
    decoder: CODE,
    outputs: List[TEXT],
    postprocess: CODE,
    output: TEXT,
    icon: Path,
):
    icon = icon
    icon = Image.open(icon)
    icon = PhotoImage(icon)

    tk = Tk()
    tk.title(name)
    tk.geometry('640x480')
    tk.wm_iconphoto(True, tk_icon)
    tk.attributes('-zoomed', True)
    tk.grid_rowconfigure(0, weight=1)
    tk.grid_rowconfigure(1, weight=0)
    tk.grid_columnconfigure(0, weight=1)

    tk_style = \
    style = Style(tk)
    style.configure('stacked.TNotebook', tabposition='nw', tabplacement='nw')

    tk_main = \
    frame = Frame(tk)
    frame.grid(row=0, column=0, sticky='nsew')
    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=1)

    tk_main_notebook = \
    notebook = Notebook(tk_main)
    notebook.grid(row=0, column=0, sticky='nsew')
    notebook.grid_rowconfigure(0, weight=1)
    notebook.grid_columnconfigure(0, weight=1)

    tk_main_input = \
    editor = Editor(tk_main_notebook, value=input)
    editor.grid(row=0, column=0, sticky='nsew')
    tk_main_notebook.insert(0, editor, text='1 Input', underline=0)

    tk_main_preprocess = \
    editor = Editor(tk_main_notebook, value=input)
    editor.grid(row=0, column=0, sticky='nsew')
    tk_main_notebook.insert(1, editor, text='2 Preprocess', underline=0)

    tk_main_inputs = None
    def _tk_main_inputs():
        nonlocal tk_main_inputs

        if tk_main_inputs is not None:
            tk_main_notebook.forget(tk_main_inputs)

        tk_main_inputs = \
        notebook = Notebook(tk_main_notebook)
        notebook.grid(row=0, column=0, sticky='nsew')
        notebook.grid_rowconfigure(0, weight=1)
        notebook.grid_columnconfigure(0, weight=1)
        tk_main_notebook.insert(2, notebook, text='3 Inputs', underline=0)

        for input in inputs:
            tk_main_inputs_editor = \
            editor = Editor(tk_main_inputs, value=input)
    _tk_main_inputs()

    

    #/tk_main_inputs


    #/tk_main_notebook

    #/tk_main


    tk_footer = \
    frame = Frame(tk)
    frame.grid(row=1, column=0, sticky='sew')
    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=1)

    tk_footer_text = \
    text = ScrolledText(tk_footer, height=8)
    _configure_text_defaults(text)
    text.tag_configure('stderr', foreground='#b22222')
    text.grid(row=0, column=0, sticky='nsew')
    sys.stdout = TextRedirector(sys.stdout, text, 'stdout')
    sys.stderr = TextRedirector(sys.stderr, text, 'stderr')

    #/tk_footer

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
    parser.add_argument('--title', default='VisualChatGPT', type=lambda s: f'VisualChatGPT - {s}')
    parser.add_argument('--document', type=Path, default=Path('/dev/null'))
    parser.add_argument('--code', type=Path, default=Path('/dev/null'))
    parser.add_argument('--icon', type=icon, default=icon('C'))
    args = vars(parser.parse_args())

    main(**args)


if __name__ == '__main__':
    cli()
