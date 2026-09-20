# civ6-mcp DSH Orchestrator — Windows setup record

Repo: `https://github.com/windances/civ6-mcp` (fork of `lmwilki/civ6-mcp`)
Workspace: `C:\mine\mine\ws_dsh\civ6`
Target mode: **DeepSeek Harness orchestrator** (parent agent + 4 read-only advisors)

This file records what was installed, what had to be patched for Windows, and the
two actions that still need a human.

---

## 1. Status

| Component | State |
|---|---|
| Repo source | Downloaded via `codeload.github.com` zip (no `.git` — see §6) |
| Node.js | v24.11.1 (meets the `>=24` engine) |
| DSH | `@deepseek-ai/dsh@0.1.2-rc.1` in `node_modules/` — `dsh --version` replies `0.1.2-rc.1` |
| `uv` | 0.12.17 — project-local at `.tools/bin/uv.exe` (plus extensionless `.tools/bin/uv`), **and installed globally on PATH** (see §7) |
| Python env | `.venv` on Python 3.12.10, `civ-mcp` entry point present |
| Static gate | `npm run qualify` — **PASS** (76 tools inventoried) |
| Orchestrator tests | **19/19 PASS** |
| MCP stdio handshake | **PASS** — 75 tools, `run_lua` correctly absent |
| DSH overlay resolve | **PASS** (`--dump-config`) |
| Python suite | 96 passed / 3 blocked by the agent sandbox (see §6) |
| **FireTuner on :4318** | **WORKING** — verified 2026-09-19: `netstat` shows `127.0.0.1:4318 LISTENING`; the adapter read live state (turn 133, China, 4 cities, 15 units) |
| **CivBench scenario saves** | **INSTALLED** — `0A_GROUND_CONTROL`, `0B_SNOWFLAKE`, `0C_CRY_HAVOC` copied into the game's `Saves\Single` (22 saves listed in total) |
| **`DEEPSEEK_API_KEY`** | **NOT SET — action required (last blocker)** |

Qualification totals: 76 tools available to a plain MCP client; 75 once the DSH
overlay sets `CIV_MCP_DISABLE_LUA=1`, which is the intended safety control.

---

## 2. Required actions (only you can do these)

### 2a. Enable the FireTuner TCP interface — DONE ✅

Confirmed working. This section is retained as a reference for the next time the
setting is lost (e.g. a fresh install or a reset `AppOptions.txt`).

**Config file location on this machine** (the README's documented path is wrong
here — see the note below):

```
C:\Users\pala\AppData\Local\Firaxis Games\Sid Meier's Civilization VI\AppOptions.txt
```

Under the `[Debug]` section it must contain `EnableTuner 1`. As of 2026-09-19 that
is **already set**:

```
[Debug]
;Enable FireTuner.
EnableTuner 1
```

> **Why the README's path misleads:** upstream says to edit
> `Documents\My Games\Sid Meier's Civilization VI\AppOptions.txt`. On this
> install, `C:\Users\pala\OneDrive\文档\My Games\Sid Meier's Civilization VI\`
> holds only **saves and mods** — `AppOptions.txt` does not exist there at all.
> This Civ 6 build keeps **configuration** under
> `%LOCALAPPDATA%\Firaxis Games\Sid Meier's Civilization VI\` (alongside
> `UserOptions.txt`, `GraphicsOptions.txt`, `SoundOpts.txt`, `InputSettings.json`)
> and **saves** under OneDrive-redirected Documents. Edit the LocalAppData file.

**The setting only takes effect at launch.** The tuner listener is created during
startup, so toggling "Tuner (disables achievements)" in the Options menu writes
`EnableTuner 1` to the file but does **not** open the port until you restart the
game. If `AppOptions.txt` has a newer timestamp than the game process start time,
that is exactly what happened — restart Civilization VI, reload your save, then
re-test.

Recommended settings at the same time:

| Setting | Value | Why |
|---|---|---|
| Tuner | Enabled | Required — opens the TCP debug port; disables achievements |
| Auto End Turn | Disabled | The agent decides when turns end |
| Windowed mode | Recommended | Watch the agent play; needed for OCR save loading |

Then confirm the port is actually open. **Use the project's own test — it is the
definitive check** (it performs the real FireTuner handshake, not just a port
probe):

```powershell
cd C:\mine\mine\ws_dsh\civ6
.\.venv\Scripts\python.exe scripts\test_connection.py
```

With the Tuner off it prints `FAIL — Connection refused.`; once enabled it reports
a successful handshake and lists Lua states such as `GameCore_Tuner` and `InGame`.

If you just want a quick port probe, **use `netstat`**:

```powershell
netstat -ano | findstr :4318                              # any output = listening
```

> **Do not use `Get-NetTCPConnection` on this machine — it returns false
> negatives.** Verified 2026-09-19: `netstat -ano` reported
> `TCP 127.0.0.1:4318 LISTENING 12004` and a raw socket connected successfully,
> while `Get-NetTCPConnection -LocalPort 4318` returned **nothing in any state**.
> The cmdlet's data source appears to be blocked in this environment (same class
> of issue as the directory-enumeration restriction noted in §6), so it will tell
> you the tuner is down when it is fine.

`Test-NetConnection` is unreliable for a different reason — it is a `NetTCPIP`
module cmdlet, so it is absent from cmd.exe and from sessions where that module is
not loaded. It may also inherit the same false-negative behaviour above.

Or a PowerShell 5.1-safe socket probe (do **not** use the `??` null-coalescing
operator here — that is PowerShell 7+ only and this box runs 5.1):

```powershell
$c = New-Object Net.Sockets.TcpClient
try { $c.Connect('127.0.0.1', 4318); 'OPEN' } catch { 'CLOSED' } finally { $c.Close() }
```

> **`CLOSED` from that probe does not mean the tuner is down.** It serves one connection
> at a time, so a second client is refused while the port is listening and busy.
> `netstat -ano | findstr :4318` shows that case as `ESTABLISHED` with the client's pid,
> and `get_game_status` reports it as `tuner_busy` — verified 2026-09-20 with an agent
> playing while a second process was refused. See **§ FireTuner serves one connection**.

