# Prompt Log

Verbatim record of every significant prompt sent to Claude Code during this project, numbered
progressively in the order they were sent. This is a required submission artefact (per the
assessment brief's `ai/` directory requirement) and doubles as the raw material for the
"how you directed your AI tools" section of the presentation.

Rules for this file:
- Prompts are logged **as typed**, not cleaned up or summarised.
- Numbering is sequential and never reused, even if a prompt is later judged unimportant.
- This file is append-only during the build; we do not rewrite history here (editorial commentary,
  if any, belongs in `DECISIONS.md`, cross-referenced by prompt number).

---

## P1

so I a @2026 AI Engineering Assessment.pdf file which contains an exercise to perform. Let's review and pick a specific idea and what are the fundamental requirements to keep in mind. Besides I have added a @AI FDE Training/ folder that contains a series of folders with weekly work with claude.md files, specification files and other files that I used to work on the projects. Importantly, they refer to a methodology called ATX that is in all the files in the @AI FDE Training/Reference/ folder. Please read all the files in that folder and let's understand what, in this methodology will be useful for us and to perform this exercise. Also we need to start to create a claude.md file. This file will contain the main rules to proceed. You can look at the template inside the @AI FDE Training/Reference/ folder. Please don't assume anything. Ask for clarification,when needed, at every step. Also, we need to create a file to record all the important desicions we are making, scope, design, constraint, rules, goal, intended result. Separate from the file I just mention, there must be another file that will contain all the prompt I am using, one by one, just as they are prompted to you, included the present prompt. They can be numbered progressively and we can later elaborate on them for the sake of the presentation. Also, do things step by step, always tell me what file you have created or edited, what changes you made and wait for me before proceeding. The project folder for this project is Food Connected Demo. Don't write inside @AI FDE Training/ folder. Le't start

## P2

[Response to clarifying questions on "Which use case should we build?" and "What model access do you have for the backend agent?"]

- Use case question: "help me choose. I am thinking about the guithub one and the custom food MCP server. What I have in mind is that the Github scenario would give us some premade datasets from public repo we can work with. However I would be curious to try createing the custom MCP as well and do something more relevant to the company. What are the trade offs? Also, I have created the prompt.md file, as you should have done already. I tcontains the first prompt. Please number it and start adding all of the othetrs I am using to talk to you. Also start creating the files I have requested in the previous prompt. Importantly, Before the context windows gets compressed, you need to save the context into a file so that progress is never lost and we can keep working seemlessly"
- Model access question: "Anthropic API key"

## P3

[Response to clarifying question "Final call on the use case — go with my recommendation or play it safe?", after Claude presented the GitHub-MCP vs. custom-food-MCP trade-off analysis in chat]

- "Custom food-supply-chain MCP server (recommended)"

## P4

[Response to clarifying question "Does this dataset/tools/stack design work, or should we adjust before scaffolding any code?", after Claude proposed the concrete dataset, 5 MCP tools, failure/untrust scenarios, and tech stack in chat]

- "I want to adjust something first"

## P5

tech stack needs to be the one mentioned in the @2026 AI Engineering Assessment.pdf file.
The mock data you presented is good but please make a research about the company Food Connected online so we know the scenario is what fits best the actual business domain.

Also, analyse what the exercise is designed to assess and let's keep track of the fundamental aspects in a separate file so that we know we are covering what we have been asked, so we can self assess at the end.

Please write in Claude.md file all the important rule I am giving you and use @AI FDE Training/Reference/claude-md-examples-guide.md as a template to build the claude file, if that works for you. Also, the ATX methodology is about defining scope, breaking down tasks and deciding delegation rules, so I think it is still very useful for us. In the Week1 and subsequent weeks, I have created different artifacts that rapresent the decisional process using this approach. I would like you to go in the files for every week and espablish a plan, which we can write to a separate file, if it helps to design a roadmap for this work. you will find build loops, specification files, API specification, (we might need one or more for our MCP's). Don't underestimate that methodology and the approach I used. You will see a different organisation ofr each of the week up to the 5th but the sequence is similar and they are usually numbered. Please keep writing to decisions file, prompt ecc as I instructed, without needing reminders from now on. To the MCP I would like to use, I want playwright, as it can help to test in an automated fashion, once we have a web UI ready.

## P6

[Response to clarifying question "How should Playwright MCP fit into the architecture?"]

- "Definitely for me. If we want to include an automated demo than playwright may play a role in the demo with the interviewer. Would it be worth? wo it can show the intended use by itself and then it can also be used manually by the user or would it be adding too much complication? Please don't foerget the other files I was telling you about in the previous prompts and keep recording everything"

## P7

ok at every step print on screen roadmap and where we are in it (add to claude file)
Also, use @AI FDE Training/Reference/integration-spec-template.md for MCP spec, if it helps. It's a template
agree on Playwright
Keep mockdata into a mockdata separate folder
for testing I want happy path, 2 or 3 failures and edge cases that test validation. Mock of course needs to contain this type of data so that all cases are covered

please clarify this you said

Flagged for your review (DECISIONS.md §12) — I set some product-agent defaults under the latitude you gave me, not individually confirmed: single-shot interaction (no mid-task clarification turns), iteration cap = 8 tool calls, 10s per-call/60s total timeout, and the escalation ranking. Easy to change if any of that looks wrong.

## P8

[Response to clarifying question "Keep these four defaults as-is, or change any of them?"]

Keep all four. Please create a an md file that describes the purpose oif what we are building and an handbook for the user. So to clarify it's one shot and there can be no follow ups to further query the results? Does the 8 tool calls limit refers to the single shot usage where the agent may decide what MCP tools to use? Remember we need to setup our own local MCP server. Also. The app, as the exercise says, need to be transparent and show exactly what is happening, what data is being used, what mcp tools are being called, what calls if any error, if any limit was hit. Everything to make it as excplicit and transparent as possible. Is this not part of the requirements in the @Assessment-Criteria.md file?

## P9

show me the assessment criteria on screen (should reflect the file) and how we are doing against it. Are planning to cover every point?

What is the app planning to show on the UI? When and how should we design the main user interactions? Should we have a list of acceptancee criteria? We can use playwhright to have a build loop specific for the UI but we need to make sure the foundation are solid before we start building the solution.

regarding the 3 points. Wouldn;t it be niceer if the user could write follow ups instead of one shots? Would it add much more complexity and work?
UI could also show validation (if successful or not)

Should claude.md file contains the requirementrs or this should belong somewhere else? is this the canonical use of the claude.md file?

## P10

OK let's leave as is.
Write the files we discussed Handbook etc
Can you also create a folder with an image of the hypotetical UI? At this point I need to have a summary of the fucntionality, the aspect, what user can do.

So transparency also include what MCP tools are called? What data has been retrieved? What data processing has been done? What reasoning the LLM has done? all this should be included and please suggest more if you can thnk of more.
Write everything to files (desicions, requirements) all else, before we move on.
Add any new steop to roadmap

## P11

you should also add raw chain of though but needs displayed in a readable way or explain why it's not appropriate
clarify Raw trace JSON view
you should keep everything within the ai folder. is this not stated in the exercise instruictions? specifically you need to move design folder, specs folder and readme file only

## P12

so the two files you created are required deliverables? is session-summary not just the same as our decisions file?

## P13

[Response to clarifying question "What should happen to ai/session-summary.md, now that it's not actually a required file?"]

- "Keep it, repurposed as presentation-prep narrative"

## P14

before you create new files, verify with me. Don't create new files easily. Add this to claude file. Now run a check across all work carried so far. We are lloking for inconsistencies, contradictions, major gaps or concerns, possible impriovements, reference issues, underdeveloped ideas, missing parts Update claude file with this check which we shyould run from time to time. We call it how? integrity check?

## P15

[Response to clarifying question "Does the 'confirm before creating a new file' rule apply to routine implementation code (Phases 1-3), or just artefact/documentation files?"]

- "Artefact/docs only (recommended)"

## P16

fix reference issues
fix contradictions
fix point 8 (major issue)
we need to fix 9, please xplain more clearly

question: how the agent decides what tools to call, are there any rules we should establish? in what document we need to define them? I think they belong in the Agent purpose document? when do we write this file? is it in the roadmap? then there will be the actual specs, Agent specs and integration (MPC specs). Agree?

## P17

is there any other opportunity to establish schemas and structured data so that we are based on solid foundation for the data? I guess this can be done soon after we have the mock data. Proceed with writing files. But before save state of the work as compression is imminent. This should happen automatically, at every step,  without me asking for it

## P18

[Response to clarifying question "How should we get the MCP server actually running and verified?"]

- "Try installing Python here via winget"

## P19

one of the requirements is having a repository. I also have an account on github. Let' screate a repo and star making commits at every important step, with proper description and push it remotely too. Then I want to go over the logic, I want to see rules, thresholds, subtask breakdown, any delegation decision to make between agentic or human. Where is this logic? in the spec or in the claude md file? I fI understand the agent-spec should be the place

## P20

[Response to clarifying questions "Exclude AI FDE Training/ from the git repo entirely?" and "How should GitHub authentication work?"]

- Repo scope: "Yes, exclude it (recommended)"
- GitHub auth: "I'll run `gh auth login` myself, then tell you"

## P21

name is Giuseppe
