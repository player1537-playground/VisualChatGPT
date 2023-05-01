local document = |||
  The visualization of large datasets is crucial to modern data scientific analysis. Often,
  visualizing a dataset is the first step to understanding the patterns within. so one can make
  informed decisions about the data. Although “seeing” the data is important, it is interactive
  control of the visuals that generates insights. Interactive visualization necessitates powerful
  computers.


  The era of remote work has meant that powerful computers are not as available on-
  demand, and so visualization is also not as available. The access to powerful computers is
  due to several compunding factors, ranging from the use of portable laptops for daily work
  to the distance between workers and their assigned powerful computers. Commonly, workers
  have had access to powerful workstations with the ability to do intensive visualization locally,
  but it is now more common to have to remotely interact with that workstation, incurring
  network latency and technical difficulties. There is a need for efficient interaction with
  intensive visualization on portable, lower-powered machines. There exists a gap between the
  computational needs for interactivity and the lack of access to computing power.


  The primary challenge introduced by this gap can be largely attributed to the traditional
  monolithic design of data applications. These include the difficulty faced when scaling an
  application–to larger size of data, to multiple computers, and to many users. A monolithic
  application is designed to be an all-encompassing environment for visualization, from the data
  loading to the actual rendering tasks. There have been attempts at splitting up monolithic
  applications into a client-server model, but many of these approaches are limited in their
  ability to scale to multiple users at once, as each user will be accessing a single instance of
  the application. Another difficult lies in the ease of acquiring multiple powerful computers
  and in supporting their infrastructure.


  Visualization-as-a-Service (VaaS) architecture has been shown to effectively bridge this
  gap in an fast and accessible manner. The VaaS approach introduces a restrictive, request
  and response interface to an application, and separates the user interface from the data
  processing layers. VaaS has been demonstrated for domains where stateless rendering is
  possible and sufficient, such as volume rendering. However, problems that do require state
  management need more flexibility than existing VaaS solutions have explored. There is
  a need for a scalable solution to state management in a deployed VaaS environment that
  addresses problems of efficiency, consistency, and flexibility.

  - There needs to be more focus on "old VaaS is simplistic, by design." It needs to differentiate simplistic problems that are inherently a good fit for VaaS, with complex problems that are non-trivial to make a VaaS.

  - In this dissertation, I aim to extend the capabilities of previous VaaS implementations.
  - Previously, VaaS has been demonstrated for problems that are natural fits for it.
  - Natural VaaS problems have characteristics: problems that have task-parallelism are a natural fit for restrive, request and response interfaces; problems where every user and visualization is independent are a good fit for stateless services; and problems that are result-oriented with predetermined visualizations and characteristics are a good fit for highly optimized and specific visualization kernels.
  - For these problems, VaaS can be highly portable across different infrastructures, scalable across multiple processors, accessible across many users, and cost-effective across cloud providers.
  - In this dissertation, I explore how to adapt VaaS for problems that are not natural fits.


  In this dissertation, I demonstrate an improvement on VaaS with expanded capabilities
  for three previously unaddressed domains. These domains include: (Chapter 4) a task-
  and data-parallel implementation of particle flow advection; (Chapter 5) a cross-device and
  collaborative approach to combining desktop and augmented reality (AR) interfaces; and
  (Chapter 6) a hypothesis-driven and visual approach to resolving visual clutter in graph
  visualization. Each of these domains requires more capabilities from VaaS than existing
  implementations, especially capabilities for state management between VaaS instances.

  - Don't talk about "unexplored domains." They are explored. Instead, refocus this paragraph to talk about how these are "studies" into expanded capabilities. Maybe combine with next paragraph. By this point, I should have already made the new capabilities clear.

  - In the following chapters, I will address the relevant background information for both VaaS and 
  - In Chapters ?-?, I present 3 applications that each explore a different area of improvement for VaaS.
  - In the following chapters, I present (Chapter ?) a study of particle flow advection and its implications for data-parallel VaaS; (Chapter ?) a study of generative mixed-reality and its implications for multiple-device VaaS; and (Chapter ?) a study of parallel graph rendering and its implications for hypothesis-oriented VaaS.


  The improvements presented in this dissertation will enable new
  possibilities for VaaS, including the ability to control visualizations
  expressively, to host them nimbly, and to generate them adaptably. These
  advancements will contribute to the development of a more robust and
  versatile VaaS platform, catering to the diverse needs of users across
  various domains.

  - too high level. Should be grounded in real problem areas.

  - The improvements presented in this dissertation expand the capabilities of VaaS to include data-parallel, multiple-device, and hypothesis-oriented tasks. These advancements will contribute to the development of a more robust and versatile VaaS platform, catering to the diverse needs of users across various domains.


  In the following chapters, I will delve deeper into the specifics
  of these improvements and their implications for the future of data
  visualization. By providing detailed explanations and real-world
  examples, this dissertation aims to pave the way for the next generation
  of Visualization-as-a-Service platforms.

|||;
local paragraphs = std.split(document, '\n\n\n');
local each(i, paragraph) =
  local parts = std.split(paragraph, '\n\n');
  if std.length(parts) == 1 then
    { a: parts[0], b: null, c: null }
  else
    { a: parts[0], b: parts[1], c: parts[2] };

local parts = std.mapWithIndex(each, paragraphs);

{ requests: [ {
  local request = self,
  context:: {
    Task: "You will be given multiple paragraphs and associated notes from the introduction chapter. Each message will include: %(A)s, %(B)s, and %(C)s. For each message, you will generate: %(D)s. If neither (B) or (C) are provided, then you should just give me (A) again, unmodified" % self,
    A: "A) the original text from the dissertation",
    B: "B) a high-level note about what should be changed",
    C: "C) an itemized list of sentences that have the wording I want to use",
    D: "D) a revised paragraph based on (A), (B), and (C)",
  } + part,

  messages: [
    { role: 'system', content: |||
      You are a helpful AI assistant that helps a PhD student write their dissertation.

      %(Task)s.
    ||| % request.context },
    { role: 'user', content: |||
      %(A)s.

      %(a)s

      %(B)s.

      %(b)s

      %(C)s.

      %(c)s.
    ||| % request.context },
    { role: 'user', content: |||
      Remember %(Task)s.

      Give me %(D)s.
    ||| % request.context },
  ]
} for part in parts if part.b != null ] }