> **If port 4318 never opens:** the *Sid Meier's Civilization VI SDK* Steam tool
> is not installed on this machine (only app `289070`, the base game). The base
> install does ship `Debug\Civ6TunerPlugin.dll`, which is usually enough for a
> direct client like civ6-mcp, so try the menu route first. If the port stays
> closed, install the SDK from Steam → Library → filter by **Tools**, then
> restart. Also make sure `FireTuner.exe` (the SDK's GUI) is **not** running —
> the game accepts only one tuner connection.

### 2b. Export your DeepSeek key

Do this in your own terminal so the key never passes through chat:

```powershell
$env:DEEPSEEK_API_KEY = "sk-..."        # current session only
# or persist for your user account:
[Environment]::SetEnvironmentVariable("DEEPSEEK_API_KEY", "sk-...", "User")
```

---

## 3. How to run

### Headless — one turn

```powershell
cd C:\mine\mine\ws_dsh\civ6
$env:DEEPSEEK_API_KEY = "sk-..."
npm run dsh:play:win
# or with a custom task:
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-dsh-headless.ps1 "Play one complete turn using the civ6-orchestrator skill."
```

### Web interface

```powershell
npm run dsh:web:win
```

Then create a **Standard** agent and ask it to use the `civ6-orchestrator` skill.

### Re-verify the installation (no key, no game needed)

```powershell
npm run qualify
node --test --experimental-test-isolation=none test\dsh\*.test.mjs
.\.venv\Scripts\pytest.exe tests -q          # run from a normal terminal
.\.venv\Scripts\python.exe scripts\qualify-mcp.py
```

### Why the `:win` scripts exist

On this machine `bash` resolves to **WSL bash** (`C:\WINDOWS\system32\bash.exe`).
The upstream README explicitly warns against running civ6-mcp from WSL (unreliable
WSL2↔Windows networking; failed tuner connections lock up the game). The `.ps1`
launchers perform the identical steps — project-local `DSH_HOME`, telemetry
disabled, overlay applied — without going through WSL. `npm run dsh:play` and
`npm run dsh:web` (the POSIX ones) will still route through WSL; prefer the
`:win` variants. Git Bash (`C:\Program Files\Git\bin\bash.exe`) also works and is
not WSL, if you prefer the `.sh` scripts and invoke bash by full path.

---

## 4. Windows portability fixes applied

These are real bugs on a non-UTF-8-locale Windows; each was confirmed by a
failing command before being fixed.

| File | Change | Symptom fixed |
|---|---|---|
| `src/civ_mcp/version.py` | `read_text(encoding="utf-8")` | `import civ_mcp` died with `UnicodeDecodeError: 'gbk' codec can't decode byte 0x94` — `pyproject.toml` contains an em dash and this box's locale encoding is **cp936** |
| `src/civ_mcp/diary.py` | `read_text(encoding="utf-8")` ×2, `open(..., encoding="utf-8")` | The diary is agent-authored text; would crash on any non-GBK character. This is your cross-session memory file |
| `src/civ_mcp/game_launcher.py` | `open(vdf, encoding="utf-8", errors="replace")` | Steam `libraryfolders.vdf` locale-decoded |
| `src/civ_mcp/game_launcher.py` | win32 save path resolved via `SHGetFolderPathW(CSIDL_PERSONAL)`, falling back to the registry `User Shell Folders\Personal`, then `~/Documents` | `~/Documents` is only a guess. This machine's Documents is **OneDrive-redirected** to `C:\Users\pala\OneDrive\文档`, so `SINGLE_SAVE_DIR` resolved to `C:\Users\pala\Documents\...` — a path that **does not exist**. `install_saves.py` would have copied saves where the game never reads them, and `list_saves` globbed an empty directory |
| `scripts/qualify-static.mjs` | `fileURLToPath()` instead of `URL.pathname` | `URL.pathname` yields `/C:/...`, so `join()` produced `C:\C:\...` and `npm run qualify` died with `ENOENT` |
| `scripts/qualify-mcp.py` | Reader thread + `queue.Queue` instead of `select()`, and `Popen(..., encoding="utf-8", errors="replace")` + `PYTHONUTF8=1` for the child | (a) `select()` cannot poll a pipe on Windows → `OSError: [WinError 10093] WSAStartup`. (b) With `text=True` alone the child's JSON-RPC output was decoded with the locale codec → `UnicodeDecodeError: 'gbk' codec can't decode byte 0x94`, so `npm run qualify:mcp` failed on this machine |
| `dsh/civ6.cordis.yml` | Added `PYTHONUTF8: '1'` to the `mcp-civ6` env | Belt-and-braces against any remaining locale-encoded text I/O inside the adapter |

### The missing `launcher-windows` extra broke every hang recovery (found 2026-09-20)

`game_launcher.restart_and_load()` / `load_save_from_menu()` drive the main menu
with Windows Runtime OCR and pywin32 `PrintWindow`. Those live in an **optional**
extra, so a plain `uv sync` installs a server that can read the game but can never
recover it:

```powershell
# required on Windows — not part of the base dependencies
uv pip install -e ".[launcher-windows]"
```

Symptoms when it is absent (both observed on 2026-09-20, T109 and T111):

- `end_turn` returns `HANG:<turn>:<save>` and the built-in auto-recovery answers
  `HANG RECOVERY FAILED at T<turn>: restart_and_load threw an exception` — the
  `winrt` import inside `_ocr_winrt()` raises, and the running agent is then left
  to hand-recover.
- The game is relaunched but lands on the **main menu** with the save never
  loaded, so the turn never advances.

The imports are lazy (inside the functions), so installing the extra fixes a
*running* server with no restart.

### Hang diagnosis before recovery (2026-09-20)

The AI-turn hang is the single largest cost in a long game: **six hangs on
2026-09-20 alone** (T20, T37, T91 ×2, T107, T109, T111), every one of them
587–591 s, i.e. ~5% of turns and roughly an hour of wall clock. They are not
caused by anything the agent does — across the whole day there was exactly one
war declaration, at T111, and the other five hangs have no diplomatic action
anywhere near them.

The recovery path used to kill and relaunch the game immediately, which destroys
the only evidence of *why* the turn stopped. Now `end_turn` records that evidence
first:

- `server.py::_diagnose_hang(turn)` writes one JSON line per hang to
  `hang_diagnosis.jsonl` in the MCP data dir: window rect, whether the window was
  visible / minimised / in the foreground, which window *was* in the foreground,
  and the first 25 OCR lines of the screen. Deliberately **Lua-free** — the poll
  loop's own comments note that extra InGame queries during an AI turn are
  themselves a hang trigger, so this costs only a window snapshot and one OCR pass.
- `server.py::_hang_window_unfocused()` then decides whether to retry in place.
  Civ VI does not advance an AI turn while its window is in the background, and
  the poll loop never checked for that. When — and only when — the window had
  actually lost focus (or was minimised), the server re-focuses it and retries
  `end_turn` once before paying for a restart. The common case adds no extra wait,
  because a focused window skips the branch entirely.

Read the next hang from `hang_diagnosis.jsonl` rather than re-deriving it from a
ten-minute silence.

### The launcher only read an English main menu — FIXED 2026-09-20

**Correction to an earlier note in this file.** The `load_game_save` failure below
was first written up here as the cause of the 2026-09-20 outage. It was not. The
auto-recovery had already thrown on the missing `winrt` import *before* it could
navigate anything, and the relaunched game resumed its own autosave by itself,
so play continued at T111 → T113 unattended. This section is still a real latent
blocker — it just was not the one that bit that day.

The failure, as actually observed:

```
load_game_save("0_MCP_0111")
-> FAILED: Could not find 'Single Player' on main menu. Is the game at the main menu?
```

Cause, verified two ways:

- `_navigate_to_save_sync()` searched only English literals (`"Single Player"`,
  `"Load Game"`, the `"Autosaves"` filter) and there was **no localization layer
  anywhere** in `src/civ_mcp` — the only `language` reference in the package was
  the OCR engine's `try_create_from_user_profile_languages()`.
- `%LOCALAPPDATA%\Firaxis Games\Sid Meier's Civilization VI\AppOptions.txt`:

  ```
  [Language]
  SteamLanguage  schinese
  DisplayLanguage zh_Hans_CN
  ```

  The UI is Simplified Chinese, so the string `Single Player` never appears on
  screen. The window capture was always fine — capturing a live screen and
  OCR'ing it returns real Chinese UI text.

**Fix applied** (keeps the Chinese UI; chose this over switching the game to
English):

| File | Change |
|---|---|
| `src/civ_mcp/game_launcher.py` | `_MENU_LABELS` maps each logical control to every spelling it can appear under — `single_player` → `单人模式`, `load_game` → `加载游戏`, `continue` → `继续`, `autosaves` → `自动保存`. The Chinese strings are the game's own, joined out of `Vanilla_zh_Hans_CN.xml` by Tag (`.tools/join-loc-strings.py`), not transliterations |
| `src/civ_mcp/game_launcher.py` | `_find_text` / `_wait_for_text` / `_click_text` accept a label *list*; `_label_matches` compares again with spaces removed, because the Windows OCR engine returns CJK one glyph per word (`单 人 模 式`) |
| `src/civ_mcp/game_launcher.py` | `_normalize` trim was `[^a-z0-9]`, which **deleted every non-ASCII character** — both sides then normalized to `""` and compared equal. Now Unicode-aware; verified byte-identical on English inputs (`.tools/check-normalize.py`) |
| `src/civ_mcp/game_launcher.py` | CONTINUE lookup uses `prefer_bottom`, since `继续` is an ordinary word and the leader-screen blurb can contain it |
| `src/civ_mcp/game_launcher.py` | The misleading `"Is the game at the main menu?"` message now says the game may still be loading or already in-game |
| `src/civ_mcp/server.py`, `scripts/menu_audit.py` | `_auto_boot`'s CONTINUE click and the menu-audit tool use the same label table |
| `tests/test_menu_labels.py` | 21 tests, including real Windows-OCR-shaped input (`单 人 模 式`) and a regression set proving the English path is unchanged |

Verified against real OCR output from this machine (`.tools/e2e-real-ocr.py`): on
a live capture containing `继 续`, the localized label matches at `exact=True`
while the old English `"CONTINUE"` does not.

**Caveat:** the main-menu labels (`单人模式`, `加载游戏`, `自动保存`) come from the
game's localization database, but the *positive* live check on this machine only
covered `继续`, which was on screen at the time. The main-menu strings could not
be exercised without interrupting a running game, so the next recovery that lands
on the main menu is the real test of those three.

New files (additive only):

- `scripts/run-dsh-headless.ps1`, `scripts/run-dsh-web.ps1` — WSL-free launchers
- `scripts/civ6-clean.ps1` — stop the game, the MCP and the agent, and clear the
  stale heartbeat; never touches the Web GUI (see "Stopping a session cleanly")
- `package.json` — added `dsh:play:win` / `dsh:web:win`
- `.tools/bin/uv.exe` + `.tools/bin/uv` — uv 0.12.17
- `.venv/bin/python`, `.venv/bin/pytest` — Git Bash shims (upstream scripts expect
  the POSIX `.venv/bin/` layout; uv creates `.venv/Scripts/` on Windows)

---

## 5. Network notes (important on this machine)

This network is in China and PyPI's CDN is **severely throttled**:

| Host | Measured speed |
|---|---|
| `files.pythonhosted.org` (PyPI CDN) | **0.05 MB/s** |
| `pypi.tuna.tsinghua.edu.cn` (TUNA) | **38.7 MB/s** |
| `registry.npmjs.org` | fast (522 packages in 13s) |
| `github.com` release assets (`objects.githubusercontent.com`) | unusable (connection reset) |

Consequences and workarounds:

- `npm install` must use a **workspace-local cache**; npm's default cache lives
  outside the workspace and is denied here:
  `npm install --ignore-scripts --cache .npm-cache`
- `--ignore-scripts` was required: a `@google/genai` lifecycle script aborted the
  install with `spawn EPERM`. The 522 packages installed fine without it.
- `uv sync` completed quickly because it was pointed at TUNA:
  ```powershell
  $env:UV_INDEX_URL = "https://pypi.tuna.tsinghua.edu.cn/simple"
  .\.tools\bin\uv.exe sync --project .
  ```
  If you ever re-sync and it crawls, set that variable first. `uv.lock` pins
  absolute `files.pythonhosted.org` URLs, so the mirror variable matters.
- `git clone` over HTTPS fails (`schannel: AcquireCredentialsHandle failed:
  SEC_E_NO_CREDENTIALS`). The **openssl** backend works:
  `git -c http.sslBackend=openssl clone ...`

---

## 6. Known leftovers / caveats

- **No `.git` directory.** The repo was fetched as a zip because `git clone` was
  unusable on this network. If you want history: `git init` and add a remote, or
  re-clone with `-c http.sslBackend=openssl` (a shallow clone did start working
  once the openssl backend was used).
- **`CLAUDE.md` / `GEMINI.md` are missing.** Upstream these are symlinks to
  `AGENTS.md`; zip extraction cannot create them on Windows. Recreate if wanted:
  `New-Item -ItemType HardLink -Path CLAUDE.md -Target AGENTS.md`
- **The sandbox blocks the system temp directory**, so pytest's temp factory used to fall
  back to the workspace root. `pyproject.toml` now pins `basetemp = ".pytest-tmp"` and turns
  the cache provider off (`addopts = "-p no:cacheprovider"`), because the cache's atomic write
  also stages through the system temp and left an unreadable `pytest-cache-files-*` directory
  behind on **every** run - 169 of them had accumulated, and they cannot be deleted from
  inside the sandbox (`Access is denied`, even for the owner; they came back with
  `removed: 169 failed: 0` only under full access). Tests themselves use plain `.tools/`
  scratch paths rather than `tmp_path`, and the full suite runs clean from the workspace:
  `373 passed`.
- **Undeletable junk dirs**: `.tmp` contains pip temp dirs with deny-ACLs that cannot be
  reset without elevation (`icacls /reset` → "Access is denied"). They are inert. Delete them
  from an elevated prompt if they bother you.
- **`node_modules` was installed with `--ignore-scripts`.** DSH and the
  orchestrator tests work, but if you ever hit a missing native binary from a
  package that needed a postinstall, re-run `npm install --cache .npm-cache`
  from a normal (non-sandboxed) terminal.
- `.venv/`, `.tools/`, `.uv-cache/`, `.dsh-home/`, `.civ6-mcp-data/` are
  gitignored upstream; `.npm-cache/` is not in `.gitignore` if you later add a
  remote.

---

## 7. Global `uv` command

The upstream README's install step is `uv sync`, and `.mcp.json` (the Claude
Code / Claude Desktop path) invokes a bare `"command": "uv"`. Neither works with
only the project-local copy, so `uv` was installed globally:

```
C:\Users\pala\AppData\Local\Programs\Python\Python312\Scripts\uv.exe
C:\Users\pala\AppData\Local\Programs\Python\Python312\Scripts\uvx.exe
```

**No PATH or registry change was needed** — that directory is the Python 3.12
`Scripts` folder, which was already on the user PATH. Verify from anywhere:

```powershell
uv --version     # uv 0.12.17
uvx --version    # uvx 0.12.17
```

Both now work, from any directory:

```powershell
cd C:\mine\mine\ws_dsh\civ6
uv run python scripts/test_connection.py      # README's documented command
uv run --directory . civ-mcp                  # what .mcp.json launches
```

Notes:

- This is a plain copy of the same 0.12.17 binary used at `.tools/bin/uv.exe`, so
  the two cannot drift until you update one of them.
- `uv` here is a **standalone binary, not a Python package** — it was extracted
  from the PyPI wheel because GitHub release downloads are blocked on this
  network (§5). `pip install uv` would also work but would download from the
  throttled PyPI CDN unless you pass the TUNA index.
- The DSH overlay still points at `.tools/bin/uv` and is unaffected by this.
- To uninstall: delete those two `.exe` files. Nothing else was modified.

---

## 8. Verified working: Git Bash (not WSL)

The repo's POSIX entry points were verified end-to-end under **Git Bash**
(`MINGW64_NT-10.0`, bash 5.3.15) — `uname` confirms MINGW64, and `WSL_DISTRO_NAME`
is empty, so this is *not* WSL. The test deliberately ran with `PYTHONUTF8`
unset and `PYTHONIOENCODING` cleared, to prove the repo works on a cp936 machine
without environment hacks.

| Check | Result |
|---|---|
| `.venv/bin/python` shim | `-x OK` → Python 3.12.10; `import civ_mcp` OK |
| `.venv/bin/pytest` shim | `-x OK` |
| `node_modules/.bin/dsh` | `-x OK` → 0.1.2-rc.1 |
| `.tools/bin/uv` (extensionless PE) | `-x OK` → uv 0.12.17 |
| `bash scripts/qualify-mcp.sh` | **PASS** — 75 tools, `run_lua` disabled |
| `bash scripts/dump-dsh-config.sh` | **PASS** — overlay resolves |
| `bash scripts/run-dsh-headless.sh` | Starts the civ6 MCP server, then stops at `MISSING_CREDENTIAL` (no key set) |

So the bash toolchain is sound. The only outstanding item is the LLM credential.

### Running from bash

Git Bash works and is Windows-native, so exported variables **do** reach the
child processes:

```bash
cd /c/mine/mine/ws_dsh/civ6
export DEEPSEEK_API_KEY="sk-..."      # or use the credential file in §2b
bash scripts/run-dsh-headless.sh "Play one complete turn using the civ6-orchestrator skill."
```

**Do not run this from WSL.** Even though `bash` on PATH resolves to
`C:\WINDOWS\system32\bash.exe` (WSL), that path puts the process inside Linux,
where it cannot inherit the Windows environment and where WSL2↔Windows networking
breaks the tuner on `127.0.0.1:4318`. Always invoke Git Bash explicitly
(`C:\Program Files\Git\bin\bash.exe`) or use the `npm run dsh:play:win` launcher.

The failure mode if you do run it under WSL is worth recognizing, because the
error does not mention WSL at all:

```
/mnt/c/mine/mine/ws_dsh/civ6/node_modules/.bin/dsh: 15: exec: node: not found
```

Two clues identify it: the **`/mnt/c/...`** path, and line 15 of the npm shim.
`node_modules/.bin/dsh` only applies its `cygpath` path conversion when
`uname` matches `*CYGWIN*|*MINGW*|*MSYS*`; under WSL `uname` is `Linux`, so it
skips that branch and falls through to `exec node`, which a bare distro does not
have installed.

`scripts/run-dsh-headless.sh` and `run-dsh-web.sh` now **refuse to run under
WSL** (detecting `WSL_DISTRO_NAME` or `microsoft`/`wsl` in `/proc/version`) and
exit 2 with the Git Bash invocation printed, instead of surfacing that cryptic
Node error. Verified: the guard fires on both WSL signatures and does not
interfere with normal Git Bash operation.

### Startup prompts: read by the agent, never passed as an argument

Startup prompts live in `prompts/tasks/` as `.zh.txt` / `.en.txt` pairs, one pair
per situation:

| Pair | Use it when |
|---|---|
| `continue-from-t59.{zh,en}.txt` | resuming after a **deliberate rollback**: it names the turn, forbids rolling forward, and allows a load only to recover the current turn |
| `resume-after-crash.{zh,en}.txt` | resuming after the **game exited abnormally**: launch it, load the newest autosave, verify the loaded turn against the save's name, rebuild state, carry on |

**`-TaskFile` / `--task-file` does not pass the file's text as the task.** It
passes a one-line pointer, and the agent reads the file with its own read tool:

