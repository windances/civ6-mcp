> 本文件是 `PUSH-TO-GITHUB.md` 的中文备份（由英文文件翻译而来，供人阅读）：DSH 只读英文文件，请勿在此修改。

# 把这份检出推送到 GitHub，以及把改动拉回来

## 把改动拉下来

这个分支是在这里创建的，所以它一开始**没有上游**：`git status -sb` 会打印 `## main`，而没有 `...origin/main`。设置一次跟踪关系，之后 `pull` 就可以不带参数使用：

```powershell
git push -u origin main         # pushes and records the upstream in one step
git pull --ff-only              # afterwards: fast-forward only, never a surprise merge
```

不加 `-u` 的话，就要显式点名分支：`git pull --ff-only origin main`。

在拉取之前，先看看有什么在等着你：

```powershell
git fetch origin
git status -sb                          # "behind N" / "ahead M"
git --no-pager log --oneline HEAD..origin/main    # in the remote, not here yet
git --no-pager diff --stat HEAD..origin/main
```

如果 pull 以*"Your local changes would be overwritten"*为由拒绝，先把这些改动暂存起来：

```powershell
git stash -u
git pull --ff-only origin main
git stash pop
```

在一个仍然有 CRLF 换行的 shell 脚本的克隆里（也就是 `npm run bootstrap` 失败的那种），拉取之后把工作副本修一次——`.gitattributes` 只对 git 重写的文件生效：

```powershell
git add --renormalize .
git checkout -- '*.sh' '*.bash'
```

然后重新构建并重新验证：`npm run bootstrap:win`、`npm run qualify`、`.\.venv\Scripts\python.exe -m pytest tests -q`。

针对**这个**目录有两条专门的提醒：它是游戏会话的工作树，而且 `prompts/checks/turn-checks.md` 和技能是每回合都要读取的——所以要在回合边界处拉取，不要在回合中途拉。另外，某次拉取如果改动了 `pyproject.toml`，就必须重新同步 Python 环境（`npm run bootstrap:win` 会做这件事）。

## 把这份检出推送到 GitHub

这份工作副本是以 **zip** 包而不是克隆的形式拿到的，所以没有可推送的历史：仓库必须在这里初始化，而记录下这些工作的那个提交是一个**根提交**（与 `origin/main` 无关）。正因如此，普通的 `git push` 会被以 non-fast-forward 为由拒绝，而 `git push --force` 会**替换掉上游历史**——不要用它。（这一步已经做完了：`cc1c4a1` 已经在 `origin/main` 上；保留这段话是为了下次还要从 zip 包重复这套操作时用。）

正确的做法是把这些工作叠到上游之上，并且在一个有网络访问权限的终端里操作（维护这个仓库所用的沙箱 shell 完全没有对外的 HTTPS，Git 的凭据助手在那里也跑不起来——它需要的管道被沙箱拒绝）：

```powershell
cd C:\mine\mine\ws_dsh\civ6

# 1. Get upstream history. Reviewed: this commit is a snapshot of the whole tree, so the diff
#    against upstream is only "our changes" if the zip was taken from (or near) this commit.
git fetch origin main

# 2. Move this branch onto upstream, keeping the working tree. The index still holds our
#    snapshot, so the next diff is exactly our changes vs upstream.
git reset --soft origin/main

# 3. REVIEW before committing. Anything upstream changed since the zip was taken shows up here
#    as a change of ours - look at it, because it is the one thing that can go wrong.
git status --short
git --no-pager diff --stat --cached origin/main

# 4. Commit on top of upstream. The snapshot commit's full message is kept in
#    .git/COMMIT_MSG.txt, so it does not matter which hash it had before the reset.
git commit -F .git/COMMIT_MSG.txt

# 5. Push.
git push origin main
```

如果第 3 步显示某些上游文件被回退，而这项工作从未碰过它们，那就不要提交：如实说明，并改为从一份全新的克隆重新取一次 zip 包。

## 行尾符：`*.sh` 必须保持 LF

`npm run bootstrap` 会运行 `bash scripts/bootstrap.sh`，而在 Windows 上 `bash` 解析到的是 `C:\WINDOWS\system32\bash.exe`（WSL）。一份 CRLF 的检出会让 bash 把最后一个词读成 `pipefail\r`，于是失败并报 `: invalid option name` / `line 2: set: pipefail`。Git for Windows 自带 `core.autocrlf=true`，所以没有 `.gitattributes` 的话，每个克隆都会重写这些脚本，每个 bash 入口点都会坏掉。这条策略钉在 `.gitattributes` 里（`*.sh`、`*.bash` = LF；`*.cmd`、`*.bat`、`*.ps1` = CRLF）。

在一个已经有 CRLF 脚本的克隆里，从索引重写它们一次：

```powershell
git add --renormalize .          # index: LF for the scripts
git checkout -- '*.sh' '*.bash'  # working tree: rewritten with LF
```

`git config --global core.autocrlf input` 可以在这台机器上的每个仓库里杜绝这一类问题；在一台要运行 POSIX shell 脚本的 Windows 机器上，它值得设置。

## 这个快照提交里包含什么

*把战略指令变成一份被强制执行、可审计的契约*：MCP 侧的回合检查及其反馈（目标退役与文件清扫、接触指标、`BATTLE ASSESSMENT`、`SIEGE POSTURE`、`SIEGE PROGRESS` / `SIEGE STALLED`、未使用攻击的报告、每次攻击都显示的城防 HP、以 `ACTION_ENDTURN` 基线报告的我们自己的损失、`[IN <city>]` 标记），`prompts/tactics/` 下的六个战术文件，技能里的顾问 brief/validate/trace 契约，以及 509 个测试。

`.tools/` 在这个仓库里是被 git 忽略的；文档引用到的五个验证脚本（`advisor-rehearsal.py`、`verify-advisor-proposal.py`、`siege-retro.py`、`goal-status.py`、`show-check-prune.py`）被强制加入版本控制，好让那些引用不至于悬空。
