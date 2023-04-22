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
		job: "Your job is to help identify problems with some text",
		a: "A) Some text from the dissertation",
		b: "B) Some specific problems to identify",
		c: "C) The modified text from (A) with an attempt at resolving the problems in (B)",
	},
	messages: [
		system(|||
			%(character)s. %(job)s.

			You will be given: %(a)s and %(b)s. You will produce: %(c)s.
		||| % context),

		user(|||
			I will now provide you with: %(a)s.

			%(document)s
		||| % context),

		user(|||
			I will now provide you with: %(b)s.

			I believe there should be a thread of logic within the text so that every paragraph advances that thread of logic with each sentence. Every sentence should follow from each other.

			The thread of logic for this text should be: Visualization-as-a-Service (VaaS) is an important idea but existing VaaS implementations are not advanced enough to handle the new kinds of problems I am presenting.
		||| % context),

		user(|||
			Remember %(job)s.

			Give me %(c)s.
		||| % context),
	],
};

{ requests: [ request(document) ] }

