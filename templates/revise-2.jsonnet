local inputs =
  local x = std.extVar('document');
  local y = std.split(x, "\n\n\n");
  local z = [
    std.split(y, "\n\n")
    for y in y
  ];
  local w = [
    { a: z[0], b: z[1], c: z[2], d: z[3] }
    for z in z
  ];
  w;

local config = {
  character: "You are a helpful AI assistant that helps a PhD student write their dissertation",
  job: "Your job is to revise a paragraph of text from the dissertation according to my notes",
  A: "A) The original paragraph from the dissertation",
  B: "B) The original summary of the paragraph",
  C: "C) The set of high-level goals of this revision",
  D: "D) The partially revised paragraph with the wording I want to use",
  E: "E) The newly revised paragraph according to my goals",
};

{ requests: [ {
  local context = config + input,
  messages: [
    { role: 'system', content: |||
      %(character)s. %(job)s. You will be given: %(A)s, %(B)s, %(C)s, and %(D)s. You will produce %(E)s.
    ||| % context },
    { role: 'user', content: |||
      I will now provide %(A)s.

      %(a)s

      I will now provide %(B)s.

      %(b)s

      I will now provide %(C)s.

      %(c)s
      
      I will now provide %(D)s.

      %(d)s
    ||| % context },
    { role: 'user', content: |||
      Remember: %(job)s.

      You will now produce %(E)s.
    ||| % context },
  ] }
  for input in inputs
] }

