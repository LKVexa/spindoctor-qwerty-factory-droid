#!/usr/bin/env python3
# SpinDoctor Qwerty 1.1.0 - Factory Droid host check
# Copyright (C) 2026 RUSSELL PHILIP SMITHSON <russellsmithson77@outlook.com>
# SPDX-License-Identifier: GPL-3.0-or-later
# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version. It is distributed WITHOUT ANY WARRANTY; see the LICENSE file for details.
"""Run from the repo root:  python3 tests/droid_host_check.py [--droid PATH] [--out tests/host_check.json]

Static: marketplace + plugin manifests, native Droid layout, front matter, mcp.json (no ${...} references), the MCP bootstrap,
tools/set_python.py. Real host (when the Droid CLI is found: --droid, $DROID or `droid` on PATH), in a throwaway HOME with no
Factory account: `droid plugin marketplace add <this repo>` + `droid plugin install`, `droid mcp list`, `droid exec --list-tools`,
a scripted `droid exec` session against the local stand-in model (tests/stub_llm.py, a BYOK custom model on 127.0.0.1) that calls
the plugin's MCP tools, the skill and a slash command, then the shared end-to-end suite through the INSTALLED plugin's own
mcp.json command, and finally uninstall. Standard library only (Python 3.8+). Nothing here signs in or uses an API key.
"""
import glob, json, os, re, shutil, socket, subprocess, sys, tempfile, time
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); PLUG = os.path.join(ROOT, "spindoctor-qwerty")
R = []
TOOLS = ["spindoctor_run_script", "spindoctor_run_preset", "spindoctor_list_presets", "spindoctor_report", "spindoctor_functions", "spindoctor_test_theory"]


def T(name, ok, detail=""):
    R.append({"check": name, "pass": bool(ok), "detail": str(detail)[:600]})
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else "  -- " + str(detail)[:500])); sys.stdout.flush()


def INFO(msg):
    R.append({"check": "INFO " + msg, "pass": True, "detail": ""}); print("INFO " + msg)


def fm(path):
    t = open(path, encoding="utf-8").read(); m = re.match(r"^---\n(.*?)\n---\n(.*)$", t, re.S)
    if not m: return None, t
    d = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1); d[k.strip()] = v.strip().strip('"')
    return d, m.group(2)


