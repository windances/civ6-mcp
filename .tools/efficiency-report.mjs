// Decision and execution efficiency report from civ6-mcp telemetry.
//
// Measures, per turn: wall-clock duration, how many queries vs mutations, the
// longest silent gap (agent thinking vs waiting on the game), and how much of
// the turn was spent waiting for the turn to advance. Also flags wasted work:
// repeated identical calls inside a turn.
import fs from 'node:fs';
import path from 'node:path';

const dataDir = path.join(process.cwd(), '.civ6-mcp-data');
const want = process.argv[2] ?? process.env.CIV6_GAME;
if (!want) {
  console.error('usage: efficiency-report.mjs <civ>_<seed>   (or set CIV6_GAME)');
  process.exit(2);
}

const files = fs
  .readdirSync(dataDir)
  .filter((f) => f.startsWith('log_') && f.endsWith('.jsonl') && f.includes(want))
  .map((f) => path.join(dataDir, f));

if (!files.length) {
  console.log('no telemetry logs found for', want);
  process.exit(1);
}

let entries = [];
for (const f of files) {
  for (const line of fs.readFileSync(f, 'utf8').split('\n')) {
    if (!line.trim()) continue;
    try {
      const o = JSON.parse(line);
      if (o.ts && o.tool) {
        // ts is unix seconds in most sinks but milliseconds in a few; normalise
        // to seconds so all durations are comparable.
        const raw = Number(o.ts);
        const t = raw > 1e12 ? raw / 1000 : raw;
        if (!Number.isFinite(t)) continue;
        entries.push({
          t,
          tool: o.tool,
          turn: o.turn,
          cat: o.category ?? '?',
          params: JSON.stringify(o.params ?? {}),
        });
      }
    } catch {
      /* skip */
    }
  }
}
entries.sort((a, b) => a.t - b.t);

const fmt = (s) => {
  if (s < 90) return `${Math.round(s)}s`;
  return `${Math.floor(s / 60)}m${String(Math.round(s % 60)).padStart(2, '0')}`;
};

console.log(`game ${want}`);
console.log(`logs: ${files.length}   calls: ${entries.length}`);
const span = entries.at(-1).t - entries[0].t;
console.log(`wall clock: ${(span / 3600).toFixed(1)}h`);

// A gap longer than this is a boundary between two orchestrator runs, not the
// agent thinking. Counting it as thinking time produced a 6-hour "turn".
const RUN_GAP = 900;

// Per-run summary first: throughput is only meaningful inside one run.
console.log('');
console.log('PER RUN');
console.log('  log                                  turns        span    turns/h');
for (const f of files) {
  const es = [];
  for (const line of fs.readFileSync(f, 'utf8').split('\n')) {
    if (!line.trim()) continue;
    try {
      const o = JSON.parse(line);
      if (o.ts && o.tool && o.turn != null) {
        const raw = Number(o.ts);
        es.push({ t: raw > 1e12 ? raw / 1000 : raw, turn: o.turn });
      }
    } catch {
      /* skip */
    }
  }
  if (!es.length) continue;
  es.sort((a, b) => a.t - b.t);
  const tn = [...new Set(es.map((e) => e.turn))].sort((a, b) => a - b);
  const hrs = (es.at(-1).t - es[0].t) / 3600;
  console.log(
    `  ${path.basename(f).replace('log_${want}_', '').replace('.jsonl', '').padEnd(36)} ` +
      `${String(tn.length).padStart(3)}  ${tn[0]}..${tn.at(-1)}  ${hrs.toFixed(2).padStart(6)}h  ` +
      `${hrs > 0.05 ? (tn.length / hrs).toFixed(1).padStart(6) : '   n/a'}`,
  );
}

// Group into turns. Entries with no turn number cannot be attributed.
const turns = new Map();
for (const e of entries) {
  if (e.turn === null || e.turn === undefined) continue;
  if (!turns.has(e.turn)) turns.set(e.turn, []);
  turns.get(e.turn).push(e);
}
const nums = [...turns.keys()].sort((a, b) => a - b);

let totalQuery = 0;
let totalAction = 0;
let totalTurn = 0;
let totalEndWait = 0;
let totalThink = 0;
let dupes = 0;
const rows = [];

