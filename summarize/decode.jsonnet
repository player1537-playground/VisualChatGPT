{ summaries: [
  response.choices[0].message.content
  for response in std.extVar('responses')
] }
