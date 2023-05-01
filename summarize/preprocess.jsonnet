local input = std.extVar('input');

{ fragments: [
  std.join("\n", [
    line
    for line in std.split(paragraph, "\n")
#     if !std.startsWith(line, "#")
#     if !std.startsWith(line, "\\")
#     if !std.startsWith(line, "}")
  ])
  for paragraph in std.split(input, "\n\n")
] }

# + { fragments: [super.fragments[std.length(super.fragments)-1]] }
