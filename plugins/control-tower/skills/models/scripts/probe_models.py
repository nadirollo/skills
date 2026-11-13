#!/usr/bin/env python3
"""Find the models each installed agent harness offers, and write them to
~/.config/control-tower/models.json for the dispatch spec approval page.

It starts each harness interactively in a hidden hc terminal (no parent, no
herdr labels), reads its model list from the harness itself, and ends the
terminal. Nothing is sent to a model, so it costs nothing.

  claude   /model picker: aliases, the model each one points at.
  copilot  `/model <unsupported>` prints every model ID; the /model picker
           adds display names, default efforts, and which are unavailable.

Usage: probe_models.py [--out PATH] [--only claude,copilot] [--timeout S]
Exit 0 when every installed harness was probed, 1 when any failed (the file
keeps that harness's previous entry, marked stale), 2 on bad usage.
"""
import argparse
import datetime
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time

HOME = os.path.expanduser("~")
DEFAULT_OUT = os.path.join(HOME, ".config", "control-tower", "models.json")
PROBE_DIR = os.path.join(HOME, ".cache", "control-tower", "model-probe")
HC = shutil.which("hc") or os.path.join(HOME, ".local", "bin", "hc")


def run(argv, timeout=30, check=True):
    return subprocess.run(argv, capture_output=True, text=True, timeout=timeout, check=check).stdout


def hc(*args, timeout=30, check=True):
    return run([HC, *args], timeout=timeout, check=check)


def screen(name, lines=0):
    return hc("read", name, "--lines", str(lines), check=False)


def clean(text):
    """Drop the scrollbar and box characters some harnesses draw at line ends."""
    return "\n".join(re.sub(r"[\s┃│╹╻]+$", "", line) for line in text.splitlines())


def wait_for(name, pattern, timeout, lines=0):
    """Read the terminal until `pattern` shows, or `timeout` seconds pass."""
    end = time.time() + timeout
    text = ""
    while time.time() < end:
        text = clean(screen(name, lines))
        if re.search(pattern, text, re.M):
            return text
        time.sleep(0.5)
    return None


class Session:
    """One hidden, interactive harness session in hc."""

    def __init__(self, harness, argv):
        self.name = ("ct-models-%s-%d" % (harness, os.getpid()))[:32]
        self.argv = argv

    def __enter__(self):
        os.makedirs(PROBE_DIR, exist_ok=True)
        hc("run", "--bg", "--json", "--no-parent", "--no-notify", "--name", self.name,
           "--cwd", PROBE_DIR, "--", *self.argv)
        return self

    def __exit__(self, *exc):
        hc("kill", self.name, check=False)
        time.sleep(0.5)
        hc("rm", self.name, check=False)

    def send(self, text):
        hc("send", self.name, text)

    def keys(self, *keys):
        hc("keys", self.name, *keys)


def help_values(binary, flag):
    """Accepted values of a flag, from the harness's --help."""
    text = run([binary, "--help"], check=False)
    i = text.find(flag)
    if i < 0:
        return []
    chunk = text[i:i + 400]
    m = re.search(r"possible values: ([^\]]+)\]", chunk) or re.search(r"\(([a-z]+(?:, [a-z]+)+)\)", chunk)
    return [v.strip() for v in m.group(1).split(",")] if m else []


def version(binary):
    out = run([binary, "--version"], check=False).strip().splitlines()
    return out[0] if out else ""


# ---------------------------------------------------------------- claude

CLAUDE_ROW = re.compile(r"^\s*(?:❯\s*)?(\d+)\.\s+(\S.*?)\s{2,}(\S.*?)\s*$")


def probe_claude(timeout):
    with Session("claude", ["claude"]) as s:
        text = wait_for(s.name, r"Yes, I trust this folder|Claude Code v", timeout)
        if text is None:
            raise RuntimeError("Claude Code did not start")
        time.sleep(2)
        if "Yes, I trust this folder" in clean(screen(s.name)):
            # Only ever this script's own empty probe folder.
            s.keys("down", "enter")
            if wait_for(s.name, r"Claude Code v", timeout) is None:
                raise RuntimeError("Claude Code did not get past the trust prompt")
            time.sleep(2)
        s.send("/model")
        text = wait_for(s.name, r"Select model", timeout)
        if text is None:
            raise RuntimeError("the /model picker did not open")
        s.keys("esc")
    models = []
    for line in text.splitlines():
        m = CLAUDE_ROW.match(line)
        if not m:
            continue
        name = m.group(2).replace("✔", "").strip()
        desc = m.group(3).strip()
        alias = name.split()[0].lower()
        full = re.search(r"\(([A-Za-z0-9._:/@\[\]-]+)\)\s*$", desc)
        if alias == "default":
            cur = re.search(r"currently ([^)]+)\)", desc)
            label = "default (harness setting%s)" % (": " + cur.group(1) if cur else "")
        else:
            label = name + (" · " + full.group(1) if full else "")
        entry = {"id": alias, "label": label}
        if full:
            entry["model"] = full.group(1)
        if not any(e["id"] == alias for e in models):
            models.append(entry)
    if not any(e["id"] == "default" for e in models):
        models.insert(0, {"id": "default", "label": "default (harness setting)"})
    if len(models) < 2:
        raise RuntimeError("could not read the /model picker")
    efforts = help_values("claude", "--effort") or ["low", "medium", "high", "xhigh", "max"]
    return {"id": "claude", "label": "Claude Code", "version": version("claude"),
            "models": models, "efforts": ["default"] + efforts}


