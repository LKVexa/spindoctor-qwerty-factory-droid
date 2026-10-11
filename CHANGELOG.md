# Changelog

## 1.1.0 - 2026-10-11

- Engine 1.1.0 at parity with the updated SpinDoctor 3.1.2: 1-298 logical qubits (59 per entangled factor), the `mcx7` gate,
  wide-register Born-Z sampling, `q.folder` with 3.1.2 semantics (.qasm2/.circuit, skipped-file listing, compact status, 128 files /
  4 MiB / 128 commands / 4096 characters), CSV report copies and measurement-CSV fitting equations. All 241 presets replayed.
- New tools `spindoctor_functions` (in-chat function table) and `spindoctor_test_theory` (theory testing from a file, pasted text or
  the chat history, with TXT+JSON+PDF theory reports). New command `/qwerty-folder`.
- **MCP server now starts in real Droid.** 1.0 used `${DROID_PLUGIN_ROOT}` in `mcp.json`; Droid 0.238.0 expands that variable only in
  hook commands, skill and droid bodies and output styles, not in `mcp.json` (it passed the literal text and the server failed to
  start). `mcp.json` now runs a short standard-library bootstrap (`python3 -c ...`) that finds the installed plugin folder from Droid's
  install record (newest `spindoctor-qwerty@*` entry), or from `SPINDOCTOR_QWERTY_ROOT` if you set it.
- `agents/` renamed to `droids/` (1.0 mixed the native `.factory-plugin/` layout with the Claude-layout folder name); the droid now sets
  `model: inherit`. Removed the empty `hooks/hooks.json`. Commands no longer use `${DROID_PLUGIN_ROOT}` (Droid doesn't expand it there);
  they call the tools or point to the skill, whose CLI path Droid does fill in.
- The repo root is now a Droid marketplace (`.factory-plugin/marketplace.json`) with the plugin in `spindoctor-qwerty/`, so
  `droid plugin marketplace add LKVexa/spindoctor-qwerty-factory-droid` works directly.
- MCP annotations: `spindoctor_functions` is now marked read-only (it writes nothing), and every tool says `destructiveHint: false`.
  Droid runs read-only MCP tools at autonomy Low and treats the others as high impact.
- New `tools/set_python.py` for Windows (edits only `spindoctor-qwerty/mcp.json`, refuses shell metacharacters, restores byte for byte).
- Tests: `tests/droid_host_check.py` (static checks, bootstrap tests, and the real Droid CLI: marketplace install, `mcp list`,
  `exec --list-tools`, a scripted `droid exec` session against a local stand-in model, a slash command, the shared end-to-end suite
  through the installed plugin, uninstall).
- License changed from MIT to GPL-3.0-or-later. Author RUSSELL PHILIP SMITHSON. README, NOTICE, COPYRIGHT and SPDX headers added.

## 1.0.0

- First release: `spindoctor-qwerty/` with `.factory-plugin/plugin.json`, skill, commands, `agents/` subagent, empty `hooks.json`,
  `mcp.json` using `${DROID_PLUGIN_ROOT}`.