```
Read prompts/tasks/continue-from-t59.zh.txt and carry out every instruction in it before doing anything else.
```

That indirection is not a style choice, it is the only thing that works. The task
reaches dsh as a process argument, and this box corrupts long text on that hop in
two independent ways. Both are measurable with `.tools/_argvprobe.cmd` and
`.tools/_argvprobe.mjs`:

| Prompt passed as text | via `node.exe` directly | via the `dsh.cmd` shim |
|---|---|---|
| `zh` — 385 chars, 4 ASCII `"` | 381 chars: every `"` deleted | 80 bytes: the first line only |
| `en` — 1130 chars, 2 ASCII `"` | 1128 chars, split into 3 arguments that the CLI rejoins with spaces | 80 bytes: the first line only |

The shim failure is silent: cmd.exe ends the command line at the first newline, so
dsh receives less task than was written and never complains. Bypassing the shim is
not a fix either — Windows PowerShell does not escape embedded `"` when it builds a
native command line, so the quotes vanish outright, and when they are surrounded by
spaces the argument also splits into pieces that `program.args.join(' ')` in the
headless bundle reassembles with spaces.

A pointer is short, single-line and pure ASCII, which is byte-exact through both
hops (109 characters, digest verified), and it takes the command-line length limit
off the table entirely. Inline task arguments still work for short one-liners, and
are now **rejected outright** if they contain a newline or a double quote instead
of being silently truncated.

One consequence is worth stating plainly: because the launcher no longer carries
the prompt text, **the file's encoding stops mattering to the shell**. A Chinese
prompt launches exactly as safely as an English one, from either launcher, and
the bash launcher no longer warns about non-ASCII. The zh/en pair is now a
language preference rather than a launcher constraint.

The Chinese file carries a **UTF-8 BOM**, and that is load-bearing rather than
cosmetic. This box's code page is cp936, so Notepad, PowerShell 5.1's
`Get-Content` (which decodes BOM-less UTF-8 with the ANSI code page and mangles
every CJK character), and any editor configured for GBK all render a BOM-less
UTF-8 file as mojibake. The BOM is what makes them detect UTF-8. The English file
must not have one: it is pure ASCII, so a BOM would be pointless.

**Editing that file with a tool that round-trips decoded text silently drops the
BOM**, which puts the mojibake straight back. That is not hypothetical — it
happened while adding a paragraph to this very prompt. If `Get-Content` starts
showing `缁х画褰撳墠...` again, the content is fine and only the prefix is missing:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .tools\ensure-utf8-bom.ps1 `
  prompts\tasks\continue-from-t59.zh.txt
```

`-Check` reports without writing and exits 1 when the BOM is absent; both test
suites assert it, so a dropped BOM turns a suite red instead of reaching a user.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-dsh-headless.ps1 `
  -TaskFile prompts\tasks\continue-from-t59.zh.txt
```

```bash
bash scripts/run-dsh-headless.sh --task-file prompts/tasks/continue-from-t59.zh.txt
```

### Resuming after an abnormal exit

`resume-after-crash.{zh,en}.txt` is shaped by three things that are easy to get
wrong, and each one is a rule in the prompt rather than something the agent is
expected to infer.

**The newest autosave is the current position, not a rollback.** `end_turn` writes
`0_MCP_<turn>` when the turn *begins*, so the newest file holds the state at the
start of the turn you were on. Loading it costs at most the actions of the turn in
progress and no completed turn — which is why the prompt can say "this is not a
rollback" while the rollback prompt says the opposite about the same operation.

**Which save is "newest" comes from the filesystem, not from the name.**
`list_saves` is a pure directory scan sorted by date, newest first, so entry 1 is
the answer. Sorting by the number in the filename is wrong after any rollback, and
entry 1 is what the pruning in `cleanup_old_autosaves` also uses.

**The verification is the save name against the loaded turn.** `0_MCP_0077` must
load as turn 77, and the prompt stops the run if it does not. This is deliberate:
`get_diary` clamps to the live turn, so if you accidentally load a much earlier save
the diary will hide the later rows and *look* consistent. Comparing a filename to
`get_game_overview` cannot be fooled that way.

The prompt carries **no turn number**, so the same file is reused for every crash
without editing — and a stale number is what would otherwise send the agent looking
for a position that does not exist. It also tells the agent that the
menu-navigation step after `launch_game` may report an error while the game is in
fact coming up, because that has been observed, and to retry a failed load at most
once before stopping rather than looping.

**Step 0 is to ask, not to act.** `get_game_status` reports one of `not_running`,
`starting`, `in_game`, `leader_screen`, `main_menu`, `loading`, `tuner_busy`, plus the
turn and a `NEXT:` line, and the prompt branches on it: `in_game` skips the launch *and*
the load, the two menu states skip the launch, `not_running` starts from the launch, and
`tuner_busy` stops the run. The state is composed from four independent readings — the
process list, the TCP table, the tuner handshake, and OCR of the window — so it does not
collapse when one of them is unavailable.

### FireTuner serves one connection, and a refused connect is not "not started"

Measured 2026-09-20 16:38 while one agent was playing a turn-80 game: the port was
`ESTABLISHED` with that agent's MCP (pid 23276), and `connect()` from a second process
was **refused** — byte for byte the same answer as a tuner that has not started. Read
that way, `game_status` said `starting` and advised waiting 30-60s for something that
was already up, was in a game, and would never become free.

`_tuner_port_state()` now reads `GetExtendedTcpTable` (no subprocess, the same shape as
the Toolhelp process scan) and reports the listener and its clients, so the state
becomes `tuner_busy` with the holding pid and the advice that fits: stop that process,
or keep playing in its session — waiting changes nothing. `_is_tuner_port_open()` keeps
its old meaning, "this process can attach", because the launch and load flows must not
proceed on a port somebody else owns.

**The screen is read even when the tuner is not ours.** With another process holding the
connection, OCR is the only source left, and the HUD prints `回合 80 / 500` — so
`game_status` still names the turn and says plainly that this process cannot attach,
instead of degrading to "unknown". Verified live on 2026-09-20 while an agent played turn
83: the probe could not attach (the connection was held), and the screen still read
`screen turn: 83` with `kind: in-game`. A refused port plus an in-game screen is also what
identifies a game started *outside* the MCP (Steam, or a plain double-click): it is
playable by hand, but no query or command will work until it is relaunched through
`launch_game`.

**OCR boxes are rebuilt into visual lines before anything is parsed.** One line of the
game's UI comes back as several boxes and **the box order is not the reading order**: a
live session reported turn 81 as "turn 8" because the HUD had been split into `回 合 8`
and `1 / 5 0 0` with the tail first, so joining the whole screen into one string put the
digits out of order. `_ocr_lines` groups boxes by y (within a third of the text height)
and sorts each group by x, and `_ocr_turn` reads the first line that carries the counter.
A stray "回合 3" lower down in a tooltip no longer wins over the HUD in the top strip.

### A load request while the front end is not up yet (found 2026-09-20)

A live session asked `get_game_status` (correctly, first), was told `not_running`, launched
the game, listed saves, and then asked to load `AutoSave_0080` one second after the launch
returned. The window was still on the splash. Every menu step waits for its own control, so
the fast path spent 90s looking for 单人模式 and the list path spent another 90s — **172s** —
before answering `FAILED: the game is not showing its main menu`, which reads like a broken
game and was not: `get_game_status` 35s later said `in_game`, and the turn was read in 3s.

Three changes, in order of how much time they save:

1. **The front end is waited for exactly once.** `_navigate_to_save_sync` waits for the main
   menu up front (180s, which a cold start needs) and only then picks the fast path or the
   list path. Previously both paths waited for the same menu, so a game that had not reached
   it yet paid twice.
2. **An already-loaded game is not navigated at all.** The first thing the path does is ask
   the game for its turn (~2s): the same turn as the save asked for is `Already loaded …
   Nothing to load.`, a different turn is a fast `FAILED` naming `restart_and_load`. This is
   the common case — a recovery asked to load the save the game is already sitting on.
3. **The failure names the state.** When the menu never appears, the message says which of
   the three it is — a game already in progress, a main menu whose row OCR did not match, or
   `still starting (its window shows: …)` — instead of one sentence covering all three.

`game_lifecycle.load_game_save` had the same hole one level up: it chose between the menu
path and `restart_and_load` from `conn.gamecore_index`, a *cached* connection fact, so a
connection opened while the game was starting sent an in-progress game down the menu path.
It now asks the game for its turn instead of trusting the cache.

### Open: a turn that starts with no unit movement points (untriggered)

About 4% of turn advances (8 of 195 with a readable unit list) come out with **every** unit
at 0 moves, while the game's own `NOTIFICATION_COMMAND_UNITS` still says "units have moves
remaining". In half of those turns an action later in the same turn worked; in the rest every
action was refused by the game's Lua with `NO_MOVES` until the next rollover. Ending the turn
clears it and costs one turn of orders; the live session that hit it at T81 spent four minutes
and five `get_units` reads first.

Four explanations were tested against every logged run and **ruled out**:

| Candidate | Test | Result |
|---|---|---|
| the turn advanced through a paused diplomacy exchange | count pause-then-advance sequences | 0 of 195 |
| reading too soon after the rollover, before units refresh | delay from advance to the first unit read | the 8 cases were read 4-16s after the advance, but 65 *clean* turns were read within 4-10s |
| an artefact of the truncated log summary | re-ran against the full `result` field | the anomaly survives it: it is every unit, not the first |
| `skip_remaining_units` before the advance | share of turns that used it | 50% of anomalous turns, 68% of normal ones - inverse |

What is left is a race in the turn transition, most likely around the MCP's own work right
after the advance (snapshot, diff, `save_game("0_MCP_NNNN")`, notification and threat
queries). Testing that needs the next live occurrence instrumented, not more log archaeology.

`narrate_units` now appends the diagnosis whenever every unit in the list is at 0 moves - the
data is already in hand, so it costs nothing, and it lands exactly where the agent looks:

```
NOTE: every unit is at 0 moves. If you have not acted yet this turn, the turn's movement
points were never granted (7 units; seen in 8 of 195 logged turns, ...). Re-read once; if it
holds, end the turn - the next turn starts with full moves. Do not restart the game for this.
```

### Rolling back to a chosen turn

`scripts/rollback-to-turn.py TURN` is the whole procedure in one place, because a rollback
is three jobs and doing only the first is how a session ends up confused:

```
.venv\Scripts\python.exe scripts\rollback-to-turn.py 59              # plan only, touches nothing
.venv\Scripts\python.exe scripts\rollback-to-turn.py 59 --apply      # archive + roll back
.venv\Scripts\python.exe scripts\rollback-to-turn.py 59 --archive-only
.venv\Scripts\python.exe scripts\rollback-to-turn.py 59 --save "0A_GROUND_CONTROL"
```

1. **Archive the future.** Every save after the target turn is copied into
   `.civ6-mcp-data/branches/rollback-to-T<turn>-from-T<a>-T<b>-<timestamp>/saves/`, with a
   `manifest.json` (name, turn, source directory, size, mtime, sha256) and a `README.txt`
   saying how to restore or compare. The entry save travels with it. The game prunes
   autosaves, so the manifest notes that the earliest turns of a long branch may already be
   gone - what existed at archive time is what is there.
2. **Archive the diary.** `.tools/archive-branch.py` splits the per-game diary at the
   boundary, so the abandoned branch's rows stop being read as memory of the current one.
3. **Restart the way the state calls for.** The script asks the game where it is and picks:

| state | action | why |
|---|---|---|
| another session is playing | **refuse** | killing or loading would interrupt it mid-turn (and `kill_game` refuses too) |
| no save for that turn | **refuse** | and it lists the nearest saves, since the entry point is often a *named* save whose name carries no turn |
| not running | `launch-then-load` | the game has to come up first |
| running, nothing loaded | `load-from-menu` | the main menu is on screen, so no restart is needed |
| running at a later turn | `restart-and-load` | the main menu is not on screen; a bare load would wait out its timeouts, which the launcher's own guard refuses |
| running at the target turn | `already-there` | nothing to do, and it says so |
| running at an *earlier* turn | **refuse** | that is not a rollback |

A named entry save has its turn **read from the file** (`scripts/parse_save.py`), so a plan
states the turn it is about to load instead of discovering it afterwards; a mismatch is
refused unless `--force` accepts the save's own turn as the target. Scenario saves have no
timeline blocks to read a turn from, so the entry line says "turn unknown" and the rollback
verifies after loading (`VERIFIED: the game is at turn N`, or a WARNING naming what it got).

Measured on the live game: target T72 resolved the entry save `0_MCP_0072` and refused,
because the game was at T59 ("this is not a rollback"); `--save 0A_GROUND_CONTROL` resolved
the named save and reported the turn as unknown, with the verification left for after the
load. The decision table is pinned by `tests/test_rollback_decisions.py`.