# ---------------------------------------------------------------- copilot



def slug(display):
    s = display.lower()
    s = s.replace("(fast mode)", "fast").replace("(preview)", "")
    s = re.sub(r"[()]", "", s)
    return re.sub(r"\s+", "-", s.strip())


def probe_copilot(timeout):
    with Session("copilot", ["copilot"]) as s:
        text = wait_for(s.name, r"Confirm folder trust|/ commands", timeout)
        if text is None:
            raise RuntimeError("Copilot CLI did not start")
        if "Confirm folder trust" in text:
            # "1. Yes": this session only, and only this script's probe folder.
            s.keys("enter")
            if wait_for(s.name, r"/ commands", timeout) is None:
                raise RuntimeError("Copilot CLI did not get past the trust prompt")
        s.send("/model ct-list-models")
        if wait_for(s.name, r'"ct-list-models" is unsupported', timeout, lines=400) is None:
            raise RuntimeError("Copilot did not print its model list")
        listing = clean(screen(s.name, 600))
        listing = listing[listing.rfind('"ct-list-models" is unsupported'):]
        ids = []
        for m in re.finditer(r'^\s*-\s+"([^"]+)"', listing, re.M):
            if m.group(1) not in ids:
                ids.append(m.group(1))
        s.send("/model")
        picker = wait_for(s.name, r"Search models", timeout) or ""
        s.keys("esc")
    if not ids:
        raise RuntimeError("no model IDs in Copilot's list")
    rows, unavailable, section = {}, set(), ""
    for line in picker.splitlines():
        parts = re.split(r"\s{2,}", line.strip().lstrip("❯").strip())
        if len(parts) == 1 and re.fullmatch(r"(Recommended|New|Other|Unavailable)( models)?", parts[0]):
            section = parts[0] if parts[0].endswith("models") else parts[0] + " models"
            continue
        if len(parts) < 2:
            continue
        if section == "Unavailable models":
            if re.fullmatch(r"[a-z0-9][a-z0-9._-]*", parts[0]):
                unavailable.add(parts[0])
            continue
        # name, [class], context, effort: the class column only shows in some views
        if len(parts) >= 3 and re.fullmatch(r"—|[A-Za-z]+", parts[-1]):
            if slug(parts[0]) in rows:
                continue  # the current model also shows again in its section
            rows[slug(parts[0])] = {"label": parts[0], "group": section or "Current",
                                    "context": parts[-2], "default_effort": parts[-1]}
    efforts = help_values("copilot", "--reasoning-effort") or ["none", "minimal", "low", "medium", "high", "xhigh", "max"]
    models = [{"id": "default", "label": "default (Copilot setting)"}, {"id": "auto", "label": "auto (Copilot picks)"}]
    for mid in ids:
        if mid in unavailable:
            continue
        row = rows.get(mid, {})
        entry = {"id": mid, "label": row.get("label", mid)}
        if row.get("group"):
            entry["group"] = row["group"]
        if row.get("default_effort") and row["default_effort"] != "—":
            entry["default_effort"] = row["default_effort"].lower()
        if row.get("default_effort") == "—":
            entry["efforts"] = ["default"]  # no reasoning effort for this model
        models.append(entry)
    rank = {"Current": 0, "Recommended models": 1, "New models": 2, "Other models": 3}
    models[2:] = sorted(models[2:], key=lambda m: rank.get(m.get("group"), 4))
    return {"id": "copilot", "label": "Copilot CLI", "version": version("copilot"),
            "models": models, "efforts": ["default"] + efforts,
            "unavailable": sorted(unavailable)}


PROBES = {"claude": probe_claude, "copilot": probe_copilot}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--only", default="", help="comma-separated harness ids")
    ap.add_argument("--timeout", type=float, default=45)
    a = ap.parse_args()
    only = [h for h in a.only.split(",") if h]
    bad = [h for h in only if h not in PROBES]
    if bad:
        print("unknown harness: " + ", ".join(bad), file=sys.stderr)
        return 2
    if not os.path.exists(HC):
        print("hc not found", file=sys.stderr)
        return 2
    previous = {}
    try:
        with open(a.out) as f:
            previous = {h["id"]: h for h in json.load(f).get("harnesses", [])}
    except (OSError, ValueError):
        pass
    now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    result, failed = [], []
    for hid, probe in PROBES.items():
        if only and hid not in only:
            if hid in previous:
                result.append(previous[hid])
            continue
        if not shutil.which(hid):
            continue  # not installed: not offered
        try:
            entry = probe(a.timeout)
            entry["probed_at"] = now
            result.append(entry)
            print("%s: %d models" % (hid, len(entry["models"])))
        except Exception as e:  # keep going; report and keep the old entry
            failed.append(hid)
            print("%s: failed: %s" % (hid, e), file=sys.stderr)
            if hid in previous:
                old = dict(previous[hid])
                old["stale"] = True
                result.append(old)
    doc = {"generated_at": now, "machine": socket.gethostname(), "harnesses": result}
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(a.out), prefix=".models-")
    with os.fdopen(fd, "w") as f:
        json.dump(doc, f, indent=2)
        f.write("\n")
    os.chmod(tmp, 0o644)
    os.replace(tmp, a.out)
    print("wrote " + a.out)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
