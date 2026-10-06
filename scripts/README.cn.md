# scripts

命令行工具集。所有命令都在仓库根目录执行；下文的 `python` 指项目虚拟环境——Windows 上是
`.venv\Scripts\python.exe`，其他平台是 `.venv/bin/python`。

这里大多数脚本通过 FireTuner 连接活着的《文明 VI》（即"路线 A"驱动器，在没有 MCP 会话占用连接时使用）。
不连游戏的标为 **offline**。

## 数据放在哪里

会话一次只读一个开局。数据根目录下每个开局一个子目录，外加一个 `current` 指针；
**每个脚本都会替你解析 `current`**，所以没有任何命令需要传 run 参数。

```
.civ6-mcp-data/
  current                     -> china-911679432-a
  runs/
    china-911679432-a/        run.json、日记、退役目标状态、心跳、saves/
  branches/                   回滚归档（所有开局共用）
  loc-en-names.json           本地化表（所有开局共用）
```

每次会话开始都会打印一行 `SESSION` 和一行 `RUN`，点名当前开局，并把该 run 期望的 `(civ, seed)`
与载入的游戏比对。不匹配时打印 `RUN MISMATCH`，且 `play-turn.py end` 会**拒绝推进回合**（除非 `--force`）。
目录里没有 `run.json` 则完全不做校验，未命名的环境行为与从前一模一样。

## 开局

```powershell
python scripts\run.py status                     # 本目录声明的身份 vs 游戏实际的身份
python scripts\run.py init --id china-a --label "中国征服 A 线" --from-game
python scripts\run.py touch --turn 116           # 记录进度（play-turn.py end 也会做）
python scripts\run.py clear
#   init 参数：--civ --seed --notes --from-game --replace

python scripts\runs.py inventory                 # 按开局分组列出数据根目录里的东西
python scripts\runs.py plan                      # 只打印迁移计划（不写盘）
python scripts\runs.py apply --current china-911679432-a
python scripts\runs.py verify                    # 断言各局之间不重叠
```

`--from-game` 从**载入的游戏**取身份而不是从命令行取，这样清单不可能写错到别的存档上。

## 打一个回合

```powershell
python scripts\orient.py                                  # 完整定位读取；先打 SESSION 和 RUN 行
python scripts\orient.py --only diplomacy,units
python scripts\orient.py --full --only governors
python scripts\orient.py --maps --radius 2

python scripts\play-turn.py <动词> ...
```

`play-turn.py` 的动词：

| 动词 | 作用 |
|---|---|
| `units` | 每个单位的序号、类型、坐标与剩余移动力 |
| `move <单位> <x> <y>` | 下令移动，然后打印单位**实际**停在哪里 |
| `march <TYPE:X,Y> ...` | 一次一个单位，屏卫在前、攻城在后 |
| `attack <单位> <x> <y>` | 攻击一个格子；城市格按城市结算 |
| `diplo` / `respond <pid> POSITIVE\|NEGATIVE` | 列出并回答打开的外交会话 |
| `dismiss` | 清掉弹窗层（灾难、邀请、科技/市政完成屏） |
| `scan <x> <y> [半径]` | 射程内的敌方城市，加叙述式地图 |
| `civic <市政>` | 开始一个市政 |
| `produce <城> <项> [X,Y]` | 设置生产；类别自动解析 |
| `purchase <城> [项]` | 用金币购买，或 `--faith`；不给项则列出买得起的 |
| `improve <单位> <改良>` | 建造者或军事工程师的工作 |
| `order <单位\|all> <fortify\|heal\|alert\|sleep\|skip\|auto>` | 单位指令 |
| `governor`、`dedication`、`research`、`pantheon` | 其余回合结束阻塞项 |
| `clear`、`posture` | 政策槽；攻城阵型报告 |
| `end [--force]` | 结束回合，带"未用攻击"和阵型两道守卫 |

城市可以用 `city_id`（工具打印出来的那个，例如 `65536`）或名字给出。