**Verified end to end on 2026-09-20** (`60 --apply`, game sitting at the main menu, no other
session): the diary split found nothing to archive and left the file byte-identical, the save
archive **reused** the folder an earlier run had made (0 new save, 80 already archived - the
idempotence that a second run needs), then `load-from-menu` took 35s
(`Clicked Single Player → Continue Game → CONTINUE (colour match)`) and the run ended
`VERIFIED: the game is at turn 60`. The load path needed **no wider sandbox mode**.

The earlier pair of runs (20:45:58 and 20:47:03) had archived the same 80 saves twice, 127 MB
each; they were byte-identical (81 files, same names and sha256), the duplicate was removed,
and the reuse fix above is what stops it happening again. Write-path checks live in
`.tools/verify-rollback-paths.py` (19 checks over archive, sha256, manifest, reuse and the
diary split on a synthetic fixture, using copies only).

### Start-of-turn briefing: is the plan being executed?

`end_turn` can only report that a turn went by without progress. The same rules are therefore
evaluated at the **start** of every turn too, carried by `get_game_overview` - the call the
turn loop begins with - and only once per turn, so the reminder does not become wallpaper.
Measured on the live T60 position, from the running session's own `get_units` result:

```
TURN START (T60) - read this before planning. Rules: turn-checks.md, measured against your army and your diary.
  FAILING:
    [ram-tower-before-civil-engineering] failing for 40 turn(s) - No Battering Ram or Siege Tower exists ...
    [dynasty-cycle-wonder] failing for 14 turn(s) - No wonder built.
    [idle-district-slot] failing for 14 turn(s) - District slots are being left idle ...
    [builder-backlog] failing for 14 turn(s) - Fewer than three improvements per city.
  the last turn bought: gold/turn -1.0; military -38
  rate over that window: science +0.17/t, military -12.00/t, improvements +0.00/t
  you planned last turn (planning): T60-T72: (1) 西安 65536 on Plaza completion -> UNIT_TRADER ...
  you planned this turn (planning): T61-T75: (1) 北京 builder 720900 -> STONE quarry (57,27) ...
  VERDICT: no failing rule cleared and the last turn bought nothing measurable - the plan is
  not being executed as written. Change one thing this turn, name it in the diary, and say
  which turn it lands.
```

How "is the plan being executed" is measured, rather than felt: every diary row records
`unit_composition` and the yields, so the rule set of **each of the last forty rows** is
recomputed and each failing rule gets a streak. A rule that has been failing for forty turns
is not a reminder, it is a finding; a rule that has just cleared shows up as `CLEARED`, which
is what moves the verdict from "not being executed" to "keep going". "Bought something" means
a positive move in structure (cities, districts, improvements, wonders, population, army) or a
yield that rose by 0.5 or more - a 0.1 science tick is not progress, and losing 38 military is
not either (`tests/test_turn_start_briefing.py`, 11 cases).

**Goals retire themselves (`once: true`).** A reminder that has been dealt with must stop
being a reminder, or the list becomes wallpaper and the rules that still matter drown in it. A
rule marked `once: true` is finished the first turn its requirement holds: it is reported once
as `CHECK ACHIEVED [id] at T<n> - retired`, recorded in
`.civ6-mcp-data/turn-checks-state.json` **keyed by game** (`china_-1894041591`), and never
evaluated again for that game - a new game starts with every goal open. Standing rules carry
no `once` and keep firing, because their conditions can regress: a district slot goes idle
again as the city grows, a siege unit dies. Two rules are goals today
(`ram-tower-before-civil-engineering`, `dynasty-cycle-wonder`); a rule whose `when` gate is
false is *skipped*, not achieved, so it cannot retire by accident
(`tests/test_turn_check_retirement.py`, 22 cases).

**An achieved goal is also deleted from the file, not just ignored.** Retirement makes a done
goal stop nagging, but it stayed in `prompts/checks/turn-checks.md` - so the file the agent
reads at the start of every turn kept listing work that was finished, which is the opposite of
its purpose. The sweep runs where the checks run, at the end of the turn that achieves the
goal: the file is copied to `prompts/checks/archive/turn-checks-<YYYYmmdd-HHMMSS>.md`
**first**, the rule block is replaced by a one-line trace
(`<!-- achieved T60: ram-tower-before-civil-engineering (original in archive/…) -->`), the
hand-written prose is left alone, and the turn result reports

```
CHECK FILE PRUNED: achieved goal(s) ram-tower-before-civil-engineering removed from
turn-checks.md; the file as it was is kept at prompts\checks\archive\turn-checks-20260920-213546.md
```

Three properties matter and are tested: the **backup is written before the live file is
touched** and holds the pre-edit text byte for byte; the removal is **idempotent** (a second
sweep finds the id gone and writes no second backup); and the trace comment is not parsed as a
rule, so the pruned file does not report itself broken
(`tests/test_turn_check_prune.py`, 21 cases).

**It ran live, unprompted.** On the T99 turn the sweep fired for real: the file went from 15 rules
to 13, with two traces (`achieved T99: ram-tower-before-civil-engineering` and
`dynasty-cycle-wonder`) and a byte-identical copy in `prompts/checks/archive/`, while
`.civ6-mcp-data/turn-checks-state.json` recorded both for `china_-1894041591`.

**But the swept file is per-game state, so the repository copy keeps the full set.** The file is
also the template every future game starts from, and retirement is recorded per game. Restoring it
from `archive/` is safe for the game in progress, because a retired goal is skipped rather than
re-achieved (`_evaluate_checks` excludes ids already in the retirement state). So: **commit the full
rule set**; treat `archive/` and the state file as the per-game record, and restore from the archive
when starting a new game from the repository.

**Test hygiene, learned twice.** The briefing tests first wrote retirement state into a shared
`.tools/` directory, so the second consecutive run started with the goal already achieved. Then
the sweep made it worse: running the hook against the **default** path edited the repository's
own `prompts/checks/turn-checks.md` - a test whose fake army contained a ram pruned the live
ram/tower goal out of the shipped directive. `tests/conftest.py` now gives every test a scratch
copy of the shipped file (`CIV_MCP_TURN_CHECKS`) and a scratch data directory
(`CIV_MCP_DATA_DIR`), and a session-scoped fixture re-hashes the shipped file at teardown so a
future test that writes to it fails the suite instead of quietly shipping a pruned directive.

### Contact on the march: "engage what is in the way, prefer the counter unit"

The human's rule - while the army is assembling, an enemy in the way is attacked first, with
the counter unit if one exists - cannot be checked from yields or unit counts, so two facts
were added to the check context (`tests/test_march_contact.py`, 25 cases):

- **`enemies_within_1/2/3`**, split by the game's own `PROMOTION_CLASS_*` into
  `enemies_cavalry_within_2`, `enemies_anti_cavalry_within_2`, `enemies_siege_within_2`,
  `enemies_ranged_within_2`, `enemies_melee_within_2`, plus `weakest_enemy_hp_within_2`. The
  threat scan already reported a distance, but against our units **and cities** - "the enemy
  is next to the army" is a different fact, so the Lua now also prints `udist:` (nearest of
  our units only) and the classification comes from the game, not from a unit-name table that
  would rot with each era. `ANTI_CAVALRY` is matched before `CAVALRY`, or the counter files
  itself as the thing it counters.
- **`attacks_this_turn`**, counted where the attack happens (`GameState.attack_unit`) and
  reset in `end_turn` *after* the checks have read it, so a blocker turn earlier in the same
  turn still sees the attacks already made.

The rules that use them: `counter-the-cavalry` (enemy cavalry within 2 requires an anti-cavalry
unit **or** an attack this turn), `mass-on-contact` (contact requires two of our units in range),
`use-your-attacks` (no legal attack may be left unused) and `finish-the-wounded` (an enemy at
20 HP or less within 2 tiles must be attacked). The full
counter table - anti-cavalry beats cavalry, ranged beats melee, cavalry beats ranged/siege,
siege beats only cities - lives in the directive and in the `military-map` advisor prompt, and
the same text is injected into `SKILL.md` by `scripts/use-strategy.ps1 china-conquest`.

**`engage-the-screen` was retired after the siege replay** (see the T101-T116 section below): its
requirement was "at least one attack this turn", and a turn of two Catapults shelling Moscow - with
a 7 HP Swordsman one tile away - satisfied it. A rule that a real failure passes is worse than no
rule, because it teaches the agent that the check list can be ignored. `use-your-attacks` asks the
question that discriminates ("is a legal attack still unused"), and `mass-on-contact` covers the
concentration half.

A historical diary row cannot be asked about enemy positions or attack counts, so
`_context_from_row` fills the contact metrics with **zeros**: the rules read as "not
applicable" instead of `un-evaluable`. Without that, the briefing's streak computation would
report a forty-turn failing streak for a rule that was never evaluated on those rows.

**The same change fixed a real false-alarm generator.** Live `CHECK FAILED` output at T103,
T104 and T106-T114 listed four unit-count rules as failing while the diary recorded 2
Catapults, 5-6 Archers, 2-3 Warriors and a Battering Ram - every `units(...)` rule read 0
because the check context had an empty unit list. The agent concluded, correctly, that "the
re-appearing check failures contradict get_units and should be treated as a stale metric" and
stopped trusting the mechanism. `_evaluate_checks` now falls back to the diary row's
`unit_composition` when the snapshot yields no units, so the count rules are answered from the
recorded army rather than from nothing.

### War footing: one garrison per city, and an answer to every hit

Two wartime rules (`tests/test_war_footing.py`, 29 cases), both gated on `at_war` so peacetime
garrisons stay legitimate:

- **`one-garrison-per-city`** - a second unit standing on a city tile does what the first one
  already does while the front is a unit short. Counting it needed two facts that were not in
  the check context: the **city-centre coordinates** (now carried on `CitySnapshot`, so
  "standing in the city" is distinguishable from "somewhere near it") and whether a **war is
  on**. `at_war` is read from the diary row's `diplo_states` (state index 6 is WAR: 0 ALLIED
  ... 5 DENOUNCED, 6 WAR), which makes it reconstructible from history rather than live-only.
  A garrison is a unit with combat or ranged strength, so a builder parked on a city tile is
  not counted.
- **`answer-the-attack`** - a unit that is hit and ignored is hit again next turn. The damage
  is only visible in the **snapshot diff** (the check context sees the army as it is now, not
  as it was before the enemy moved), so `end_turn` records the ids whose HP fell during the AI
  turn into `gs._damaged_last_turn`, and the context exposes `damaged_this_turn`. The rule
  requires an attack in response; withdrawing or healing instead is allowed but must be written
  in the diary's tactical line, the same release valve the other rules use.

Both metrics read 0 when their data is missing (no city coordinates, no diff, no row), and the
rules are gated on `at_war >= 1`, so absent data means silence rather than a false alarm.

**Assess, mass, annihilate.** `answer-the-attack` covers a unit that was hit; the doctrine the
human asked for starts at *discovery* and goes further - the answer is not a trade. Two things
make it executable rather than aspirational:

- **`BATTLE ASSESSMENT`**, emitted when a unit was damaged **or** when enemy forces come into
  contact during a war (within three tiles; outside a war only damage triggers it, so barbarian
  skirmishing does not become wallpaper): for every enemy within three tiles, its class, combat
  strength, HP, distance and **how many of our fighting units are within two tiles** (new
  `near:`/`adj:` fields on the threat scan, computed by the game with `Map.GetPlotDistance` over
  our military positions - no Python hex math), which enemies are killable right now, which are
  one move out of reach, and the counter hint for the class in contact.
- **`mass-on-contact`**: while an enemy is in contact, facing it with only one of our units in
  range (`metric(local_superiority) < 2`) fails - whether or not we attacked. `local_superiority`
  is the best of the per-enemy in-range counts and `enemies_massed_on` how many enemies already
  have two or more of ours in range. Limitation, stated plainly: the metric is a maximum over the
  enemies in range, so it proves we *have* concentration somewhere, not that every attack was
  concentrated - the rule is a floor, not a proof.

### Who analyses, who executes, and how that is audited

| Step | Owner | Mechanism |
|---|---|---|
| Strategy (target, timing, establishment) | the human | `prompts/strategies/<preset>/directive.md`, injected into `SKILL.md` |
| Analysis (threats, formation, composition) | the `military-map` worker, plus `strategy`, `economy-cities`, `diplomacy-victory` | `civ_advisor` - the only permitted worker route (`dsh/civ6.cordis.yml`, `toolFilter.allow: []`, so advisors hold **no tools at all**); proposals validated against `contracts/worker-proposal.schema.json` |
| Execution (sole writer) | the orchestrator session | the MCP tools; SKILL Phase 4 |
| Judgement and enforcement | the MCP itself | the 15 rules in `prompts/checks/turn-checks.md` plus `BATTLE ASSESSMENT`, `SIEGE POSTURE`, `SIEGE PROGRESS`, `UNUSED ATTACK` |