def static():
    mk = json.load(open(os.path.join(ROOT, ".factory-plugin", "marketplace.json"), encoding="utf-8"))
    pj = json.load(open(os.path.join(PLUG, ".factory-plugin", "plugin.json"), encoding="utf-8"))
    ent = mk.get("plugins") or [{}]
    T("marketplace.json: name, owner, one plugin entry with relative source ./spindoctor-qwerty that exists",
      mk.get("name") == "spindoctor-qwerty-factory-droid" and mk.get("owner", {}).get("name") == "RUSSELL PHILIP SMITHSON" and len(ent) == 1
      and ent[0].get("name") == "spindoctor-qwerty" and ent[0].get("source") == "./spindoctor-qwerty" and os.path.isdir(PLUG), mk)
    T("plugin.json: name, version 1.1.0, author RUSSELL PHILIP SMITHSON, license GPL-3.0-or-later, homepage/repository",
      pj.get("name") == "spindoctor-qwerty" and pj.get("version") == "1.1.0" and pj.get("author", {}).get("name") == "RUSSELL PHILIP SMITHSON"
      and pj.get("license") == "GPL-3.0-or-later" and pj.get("repository", "").startswith("https://github.com/"), pj)
    bad = [x for x in (".claude-plugin", "agents", ".mcp.json", "hooks", ".factory-plugin/mcp.json") if os.path.exists(os.path.join(PLUG, x))]
    have = [x for x in ("skills/spindoctor-qwerty/SKILL.md", "commands", "droids/qwerty-helper.md", "mcp.json") if os.path.exists(os.path.join(PLUG, x))]
    T("native Droid layout: .factory-plugin/ + skills/ commands/ droids/ mcp.json at the plugin root; no Claude-layout names, no empty hooks",
      not bad and len(have) == 4, {"unexpected": bad, "present": have})
    d, body = fm(os.path.join(PLUG, "droids", "qwerty-helper.md")); s, sbody = fm(os.path.join(PLUG, "skills", "spindoctor-qwerty", "SKILL.md"))
    cmds = sorted(glob.glob(os.path.join(PLUG, "commands", "*.md"))); cfm = [fm(c) for c in cmds]
    T("front matter: droid name/description/model inherit; skill name/description; %d commands with description; honest limits" % len(cmds),
      d and re.fullmatch(r"[a-z0-9_-]+", d.get("name", "")) and d.get("model") == "inherit" and d.get("description") and body.strip()
      and s and s.get("name") == "spindoctor-qwerty" and "298" in sbody and "not a" in sbody.lower() and len(cmds) == 5 and all(c[0] and c[0].get("description") for c in cfm), [d, s])
    T("plugin-root variable only where Droid expands it (skill and droid bodies), never in commands or mcp.json",
      "${DROID_PLUGIN_ROOT}" in sbody and "${DROID_PLUGIN_ROOT}" in body and not any("PLUGIN_ROOT" in open(c).read() for c in cmds)
      and "PLUGIN_ROOT" not in open(os.path.join(PLUG, "mcp.json")).read())
    mcp = json.load(open(os.path.join(PLUG, "mcp.json"), encoding="utf-8"))["mcpServers"]
    srv = mcp.get("spindoctor-qwerty", {})
    T("mcp.json: one stdio server `python3 -c <bootstrap>`, no ${...} references (Droid treats them as environment variables), no secrets",
      list(mcp) == ["spindoctor-qwerty"] and srv.get("type") == "stdio" and srv.get("command") == "python3" and srv.get("args", [""])[0] == "-c"
      and "${" not in json.dumps(srv) and set(srv.get("env", {})) <= {"PYTHONUTF8", "PYTHONDONTWRITEBYTECODE"}, srv)
    return srv


def mcp_init(cmd, env, cwd):
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, cwd=cwd)
    try:
        p.stdin.write(b'{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"t","version":"1"}}}\n'); p.stdin.flush()
        line = p.stdout.readline(); p.stdin.close(); p.wait(20)
        return json.loads(line)["result"]["serverInfo"] if line else p.stderr.read().decode("utf-8", "replace")[-300:]
    except Exception as e:  # noqa: BLE001
        p.kill(); return str(e)


