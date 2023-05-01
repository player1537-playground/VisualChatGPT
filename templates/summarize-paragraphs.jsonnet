local grouper(n, arr) =
  local each(i) =
    local each(j) =
      arr[i+j];
    std.makeArray(n, each);
  std.makeArray(std.length(arr) - n, each);

{ requests: [
  {
    role:: "You are a helpful assistant designed to aid a PhD student with writing their dissertation",
    job:: "Your job is to summarize every paragraph into a single sentence. It is helpful to know that you will be operating on \"fragments\" of text, which are short selections of text from the dissertation. You only need to summarize the current fragment, but you will also have access to the previous and next fragments. You should only summarize the current fragment",
    A:: "A) The previous fragment",
    B:: "B) The current fragment",
    C:: "C) The next fragment",
    D:: "D) The one sentence summary of (%(B)s" % self,
  } + { messages: [
    { role: 'system', content: |||
      %(role)s. %(job)s.

      You will be given: %(A)s, %(B)s, and %(C)s. You will produce %(D)s.
    ||| },
    { role: 'user', content: |||
      I will now provide you with %(A)s.

      %(a)s
    ||| },
    { role: 'user', content: |||
      I will now provide you with %(B)s.

      %(b)s
    ||| },
    { role: 'user', content: |||
      I will now provide you with %(C)s.
local grouper(n, arr) =
  local each(i) =
    local each(j) =
      arr[i+j];
    std.makeArray(n, each);
  std.makeArray(std.length(arr) - n, each);

{ requests: [
  {
    role:: "You are a helpful assistant designed to aid a PhD student with writing their dissertation",
    job:: "Your job is to summarize every paragraph into a single sentence. It is helpful to know that you will be operating on \"fragments\" of text, which are short selections of text from the dissertation. You only need to summarize the current fragment, but you will also have access to the previous and next fragments. You should only summarize the current fragment",
    A:: "A) The previous fragment",
    B:: "B) The current fragment",
    C:: "C) The next fragment",
    D:: "D) The one sentence summary of (%(B)s" % self,
  } + { messages: [
    { role: 'system', content: |||
      %(role)s. %(job)s.

      You will be given: %(A)s, %(B)s, and %(C)s. You will produce %(D)s.
    ||| },
    { role: 'user', content: |||
      I will now provide you with %(A)s.

      %(a)s
    ||| },
    { role: 'user', content: |||
      I will now provide you with %(B)s.

      %(b)s
    ||| },
    { role: 'user', content: |||
      I will now provide you with %(C)s.

      %(c)s
     ||| },
    { role: 'user', content: |||
      Remember %(job)s.

      You will now produce %(D)s.
    ||| },
  ] } + {
    a:: group[0],
    b:: group[1],
    c:: group[2],
  }
  for group in grouper(3, std.split(std.extVar('document'), "\n"))
] } + { local requests = self, requests: [
  request + { local request = self, messages: [
    message + { local message = self, content:
      std.stripChars(super.content, " \t\n") % (requests + request + message),
    }
    for message in super.messages
  ] }
  for request in super.requests
] }

      %(c)s
     ||| },
    { role: 'user', content: |||
      Remember %(job)s.

      You will now produce %(D)s.
    ||| },
  ] } + {
    a:: group[0],
    b:: group[1],
    c:: group[2],
  }
  for group in grouper(3, std.split(std.extVar('document'), "\n"))
] } + { requests: [
  request + { messages: [
    message + { content:
      std.stripChars(super.content, " \t\n") % (requests + request + message),
    }
    for message in super.messages
  ] }
  for request in super.requests
] }