for (let i = 0; i < nums.length; i++) {
  const g = turns.get(nums[i]);
  if (g.length < 2) continue;
  g.sort((x, y) => x.t - y.t);
  const q = g.filter((e) => e.cat === 'query').length;
  const a = g.filter((e) => e.cat === 'action').length;
  const et = g.filter((e) => e.tool === 'end_turn').length;

  // Split the turn's silent time into "thinking" (gap before a non-end_turn call)
  // and "waiting" (gap before an end_turn call, i.e. the game processing).
  let think = 0;
  let wait = 0;
  let maxThink = 0;
  let maxWait = 0;
  let skipped = 0;
  for (let k = 1; k < g.length; k++) {
    const gap = g[k].t - g[k - 1].t;
    if (gap > RUN_GAP) {
      skipped += gap;
      continue;
    }
    if (g[k].tool === 'end_turn') {
      wait += gap;
      maxWait = Math.max(maxWait, gap);
    } else {
      think += gap;
      maxThink = Math.max(maxThink, gap);
    }
  }

  // Wasted work: the same tool with the same arguments more than once in a turn.
  const seen = new Map();
  let dup = 0;
  for (const e of g) {
    const key = e.tool + '|' + e.params;
    if (seen.has(key)) dup++;
    seen.set(key, true);
  }
  dupes += dup;

  // Active turn duration: total span minus time that belongs to the gap between
  // two separate orchestrator runs.
  const dur = g.at(-1).t - g[0].t - skipped;

  totalQuery += q;
  totalAction += a;
  totalTurn += dur;
  totalEndWait += wait;
  totalThink += think;
  rows.push({ turn: nums[i], dur, q, a, et, wait, think, maxThink, maxWait, dup, calls: g.length });
}

console.log(`turns: ${rows.length} (${nums[0]}..${nums.at(-1)})`);

const mean = (f) => rows.reduce((s, r) => s + f(r), 0) / rows.length;
const median = (f) => {
  const v = rows.map(f).sort((x, y) => x - y);
  return v[Math.floor(v.length / 2)];
};

console.log('');
console.log('PER TURN              mean    median    worst');
console.log('  duration            ' + fmt(mean((r) => r.dur)).padEnd(8) + fmt(median((r) => r.dur)).padEnd(10) + fmt(Math.max(...rows.map((r) => r.dur))));
console.log('  tool calls          ' + mean((r) => r.calls).toFixed(1).padEnd(8) + median((r) => r.calls).toFixed(0).padEnd(10) + Math.max(...rows.map((r) => r.calls)));
console.log('  queries             ' + mean((r) => r.q).toFixed(1).padEnd(8) + median((r) => r.q).toFixed(0).padEnd(10) + Math.max(...rows.map((r) => r.q)));
console.log('  mutations           ' + mean((r) => r.a).toFixed(1).padEnd(8) + median((r) => r.a).toFixed(0).padEnd(10) + Math.max(...rows.map((r) => r.a)));
console.log('  thinking time       ' + fmt(mean((r) => r.think)).padEnd(8) + fmt(median((r) => r.think)).padEnd(10) + fmt(Math.max(...rows.map((r) => r.think))));
console.log('  end_turn wait       ' + fmt(mean((r) => r.wait)).padEnd(8) + fmt(median((r) => r.wait)).padEnd(10) + fmt(Math.max(...rows.map((r) => r.wait))));
console.log('  longest think gap   ' + fmt(mean((r) => r.maxThink)).padEnd(8) + fmt(median((r) => r.maxThink)).padEnd(10) + fmt(Math.max(...rows.map((r) => r.maxThink))));
console.log('  longest wait gap    ' + fmt(mean((r) => r.maxWait)).padEnd(8) + fmt(median((r) => r.maxWait)).padEnd(10) + fmt(Math.max(...rows.map((r) => r.maxWait))));

console.log('');
console.log('WHERE THE TIME GOES (share of counted turn time)');
const denom = totalTurn || 1;
console.log(`  thinking (LLM)      ${fmt(totalThink)}  ${((totalThink / denom) * 100).toFixed(0)}%`);
console.log(`  waiting on game     ${fmt(totalEndWait)}  ${((totalEndWait / denom) * 100).toFixed(0)}%`);
const other = totalTurn - totalThink - totalEndWait;
console.log(`  between calls       ${fmt(other)}  ${((other / denom) * 100).toFixed(0)}%`);

console.log('');
console.log('CALL MIX');
const total = totalQuery + totalAction;
console.log(`  queries   ${totalQuery}  ${((totalQuery / total) * 100).toFixed(0)}%`);
console.log(`  mutations ${totalAction}  ${((totalAction / total) * 100).toFixed(0)}%`);
console.log(`  repeated identical calls inside a turn: ${dupes}`);

console.log('');
console.log('SLOWEST TURNS');
for (const r of [...rows].sort((x, y) => y.dur - x.dur).slice(0, 6)) {
  console.log(
    `  turn ${String(r.turn).padEnd(4)} ${fmt(r.dur).padEnd(7)} q=${String(r.q).padEnd(3)} a=${String(r.a).padEnd(3)} think=${fmt(r.think).padEnd(7)} wait=${fmt(r.wait).padEnd(7)} calls=${r.calls}`,
  );
}
