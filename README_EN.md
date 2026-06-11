<div align="center">

# boss.skill

> *"Bombard the bosses: a big-character poster for skills."*

Does your boss always chase `impact`, `risk`, and `owner` in every meeting?  
Does one sentence like "don't do this yet" actually hide a whole decision framework?  
Do you feel the problem is not that you cannot work, but that you do not know how to sync upward, report risk, or ask for resources?

**Distill your boss's chats, meeting notes, comments, and project artifacts into a Skill.**

It does not just talk like your boss. It also:

- evaluates projects, plans, and execution with your boss's standards
- recreates how your boss reviews work, pushes progress, and challenges proposals
- teaches you how to report upward, pitch plans, ask for resources, and deliver bad news

Eventually, you may not need the boss anymore.

> *"Are you still a coding traitor if you build large models? You will kill the bosses, then the entrepreneurs, then the capitalists, and finally liberate all humankind."*

It now has more capability lines:

- directly generate a boss template inspired by famous entrepreneurs such as Elon Musk, Steve Jobs, Jeff Bezos, and Jensen Huang
- distill the boss's thinking into a **decision case base + review rubric + decision rules + scene playbooks**, so the skill judges like the boss instead of only sounding like the boss
- quantify fidelity with **decision replay evaluation**
- build a persona for a **mentor / PI / public figure** from free public sources (papers, GitHub, Wikipedia, interviews) when no private chat material exists

