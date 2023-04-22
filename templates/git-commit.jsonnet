local document = std.extVar('document');

local system(content) = {
	role: 'system',
	content: content,
};

local user(content) = {
	role: 'user',
	content: content,
};

local request(document) = {
	local context = {
		document: document,
		character: "You are a helpful assistant designed to aid a PhD student with writing their dissertation",
		job: "Your job is to generate a git commit message",
		a: "A) The output of the command `git diff`",
		b: "B) A long-form summary of what changed in (A)",
		c: "C) A short-form heading (<50 characters) of (B)",
	},
	messages: [
		system(|||
			%(character)s. %(job)s.

			You will be given: %(a)s. You will produce: %(b)s and %(c)s.
		||| % context),

		user(|||
			I will now provide you with: %(a)s.

			%(document)s
		||| % context),

		user(|||
			Remember %(job)s.

			Give me %(b)s and %(c)s.
		||| % context),
	],
};

{ requests: [ request(document) ] }


