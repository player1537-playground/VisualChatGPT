local zip(func, arr1, arr2) =
  local len1 = std.length(arr1);
  local len2 = std.length(arr2);
  assert std.assertEqual(len1, len2);
  local each(i) = func(arr1[i], arr2[i]);
  std.makeArray(len1, each);

local comment(s) =
  local each(line) = "%" + line;
  std.join("\n", std.map(each, std.split(s, "\n")));
 
local each(fragment, summary) = |||
  %(summary)s
  %(fragment)s

||| % { fragment: comment(fragment), summary: summary };

local fragments = std.extVar('fragments');
local summaries = std.extVar('summaries');
 
local outputs = zip(each, fragments, summaries);
{ output: std.join("\n", outputs) }
