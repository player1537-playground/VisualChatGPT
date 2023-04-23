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
      job: "Your job is to help me write two paragraphs that help address a goal. You will follow a generalized 3-phase workflow for writing information in a supported and academic method",
      p1: "Phase 1: Search) You will be given: %(p1a)s and %(p1b)s. You will produce: %(p1c)s" % self,
      overview: "a brief overview of my dissertation",
      goal: "a brief overview of what goal I want the new text to achieve",
      p1a: "A) %(overview)s" % self,
      p1b: "B) %(goal)s" % self,
      p1c: "C) an itemized list of Google Scholar search terms for papers that you will use in Phase 2",
      p2: "Phase 2: Summarize) You will be given: %(p2a)s and %(p2b)s. You will produce: %(p2c)s" % self,
      p2a: "A) %(goal)s" % self,
      p2b: "B) a selection of text from a paper",
      p2c: "C) an itemized list of notes from the paper that you will use in Phase 3",
      p3: "Phase 3: Synthesize) You will be given: %(p3a)s and %(p3b)s. You will produce %(p3c)s" % self,
      p3a: "A) %(goal)s" % self,
      p3b: "B) an itemized list of notes from Phase 2",
      p3c: "C) two paragraphs that address the goal",
      thedocument: document,
      thegoal: goal,
    },
  },

  messages: [
    Message('system', |||
      %(character)s. %(job)s. Your job is split into multiple phases:

      %(p1)s.

      %(p2)s.

      %(p3)s.

      You are currently in Phase 1.
    |||),
    Message('system', |||
      I will now provide you with %(p1a)s.

      %(thedocument)s.
    |||),
    Message('system', |||
      I will now provide you with %(p1b)s.

      %(thegoal)s.
    |||),
    Message('system', |||
      Remember %(p1)s.

      Give me %(p1c)s.
    |||),
  ],    
};

{ requests: [ Request(document) ] }
