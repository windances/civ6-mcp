// Dump a DSH session log (zstd-compressed JSONL) for retrospective inspection.
//
//   node .tools/dsh-session-dump.mjs <session.jsonl.zstd> [--schema | --user | --tools | --tail N]
//
// The .dsh-home of a game clone keeps its own sessions; this reads them without needing the
// GUI. Node 24 has zlib.zstdDecompressSync.
import { readFileSync } from "node:fs";
import { zstdDecompressSync } from "node:zlib";

const file = process.argv[2];
if (!file) {
  console.error("usage: node .tools/dsh-session-dump.mjs <session.jsonl.zstd> [mode]");
  process.exit(2);
}
const mode = process.argv[3] ?? "--schema";
const tailArg = Number(process.argv[4] ?? 5);

// DSH appends one zstd frame per write, so the file is thousands of frames end to end and a
// single decompress call returns only the first. Every frame starts with the zstd magic
// (0x28 B5 2F FD); scanning for the magic and decoding from each hit recovers all of them - a
// false positive would not decode as a frame, so it is skipped.
const buf = readFileSync(file);
const frames = [];
for (let i = 0; i + 3 < buf.length; i += 1) {
  if (buf[i] === 0x28 && buf[i + 1] === 0xb5 && buf[i + 2] === 0x2f && buf[i + 3] === 0xfd) {
    frames.push(i);
  }
}
const parts = [];
for (const off of frames) {
  try {
    parts.push(zstdDecompressSync(buf.subarray(off)));
  } catch {
    /* not a frame start */
  }
}
const raw = Buffer.concat(parts).toString("utf8");
const lines = raw.split("\n").filter((l) => l.trim());
const events = [];
for (const line of lines) {
  try {
    events.push(JSON.parse(line));
  } catch {
    /* tolerate a partial final line */
  }
}
console.log(`bytes=${raw.length} lines=${lines.length} parsed=${events.length}`);

const kinds = new Map();
const roles = new Map();
for (const e of events) {
  const k = e.type ?? e.kind ?? "?";
  kinds.set(k, (kinds.get(k) ?? 0) + 1);
  const r = e.role ?? e.message?.role;
  if (r) roles.set(r, (roles.get(r) ?? 0) + 1);
}
console.log("kinds:", [...kinds.entries()].sort((a, b) => b[1] - a[1]).slice(0, 20));
console.log("roles:", [...roles.entries()].sort((a, b) => b[1] - a[1]).slice(0, 10));

const text = (e) => {
  const c = e.content ?? e.message?.content ?? e.text ?? "";
  if (typeof c === "string") return c;
  if (Array.isArray(c)) {
    return c
      .map((p) => (typeof p === "string" ? p : p?.text ?? p?.content ?? `[${p?.type ?? "?"}]`))
      .join("\n");
  }
  return JSON.stringify(c).slice(0, 400);
};

if (mode === "--schema") {
  for (const e of events.slice(0, 3)) console.log(JSON.stringify(e).slice(0, 700));
  console.log("--- a middle event ---");
  const mid = events[Math.floor(events.length / 2)];
  if (mid) console.log(JSON.stringify(mid).slice(0, 700));
}

if (mode === "--user") {
  let i = 0;
  for (const e of events) {
    const r = e.role ?? e.message?.role;
    if (r !== "user") continue;
    const t = text(e).replace(/\s+/g, " ").trim();
    if (!t) continue;
    i += 1;
    console.log(`\n[user #${i}] ${t.slice(0, 900)}`);
  }
  console.log(`\ntotal user messages: ${i}`);
}

if (mode === "--tools") {
  const tool = new Map();
  for (const e of events) {
    const name = e.toolName ?? e.name ?? e.tool?.name;
    if (e.type && String(e.type).includes("tool") && name) tool.set(name, (tool.get(name) ?? 0) + 1);
  }
  console.log("tools:", [...tool.entries()].sort((a, b) => b[1] - a[1]).slice(0, 25));
}

if (mode === "--tail") {
  for (const e of events.slice(-tailArg)) {
    const r = e.role ?? e.message?.role ?? e.type ?? "?";
    console.log(`\n=== ${r} ===\n${text(e).replace(/\s+/g, " ").slice(0, 1200)}`);
  }
}