```powershell
python scripts\target-report.py 53 14 [--reinforcements] [--radius N]
python scripts\staging-plan.py 58 39 [--next] [--turns N] [--kill]
python scripts\probe-tile.py 58,30 57,27
```

- `target-report.py` —— 一次调用给出战前各道门：格子与城市（城墙、血量池、驻军、防御）、三格内可见敌人，
  以及带逐格 `FIRE` / `NO LINE OF SIGHT` 判定的集结计划。`--reinforcements` 追加"队列里每个单位第几回合
  到达集结点"。
- `staging-plan.py` —— 只出集结表。`--next` 继续到下一个目标。
- `probe-tile.py` —— 指定格子的原始 `TileInfo`。

## 记录日记

`play-turn.py end` **不会**追加日记行；这个是干那个的。落后是**漏了一步**，不是缺能力，
日记落后时 `SESSION` 行的 `NOTE` 会点名它。

```powershell
python scripts\record-turn.py --reflections t99.json     # 五个契约字段，全部非空
python scripts\record-turn.py --show
python scripts\record-turn.py --retro
```

## 回滚

```powershell
python scripts\rollback-to-turn.py 59                  # 只出计划
python scripts\rollback-to-turn.py 59 --apply          # 归档未来、恢复过去
python scripts\rollback-to-turn.py 59 --archive-only
python scripts\rollback-to-turn.py 59 --force
#   还有：--save <名> --no-checks --no-diary --no-tasks

python scripts\turn-of-save.py --list                  # 每个存档里是第几回合
python scripts\turn-of-save.py "<路径>.Civ6Save"       # 单个存档，不载入
```

回滚是五件事：归档目标回合之后的自动存档、在边界处切分日记、把目标回合之后退休的临时任务恢复、
把被退休的 `once: true` 规则放回来**并且**在持久目标状态里遗忘它们，然后按游戏当前状态选正确的重启方式。
它还会把该 run 记录的进度**退回到目标回合**。

**另一种选择是遗忘过去，而不是把它恢复回来**——同一局，从载入的位置继续打，完全不带着"怎么走到这里的
记忆"：

```powershell
python scripts\fresh-start.py 352               # 只出计划：会忘掉什么、保留什么
python scripts\fresh-start.py 352 --apply       # 执行（会话在跑时拒绝）
python scripts\fresh-start.py 352 --apply --tasks   # 同时撤掉正在生效的临时任务
python scripts\fresh-start.py 352 --apply --force
```

`fresh-start.py` 会忘掉本局的日记（run 副本**以及**遗留根副本）、达成状态，以及
`prompts/checks/turn-checks.md` 里属于本局的 `achieved T...` 注释（标着别的对局的注释不动——这个文件是
共用的）——并且对每条注释把规则本体从 `prompts/checks/archive/` 装回去，因为规则文件的契约就是"一条退役
规则要么活着、要么可追溯"，即"注释走、规则留"。它还会把清单里"已打到第几回合"重置、清掉 run 的会话残留。
默认**保留**正在生效的临时任务（任务是指令，不是记忆），并打印 `temp-task.py retire` 命令让你有意地撤掉
某一条；**`--tasks` 会把它们全部撤掉**，走的正是同一条命令：任务文件移入 `prompts/tasks/tmp/done/`、登记册
行删掉、`AGENTS.md` 的 `IN FORCE NOW` 行随之重建。`branches/` 下的全部归档都保留，包括它自己先写下的那份
备份：被忘掉的整棵树在 `branches/fresh-start-<stamp>/files/` 下，所以操作可撤销。先停会话
（`stop-agent.py --wait`）；否则脚本会拒绝，因为活着的会话一个回合内就会把日记写回来。

## 把一局交给新会话

```powershell
scripts\resume-game.ps1 [-DryRun] [-Wait] [-Rollback] [-HumanMilitary]
#   还有：-TaskFile <f> -TaskPath <f> -Turns N -TimeoutSeconds N -PollSeconds N

python scripts\handoff.py [--json] [--task <路径>]
scripts\civ6-clean.ps1 [-DryRun] [-KeepGame] [-Force] [-PID N] [-TunerPort N] [-WebGuiPort N]
scripts\stop-agent.py [--status | --cancel] [--wait N] [--no-clean] [--note "..."]
scripts\run-dsh-headless.ps1 -TaskFile <f> [-Task <t>] [-DryRun]
```

