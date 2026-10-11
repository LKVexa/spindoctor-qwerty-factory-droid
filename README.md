# SpinDoctor Qwerty for Factory Droid

A [Factory Droid](https://docs.factory.ai/cli/configuration/plugins) plugin that runs the **SpinDoctor 3.1.2 quantum-circuit
simulator** on your computer: `q.*` circuit scripts (1-298 logical qubits), the 241 built-in presets, folders of command files
(`q.folder`), and theory tests from a file, pasted text or the chat itself, each with TXT, PDF, JSON and CSV reports.

> **Honest limits.** SpinDoctor is a classical FP64 simulator. It is not a quantum computer, does not connect to quantum hardware,
> and gives no quantum speed-up or advantage. One entangled group is limited to 59 qubits and dense groups are limited by memory
> (2^n x 16 bytes). Registers wider than 29 qubits sample in basis Z only. Histograms are seeded Born samples.

Version 1.1.0 - engine 1.1.0 (SpinDoctor 3.1.2 parity) - Python 3.8+, standard library only - no network, no account, no keys.

## What's in the repo

This repo is a Droid **marketplace** with one plugin:

| Path | What it is |
|---|---|
| `.factory-plugin/marketplace.json` | Marketplace `spindoctor-qwerty-factory-droid`, listing the plugin at `./spindoctor-qwerty` |
| `spindoctor-qwerty/.factory-plugin/plugin.json` | Plugin metadata (version, author, GPL-3.0-or-later) |
| `spindoctor-qwerty/mcp.json` | MCP server `spindoctor-qwerty`: the 6 `spindoctor_*` tools |
| `spindoctor-qwerty/skills/spindoctor-qwerty/` | Skill (`SKILL.md`), the bundled engine (`spindoctor/`), CLI and MCP launchers (`scripts/`), examples |
| `spindoctor-qwerty/droids/qwerty-helper.md` | Droid (subagent) `qwerty-helper`, `model: inherit` |
| `spindoctor-qwerty/commands/` | `/qwerty-functions`, `/qwerty-run`, `/qwerty-preset`, `/qwerty-folder`, `/qwerty-theory` |
| `tools/set_python.py` | Switch the server's Python command (Windows) |
| `tests/` | Host check, shared end-to-end suite, local stand-in model, reference outputs |

No hooks: the plugin never runs anything on its own.

## Install

```bash
droid plugin marketplace add LKVexa/spindoctor-qwerty-factory-droid
droid plugin install spindoctor-qwerty@spindoctor-qwerty-factory-droid --scope user     # or --scope project
droid mcp list        # spindoctor-qwerty  stdio  connected
```

Or from a local clone: `droid plugin marketplace add ./spindoctor-qwerty-factory-droid`, then the same `install` line. Droid copies
the plugin into its cache, so after you change a local clone run `droid plugin marketplace update spindoctor-qwerty-factory-droid`
and `droid plugin update spindoctor-qwerty@spindoctor-qwerty-factory-droid --scope user`. Inside Droid, `/plugins` shows the same.

Requirements: Python 3.8 or newer as `python3` on your PATH. No packages to install.

**Windows:** the python.org installer provides `python` and `py`, not `python3`. In a local clone run
`python tools/set_python.py python` (or `py`, or a full path to `python.exe`), then add the clone as a local marketplace as above.
`python3 tools/set_python.py python3` restores the original file byte for byte.

**How the server finds the plugin.** Droid fills in `${DROID_PLUGIN_ROOT}` in hooks, skills, droids and output styles, but not in
`mcp.json` (checked with Droid 0.238.0), and it starts MCP servers in the folder you launched Droid from. So `mcp.json` runs a short
bootstrap (`python3 -c ...`, standard library only, shown in the file) that reads Droid's install record under
`~/.factory/plugins/installed_plugins/`, takes the newest `spindoctor-qwerty@...` entry and starts
`skills/spindoctor-qwerty/scripts/spindoctor_mcp.py` from it. If you keep the plugin somewhere else, set `SPINDOCTOR_QWERTY_ROOT` to the
plugin folder before starting Droid. The install record format isn't documented by Factory, so a future Droid release could change
it; the skill's CLI fallback (below) does not depend on it.

**Approvals.** Droid runs MCP tools marked read-only (`spindoctor_functions`, `spindoctor_list_presets`, `spindoctor_report`) at
autonomy Low. It treats the other three (`spindoctor_run_script`, `spindoctor_run_preset`, `spindoctor_test_theory`, which write report
files into the workspace) as high impact, so an interactive session asks before running them and `droid exec` needs `--auto high`.

**Without the tools**, the skill tells the model to run the CLI with Execute:
`python3 "<plugin folder>/skills/spindoctor-qwerty/scripts/spindoctor_cli.py" functions` (Droid fills in the folder in the skill text).

Reports and state go to `~/spindoctor-workspace` unless a tool call passes `workspace` or you set `SPINDOCTOR_WORKSPACE`. Pass
**absolute** paths for files and folders, because the server runs in the folder you launched Droid from.

## SpinDoctor Qwerty - plugin tools

| Function | What it does | Command to type |
|---|---|---|
| Function table (spindoctor_functions) | Show this table in chat | `/qwerty-functions` or ask: "show the SpinDoctor functions" |
| Run a script (spindoctor_run_script) | Run any q.* lines above; returns results + TXT/JSON/CSV/PDF report paths | Ask: "run q.circuit new bell 2 / q.circuit add h 0 / ..." |
| Run a preset (spindoctor_run_preset) | Run qc-001..qc-241 with overrides | `/qwerty-preset qc-067 shots=64` |
| List presets (spindoctor_list_presets) | Search the 241 presets | Ask: "list presets about Grover" |
| Read a report (spindoctor_report) | List/read TXT reports (PDF/JSON paths alongside) | Ask: "show the newest SpinDoctor report" |
| Test a theory from a file (spindoctor_test_theory source=file) | Read a .txt/.md/.pdf/.py/.json/.csv/.q attachment, then hypothesis -> prediction -> q.* script -> run -> verdict + TXT/PDF theory report | Ask: "test the theory in C:/notes/theory.md" (the host must pass the file path/content) |
| Test a theory from text (spindoctor_test_theory source=text) | Same pipeline for pasted text | Ask: "test this theory: a Hadamard on \|0> gives 50/50" |
| Test the theory we discussed (spindoctor_test_theory source=chat) | The AI summarises the theory from the conversation (claims, assumptions, variables, prediction), you confirm, then it is tested; quoted excerpts go in the report under 'Source: chat history'. An exported chat transcript (.txt/.md/.json/.html) also works | `/qwerty-theory we discussed`, ask: "test the theory we discussed" or "test the theory in my exported chat C:/chats/conversation.json" |

Every command family is listed with a runnable example in **[FUNCTIONS.md](FUNCTIONS.md)** (the exact table the tool shows):
circuits (`q.circuit`, including 298-qubit wide registers and the `mcx7` gate), queries (`q.query`), the tranche register
(`q.tranche`), the procedural grid, presets and sequences, resource planning, math calculators, physics models, lessons, noise, error
correction, compilation, algorithms, inputs/folders/history (`q.input`, `q.folder`, `q.history`) and the cartridge commands.

## Theory testing

`spindoctor_test_theory` turns a claim into a test: hypothesis -> measurable prediction -> `q.*` script -> run -> compare -> a TXT +
JSON + PDF **theory test report** with the hypothesis, script, raw results, verdict (*supported*, *not supported* or *inconclusive*)
and limits.

- **From a file:** .txt, .md, .pdf, .py, .json, .csv or .q. In Droid, give the file's absolute path on your computer (or paste the text).
- **From pasted text.**
- **From the chat history:** say *"test the theory we discussed"*. The model writes a short summary (claims, assumptions, variables,
  measurable prediction), shows it to you to confirm or correct, then passes it with optional quoted excerpts; the report records them
  under *Source: chat history*. Exported chat transcripts (.txt/.md/.json/.html from ChatGPT, Claude and others) also work.
- The plugin cannot read your conversation or attachments by itself: only the model sees them, and very long conversations may already
  be truncated by the context window.

Sample theory files and chat transcripts are in `spindoctor-qwerty/skills/spindoctor-qwerty/examples/theory/`. The two sample
PDFs are stored as text; run `python3 spindoctor-qwerty/skills/spindoctor-qwerty/examples/theory/make_sample_pdfs.py` to
recreate them.

## Folder ingestion (`q.folder`)

`q.folder run path="<folder>"` runs every supported file at the top level of a folder (.txt, .csv, .json, .qasm, .qasm2, .circuit,
.pdf) in ordinal name order: 1-128 supported files, at most 4 MiB per file, 1-128 commands per file and 4096 characters per command,
strict UTF-8. Other files (for example .md) are skipped and listed. The first failing file stops the job.


## Testing

| Test | Command | Result for 1.1.0 |
|---|---|---|
| Host check (static + real Droid CLI) | `python3 tests/droid_host_check.py --droid "$(command -v droid)"` | see [E2E_RESULTS.md](E2E_RESULTS.md) |

**Real host, scripted model.** The real Droid CLI (0.238.0, npm package `droid`) runs on a Linux test machine with a throwaway HOME
and no Factory account: no sign-in, no API key. The host check adds this repo as a local marketplace, installs the plugin, confirms
`droid mcp list` shows the server connected and `droid exec --list-tools` lists the 6 tools, then runs `droid exec` sessions against
`tests/stub_llm.py`, a local scripted stand-in configured as a BYOK custom model on 127.0.0.1. Through Droid's own MCP client the
session loads the deferred tools with ToolSearch, shows the function table, runs a Bell circuit and preset qc-001, tests a theory from
the chat (verdict *supported*, PDF written) and activates the skill, whose text comes back with the real plugin folder filled in. It
also checks the autonomy behaviour above and that `/qwerty-folder` expands its arguments. Then it runs the shared end-to-end suite
through the installed plugin's own `mcp.json` command and uninstalls. A real model choosing the tools on its own isn't tested, the droid
(subagent) isn't invoked, and Windows wasn't tested. Details in [E2E_RESULTS.md](E2E_RESULTS.md).

## Author and license

Author: **RUSSELL PHILIP SMITHSON** <russellsmithson77@outlook.com>

Copyright (C) 2026 RUSSELL PHILIP SMITHSON. Licensed under the GNU General Public License v3.0 or later (`GPL-3.0-or-later`): see
[LICENSE](LICENSE), [NOTICE](NOTICE) and [COPYRIGHT](COPYRIGHT). `plugin.json` carries the license and author. Factory and Droid are
trademarks of their owner; this project is not affiliated with Factory.