**The worker cannot read anything.** It has no filesystem and no tools, so the orchestrator must
paste into the `civ_advisor` call: the matching tactic file's text, and the turn's own judgement
signals - the `CHECK FAILED` lines, `BATTLE ASSESSMENT`, `SIEGE POSTURE`, `SIEGE PROGRESS` /
`SIEGE STALLED`, and the `UNUSED ATTACK` line. Phase 2 of the skill requires that paste, and Phase 3
requires the proposal to survive being checked against those same numbers. The worker's `assessment`
string starts with the tactic file and the decisive metric (`tactics/05-... | siege_exposed=1 ...`)
so the orchestrator can verify it cited real data.

**Auditing that the process ran.** Two independent records:

1. `.tools/advisor-usage.mjs` reads the DSH session transcripts (`.dsh-home/sessions/**/session.jsonl.zstd`)
   and reports defined-vs-used: roles defined, `civ_advisor` call count, sessions that used a worker,
   and per-role counts. The last run: 87 sessions, **101 `civ_advisor` calls**, **46 sessions used a
   worker**, `military-map` named in 29 proposals and its role file read in 8 sessions. (Those two
   numbers are inferred markers - `immutable` for "a role file entered context", the enum string for
   "named in a proposal" - so read them as evidence of use, not as an exact call count.)
2. The diary's `tooling` reflection carries a per-turn `advisor:` trace line (Phase 5 of the skill),
   e.g. `advisor: military-map tactics/05-formation-and-screening.md -> 3 actions, 1 rejected (...)`.
   That is the record the *agent itself* can read back after compaction, and the one a human can grep
   without touching the DSH session store. Advisors never appear in the MCP telemetry, which is why
   the trace has to be written by the orchestrator.

### Several units on one city tile is normal (and why that mattered)

Civ VI reports every unit inside a city at the city's own coordinates, and a city centre is not
bound by the field's one-unit-per-tile rule. Live evidence: `get_units` showed two Archers and a
Warrior at `(57,29)` for ten consecutive turns, two units at `(52,24)`, and two at `(52,30)` -
because those tiles **are** Beijing, Shanghai and Changsha (`get_cities` lists all three there).
Three rehearsals flagged it as an impossible stack, and the first two were right to: their brief
did not carry the city coordinates, so nothing in front of them explained a multi-unit tile.

Three fixes, in the order the rehearsals forced them:

1. **`get_units` marks it**: a fighting unit standing on one of our city centres is annotated
   `[IN Beijing]` (`narrate.narrate_units(..., cities=...)`, fed from the last snapshot's cities,
   so no extra round trip). A builder in a city is not annotated - `one-garrison-per-city` counts
   fighting units.
2. **The check engine distinguishes the two cases**: `_garrison_metrics` reports
   `unexplained_stacks` for military units sharing a tile that is **not** one of our cities, and
   `end_turn` emits `SNAPSHOT WARNING: ... treat every position-based judgement as suspect`
   when it is non-zero. A stack on a city tile is a garrison (`cities_over_garrison`), a stack
   elsewhere is a data problem, and the two read completely differently.