`civ6-clean.ps1` 现在把 `runs/` 下的过期心跳也算作"未干净"，不再只看根目录那一个。
`stop-agent.py` 用温和的方式请正在跑的会话停下——它在会话的工具结果里写请求文件、记录请求何时送达，
在会话不予理会时兜底执行 `civ6-clean.ps1 -KeepGame`。

**`-HumanMilitary` 把这一局的指挥权分成两半。** 它会把一段"分工"文本追加到启动会话所用的任务里：人类
指挥军事单位、大军事家和大海军统帅，会话负责其余所有单位（**包括大科学家和大商人**）以及城市、经济、
奇观和研究，而且**每回合先动**。这段文本在**两条路径**上都会追加，所以 `-DryRun` 预览的就是会话真正
会收到的任务（它会打印 `--- the division of labour is in the task above ---`），而且追加是幂等的：任务
文件里已经有标记时原样不动。它是*任务*，不是规则——没有任何机制能机械地阻止一个无视它的会话。真正在
约束它的是每回合的报告（`get_notifications` 会追加 `WHOSE MOVE|` 那份划分，并把 `agent-half.txt` 写在
心跳文件旁边）、`SKILL.md` 里对 `skip_remaining_units` 的例外条款，以及"等人类操作"这件事本来就要由
会话自己守住。

## 任务与文档门禁

```powershell
python scripts\temp-task.py status
python scripts\temp-task.py add --title "..." --instruction "..." --expires-turn N
python scripts\temp-task.py retire 020 --done --turn 237 --note "..."

python scripts\fix-text-encoding.py [--check]     # 强制门禁：BOM / GBK 往返损坏
python scripts\repair-text.py [--apply] [--verbose]
python scripts\install-hooks.py [--revert]
```

## 本地化

这张表每台机器从游戏自己的文本文件建一次，所有开局共用。无论游戏设成什么语言，它都让工具输出保持英文：
优先用记录旁边的类型码，其次用**按标签空间限定**的反查表；解析不出来的名字**原样返回**。表不存在不是错误。

```powershell
python scripts\build-loc-names.py            # 建立或刷新
python scripts\build-loc-names.py --check    # 只报告
#   还有：--game <安装路径> --out <路径>
```

## 策略与顾问简报

```powershell
scripts\use-strategy.ps1 -Name <预设> [-List] [-IgnoreDirective]
scripts\set-strategy.ps1 -File <f> | -Text | -Show

python scripts\advisor-brief.py --role military-map --tactics 04,05,06
#   还有：--preset <f> --snapshot <f> --signals <f> --out <f> --check
```

## 资质、诊断与分析

```powershell
python scripts\qualify-mcp.py                  # 无密钥的 MCP 启动与工具发现
node scripts\qualify-static.mjs                # 对交付产物的静态检查

python scripts\test_connection.py [host] [port]
python scripts\test_game_state.py [--map <x> <y>] [--radius N] [--map-only]
python scripts\test_queries.py

python scripts\experiment-report.py --game china_911679432 [--step N] [--json] [--verdict] [--compare]
```

## 启动器、存档与批处理

```powershell
python scripts\launch_save.py [AutoSave_0221] [--kill-first] [--no-launch]
python scripts\install_saves.py [--force] [--dry-run]
python scripts\menu_audit.py [--save <名>] [--skip-launch]
python scripts\parse_save.py <存档> [-o out.jsonl] [--csv] [--player N] [--raw]

python scripts\orchestrator.py launch|resume|preflight|logs|kill-all|abandon [...]
python scripts\convex_sync.py --prod [--upload <目录>] [--cloud <url>] [--watch]
python scripts\analyze.py <子命令> [--game-id ...] [--model ...] [...]
```

