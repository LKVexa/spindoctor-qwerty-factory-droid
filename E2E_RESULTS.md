# E2E results - spindoctor-qwerty-factory-droid 1.1.0

Host: **real Factory Droid CLI 0.238.0** (npm package `droid`, Linux x64) in a throwaway HOME, no Factory account, no API key. Model turns
come from `tests/stub_llm.py`, a local scripted stand-in configured as a BYOK custom model on 127.0.0.1, so tool calls are scripted;
everything between the model and the engine (marketplace install, plugin cache, MCP startup, ToolSearch, tool permissions, MCP
client, skill loading, slash commands) is the real Droid. Python 3.13.5.

Not tested: a real model choosing the tools by itself, invoking the `qwerty-helper` droid through the Task tool, interactive approval
prompts, Windows, macOS.

## Host check: 20/20

| Result | Check |
|---|---|
| PASS | marketplace.json: name, owner, one plugin entry with relative source ./spindoctor-qwerty that exists |
| PASS | plugin.json: name, version 1.1.0, author RUSSELL PHILIP SMITHSON, license GPL-3.0-or-later, homepage/repository |
| PASS | native Droid layout: .factory-plugin/ + skills/ commands/ droids/ mcp.json at the plugin root; no Claude-layout names, no empty hooks |
| PASS | front matter: droid name/description/model inherit; skill name/description; 5 commands with description; honest limits |
| PASS | plugin-root variable only where Droid expands it (skill and droid bodies), never in commands or mcp.json |
| PASS | mcp.json: one stdio server `python3 -c <bootstrap>`, no ${...} references (Droid treats them as environment variables), no secrets |
| PASS | bootstrap: finds the newest installed spindoctor-qwerty record (skips stale/other plugins), honours SPINDOCTOR_QWERTY_ROOT, clear error when not installed |
| PASS | tools/set_python.py: python -> command 'python'; python3 restores mcp.json byte for byte; shell metacharacters refused |
| PASS | real droid 0.238.0 (no account): marketplace add <repo> + plugin install spindoctor-qwerty@spindoctor-qwerty-factory-droid --scope user; copied to the plugin cache |
| PASS | real droid: `droid mcp list` starts the plugin's MCP server -> spindoctor-qwerty stdio connected |
| PASS | real droid: `droid exec --list-tools` lists the 6 MCP tools as allowed |
| PASS | real droid autonomy: at --auto low the read-only spindoctor_functions runs; spindoctor_run_script (writes reports) stops for permission |
| PASS | real droid exec session (stand-in model): ToolSearch loads the 6 deferred MCP tools; function table returned through Droid |
| PASS | real droid exec: run_script (Bell) and run_preset qc-001 succeed through Droid's MCP client, with TXT/PDF report paths |
| PASS | real droid exec: chat-history theory test -> verdict supported, excerpts recorded, theory PDF written |
| PASS | real droid exec: the Skill tool returns the skill with ${DROID_PLUGIN_ROOT} expanded to the installed plugin folder |
| PASS | real droid exec: stand-in model's last turn shown as the answer |
| PASS | real droid exec: plugin slash command /qwerty-folder expands with $ARGUMENTS |
| PASS | shared E2E through the INSTALLED plugin's mcp.json command (bootstrap finds Droid's install record): SUMMARY 12/12 |
| PASS | real droid: plugin uninstall + marketplace remove leave no spindoctor-qwerty install |

## Shared end-to-end suite through the installed plugin: 12/12

Started with the installed plugin's own `mcp.json` command (`python3 -c <bootstrap>`), which located the plugin through Droid's
install record.

| Result | Check |
|---|---|
| PASS | initialize (server spindoctor-qwerty 1.1.0) |
| PASS | tools/list exposes the 6 tools |
| PASS | function table (Markdown, 19 sections, 298-qubit limits listed) |
| PASS | 241 presets listed |
| PASS | one script per command family (16 families, every table example) |
| PASS | 298-qubit circuit with mcx7 (prepared-factor-Born-Z) |
| PASS | q.folder on mixed .txt/.csv/.json/.qasm folder (+ .md skipped) |
| PASS | theory from a file -> supported, TXT+PDF report |
| PASS | theory from a chat summary + quoted excerpts -> supported |
| PASS | theory from an exported chat transcript -> supported |
| PASS | presets qc-001..qc-025 match the updated 3.1.2 reference (20 identical, 5 documented differences) |
| PASS | TXT+PDF reports valid (255 PDFs, 255 TXT twins) |

## Runs

- Clean room (fresh copy of the staged repo, 2026-10-11 PT): host check 20/20, shared end-to-end 12/12.
