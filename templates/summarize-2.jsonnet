local document = std.extVar('document');
local trim(x) = std.stripChars(x, " \n\t");

local goal = trim(|||
	I want this text to be about the connection between interaction and visualization. I'm hoping that it talks about how the only way you can get insights from visualization is through direct interaction
|||);

local Request(document) = {
	local Message(role, content) = {
		role: role,
		content: trim(content) % {
			character: "You are a helpful assistant designed to aid a PhD student with writing their dissertation",
			job: "Your job is to write a two paragraph summary of some text",
			p1: "Phase 1) You will be given: %(p1a)s, and %(p1b)s. You will produce: %(p1c)s" % self,
			p1a: "A) a brief overview of my understanding of the text",
			p1b: "B) a small selection of the text",
			p1c: "C) an informal set of notes based on the current text that will help you in Phase 2",
			p2: "Phase 2) You will be given: %(p2a)s and %(p2b)s. You will produce: %(p1c)s" % self,
			p2a: "A) a brief overview of what I'd like the summary to talk about",
			p2b: "B) an informal set of notes from Phase 1",
			p2c: "C) a two paragraph summary of the notes (B) according to goal (A)",
			goal: goal,
			document: document,
		},
	},

	messages: [
		Message('system', |||
			%(character)s. %(job)s. Your job is split into multiple phases:

			%(p1)s.

			%(p2)s.

			You are currently in Phase 2.
		|||),
		Message('system', |||
			I will now provide you with %(p2a)s.

			%(goal)s.
		|||),
		Message('system', |||
			I will now provide you with %(p2b)s.

			%(document)s.
		|||),
		Message('system', |||
			Remember %(p2)s.

			Give me %(p2c)s.
		|||),
	],		
};

{ requests: [ Request(document) ] }
