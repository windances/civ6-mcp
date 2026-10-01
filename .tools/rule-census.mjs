// Count how often each live rule actually failed across the recorded session transcripts.
//
// The question this answers is the enforcement half of "can the strategy be executed": a rule that
// never fired in a hundred and fifty sessions is not carrying any doctrine yet, and one that fired
// constantly is carrying it by itself.
//
// Only ids that are in `prompts/checks/turn-checks.md` count as live; anything else that appears is
// reported separately, because a retired rule's failures are history rather than enforcement (and
// rule *messages* quote the literal string `CHECK FAILED [id]`, which is not a failure at all).
//
// Usage: node .tools/rule-census.mjs
import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';

const ROOT = '.dsh-home/sessions';
const LIVE = 'prompts/checks/turn-checks.md';

function liveRules() {
  const text = fs.readFileSync(LIVE, 'utf8');
  return new Set([...text.matchAll(/^id:\s*([a-z0-9-]+)\s*$/gm)].map((m) => m[1]));
}

function transcripts(dir) {
  const out = [];
  const walk = (d) => {
    let entries = [];
    try {
      entries = fs.readdirSync(d, { withFileTypes: true });
    } catch {
      return;
    }
    for (const entry of entries) {
      const p = path.join(d, entry.name);
      if (entry.isDirectory()) walk(p);
      else if (entry.name.endsWith('.jsonl.zstd')) out.push(p);
    }
  };
  walk(dir);
  return out;
}

function text(file) {
  const raw = fs.readFileSync(file);
  const parts = [];
  for (let i = 0; i + 4 <= raw.length; i++) {
    if (raw[i] === 0x28 && raw[i + 1] === 0xb5 && raw[i + 2] === 0x2f && raw[i + 3] === 0xfd) {
      try {
        parts.push(zlib.zstdDecompressSync(raw.subarray(i)).toString('utf8'));
      } catch {
        /* skip a bad frame */
      }
    }
  }
  return parts.join('');
}

const live = liveRules();
const failures = new Map();
const retired = new Map();
const achieved = new Map();
let sessions = 0;
let briefed = 0;
let withFailure = 0;

for (const file of transcripts(ROOT)) {
  const body = text(file);
  if (!body) continue;
  sessions++;
  if (body.includes('TURN START')) briefed++;
  let sawFailure = false;
  for (const line of body.split('\n')) {
    for (const m of line.matchAll(/CHECK FAILED\s*\[([a-z0-9-]+)\]/g)) {
      const id = m[1];
      if (id === 'id') continue; // the literal placeholder inside a rule's own message
      if (live.has(id)) {
        failures.set(id, (failures.get(id) ?? 0) + 1);
        sawFailure = true;
      } else {
        retired.set(id, (retired.get(id) ?? 0) + 1);
      }
    }
    for (const m of line.matchAll(/CHECK ACHIEVED\s*\[?([a-z0-9-]+)/g)) {
      achieved.set(m[1], (achieved.get(m[1]) ?? 0) + 1);
    }
  }
  if (sawFailure) withFailure++;
}

console.log(`transcripts: ${sessions}; with a TURN START briefing: ${briefed}; with a live rule failing: ${withFailure}`);
console.log('');
console.log('live rule                        failures   sessions?   achieved');
const ranked = [...live].sort((a, b) => (failures.get(b) ?? 0) - (failures.get(a) ?? 0));
for (const id of ranked) {
  console.log(
    `  ${id.padEnd(32)} ${String(failures.get(id) ?? 0).padStart(8)} ${String(achieved.get(id) ?? 0).padStart(11)}`,
  );
}
console.log('');
console.log('never fired in any recorded session:');
console.log('  ' + ranked.filter((id) => !failures.has(id)).join(', '));
console.log('');
console.log('retired ids still visible in old transcripts:');
for (const [id, n] of [...retired.entries()].sort((a, b) => b[1] - a[1])) {
  console.log(`  ${id.padEnd(40)} ${n}`);
}
