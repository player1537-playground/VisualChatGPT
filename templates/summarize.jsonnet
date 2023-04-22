local trim(x) = std.stripChars(x, " \n\t");

local character = trim(|||
    You are a helpful assistant designed to aid a PhD student with writing their dissertation
|||);

local job = trim(|||
    Your job is to write a two paragraph summary of some text
|||);

local understanding = trim(|||
    This is foundational work on the distinction between microservices and monoliths
|||);

local phase1a = trim(|||
    A) a brief overview of my understanding of the text
|||);

local phase1b = trim(|||
    B) a small selection of the text
|||);

local phase1c = trim(|||
    C) an informal set of notes based on the current text that will help you in Phase 2
|||);

local phase1 = trim(|||
    Phase 1) You will be given: %(phase1a)s, and %(phase1b)s. You will produce: %(phase1c)s.
|||) % {
    phase1a: phase1a,
    phase1b: phase1b,
    phase1c: phase1c,
};

local phase2 = trim(|||
    Phase 2) You will be given: A) a brief overview of my understanding of the text, and B) each of the sets of notes from Phase 1. You will produce: C) a two paragraph summary of the text based on my understanding and on your notes.
|||);

local each(i, fragment) =
    local context = {
        character: character,
        job: job,
        understanding: understanding,
        phase1a: phase1a,
        phase1b: phase1b,
        phase1c: phase1c,
        phase1: phase1,
        phase2: phase2,
        fragment: fragment,
    };

    {
        messages: [
            { role: 'system', content: trim(|||
                %(character)s. %(job)s. Your job is split into multiple phases:

                %(phase1)s.

                %(phase2)s.

                You are currently in Phase 1.
            |||) % context },

            { role: 'user', content: trim(|||
                I will now provide you with: %(phase1a)s.

                %(understanding)s.
            |||) % context },

            { role: 'user', content: trim(|||
                I will now provide you with: %(phase1b)s.

                %(fragment)s
            |||) % context },

            { role: 'user', content: trim(|||
                Remember %(phase1)s

                Give me %(phase1c)s.
            |||) % context },
        ],
    };

{
    local document = std.extVar('document'),
    local fragments = std.native('split')(document, 1024, 64),

    requests: std.mapWithIndex(each, fragments),
}