3. **The brief says so**: the rehearsal brief now carries the role file (Phase 2 passes "its role
   instructions", so a faithful rehearsal must include it), and both the role prompt and tactic 02
   state the rule and the counter-example, including that a `UNIT_BARBARIAN_HORSEMAN` inside our
   own unit list is a **converted** unit from Thirty-Six Stratagems, not a foreign one.

The last rehearsal, with all three in place, reported "no unit position looks impossible" and
explained each tile correctly - which is the acceptance test for this fix. The lesson generalises:
when a worker reports an anomaly, check whether the brief was capable of explaining it before
believing the data is broken.

### Rehearsing the advisor contract, and validating what comes back


The Phase 2 brief and the Phase 3 rejection rule are testable without the game:

- `.tools/advisor-rehearsal.py` rebuilds a canonical snapshot, the two matching tactic files and
  the turn's judgement signals for **T111 of the abandoned siege line** - the turn the replay
  flagged - and writes them to `.tools/_advisor-brief.md` (+ `_advisor-snapshot.json`). That is
  exactly what the orchestrator is now required to paste.
- `.tools/verify-advisor-proposal.py <proposal.json> [snapshot.json]` is Phase 3 as a command:
  JSON Schema, `worker`/`gameId`/`turn`, every tool name and argument name against the live MCP
  tool inventory (a `tools/list` round trip, or `--inventory=<file>` for the deterministic test
  fixture, or `--no-inventory`), every unit id against the snapshot, and duplicate action ids.
  Exit 0 = accept, 1 = reject with the reasons.

Measured on the real T111 position: two independent rehearsals returned schema-valid, accepted
proposals that agreed on the decisive action - Archer 1376265 then Heavy Chariot 1310724 kill the
53/100 HP Swordsman at (53,35), the shot that was discarded on the live turn - and both flagged
the siege exposure (`siege_exposed = 2`) and named the missing screen. They disagreed on the
catapults' immediate fate (reposition both now versus keep firing from range 2 and mandate the
withdrawal next turn), which is the kind of conflict Phase 3 resolves rather than averages. Both
also reported snapshot gaps the brief did not close (our units' HP, terrain, city ids) instead of
inventing them, and one of them independently noticed that the pasted `CHECK FAILED` list
contradicted the roster it was given - the signature of the empty-unit-list bug fixed the same
day. The contract is pinned by `tests/test_advisor_proposal.py` (11 cases: both controls, the
snapshot schema, unit ids read out of the tool's own text, and the tool names the contract
depends on).

### The six tactic files, and how the military worker finds them


The military doctrine is split by decision under `prompts/tactics/` - production, contact on
discovery, under attack, staging outside enemy range, formation and screening, and assault
composition and fire discipline - plus a `README.md` with the shared vocabulary (the metric and
rule names the turn result prints) and the rules that hold in every file.

They are written for the `military-map` advisor, which is read-only and sees only the immutable
snapshot, so each one is organised as **trigger → assess → decide → prohibitions → what to
report**, with the game's own numbers (Catapult 45 vs cities, the ranged strike's two tiles,
Battlcry's +7 against melee and ranged) instead of adjectives.

Wiring, all of it checked by `scripts/qualify-static.mjs`:

- `prompts/workers/military-map.md` (the file the orchestrator reads in Phase 2) carries the
  trigger table: which file to read for which situation. The gate fails if any of the six files
  is missing, is suspiciously short, or is no longer named by that prompt.
- `prompts/strategies/china-conquest/military-map.md` keeps the same table, because
  `scripts/use-strategy.ps1` overwrites `prompts/workers/` from the preset - the gate checks that
  the preset still carries the references too, so re-applying the strategy cannot silently unwire
  them.
- `.dsh/skills/civ6-orchestrator/SKILL.md` Phase 2 tells the orchestrator to name the matching
  tactic file in the `civ_advisor` call when the turn has a clear character, and to hold the
  proposal to that file's prohibitions in Phase 3.

The tactic files are shared across presets on purpose: production, contact, defence and siege
staging are Civ VI tactics, not Chinese ones. The civ-specific parts (Crouching Tiger's range 1,
the ram/tower cliff at `CIVIC_CIVIL_ENGINEERING`) sit inside the relevant file.

### Staging the assault: the formation is measured, not assumed


The human's siege sequence - **assemble outside enemy range, screen in front, ranged behind,
the Catapult's tile protected above all, advance only once formed** - is geometry, so the game
is asked for it (`tests/test_war_footing.py`, the `TestSiegePosture` cases):

- `build_siege_posture_query()` reports, per siege unit, the distance to the nearest visible
  enemy unit, the distance from that enemy to the front-line unit **nearest the siege unit**
  (the screen), and the distance to the nearest visible enemy city (with its name). All of it
  comes from `Map.GetPlotDistance` inside the game.
- `SiegePosture.exposed` is true when the siege unit is within two tiles of an enemy and its
  screen is **not strictly closer** to that enemy - a screen standing exactly as close is not
  between the catapult and the enemy, so it does not count as cover.
- `metric(siege_exposed) > 0` fails `screen-the-siege`; `siege_in_city_range` and
  `siege_city_distance_min` say whether the train is in firing position or still staging.
- A `SIEGE POSTURE` event names each unit and its distances, and stays silent while the train is
  staging far from any target (only the exposed case, or a train already within three tiles of a
  city, is printed - otherwise it would be wallpaper).

Caching follows the other scans: one `SIEGE POSTURE` query per turn, reused by every check pass.

### Unused attacks: an attack that is discarded is reported before it is discarded


Measured live at T109-T116: a Heavy Chariot stood on (53,36) with `moves 2/2` for seven turns,
twice with a Russian Swordsman on the adjacent tile at 53 hp and once at **7 hp**, and never
attacked. `get_units` even printed `>> CAN ATTACK: UNIT_SWORDSMAN@53,35(7hp)` for it. Every
one of those turns ended with `skip_remaining_units`, which fortified the chariot and said
nothing about the attack it had just thrown away - so the omission was invisible in the turn
result and only findable by hand-diffing the telemetry.

Two additions close that (`tests/test_unused_attacks.py`, 17 cases):

- **`skip_remaining_units` now names what it is about to discard.** Before finishing moves it
  runs `build_unused_attack_query()` - the same legality test as the `>> CAN ATTACK` hints
  (adjacency for melee, `CanStartOperation(RANGE_ATTACK)` LOS beyond one tile, barbarians
  always hostile, war required otherwise), so the report can never contradict the hints - and
  appends `UNUSED ATTACK (N unit(s) had a legal attack and did not take it):` with one line
  per unit.
- **The check context carries `unused_attacks`**, and two rules use it: `use-your-attacks`
  (`require: metric(unused_attacks) <= 0`) and `finish-the-wounded` (an enemy within 2 tiles at
  ≤ 20 hp requires `attacks_this_turn >= 1`).

`use-your-attacks` exists because the rule added earlier the same day - `engage-the-screen`,
"enemies within 2 tiles and `attacks_this_turn >= 1`" - **passes a turn like T111**, where two
Catapults fired at Moscow's garrison while an adjacent 53 hp Swordsman was ignored. "Did you
attack anything" is a weaker question than "is a legal attack still sitting unused" - and
`engage-the-screen` has since been deleted rather than left in place to pass real failures.

### The T101-T116 siege replay, and the three fixes it produced

The Moscow assault (T105-T116) was rolled back to T100, so `.tools/siege-retro.py` replays the
current rule file against the archived telemetry to ask what today's rules would have caught:

| Rule | Would have fired | Evidence |
|---|---|---|
| `screen-the-siege` | **T109-T114** | a Catapult fired from `dist:1` every turn - the city tile held the garrison, so nothing could screen it |
| `use-your-attacks` | **T107/108/109/111/113** | legal-attack hints vs attacks made: 2/1, 9/3, 5/1, 3/2, 4/3 |
| `finish-the-wounded` | **T115** | the Swordsman stood at 7 HP, one tile away, with no successful attack that turn |
| `ram-tower-before-civil-engineering` | **T109-T116** | the ram was destroyed at T109 and never replaced |
| `answer-the-attack` | only T105 | only two damage events were recorded in twelve turns |
| `engage-the-screen` | **never** - `mass-on-contact` neither | two attackers satisfied "we attacked"; two units in range satisfied "not alone" |

Three fixes followed, in the order the replay put them:

1. **City HP is always reported.** The attack result built its city line behind `if w_max > 0`,
   so an unwalled city reported no city number at all - and an unwalled city is exactly the case
   where the HP pool is the only progress there is. The line is now
   `|city hp: N/200, walls: N/100|none`, `_format_attack_followup` says the same, and the
   narrate note points at these names. Every city attack also records the city's HP
   (`GameState._record_city_hp`), and `end_turn` prints a `SIEGE PROGRESS` block with the delta -
   escalating to `SIEGE STALLED` after three recorded turns without a net drop, because the city
   heals about twenty points a turn and fire that does not out-damage the healing never happened.
2. **Our own losses are reported from the right baseline.** The damage report used the snapshot
   diff, whose baseline is not pre-AI on a blocker or mid-turn-diplomacy re-entry: the Heavy
   Chariot went 74 -> 55 HP with no event recorded anywhere, which is why `answer-the-attack`
   fired once in a whole war. `end_turn` now records our units' HP at the moment `ACTION_ENDTURN`
   is sent (`gs._hp_at_end_turn_request`) and compares the new turn against that, and it also
   reports any of our units that disappeared entirely.
3. **`engage-the-screen` retired** (above), because the replay showed a real failure passing it.

The counter side of the same episode is in the directive: the Swordsman read CS 42 against our
ranged fire because of its **Battlcry** promotion (`PROMOTION_BATTLECRY`, +7 *against melee and
ranged*), which does not apply to a cavalry attack - and the chariot's matchup was never once
estimated. The agent generalized one Catapult's 8-damage result into "the army cannot engage
this", which is the mistake `counter-the-cavalry` and the directive's "test the matchup before
writing a unit off" now push against.

Note for tooling: the diary lives in `CIV_MCP_DATA_DIR`, which the MCP gets from the profile
overlay (`dsh/civ6.cordis.yml`). A helper script run from a plain shell must set it
(`$env:CIV_MCP_DATA_DIR = ".civ6-mcp-data"`) or it reads `~/.civ6-mcp` and sees no rows at all
- which is how the first run of this briefing printed every streak as zero.

### Per-turn checks: rules in a markdown file, enforced by `end_turn`

`prompts/checks/turn-checks.md` holds rules that are objectively checkable, written as
markdown so a human can edit them without touching code:

```markdown
<!-- check
id: ram-tower-before-civil-engineering
when: not researched(CIVIC_CIVIL_ENGINEERING)
require: units(BATTERING_RAM, SIEGE_TOWER) >= 1
message: No Battering Ram or Siege Tower exists and CIVIC_CIVIL_ENGINEERING is not yet
         adopted - the window is still open and closes for good.
-->
```

`end_turn` reads the file on **every** turn (not every tenth) and evaluates each complete
block against the live unit list and this turn's diary row; every failing rule appears in
the turn result as `CHECK FAILED [id]: <message> (require: <expression>)`. **Every return
path, including the blocker path** - a turn the agent cannot end is still a turn, and it is
the one where the gap is most worth stating. The first version of this hook sat after the
blocker return, so blocked turns (the common case: unmoved units, an empty queue, a
promotion) never saw the reminders at all; `tests/test_turn_check_hook.py` now pins the call
before that return and pins that a same-turn snapshot is reused, so repeated blocker turns
do not each pay for a snapshot. Functions:
`researched(NAME)`, `units(T1, T2, ...)`, `metric(NAME)` (dotted names reach sub-fields:
`metric(trade_routes.active)`), `turn()`. Operators: `+ - * / // %`, comparisons,
`and`/`or`/`not`, parentheses. Point `CIV_MCP_TURN_CHECKS` at another file to swap the set.

**Expressions are parsed with `ast` and evaluated against a whitelist of node types and
function names — never `eval`.** A check file is data: `__import__('os').system(...)` or
attribute access is rejected with a `CheckError`, and a rule that *has* a `require:` but
cannot be evaluated is reported rather than silently dropped. A block without a `require:`
is treated as an example in prose, because the file documents its own format.

Motivating case, measured on the live game at T121 - eight rules parsed, five failing:

```
CHECK FAILED [ram-tower-before-civil-engineering]  units(BATTERING_RAM, SIEGE_TOWER) >= 1
CHECK FAILED [siege-train]                         units(CATAPULT, TREBUCHET, ...) >= 2
CHECK FAILED [ranged-mass]                         units(SLINGER, ARCHER, ...) >= 4
CHECK FAILED [melee-screen]                        units(WARRIOR, SWORDSMAN, ...) >= 2
CHECK FAILED [idle-district-slot]                  metric(districts) >= metric(pop) // 3
```

The ram/tower rule is the reason the mechanism exists: both units go obsolete the moment
`CIVIC_CIVIL_ENGINEERING` is adopted, that civic was still unresearched, and no ram or tower
had been built - a one-way door that four earlier turns of prose had not closed. The checks
that pass stay silent, so the signal is only the gap.

Evaluated against the live position at T60 (the running session's own `get_units` result plus
the T60 diary row, read-only - the session holds the tuner, so the tool below could not
attach): **8 rules parsed, 4 failing** - `ram-tower-before-civil-engineering`,
`dynasty-cycle-wonder` (none built), `idle-district-slot` (2 districts for pop 12 allows 4)
and `no-idle-trade-route`. The assault-train rules are gated at `turn() >= 90`, so they stay
quiet until they can mean something. `.tools/show-turn-checks.py` prints the same evaluation
from a live tuner connection when nothing else holds it.

### The every-10-turns review

`end_turn` now carries a second 10-turn block next to the victory snapshot: a
`10-TURN REVIEW` that reads the diary back and measures the window. It exists because the
failure it catches is invisible turn by turn - the current game went from T30 to T80 with
science nearly flat (+6.3 over fifty turns), reached T100 before its first wonder, and at
T120 had three district slots idle and no siege unit, while every individual turn looked
reasonable. Measured from the same game:

```
10-TURN REVIEW (T110 -> T120)
  last 10 turns: science +2.9 (+0.29/t); culture +1.9; gold/turn -3.6; military +12; pop +3;
    improvements +2; territory +2; techs +2; civics +1
  you wrote at T110 (planning): <the agent's own plan, quoted>
  you wrote at T110 (hypothesis): <its own prediction, quoted>
  assault prerequisites (conquest directive): siege 0/2, melee 1/2, ram/tower 0/1,
    ranged 1/4, cavalry 0/1 - MISSING 2 siege, 1 melee, 1 ram/tower, 3 ranged, 1 cavalry
  Dynastic Cycle: wonders built 1
  district slots: 7 districts for pop 31 (allowed floor(pop/3)=10) - 3 slot(s) idle
  carrying capacity: gold/turn +12.4 with military 110 - ok
  projection at the window's rates: hold the same rate and T130 looks like science 47.6,
    military 122.0. State whether that reaches the milestone and by which turn.
  REQUIRED IN THIS TURN'S DIARY: (1) was this window efficient, with numbers? (2) which
    prerequisite for the next goal is in place and which is still missing? (3) does the
    planned completion turn still hold, and if not, what changes?
```

The division of labour is the point: the MCP measures (deltas, rates, the unit inventory
against the directive's own assault list, idle slots, the carrying limit), the agent
judges, and the diary is where the judgement is recorded, so it can be audited later.
`AGENTS.md` ("Around every 10 turns") and `SKILL.md` (Phase 5) both state the requirement,
and `.tools/show-ten-turn-review.py` prints the same block from the stored diary for any
turn without playing.

### One session at a time: kill_game refuses to interrupt another

Reproducing the above cost a real position. A verification run called `kill_game()` while a
live session was mid-turn-82 — that session's log shows a `get_units` eight seconds before
the kill — and the game had to be reloaded from its newest autosave (`0_MCP_0082`). A kill is
not a neutral diagnostic.

`_other_active_session()` now names the other session from two independent signals: a
non-self client on the FireTuner port (`GetExtendedTcpTable`), or a `playing` heartbeat
written within the last 120s by another pid. `kill_game` and `restart_and_load` refuse while
one is found, with `force=True` for a session known to be dead. A stale or `finished`
heartbeat is not a live session, and neither is this process's own connection.

### What the menu load does differently now

Driving the recovery by hand on 2026-09-20 exposed six defects in
`_navigate_to_save_sync`, all of the same kind: acting on an assumption instead of on
what the screen was showing. They are fixed in `src/civ_mcp/game_launcher.py` and
pinned by `tests/test_menu_navigation.py`:

| Was | Now | Why |
|---|---|---|
| four clicks to load a named save | **Continue Game first when the newest save is the one asked for** | 单人模式 → 继续游戏 resumes the most recent save in two clicks, with no save list to read and no row to pick. It is also the more correct target: the newest save is not necessarily the newest `0_MCP_` file - the game writes its own `AutoSave_*` alongside and after a plain exit that one is a turn ahead (2026-09-20: `AutoSave_0080` at turn 80 against `0_MCP_0079` at turn 79) |
| `PrintWindow` capture | screen grab (`ImageGrab`) | the flow's own comment says PrintWindow + SetForegroundWindow during the DX12 loading phase can crash the renderer, and the flow polls for the continue button in exactly that phase |
| `SetForegroundWindow` before every click | only when the game is not already foreground, and skippable with `CIV_MCP_NO_FOREGROUND_STEAL=1` | a grab reads whatever is on top, so the game has to be on top. Disabling it outright was tried first and failed the other way: after a cold launch the game comes up behind the browser, the grab captures that instead, and the flow reports "the game is not showing its main menu" while the game is right there |
| `y_offset=15` on the Load Game item | the OCR box centre | at 3840x2160 the menu rows are 38 px apart, so a +15 nudge lands in the gap or on 创建游戏 - it opened the Create Game screen and the load reported "Save not found" |
| nine-point grid for the continue button | colour match, one candidate at a time | the grid covers y 75-88% and the control is at (44%, 64%); OCR never reads it, and clicking nine positions in a row can land inside a game that is already running |
| "FireTuner port is open" = success | read the turn from the game | that port is open at the main menu too, so a load that never left the leader screen was reported as successful |
| continue control hunted by ranking teal blobs by area | the globe above the ribbon, found by shape, with the ranking kept as fallback | the control is a bar with a ring-shaped globe above its centre, and only the globe responds — clicking "the most teal thing" is not the same as clicking the control. Measured on a recorded leader screen: globe x 1664-1736 y 260-330, bar y 340-370, and the shape finder lands at (1699,308) inside the globe |
| positional clicks that could land inside a running game | read the screen first; an in-game HUD means no click at all | a click on the map is a **move order** when a unit is selected, and the OCR-timeout fallbacks reach the positional click assuming the leader screen without ever confirming it |
| "Single Player" clicked, then "Continue Game" searched for | look for 继续游戏 **first**, and click the parent only if the submenu is closed | clicking the parent again closes an open submenu, and the parent itself moves ~95px left while it is open (1862 → 1759 on 2026-09-20), so a coordinate read beforehand misses the item entirely |
| "no teal blob on the leader screen, start clicking candidates" | wait up to 120s for the globe and bar to be **drawn**, then click once | the leader screen is readable about 26s before its control exists (measured: 715 teal samples on the whole screen at detection, 7639 around the control once drawn). Clicking blind in that window produced seven stray clicks over 98s |
| "the click worked" = the turn is readable within 15s | the leader screen going away is the signal | the turn is readable minutes later, so the 15s check declared a good click a miss and clicked seven more times. Confirmed by log: click at 17:26:38, screen changed at 17:26:43, turn 80 verified moments later |

**Measured end to end (2026-09-20, kill → launch → turn 80):** 77s and 76s on two runs -
launch 15s (process 2s, FireTuner 6s), menu 24s, waiting for the control 25-26s, one
click, 5s to see the screen change, load 52-53s. The same procedure before these fixes
took 142s with eight clicks, and the run before that 304s. A later run took 179s purely
because the `steam://run` handoff timed out (60s) and FireTuner took 30s - the load
itself was still 57s.

**The first probe after a load fails, and one retry fixes it.** Measured on every run: a
reconnect immediately after another client closed comes back as
`[WinError 64] The specified network name is no longer available` even though the port is
fine - the same probe answers turn 80 five seconds later. `_game_probe` now retries once
(1.5s) when the failure is a dropped connection, and reports `yes, turn 80` on the first
call after a load instead of `no connection`. The retry keys on the error, not on the
port table: at that instant `GetExtendedTcpTable` showed no LISTEN row at all, so the
port-based condition never fired.

**Launching needs the wider sandbox mode.** Measured in the confined sandbox: the
`steam://run` handoff waits out its full 60s timeout and reports "did not start game",
the direct EXE starts and the process is gone within two minutes, and no tuner port ever
opens. With `danger-full-access` the handoff works in 2s. The *load* step needs no wider
mode - it was reproduced in the confined sandbox, which is how the submenu defect above
was separated from a sandbox effect.
| exact screen signatures | a tolerant one (`与能力`) | Windows OCR reads 特征与能力 as 每征与能力, so an exact match fails on the one screen the load must end on |

`CIV_MCP_PRINTWINDOW_CAPTURE=1` restores PrintWindow for an occluded or minimised
window, accepting the renderer risk that comes with it.

The result string now ends with `Game in progress at turn N`, which is the check the
recovery prompt asks for: compare N with the number in the save name (`0_MCP_0079`
must be turn 79).

**A launch needs the credential in the launching environment.**`run-dsh-headless.ps1` points `DSH_HOME` at the project's `.dsh-home`, which has no
credential store, so the global `~/.dsh/.credentials.yaml` does not apply. Starting
the launcher from a shell that does not export `DEEPSEEK_API_KEY` gets as far as
starting the MCP and then dies with:

```
dsh: MISSING_CREDENTIAL: llm-deepseek: no API key for provider route "deepseek-official"
```

That failure leaves a stub `session-*` directory and a `"phase": "starting"`
heartbeat behind — the residue `scripts/civ6-clean.ps1` exists to remove. Note the
launcher's own warning about the variable is easy to read past, because the launch
proceeds for several seconds before it fails.

### Checking a prompt without launching it

**`-DryRun` / `--dry-run`** prints the file's size and digest, the pointer that
will be handed to dsh, and the pointer's digest, then exits 0 without launching
anything:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-dsh-headless.ps1 `
  -TaskFile prompts\tasks\continue-from-t59.zh.txt -DryRun
```

```bash
bash scripts/run-dsh-headless.sh --task-file prompts/tasks/continue-from-t59.zh.txt --dry-run
```

The `file sha256` line is the evidence the text survived intact, and the two
launchers compute it by completely independent means (.NET `SHA256` over the
decoded text vs coreutils `sha256sum` over the file's bytes with any BOM
skipped). They must agree, and `.tools/test-taskfile.sh` asserts that for both
prompts rather than leaving it to someone eyeballing a console — a console can
still render the text badly even when the string itself is correct, and a *file*
can too if the viewer guesses the wrong encoding. It is also the digest to compare
against what the agent reports reading, so the check spans the whole path from
disk to model context. For the current Chinese prompt both report **385
characters, 1039 UTF-8 bytes, sha256
`F3D6A0FB36BE25031E61423B5FE974AF2B6741EF0CFE754771CBA31C281C8BFB`**.

Always use the dry run when exercising a launcher in a test or by hand: a real
invocation spawns a full agent session, and with no game attached it leaves a
half-initialised `session-*` directory under `.dsh-home/sessions/` plus a stale
`phase: "starting"` heartbeat in `.civ6-mcp-data/`. Both suites are dry-run-only
by construction, so they cannot launch anything even if a failure path regresses:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .tools\test-taskfile.ps1   # 12 cases
& 'C:\Program Files\Git\bin\bash.exe' .tools/test-taskfile.sh                  # 15 cases
```

### Stopping a session cleanly

Ctrl+C on the dsh console stops the agent but leaves three things behind: the game
process holding the tuner ports, any MCP server still attached to that tuner, and
`heartbeat.json` describing a run that no longer exists — which is exactly what
makes a stopped game read as a live one. `scripts/civ6-clean.ps1` stops them in the
right order and then verifies the result instead of assuming it:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\civ6-clean.ps1 -DryRun
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\civ6-clean.ps1
```

It identifies the game by image name and by which process owns the tuner ports, the
MCP server by its command line or by a live connection to that tuner, and the agent
by the project path in its command line. **The DSH Web GUI is never touched**: it is
found by the process listening on `-WebGuiPort` (3080 by default) and excluded from
every kill list, so cleaning up a game cannot take down the interface you drive it
from.

- `-DryRun` reports what it would do and changes nothing.
- `-KeepGame` stops only the agent and the MCP, leaving the game running.
- `-Force` additionally kills node processes that merely *look* like a dsh agent.
  It is only needed when the process table cannot be read: without command lines the
  script refuses to guess, and says so in the plan rather than killing an unrelated
  `node`. (Under the DSH file sandbox `Get-CimInstance Win32_Process` is denied, so
  the fallback path is what runs there; a normal desktop shell gets the exact path.)
- `-WaitSeconds` (default 20) is how long it waits for a several-gigabyte game
  process to finish exiting before it calls the kill a failure. A single 700 ms
  sample was not enough and reported a successful kill as a failure.

It exits 0 only when the environment is actually clean: no game, no tuner listener,
no MCP, no heartbeat. Sessions, diaries, archives and autosaves are never touched —
only live processes and the stale heartbeat.

To get a Git Bash prompt: **Start menu → Git Bash**, or right-click a folder in
Explorer → **Git Bash Here**, or just run
`"C:\Program Files\Git\bin\bash.exe"` from any Windows shell.

If an exported key still seems ignored, remember DSH freezes its environment at
launch: from the credential docs, *"the environment layer is the launcher's
snapshot taken at launch, so a variable exported after startup is not seen."*

---

## 9. Strategy presets

The four advisor prompts can be swapped between victory-path presets without
hand-editing, via `prompts/strategies/` plus a switcher.

```powershell
scripts\use-strategy.cmd              # list presets, show which is active
scripts\use-strategy.cmd science      # apply (live: lands on the next turn)
scripts\use-strategy.cmd balanced     # restore the upstream default
```

On Windows use the `.cmd` wrapper (or `powershell -NoProfile -ExecutionPolicy
Bypass -File scripts\use-strategy.ps1 ...`): this machine's execution policy blocks
`.ps1` files. `bash scripts/use-strategy.sh science` works from Git Bash.

Both scripts now signal failure as **exit 2** on every error path. They previously
used `Write-Error`, which throws under `$ErrorActionPreference = 'Stop'` and
surfaced as exit 1 — indistinguishable from a crash. Verified after the fix: an
unknown preset exits 2 without touching `SKILL.md`, and a preset missing a required
phrase exits 2 with the offending file named.

```bash
bash scripts/use-strategy.sh science
```

| Preset | Victory path |
|---|---|
| `balanced` | upstream default, no bias |
| `expansion` | wide opening: 4–6 cities and universal growth before committing to a victory type; **trade routes may never sit idle**; idle capacity (gold, faith, Great People, envoys) surfaced every turn |
| `science` | Campuses, tall 4–6 cities, Research Alliances, watch rival Spaceports |
| `domination` | one front at a time, siege vs walls, strategic resources, war weariness |
| `religion` | Great Prophet deadline, Holy Sites, theological combat, conversion count |

The `expansion` preset exists because the orchestrator proved good at reacting to
turn-blocking problems but blind to **non-blocking free yields**: across twenty
turns of a live game it never called a single trade tool, leaving trade route
capacity unused the whole time. `end_turn` does emit an `IDLE TRADE ROUTE:` empire
warning, but nothing forces the agent to act on a warning. The preset turns that
into an explicit standing rule for the `economy-cities` advisor, and adds a general
"surface one idle capacity per turn" obligation.

Design notes:

- **Fail-closed.** The switcher validates every file *before* touching
  `prompts/workers/`, then runs the static gate. A preset missing a required
  phrase is rejected with exit 2 and the live prompts are left untouched —
  verified by deliberately stripping a phrase and confirming `prompts/workers/`
  was unmodified.
- **Active preset is detected by SHA-256 comparison**, not a marker file, so a
  hand-edited `prompts/workers/` correctly reports as matching no preset.
- **The roster stays at four roles.** `contracts/worker-proposal.schema.json`
  fixes the `worker` enum and the static gate enforces it, so a fifth advisor is
  not possible without changing both. Strategy is expressed by reweighting the
  four existing roles, including via each proposal's `priority` (0–100).
- **Verified restore.** `balanced` holds a byte-identical copy of the upstream
  prompts (551/576/543/541 bytes), confirmed by hash after a switch cycle.

Full details in `prompts/strategies/README.md`.

---

## 10. Non-portability fixes made along the way

These are not Windows issues, but they were found while getting the setup to
work and are recorded so upstream updates do not silently undo them.

### The diary was per-run, not per-game

`AGENTS.md` documents the diary as *"your persistent memory across sessions"*,
and the skill tells the agent to call `get_diary` when resuming. In practice
`diary_path()` included the run id (`diary_{civ}_{seed}_{run_id}.jsonl`), and the
run id is the per-session logger id — so **every orchestrator restart began with
an empty diary** and the agent resumed blind. Evidence: five diary files for one
game, one per run, none aware of the others.

Fixed in two places that must agree:

| File | Change |
|---|---|
| `src/civ_mcp/diary.py` | `diary_path()` returns `diary_{civ}_{seed}.jsonl`; `run_id` still accepted for callers but ignored |
| `src/civ_mcp/telemetry.py` | the `diary` and `diary_cities` sinks write per-game paths; `log`, `spatial` and `mapturns` deliberately stay per-run |

Existing per-run diaries were merged once into the per-game files (old files left
in place), giving the current game **568 rows covering turns 1-72, 71 of them
agent reflections**. `scripts/convex_sync.py` already accepted the game-only
filename form — its own tests use `diary_india_123.jsonl` — so nothing downstream
needed changing.

Verified: `diary_path()` and the telemetry sink resolve to the same file, the
parser classifies both new forms correctly, and the Python suite still reports
96 passed.

### A single un-ordered unit froze the turn for ten minutes

This was the real cause of the recurring "stall", and the game's own UI gave it
away: it was prompting **"units need orders"** while `end_turn` sat in flight.

`end_turn` resolves end-turn blockers before advancing, and it auto-resolves
eleven kinds. For `ENDTURN_BLOCKING_UNITS` upstream auto-skips **only when every
unit already has zero moves**; if any unit still has a move, it declares a hard
blocker and hands the turn back. That is safe in principle, but the consequence
in practice was the ~9-minute poll budget being burned while the game waited for
a unit order that never came — repeatedly, and each time looking exactly like an
AI-processing hang.

Diagnosis evidence: the session log's final event was a `tool/call` for
`end_turn` with the file then unwritten for the whole window, telemetry showing no
matching completion, the heartbeat frozen on the same turn, and the game alive at
~1.5 cores. The agent had also never once called `skip_remaining_units` in the
entire session.

Changed in `src/civ_mcp/end_turn.py`: the units blocker is now **resolved** the
same way the tool does it — fortify combat units, then skip whatever still has
moves — with a `log.warning` recording that it happened, instead of bouncing the
turn.

Trade-off, stated plainly: the adapter now orders units the agent left un-ordered.
It only does so at `end_turn`, when the agent has declared its plan finished, and
it logs the event. Revert by restoring the upstream block if that is ever judged
too much autonomy.

### Strategy can now be changed mid-game

The strategy lives in the skill's `DIRECTIVE` block, and a skill is read once when
the agent loads it — so for a while every strategy change cost a restart, and the
running session was found to be playing with **no strategy directive at all**
(a session-wide search for the directive's unique phrase returned zero hits).

`src/civ_mcp/strategy_directive.py` plus a three-line hook at the end of the
`end_turn` tool closes that gap: the directive is appended to the `end_turn` result
whenever it has changed, and the agent reads that result every turn. Verified
behaviour: silent while unchanged, reports on change, reports once per process
(covering a session that started from a stale skill load), and a no-op when the
marker block is absent.

```powershell
scripts\use-strategy.ps1 domination   # lands on the next turn, no restart
```

For a one-off strategy that is not worth a preset, three equivalent entry points
write the block directly. They exist because this machine's execution policy
blocks `.ps1` files outright, so the plain `.\scripts\set-strategy.ps1` form fails
with "running scripts is disabled":

| Entry point | Use when |
|---|---|
| `scripts\set-strategy.cmd -Text "..."` | any Windows shell — wraps PowerShell with `-ExecutionPolicy Bypass` |
| `bash scripts/set-strategy.sh -Text "..."` | Git Bash; also safest for non-ASCII text |
| `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\set-strategy.ps1 -Text "..."` | explicit form, no wrapper |

All three support `-Show`, `-Text "<strategy>"` and `-File <path>`; prefer `-File`
for Chinese text, because text passed on a Windows command line is re-encoded by
the console code page and can arrive mangled.

Verified for both the PowerShell and bash paths: `-Show` prints the live directive;
no-args, unknown-arg, missing-file and empty-text all exit 2; and re-injecting the
current text round-trips **byte-identically** (equal SHA-256) with the skill's five
phases and single marker pair intact. That round-trip check is the one that matters
here, because PowerShell 5.1's `Get-Content`/`Set-Content` would mangle every
non-ASCII character.

The permanent alternative is a one-time
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, after which plain `.ps1`
invocation works everywhere (it also unblocks `npm.ps1`); that is a machine-wide
security setting, so it is your call rather than something to apply silently.

Note that an ad-hoc injection is overwritten by the next `use-strategy.ps1 <name>`.

### World Congress votes no longer stall into an empty ballot

`end_turn` has always blocked when the World Congress fires without registered vote
preferences — the session opens and closes *inside* `ACTION_ENDTURN`, so preferences
have to be stored before it is sent. The block itself is correct (it stops a blind
vote), but it had two failure modes:

- a full round trip is spent on every WC, and
- `server.py`'s safety net force-calls `submit_congress()` after the blocker fires
  **three times on the same turn**. With nothing registered, that submits an empty
  ballot — the free vote is simply lost.

`end_turn.py` now registers a **free-vote-only fallback** before it blocks, so the
ballot is never empty even if the agent never comes back:

| | |
|---|---|
| What it votes | option A, first possible target, for every resolution |
| How many votes | exactly 1 per resolution |
| Favor cost | **0** — see below |
| Overridable | yes; `queue_wc_votes` removes the stale handler and replaces it |

Why one vote is free: `lua/congress.py`'s handler initialises
`local votesForThis = 1 / local costForThis = 0` and only raises them by walking
`for v = 2, min(maxWanted, maxV)`. Requesting `votes = 1` makes that loop body
unreachable, so the vote is cast at zero cost. `tests/test_world_congress_fallback.py`
pins that invariant — if the loop ever starts at 1, the "free" vote silently starts
spending favor.

Option A is chosen because in `DLC/Expansion2/Data/Expansion2_Congress.xml` option A
is the "add / improve / buff" side of *every* resolution. The fallback deliberately
does **not** try to be clever about `WC_RES_DIPLOVICTORY`, because the game data
contradicts the advice in `AGENTS.md`:

```
<Row ResolutionType="WC_RES_DIPLOVICTORY" TargetKind="PLAYER"
     Effect1Description="LOC_WORLD_CONGRESS_ADD_DIPLOVICTORY_DESC"      <- option A: ADD
     Effect2Description="LOC_WORLD_CONGRESS_SUBTRACT_DIPLOVICTORY_DESC" <- option B: SUBTRACT
```

`AGENTS.md` says "If a DVP-stripping resolution targets you, vote Option B on
yourself (net 0 vs -2)", but option B is the one that *subtracts* DVP, so that
advice reads backwards. It is left unimplemented rather than guessed; verify it
in-game before acting on it.

A correction to the paragraph above, found by watching the real T151 session:
"option A is the buff side" is true of *most* resolutions, not all.
`WC_RES_MERCENARY_COMPANIES` and `WC_RES_GLOBAL_ENERGY_TREATY` put the ban on A
and the buff on B. The fallback is therefore a least-bad default, not a correct
one - which is exactly why it is capped at the free vote.

### `queue_wc_votes([])` used to spend the whole favour stock

The vote handler treated "no preferences" as "budget favour evenly across the
remaining resolutions":

```lua
local budgetPerRes = math.floor(favor / (resLeft + 1))   -- removed
```

An empty JSON array is falsy in Python, so `queue_wc_votes("[]")` reached that
branch. Against the live T151 session (163 favour, 2 resolutions) it would have
cast 4 votes on one resolution and 5 on the other - **spending 160 of 163
favour** - on option A / first target, for resolutions the agent had never seen
(`get_world_congress` says outright that it is showing *last* session's effects).
This is the kind of bug that never shows up in a unit test and only appears in a
real session.

Two changes, so it cannot recur:

| File | Change |
|---|---|
| `src/civ_mcp/lua/congress.py` | the no-preference branch now sets `budgetPerRes = 0`, so absent preferences mean **one free vote per resolution and no favour spent**. Nothing in the adapter can spend favour on its own any more |
| `src/civ_mcp/server.py` | `queue_wc_votes("[]")` is refused with `ERROR:EMPTY_VOTES` and an explanation of the correct shape |
| `tests/test_world_congress_fallback.py` | pins both: the old budgeting expression must not come back, and the free-vote path must stay free |

Note the interaction with the fallback described above: it only fires when
*nothing* is registered, and an empty array still counted as "registered", so the
fallback could not have caught this. Fixing the default branch is what actually
closes it.

### Two siege defects found by auditing a real campaign (2026-09-20)

Pulled 2252 tool calls from the 15 telemetry runs of one game and rebuilt the
Russia campaign from them. Two adapter defects showed up that no amount of
strategy work would have fixed.

**1. `city_attack` rejected out-of-range targets with nothing to act on.** City
ranged attack reaches 2 tiles; the error said only `Target is 3 tiles away`.
**Four of the five `city_attack` calls in that game died here**, each costing a
full round trip:

```
T108 (49,29) OUT_OF_RANGE      T153 (48,39) OUT_OF_RANGE
T154 (49,31) OUT_OF_RANGE      T157 (49,36) CITY_RANGE_ATTACK  <- the only hit
T158 (50,40) OUT_OF_RANGE
```

The message now scans the city's radius 2 for hostile units and names them, or
says there are none. Distance is a property of the command, not of the tile, so
without that the caller has nothing to aim at.

**2. The combat estimate reported "~0 damage" when attacking a city.** The
defender it finds is whatever unit occupies the tile, and when that unit has 0
combat strength the damage formula short-circuits to zero:

```python
if eff_att > 0 and eff_def > 0:
    dmg_to_def = base_damage * (10 ** ((eff_att - eff_def) / 30))
else:
    dmg_to_def = 0        # a Great Writer / Missionary standing in a city lands here
```

On T167 seven attacks against St. Petersburg all read
`Est damage to defender: ~0` while the walls were going 13 → 3. That reads as
"this attack does nothing", and the real progress sits in a different field of
the same line. The estimate now detects a city on the target tile, says so, and
replaces the meaningless zero with `n/a` plus a pointer at `city walls` /
`garrison`.

| File | Change |
|---|---|
| `src/civ_mcp/lua/cities.py` | out-of-range error lists in-range hostile units, or states there are none |
| `src/civ_mcp/lua/units.py` | estimate probes the target plot for a city and appends its name as a 10th field |
| `src/civ_mcp/lua/models.py` | `CombatEstimate.target_city` (defaults to `""`, so older lines still parse) |
| `src/civ_mcp/narrate.py` | city target: state what actually takes damage, suppress the `~0`, no spurious "LIKELY KILL" |
| `tests/test_siege_fixes.py` | 14 tests covering both, including the 9-field backward-compatibility case |

The city probe uses `Cities.GetCityInPlot(x, y)` — the call the game's own UI Lua
uses (`UnitFlagManager.lua:941`, `WorldInput.lua:456`), read out of the installed
game rather than guessed. It is wrapped in `pcall`, so a failure degrades to the
old behaviour instead of breaking the estimate.

**Caveat:** there is no Lua interpreter on this machine (`lua`, `luac` and
`luajit` are all absent, and the game ships none), so the generated Lua could not
be syntax-checked mechanically. It was checked by dumping the generated source
and reading it — `{{}}` escaping, `end end` pairing, and `gsub` returning a single
value in that assignment. The Python side is covered by tests.

### A World Congress special session stalled the turn until a human voted

Observed live on 2026-09-20, T169 of the China game. China captured **St.
Petersburg — Russia's original capital** — and the game's own notification read
`- 首都被占领` ("capital captured"), with `* 世界议会即将召开` one turn earlier.
That convenes a **special session of the World Congress** (an emergency), and the
session opened *during* `ACTION_ENDTURN`.

The gate at the top of `execute_end_turn` does check `is_in_session`:

```python
if wc_status.turns_until_next <= 0 or wc_status.is_in_session:
```

but it runs **before** `ACTION_ENDTURN` is sent, and the comment right below it
says the session opens *inside* that call. So the gate saw nothing, registered no
voter, and the session then waited for votes that nobody cast. The poll loop only
reads the turn number, so nothing noticed:

| Evidence | Value |
|---|---|
| `get_world_congress` at T169 12:29 | `Next session in 12 turns` — the *regular* counter, which does not include special sessions |
| `end_turn` T169→T170 | `duration_ms = 592953` (593 s, the full budget) |
| `queue_wc_votes` calls in that run | **0** |
| How it finally advanced | a **manual vote in the game UI** — the turn moved at the edge of the HANG threshold |

So the answer to "can the agent handle this?" was no, and it very nearly cost a
kill-and-reload.

**Fix:** `end_turn.py` now probes for an open session from the poll loop —
`_check_mid_turn_world_congress(gs)` — starting 90 s in and then every 120 s, with
a backstop in Phase 3. On finding one it casts **one free vote per resolution**
and calls `submit_congress()`. Unlike the `WorldCongressStage1` handler, which
only fires during the stage that has already passed, this uses the direct
`WORLD_CONGRESS_RESOLUTION_VOTE` operation, which works on a session that is
already open. The note is surfaced as a `TurnEvent` so the agent learns it
happened, and it is logged.

| File | Change |
|---|---|
| `src/civ_mcp/end_turn.py` | `_check_mid_turn_world_congress()`; probes in the Phase 2 loop and Phase 3; the note rides out in the turn events |
| `tests/test_mid_turn_world_congress.py` | 9 tests, including "every vote is the single free one" and "a failing vote does not stop the others" |

Interval is deliberately wide (90 s, then 120 s): the code's own comments warn
that repeated InGame queries during AI processing are themselves a hang trigger,
which is why the existing diplomacy probe is a single call.

**Unverified assumption:** that an emergency's ballot appears in
`wc:GetResolutions()` alongside regular resolutions. `IsInSession()` and a
non-empty resolution list are what the fix keys on; the regular T151 session
behaved that way, but no special session has been exercised against the new code
yet. If it turns out emergencies use a different path, the probe will simply find
nothing and the old behaviour stands — it cannot make things worse.

### The turn-regression guard fought deliberate rollbacks

`end_turn` warns when the turn goes backwards, so that an accidental wrong-save
load (the agent picking the T1 scenario save) gets caught. It cannot tell that
apart from a human deliberately replaying an earlier save, and on 2026-09-20 it
did exactly the wrong thing **twice**:

```
CRITICAL: Turn regressed from 171 to 59. You may have loaded the wrong save file.
Your most recent MCP autosave is 0_MCP_0171.
Use load_game_save("0_MCP_0171") to recover.
```

Both times the rollback was intentional (T165, then T59), and both times the
message instructed the agent to undo it. The in-process `_high_water_turn` cannot
be reset from outside, so a fresh MCP process is the only way to make a rollback
"stick" — which is a heavy price for changing your mind about a save.

Two changes:

| | |
|---|---|
| **Advisory wording** | the message now states both readings — "if that was deliberate, carry on; if not, the newest position is X" — and ends with "Do not reload by reflex". It comes from `_turn_regression_message()`, a pure function, so the wording is testable |
| **`CIV_MCP_ALLOW_TURN_REGRESSION`** | set to `1` to suppress the warning entirely for a planned rollback. Wired into `dsh/civ6.cordis.yml` as `'0'` so it is discoverable |

It also **adopts the new turn as the baseline** in both cases. Previously the
early return skipped the `_high_water_turn` update, so the same warning would
have repeated on every subsequent turn and buried the real events.

| File | Change |
|---|---|
| `src/civ_mcp/end_turn.py` | `_turn_regression_allowed()`, `_turn_regression_message()`, baseline adoption |
| `dsh/civ6.cordis.yml` | `CIV_MCP_ALLOW_TURN_REGRESSION: '0'` with a comment |
| `tests/test_turn_regression.py` | 18 tests: the flag's truthy values, and that the message states both readings, names the newer save as an option rather than an instruction, and does not start with `CRITICAL` |

Verified with `dsh --profile headless --patch dsh/civ6.cordis.yml --dump-config`:
the overlay still composes and the new variable appears in the resolved config.

### Rolling back splits the diary into two branches

The diary is keyed per game, so a rollback leaves the abandoned branch's rows in
the same file. The clamp above stops the agent *reading* the future, but two
problems remain: once the replay passes the cut the file holds two sets of rows
for the same turn numbers, and the two branches cannot be told apart afterwards.

On 2026-09-20 the game was rolled back to **T59**, so the split was done for real:

```
.civ6-mcp-data/branches/abandoned-T60-T174/
    diary_future_T60_T174.jsonl             2093 KB   rows T60..T174
    diary_cities_future_T60_T174.jsonl      1311 KB
    backup-20260920-125838/                          verbatim pre-split copies
    README.md                                        what this is and how to compare
```

Live file afterwards: 464 rows, turns 1..59 (cities: 665 rows, 1..59). The split
is verified by read-back — `464 + 943 = 1407` rows accounted for — and the backup
makes it reversible.

| File | Purpose |
|---|---|
| `.tools/archive-branch.py` | split a diary at a turn boundary; backs up first, verifies by read-back, `--dry-run` available |
| `.tools/compare-branches.py` | `--milestones` for first-appearance targets, `--at N` / no args for side-by-side metrics on overlapping turns |
| `.tools/test-taskfile.ps1` | 12 checks for the PowerShell launcher: exit codes, the newline and double-quote guards, that a bare argument binds to the task, that the pointer is one ASCII line naming the right file, and that the Chinese prompt still carries its BOM |
| `.tools/ensure-utf8-bom.ps1` | put back a dropped UTF-8 BOM, or `-Check` for one without writing |
| `.tools/test-taskfile.sh` | 15 checks for the bash launcher: the same, plus the BOM present on `zh` and absent from `en`, and cross-stack digest parity for both prompts |
| `.tools/_argvprobe.cmd`, `.tools/_argvprobe.mjs` | the reproduction for the argument hop: report what a `.cmd` shim and a native `node.exe` actually receive |
| `.tools/_argprobe.ps1` | test scaffolding: deliver a newline- or quote-bearing argument to the launcher in-process, since no real argv hop can carry it |
| `branches/abandoned-T60-T174/README.md` | provenance, the `<=T60` caveat, and the milestone table |

Two things worth remembering about the tooling:

- The archive starts at the cut, so anything built earlier reports its first
  appearance as the cut turn. The comparator prints `<=T60`, not `T60`, so a
  pre-existing Holy Site does not read as newly built.
- Output goes to `.tools/_branch_compare.txt` in UTF-8 and stdout stays ASCII:
  this console is cp936 and mangles both CJK city names and em dashes. Same
  reason `set-strategy.sh` exists.
