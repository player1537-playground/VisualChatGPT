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
		job: "Your job is to identify problems where the writing of some paragraphs introduces questions that would lead to a lack of trust in the writing or the dissertation as a whole",
		a: "A) The first few paragraphs of the dissertation's introduction",
    b: "B) A summary of what facts must be accepted at this point to agree with the text",
		c: "C) A summary of what questions a reader would need answered in the next paragraph",
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

local paragraphs = std.split(document, "\n\n");

local each(i) = std.join("\n\n", paragraphs[:i+1]);

{ requests: std.map(request, std.makeArray(std.length(paragraphs), each)) }