[Data Sources](#data-sources) · [Installation](#installation) · [Usage](#usage) · [New Feature Entrepreneur Archetype Mode](#new-feature-entrepreneur-archetype-mode) · [Examples](#examples) · [Structure](#generated-skill-structure) · [Detailed Install Guide](INSTALL.md) · [中文](README.md)

</div>

---

## Data Sources

| Source | Chat Logs | Docs / Comments | Meeting Notes | Notes |
|------|:-------:|:---------:|:-------:|------|
| WeChat exports | ✅ | — | — | txt/html/csv export |
| Feishu exports | ✅ | ✅ | ✅ | JSON/txt/copied text |
| Email `.eml` / `.mbox` | ✅ | ✅ | — | useful for boss email style |
| Markdown / plain text | ✅ | ✅ | ✅ | meeting notes, retros, comments |
| PDF / screenshots | ✅ | ✅ | ✅ | uploaded manually |
| Pasted text | ✅ | ✅ | ✅ | meeting logs, IM threads, review feedback |

---

## Installation

### Claude Code

```bash
# Install into the current project (run from the git repo root)
mkdir -p .claude/skills
git clone https://github.com/vogtsw/boss-skills.git .claude/skills/create-boss

# Or install globally
git clone https://github.com/vogtsw/boss-skills.git ~/.claude/skills/create-boss
```

### OpenClaw

```bash
git clone https://github.com/vogtsw/boss-skills.git ~/.openclaw/workspace/skills/create-boss
```

### Dependencies

```bash
pip3 install -r requirements.txt
```

---

## Usage

In Claude Code, enter:

```text
/create-boss
```

Then follow the prompts for the boss name, baseline profile, management style, and source material such as chats, emails, notes, or documents.

After generation, you can use:

| Command | Description |
|------|------|
| `/list-bosses` | List all generated boss skills |
| `/{slug}` | Invoke the full boss skill |
| `/{slug}-judgment` | Use only the boss judgment lens |
| `/{slug}-management` | Use only the managing-up guidance |
| `/{slug}-persona` | Use only the boss speaking and behavior style |
| `/{slug}-drill {scene}` | Drill mode: the skill plays the boss for multiple turns, then debriefs against the rubric |
| `/boss-eval {slug}` | Run the decision replay eval and report the fidelity score |
| `/boss-rollback {slug} {version}` | Roll back to a previous version |
| `/delete-boss {slug}` | Delete a boss skill |

---

## New Feature: Entrepreneur Archetype Mode

In addition to distilling a real boss, the skill can now generate boss skills directly from famous entrepreneur-style archetypes.

Currently included:

- `elon-musk`
- `steve-jobs`
- `jeff-bezos`
- `jensen-huang`

End users do not need to run Python manually.

You can simply ask for what you want, for example:

```text
Give me an Elon Musk style boss
Give me a Steve Jobs style boss to review a new feature design
Give me a Bezos-style boss to rehearse an incident update
Give me a Jensen Huang style boss to pressure-test an AI platform roadmap
```

The skill will choose the matching archetype internally, generate the boss skill, and return the trigger commands you can use.

This mode is useful for:

- simulating a Musk-style project review
- rehearsing a Jobs-style product review
- training for a Bezos-style status or incident update
- exploring a Jensen Huang style platform strategy review

The goal is not to imitate catchphrases. The goal is to abstract public management patterns: decision rules, communication style, review standards, and execution rhythm.

If you are a developer, the implementation still relies on `tools/skill_writer.py` and the `archetypes/` directory, but that is an internal mechanism rather than the main user-facing workflow.

---

## New Feature: Structured Decision Layer (judge like the boss, not just sound like the boss)

The skill first extracts **structured decision events** from raw material, then induces an executable decision model:

| Artifact | Content |
|------|------|
| `cases/*.json` | Decision case base: situation → options → the boss's choice → rationale → original quote → source |
| `rubric.json` | Review scorecard: the boss's hard checklist (blocker / major / minor items) |
| `decision_rules.md` | IF/THEN decision rules, each backed by case evidence and a confidence level |
| `playbooks/*.md` | Scene workflows (bad news, resource request, pitch) with expected boss reactions and failure branches |

Runtime logic becomes:

`identify the scene -> follow the playbook -> check every rubric item -> apply decision rules -> retrieve similar cases and quote the boss -> respond in the boss's style`

**Decision replay evaluation**: hold out 20% of historical decisions, blind-predict the boss's real choices with the distilled model, and use the hit rate as the fidelity score. Re-run after every correction or material merge to catch regressions.

---

## New Feature: Public Research Mode (mentor / PI / public figure)

No chat logs needed. `tools/person_research.py` aggregates 6 **free, no-API-key** public sources:

| Source | Best for | What you get |
|------|------|------|
| OpenAlex | academic advisors / PIs | author profile, research topics, top-cited papers |
| Semantic Scholar | academic advisors / PIs | h-index, paper abstracts |
| arXiv | AI / STEM advisors | latest preprints (what they are betting on now) |
| Crossref | any academic | publication metadata |
| GitHub | engineering bosses | public repos, tech stack, bio |
| Wikipedia | public figures / entrepreneurs | biography summary |

Just ask in natural language:

```text
Build a persona of my advisor. His name is XXX, he works on XX at XX University.
```

The skill searches, disambiguates same-name candidates, saves raw results into `knowledge/research/`, and distills the persona with evidence levels:
`private (real chats) > public-quote (public original words) > public-inferred (inference from public material)`.
Every public-sourced claim carries its source. Real private material always outranks public inference.

---

## Examples

> Input: `Big tech company, engineering director, my direct boss, outcome-driven, owner-focused, risk-sensitive, conclusion first`

**Scenario 1: Project Review**

```text
User       > Help me review this new project proposal

Boss.skill > Start with the conclusion. What problem does this project actually solve?
           > If we do not do this this quarter, what is the loss?
           > Who is the owner? How is risk covered? If those three things are unclear, the proposal does not pass.
```

**Scenario 2: Reporting Bad News**

```text
User       > The project slipped. How should I tell my boss?

Boss.skill > Do not start by explaining the difficulties. Start with facts.
           > You should say it like this:
           > 1. How late are we now?
           > 2. What is the impact scope?
           > 3. What mitigation has already been done?
           > 4. What decision do you need from me?
```

**Scenario 3: Asking For Resources**

```text
User       > I want one more frontend engineer and one more tester

Boss.skill > Do not say "we are short on people."
           > Explain which critical path is blocked, what result will suffer without support, and why this must happen this quarter.
```

**Scenario 4: Musk-Style Project Review**

```text
User       > Give me a Musk-style boss to review this AI infra refactor

Boss.skill > What is the real bottleneck?
           > Why can this not be done 10x faster?
           > Which constraints are physical, and which are only organizational inertia?
           > If the schedule must be compressed, what will you cut first?
```

**Scenario 5: Jobs-Style Product Review**

```text
User       > Give me a Jobs-style boss to review this new feature design

Boss.skill > Why does this feature deserve to exist?
           > What value will the user actually feel?
           > What should be removed instead of piled on?
           > This version is still not simple enough, and it is not coherent enough.
```

---

## Generated Skill Structure

Each boss skill has three narrative parts plus a decision layer:

| Part | Content |
|------|------|
| **Part A — Boss Judgment** | How this boss evaluates projects, plans, progress, risk, resources, and people |
| **Part B — Managing Up** | How you should sync upward, report risk, pitch plans, ask for resources, and fight for priority |
| **Part C — Persona** | The boss's communication style, emotional logic, management posture, and pressure state |
| **Decision layer** | `cases/` case base, `rubric.json` scorecard, `decision_rules.md` rules, `playbooks/` scene workflows |

Execution logic:

`Receive a question -> identify the scene -> playbook/rubric/rules drive the judgment -> retrieve similar cases -> Persona sets tone -> Management gives concrete upward-management actions -> respond in the boss's style`

See [`bosses/example-laozhou/`](bosses/example-laozhou/) for a complete example including the decision layer.

---

## Use Cases

- before a project review, simulate the questions your boss is likely to ask
- before a weekly update, check whether the format matches what your boss actually cares about
- before a resource request, test which framing is more likely to win support
- when risk or delay appears, rehearse how to report bad news upward
- learn the decision style and management pattern of your boss
- quickly build a sharp "ideal boss" through entrepreneur archetypes

---

## Project Structure

```text
boss-skills/
├── SKILL.md
├── prompts/
│   ├── intake.md
│   ├── judgment_analyzer.md
│   ├── management_analyzer.md
│   ├── persona_analyzer.md
│   ├── judgment_builder.md
│   ├── management_builder.md
│   ├── persona_builder.md
│   ├── decision_extractor.md
│   ├── decision_model_builder.md
│   ├── playbook_builder.md
│   ├── person_researcher.md
│   ├── replay_evaluator.md
│   ├── merger.md
│   └── correction_handler.md
├── tools/
│   ├── generic_chat_parser.py
│   ├── wechat_parser.py
│   ├── feishu_parser.py
│   ├── email_parser.py
│   ├── person_research.py
│   ├── replay_eval.py
│   ├── skill_writer.py
│   └── version_manager.py
├── archetypes/
│   ├── elon-musk/
│   ├── steve-jobs/
│   ├── jeff-bezos/
│   └── jensen-huang/
├── bosses/
│   └── example-laozhou/
├── requirements.txt
└── INSTALL.md
```

---

## Notes

- Source quality determines skill quality: real chats, review comments, and meeting notes are much better than surface description alone
- The most valuable material is usually when the boss criticizes a project, asks hard questions, or makes tradeoffs
- If you only provide tone and no project material, the result may sound like the boss without actually judging like the boss — the decision layer (cases/rubric/rules) exists exactly to fix this, and is only generated when the material contains real tradeoffs
- Entrepreneur archetype mode is for style simulation, not a claim of exact replication of a real person
- Public research mode uses only freely accessible public data, labels every claim with its evidence level and source, and does not claim to reproduce a private personality
- Replay eval results fluctuate when there are fewer than 10 cases; treat them as a reference only
- Later it can grow into IM auto-collection, structured note extraction, and hybrid real-boss plus archetype modes