## 本目录的每个文件

| 脚本 | 类型 | 用途 |
|---|---|---|
| `advisor-brief.py` | offline | 从教义与快照组装顾问简报 |
| `analyze.py` | offline | CivBench 分析 CLI：工具调用模式、策略、评测 |
| `auto-turns.py` | live | 无人值守地打例行发展回合 |
| `bootstrap.ps1` / `bootstrap.sh` | offline | 一次性环境准备 |
| `build-loc-names.py` | offline | 从游戏安装目录建立本地化表 |
| `civ6-clean.ps1` | offline | 停掉游戏、tuner 监听和过期心跳 |
| `civbench_data.py` | offline | 给 notebook 与协作者用的数据访问库 |
| `convex_sync.py` | offline | 把 JSONL 遥测同步到 Convex |
| `dump-dsh-config.sh` | offline | 打印 DSH overlay 配置 |
| `experiment-report.py` | offline | 从原始记录里取某次实验的数字 |
| `extract_tool_docs.py` | offline | 抽取 MCP 工具元数据供文档站使用 |
| `fix-text-encoding.py` | offline | 强制门禁：BOM / 乱码 |
| `generate_sas_token.py` | offline | 给协作者用的只读 SAS token |
| `handoff.py` | offline | 新会话能不能接手这一局，从哪个存档 |
| `install-hooks.py` | offline | 安装或还原仓库的 git hooks |
| `install_saves.py` | offline | 把评测存档装进文明 VI 的存档目录 |
| `launch_save.py` | offline | 启动游戏并用 OCR 导航菜单载入存档 |
| `menu_audit.py` | live | 每个菜单阶段截图与 OCR |
| `orchestrator.py` | offline | 派发、监控与管理基准运行 |
| `orient.py` | live | 一次完整的重新定位读取 |
| `parse_save.py` | offline | 从 `.Civ6Save` 提取逐玩家逐回合时间线 |
| `play-turn.py` | live | 没有 MCP 会话时下一个指令或读一次扫描 |
| `probe-tile.py` | live | 指定格子的原始 `TileInfo` |
| `publish_hf_dataset.py` | offline | 把基准发布到 Hugging Face Datasets |
| `qualify-mcp.py` | offline | 无密钥的 MCP 启动与工具发现 |
| `qualify-static.mjs` | offline | 对交付产物的静态资质检查 |
| `record-turn.py` | live | 从直连会话追加本回合的日记行 |
| `repair-text.py` | offline | 修复 PowerShell 往返损坏的文本 |
| `resume-game.ps1` | offline | 检查并把暂停的对局交给新会话 |
| `rollback-to-turn.py` | offline | 把游戏回滚到指定回合 |
| `run-dsh-headless.ps1` / `.sh` | offline | 无头跑一次 DSH 会话 |
| `run-dsh-web.ps1` / `.sh` | offline | 启动 DSH web 界面 |
| `run.py` | live | 命名本局并断言载入的游戏与之一致 |
| `runs.py` | offline | 整理并验证按开局分开的数据目录 |
| `scrape_wiki_images.py` | offline | 抓取领袖头像与文明标志 |
| `set-strategy.ps1` / `.sh` / `.cmd` | offline | 把指令文本写进 skill |
| `split_game_log.py` | offline | 一次性：把 `game_log.jsonl` 按会话拆开 |
| `staging-plan.py` | live | 目标城市的集结表 |
| `target-report.py` | live | 城市或营地的战前各道门 |
| `temp-task.py` / `.sh` / `.cmd` | offline | 增加、退休与查看临时任务 |
| `test_connection.py` | live | FireTuner 连接冒烟测试 |
| `test_game_state.py` | live | 跑一遍每个 `GameState` 读取方法 |
| `test_queries.py` | live | 跑一遍每个 Lua 查询构造器与解析器 |
| `turn-of-save.py` | offline | 存档里是第几回合，不载入 |
| `use-strategy.ps1` / `.sh` / `.cmd` | offline | 把策略预设载入 skill |