def bootstrap_checks(srv):
    cmd = [sys.executable, "-c", srv["args"][1]]; tmp = tempfile.mkdtemp(prefix="sdq-boot-")
    try:
        home = os.path.join(tmp, "home"); rec = os.path.join(home, ".factory", "plugins", "installed_plugins"); os.makedirs(rec)
        json.dump({"pluginId": "spindoctor-qwerty@m", "entry": {"installPath": os.path.join(tmp, "old-missing"), "lastUpdated": "2026-01-01T00:00:00Z"}}, open(os.path.join(rec, "a.json"), "w"))
        json.dump({"pluginId": "spindoctor-qwerty@m", "entry": {"installPath": PLUG, "lastUpdated": "2026-10-11T00:00:00Z"}}, open(os.path.join(rec, "b.json"), "w"))
        json.dump({"pluginId": "other@m", "entry": {"installPath": "/nonexistent", "lastUpdated": "2027-01-01T00:00:00Z"}}, open(os.path.join(rec, "c.json"), "w"))
        base = {k: v for k, v in os.environ.items() if k not in ("SPINDOCTOR_QWERTY_ROOT",)}
        a = mcp_init(cmd, dict(base, HOME=home, USERPROFILE=home), tmp)
        b = mcp_init(cmd, dict(base, HOME=os.path.join(tmp, "empty"), USERPROFILE=os.path.join(tmp, "empty"), SPINDOCTOR_QWERTY_ROOT=PLUG), tmp)
        r = subprocess.run(cmd, env=dict(base, HOME=os.path.join(tmp, "empty"), USERPROFILE=os.path.join(tmp, "empty")), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        T("bootstrap: finds the newest installed spindoctor-qwerty record (skips stale/other plugins), honours SPINDOCTOR_QWERTY_ROOT, clear error when not installed",
          isinstance(a, dict) and a.get("version") == "1.1.0" and isinstance(b, dict) and b.get("version") == "1.1.0" and r.returncode != 0 and b"plugin folder not found" in r.stderr, [a, b, r.stderr[-200:]])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def set_python():
    p = os.path.join(PLUG, "mcp.json"); orig = open(p, "rb").read(); sp = os.path.join(ROOT, "tools", "set_python.py")
    try:
        a = subprocess.run([sys.executable, sp, "python"], stdout=subprocess.PIPE); c1 = json.load(open(p))["mcpServers"]["spindoctor-qwerty"]["command"]
        bad = subprocess.run([sys.executable, sp, "python;rm"], stdout=subprocess.PIPE)
        subprocess.run([sys.executable, sp, "python3"], stdout=subprocess.PIPE); same = open(p, "rb").read() == orig
    finally:
        open(p, "wb").write(orig)
    T("tools/set_python.py: python -> command 'python'; python3 restores mcp.json byte for byte; shell metacharacters refused", a.returncode == 0 and c1 == "python" and bad.returncode != 0 and same)


def free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p


def real_droid(droid):
    ver = subprocess.run([droid, "--version"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60).stdout.decode().strip().splitlines()[-1]
    tmp = tempfile.mkdtemp(prefix="sdq-droid-"); home = os.path.join(tmp, "home"); work = os.path.join(tmp, "work"); os.makedirs(home); os.makedirs(work)
    env = {k: v for k, v in os.environ.items() if not k.startswith(("FACTORY_", "DROID_", "XDG_", "SPINDOCTOR_"))}
    env.update(HOME=home, USERPROFILE=home)
    run = lambda *a, **k: subprocess.run([droid] + list(a), cwd=k.get("cwd", work), env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=k.get("timeout", 180)).stdout.decode("utf-8", "replace")
    stub = None
    try:
        mk = os.path.basename(ROOT.rstrip("/\\"))
        o1 = run("plugin", "marketplace", "add", ROOT); o2 = run("plugin", "install", "spindoctor-qwerty@" + mk, "--scope", "user"); o3 = run("plugin", "list", "--scope", "user")
        recs = glob.glob(os.path.join(home, ".factory", "plugins", "installed_plugins", "*.json"))
        inst = json.load(open(recs[0]))["entry"]["installPath"] if recs else ""
        T("real droid %s (no account): marketplace add <repo> + plugin install spindoctor-qwerty@%s --scope user; copied to the plugin cache" % (ver, mk),
          "Successfully added marketplace" in o1 and "Successfully installed" in o2 and "spindoctor-qwerty@" + mk in o3 and os.path.isfile(os.path.join(inst, "skills", "spindoctor-qwerty", "scripts", "spindoctor_mcp.py")), (o1 + o2 + o3)[-500:])
        o = run("mcp", "list")
        T("real droid: `droid mcp list` starts the plugin's MCP server -> spindoctor-qwerty stdio connected", re.search(r"spindoctor-qwerty\s+stdio\s+connected", o), o[-400:])
        # BYOK stand-in model (local, no key) for exec sessions
        port = free_port(); log = os.path.join(tmp, "stub.jsonl"); script = os.path.join(tmp, "script.json")
        sett = os.path.join(home, ".factory", "settings.json"); s = json.load(open(sett)) if os.path.exists(sett) else {}
        s["customModels"] = [{"model": "stub", "displayName": "local stand-in", "baseUrl": "http://127.0.0.1:%d/v1" % port, "apiKey": "local-stub", "provider": "generic-chat-completion-api", "maxOutputTokens": 1024}]
        json.dump(s, open(sett, "w"), indent=1)
        o = run("exec", "-m", "custom:stub", "--list-tools")
        listed = sorted(set(re.findall(r"spindoctor-qwerty___(spindoctor_[a-z_]+)", o)))
        T("real droid: `droid exec --list-tools` lists the 6 MCP tools as allowed", listed == sorted(TOOLS) and o.count("status: allowed") >= 6, o[-500:])
        N = lambda t: "spindoctor-qwerty___" + t
        P1 = lambda x: {"kind": "probability", "outcome": x, "expected": 0.5, "tolerance": 0.05}
        steps = [{"tool": "ToolSearch", "args": {"query": "select:" + ",".join(N(t) for t in TOOLS)}},
                 {"tool": N("spindoctor_functions"), "args": {}},
                 {"tool": N("spindoctor_run_script"), "args": {"script": "q.circuit new bell 2\nq.circuit add h 0\nq.circuit add cx 0 1\nq.circuit run shots 1000 basis z"}},
                 {"tool": N("spindoctor_run_preset"), "args": {"preset_id": "qc-001"}},
                 {"tool": N("spindoctor_test_theory"), "args": {"source": "chat", "text": "Theory: H then CX makes a Bell state; only 00 and 11, about half each.", "excerpts": ["User: does H then CX entangle two qubits?", "Assistant: yes, a Bell state."],
                  "hypothesis": "H(0) then CX(0,1) prepares a Bell state", "prediction": "P(00)=P(11)=0.5", "script": "q.circuit new th 2\nq.circuit add h 0\nq.circuit add cx 0 1\nq.circuit run shots 4000 basis z", "checks": [P1("00"), P1("11")]}},
                 {"tool": "Skill", "args": {"skill": "spindoctor-qwerty"}},
                 {"text": "Done. SpinDoctor is a classical simulation."}]
        # autonomy: read-only tools (readOnlyHint) run at --auto low; Droid treats the writing tools as high impact
        json.dump([{"tool": "ToolSearch", "args": {"query": "select:" + N("spindoctor_functions") + "," + N("spindoctor_run_script")}},
                   {"tool": N("spindoctor_functions"), "args": {"section": "gates"}}, {"tool": N("spindoctor_run_script"), "args": {"script": "q.circuit new a 1"}}, {"text": "low done"}], open(script, "w"))
        stub = subprocess.Popen([sys.executable, os.path.join(HERE, "stub_llm.py"), str(port), log, script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1.0)
        o = run("exec", "-m", "custom:stub", "--auto", "low", "functions", timeout=300)
        lo = [json.loads(l) for l in open(log)] if os.path.exists(log) else []
        lres = [r["tool_results"] for r in lo if r.get("tools")]
        T("real droid autonomy: at --auto low the read-only spindoctor_functions runs; spindoctor_run_script (writes reports) stops for permission",
          len(lres) >= 3 and "| Function |" in json.dumps(lres[2]) and "insufficient permission" in o, o[-300:])
        stub.terminate(); stub.wait(10); open(log, "w").close()
        json.dump(steps, open(script, "w"))
        stub = subprocess.Popen([sys.executable, os.path.join(HERE, "stub_llm.py"), str(port), log, script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1.0)
        o = run("exec", "-m", "custom:stub", "--auto", "high", "Show the SpinDoctor functions, run a Bell circuit and preset qc-001, test the Bell theory we discussed.", timeout=900)
        recs = [json.loads(l) for l in open(log)] if os.path.exists(log) else []
        agent = [r for r in recs if r.get("tools")]
        res = agent[-1]["tool_results"] if agent else []
        txt = lambda x: x if isinstance(x, str) else json.dumps(x)
        R6 = [txt(x) for x in res]
        def has(i, pat): return len(R6) > i and re.search(pat, R6[i]) is not None
        T("real droid exec session (stand-in model): ToolSearch loads the 6 deferred MCP tools; function table returned through Droid",
          len(R6) >= 6 and has(1, r"\| Function \|") and has(1, "298"), R6[1][:300] if len(R6) > 1 else o[-400:])
        T("real droid exec: run_script (Bell) and run_preset qc-001 succeed through Droid's MCP client, with TXT/PDF report paths",
          has(2, r'"ok":\s*true') and has(2, r"\.pdf") and has(3, r'"ok":\s*true') and has(3, r"qc-001"), [R6[2][:200] if len(R6) > 2 else "", R6[3][:200] if len(R6) > 3 else ""])
        pdfs = re.findall(r'"([^"]+theory[^"]*\.pdf)"', R6[4]) if len(R6) > 4 else []
        T("real droid exec: chat-history theory test -> verdict supported, excerpts recorded, theory PDF written",
          has(4, r'"verdict":\s*"supported"') and has(4, r'"excerptsRecorded":\s*2') and pdfs and all(os.path.isfile(p.replace("\\\\", "\\")) for p in pdfs[:1]), R6[4][:300] if len(R6) > 4 else "")
        sk = R6[5] if len(R6) > 5 else ""
        T("real droid exec: the Skill tool returns the skill with ${DROID_PLUGIN_ROOT} expanded to the installed plugin folder",
          (inst + "/skills/spindoctor-qwerty/scripts/spindoctor_cli.py") in sk.replace("\\\\", "/").replace("\\", "/") or (inst.replace("\\", "/") + "/skills") in sk.replace("\\", "/") and "${DROID_PLUGIN_ROOT}" not in sk, sk[:300])
        T("real droid exec: stand-in model's last turn shown as the answer", "classical simulation" in o, o[-300:])
        open(log, "w").close()
        json.dump([{"text": "ok"}], open(script, "w"))
        run("exec", "-m", "custom:stub", "/qwerty-folder /data/my-folder", timeout=300)
        recs = [json.loads(l) for l in open(log)] if os.path.exists(log) else []
        u = json.dumps(recs[-1]["user"]) if recs else ""
        T("real droid exec: plugin slash command /qwerty-folder expands with $ARGUMENTS", 'q.folder run path=\\\\\\"/data/my-folder\\\\\\"' in u or 'q.folder run path=\\"/data/my-folder\\"' in u, u[-300:])
        stub.terminate(); stub.wait(10); stub = None
        # shared E2E through the installed plugin's own mcp.json entry point
        icfg = json.load(open(os.path.join(inst, "mcp.json")))["mcpServers"]["spindoctor-qwerty"]
        e2e_out = os.path.join(HERE, "e2e_results.json")
        r = subprocess.run([sys.executable, os.path.join(HERE, "e2e_mcp.py"), "--server", sys.executable] + icfg["args"]
                           + ["--examples", os.path.join(inst, "skills", "spindoctor-qwerty", "examples", "theory"), "--out", e2e_out],
                           cwd=work, env=dict(env, **icfg.get("env", {})), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=3600)
        t = r.stdout.decode("utf-8", "replace"); m = re.search(r"SUMMARY (\d+)/(\d+)", t)
        T("shared E2E through the INSTALLED plugin's mcp.json command (bootstrap finds Droid's install record): %s" % (m.group(0) if m else "?"),
          r.returncode == 0 and m and m.group(1) == m.group(2), "\n".join(l for l in t.splitlines() if l.startswith("FAIL"))[-600:])
        o4 = run("plugin", "uninstall", "spindoctor-qwerty@" + mk, "--scope", "user"); o5 = run("plugin", "marketplace", "remove", mk); o6 = run("plugin", "list", "--scope", "user")
        T("real droid: plugin uninstall + marketplace remove leave no spindoctor-qwerty install", "spindoctor-qwerty@" not in o6, (o4 + o5 + o6)[-300:])
    finally:
        if stub: stub.kill()
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    a = sys.argv[1:]; opt = dict(zip(a[::2], a[1::2]))
    droid = opt.get("--droid") or os.environ.get("DROID") or shutil.which("droid")
    outp = opt.get("--out", os.path.join(HERE, "host_check.json"))
    srv = static(); bootstrap_checks(srv); set_python()
    if droid:
        real_droid(os.path.abspath(droid) if os.path.exists(droid) else droid)
    else:
        T("Droid CLI found (pass --droid PATH)", False, "not found")
    json.dump({"passed": sum(r["pass"] for r in R), "total": len(R), "python": sys.version.split()[0], "checks": R}, open(outp, "w"), indent=1)
    n = [r for r in R if not r["check"].startswith("INFO")]
    print("HOST CHECK %d/%d passed" % (sum(r["pass"] for r in n), len(n)))
    return 0 if all(r["pass"] for r in n) else 1


if __name__ == "__main__":
    sys.exit(main())
