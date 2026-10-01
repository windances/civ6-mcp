> 本文件是 `save-file-format.md` 的中文备份（由英文文件翻译而来，供人阅读）：DSH 只读英文文件，请勿在此修改。

# Civ 6 存档文件格式

从 `CHANDRAGUPTA 215 1520 AD.Civ6Save`（1,799,939 字节）逆向工程得出。
基于社区工具（[pydt/civ6-save-parser](https://github.com/pydt/civ6-save-parser)、[lucienmaloney/civ6save-editing](https://github.com/lucienmaloney/civ6save-editing)）以及原创分析。

## 概述

一个 `.Civ6Save` 文件有两部分：

```
[Uncompressed header ~390KB] [Zlib-compressed game data ~1.4MB → 16MB]
```

文件头包含游戏配置（速度、地图、难度、本地化 JSON、已安装的领袖/文明池）。压缩段包含全部游戏状态：地图地块、战争迷雾、每玩家时间线、城市记录、回放数据集以及修饰符定义。

## 文件头

以魔数字节 `CIV6` 开头。使用 4 字节标记 ID 的带标签键值对：

| 标记 | 字段 | 类型 |
|--------|-------|------|
| `9D 2C E6 BD` | GAME_TURN（见注释） | int32 |
| `99 B0 D9 05` | GAME_SPEED | string（例如 `GAMESPEED_STANDARD`） |
| `40 5C 83 0B` | MAP_SIZE | string（例如 `MAPSIZE_SMALL`） |

**关于 GAME_TURN 的说明——2026-09-27 实测，它在这个版本中并不成立。** 共扫描了六个存档
（T216-T218，两个系列）：该标记在每一个中都只出现**一次**，位置大约在字节 88,600 处，而紧随其后的
int32 在每一个中都读作 **`2`**。因此无法从文件头读取回合数，工具报告的回合数来自解压后的
时间线（`scripts/parse_save.py`：`meta.game_turn = first_tl[-1].turn`）。`handoff` 和
`turn-of-save.py` 都经过那个解析器，这就是为什么读取一个存档的真实回合只需大约十分之一秒，
而不是完整加载一次游戏。

标记之后的类型字节：`1`=bool，`2`=int32，`5`=string，`6`=UTF string，`0x0A`=array。

文件头还包含完整的领袖/文明池（每一个已安装的 DLC 领袖），而不只是当前活跃的玩家。活跃玩家必须从游戏状态数据中识别。

### 定位压缩数据

```python
mod_index = save_data.rfind(b'MOD_TITLE')
buf_start = save_data.index(b'\x78\x9c', mod_index)  # zlib magic
```

## 解压

压缩数据使用 **zlib，按 64KB 分块，块之间有 4 字节间隔**。标准的 `zlib.decompress()` 会失败。

```python
import zlib

buf_end = save_data.rfind(b'\x00\x00\xff\xff')
comp_data = save_data[buf_start:buf_end + 4]

# Split into 64KB chunks, strip 4-byte spacers between chunks
CHUNK_SIZE = 64 * 1024
chunks = []
pos = 0
while pos < len(comp_data):
    chunks.append(comp_data[pos:pos + CHUNK_SIZE])
    pos += CHUNK_SIZE + 4  # skip 4-byte spacer

combined = b''.join(chunks)
d = zlib.decompressobj()
decompressed = d.decompress(combined)
decompressed += d.flush(zlib.Z_SYNC_FLUSH)
```

结果：约 16MB 的二进制数据块。

## 解压后数据布局

```
Offset      Size        Content
─────────────────────────────────────────────
0x000000    ~1.2MB      Map data (tiles, terrain, features, improvements)
~1.2MB      ~7MB        Per-player data blocks (one per civ + city-states)
~8MB        ~6MB        City-state data, modifier definitions
~14.6MB     ~0.4MB      Citizen names, river names, geographic features
~15.0MB     ~0.5MB      Modifier/requirement definitions (GAME_EFFECTS)
~15.47MB    ~0.3MB      Replay dataset labels + notification templates
~15.77MB    ~0.5MB      Per-player per-turn timelines (yields, stats, score)
~15.74MB    ~0.03MB     Per-city production history records
~16.0MB     ~0.3MB      (sparse/zero padding)
```

### 地图尺寸

地图尺寸以地块数量编码。已知尺寸：

| 地块数 | 尺寸 | 地图大小 |
|-------|-----------|----------|
| 1144 | 44×26 | Duel |
| 2280 | 60×38 | Tiny |
| 3404 | 74×46 | Small |
| 4536 | 84×54 | Standard |
| 5760 | 96×60 | Large |
| 6996 | 106×66 | Huge |

通过搜索由三个连续 int32 构成的 `[tiles, width, tiles]` 模式来找出尺寸。

### 战争迷雾

按队伍存储，**每个地块一个字节**（不是每个比特）。每个字节是 `0x00`（迷雾）或 `0x01`（已揭示）。

```
17 teams × 3,404 bytes = 57,868 bytes of fog data
```

队伍是 5 个 int16 数组（observation、modifiers、resources、roads、unknown）的组合，每个数组各有 `tile_count` 个条目，队伍边界之间有 12 字节的标记。

印度（我们存档中的 Team 16）已揭示 2,255/3,404 个地块（66.2%）。

### 地块数据段

通过搜索以下标记来定位：
```
[0x0E, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00, 0x06, 0x00, 0x00, 0x00]
```

每个地块是变长的：
```
base:       55 bytes (terrain hash, feature hash, road level, appeal, etc.)
+ overlay:  24 bytes if overlay flag at byte 51 is non-zero
+ ownership: 17 bytes if ownership byte at byte 49 >= 64
```

存档中的地形/特征类型哈希与 FNV-1a 不匹配——Civ 6 使用了另一种哈希算法（尚未确认）。海洋与陆地可以通过陆块索引（landmass indices）区分。

## 每玩家每回合时间线

12 个具名的时间线数组，每个数组包含 215 个条目（每回合一个），形式为 `(turn: int32, value: int32)` 对。每个名称有六个块 = 每个主要文明一个。

### 可用的时间线

| 名称 | 类型 | 说明 |
|------|------|-------------|
| `Score` | 累计 | 总得分 |
| `Gold` | 快照 | 金币国库余额 |
| `Science` | 快照 | 每回合科技产出 |
| `Culture` | 快照 | 每回合文化产出 |
| `Faith` | 快照 | 每回合信仰产出 |
| `Favor` | 累计 | 累计的外交支持 |
| `TechsAcquired` | 累计 | 已研究的科技 |
| `CivicsAcquired` | 累计 | 已完成的市政 |
| `BarbariansKilled` | 累计 | 击杀的蛮族单位 |
| `BarbarianCampsCleared` | 累计 | 清除的蛮族营地 |
| `DiploVP` | 累计 | 外交胜利点数 |
| `ScienceVP` | 累计 | 科技胜利点数 |

### 定位时间线

以长度前缀字符串的形式搜索时间线名称，其后是 `0xD7000000`（count=215），然后是 215 对 `(turn: uint32, value: int32)`。

```python
name_pos = data.find(b'Gold')  # in the 15.77M+ region
count_pos = name_pos + len('Gold') + padding  # skip to count
assert struct.unpack('<I', data[count_pos:count_pos+4]) == (215,)

for i in range(215):
    turn = struct.unpack_from('<I', data, count_pos + 4 + i*8)[0]
    value = struct.unpack_from('<i', data, count_pos + 4 + i*8 + 4)[0]
```

### 示例：Score 时间线

```
Player 1: T1=4   T50=49   T100=145  T150=250  T200=353  T215=402
Player 2: T1=0   T50=34   T100=75   T150=182  T200=301  T215=329
Player 3: T1=0   T50=47   T100=131  T150=248  T200=330  T215=329
Player 4: T1=0   T50=48   T100=166  T150=304  T200=426  T215=447
Player 5: T1=0   T50=42   T100=143  T150=260  T200=350  T215=373
Player 6: T1=0   T50=65   T100=168  T150=293  T200=468  T215=524
```

## 回放数据集

在约 15.47M 处发现 30 个具名的数据集类别。这些是映射到实际时间线数据的标签/元数据：

| 数据集 | 追踪内容 |
|---------|---------------|
| SCOREPERTURN | 每回合得分 |
| SCIENCEPERTURN | 每回合科技产出 |
| CULTURE | 每回合文化产出 |
| FAITHPERTURN | 每回合信仰产出 |
| TOTALGOLD | 金币国库 |
| ERASCORE | 时代得分 |
| TOTALCITIESBUILT | 建立的城市（累计） |
| TOTALCITIESDESTROYED | 被夷平的城市 |
| TOTALCITIESCAPTURED | 被占领的城市 |
| TOTALCITIESLOST | 失去的城市 |
| TOTALDISTRICTSBUILT | 建造的区域 |
| TOTALBUILDINGSBUILT | 建成的建筑 |
| TOTALWONDERSBUILT | 建成的奇观 |
| TOTALUNITSDESTROYED | 击杀的敌方单位 |
| TOTALPLAYERUNITSDESTROYED | 损失的自有单位 |
| TOTALCOMBATS | 交战总次数 |
| TOTALWARSDECLARED | 宣战的次数 |
| TOTALWARSWON | 赢得的战争 |
| TOTALWARSAGAINSTPLAYER | 针对玩家宣战的次数 |
| TOTALRELIGIONSFOUNDED | 创立的宗教 |
| TOTALPANTHEONSFOUNDED | 创立的万神殿 |
| GREATPEOPLEEARNED | 招募的伟人 |
| GOVERNORS | 任命的总督 |
| GOVERNORTITLES | 获得的总督头衔 |

## 每城市生产历史

位于约 15.74M 处。每条城市记录包含：

```
TurnFounded: <turn_number>
  BuildingsBuiltByType:  <player_id> → BUILDING_name
  UnitsTrainedByType:    <player_id> → UNIT_name
  UnitsKilledByType:     <player_id> → UNIT_name (killed FROM this city)
  UnitsLostByType:       <player_id> → UNIT_name (lost FROM this city)
  DistrictsBuiltByType:  <player_id> → DISTRICT_name
  WondersBuiltByType:    <player_id> → BUILDING_name
  GovernmentInUseByType: <player_id> → GOVERNMENT_name
  CurrentGovernment:     <player_id> → GOVERNMENT_name
```

所有城市都有记录（主要文明的城市、城邦、被占领的城市）。

### 类别记录格式

```
[4B string_len]["CategoryName"][4B player_id][4B zeros][1B flag][4B value][4B zeros]
[4B string_len]["ENTITY_NAME"]
```

城市记录中的玩家 ID 与时间线块中的相同（主要文明为 1-6）。

### 识别文明

存档文件头包含所有已安装的领袖（含 DLC 共 80+ 个），而不只是活跃的 6 个。活跃玩家必须通过生产记录中的独特单位/区域来识别：

| 独特项目 | 文明 |
|------------|-------------|
| UNIT_MAYAN_HULCHE | 玛雅 |
| UNIT_EGYPTIAN_CHARIOT_ARCHER | 埃及 |
| UNIT_PERSIAN_IMMORTAL | 波斯 |
| DISTRICT_OBSERVATORY | 玛雅 |
| DISTRICT_THANH | 越南 |

在生产记录中没有独特项目的玩家，需要交叉参照每玩家数据块中的城市名称（每个主要文明都有一个约 1MB 的数据块，其中包含它的城市名称池）。

## 每玩家数据块

每个主要文明在 1-8MB 区域都有一个约 1MB 的块，其中包含：
- 城市名称池（`LOC_CITY_NAME_*` 字符串）
- 单位数据、改良设施数据、地块所有权
- 城市特定状态（产出、建筑、人口）

城市名称字符串可用来识别文明：
```
1.4MB-1.6MB: India (Patna, Mysore, Mumbai, Ahmadabad, Madurai, Agra)
2.6MB-2.7MB: Maya (Naranjo, Tikal, Palenque, Uxmal, Coba)
4.6MB-4.8MB: Ottoman (Istanbul, Izmir, Sivas, Edirne)
5.9MB-6.1MB: Egypt (Ra-Kedet, Sais, Thebes, Abydos, Swenett)
7.1MB-7.3MB: Persia (Mashhad, Susa, Pasargadae, Bakhtri, Hagmatana)
```

城邦占据 8-14MB 区域：
```
La Venta, Yerevan, Nan Madol, Caguana, Singapore,
Akkad, Kumasi, Geneva, Kandy, Shahr-i-Qumis
```

## DLC 条目

文件头包含一个已安装 DLC/模组条目的带标签数组。该数组按每个玩家槽位重复一次（通常为 6 份拷贝）。

### 结构

每份拷贝以一个**计数字段**（uint32）开始，后跟 `0x0A`（数组类型标记），然后是 N 个 DLC 块：

```
[count: uint32][0x0A][padding: 6 bytes][block_0][block_1]...[block_N-1]
```

每个 DLC 块以标记 `05 00 00 00 00 04 00 00 00 54 5F C4 04` 开始，其后是：
- 一个 36 字符的 GUID 字符串（以 null 结尾）
- 一个 JSON 本地化载荷：`{"LOC_<NAME>_MOD_TITLE":[<locale array>]}`
- 结尾的标记字节

块的大小约为 150–1000 字节，取决于 JSON 包含多少条本地化字符串。Leader Pass 条目具有空的本地化数组（`:[]}`），而大多数其他 DLC 包含 `de_DE`、`en_US`、`es_ES`、`fr_FR` 等。

### Leader Pass 与 Linux

6 个 Leader Pass DLC（Great Builders、Great Commanders/Warlords、Great Negotiators、Rulers of the Sahara、Rulers of China、Rulers of England）**从未被 Aspyr 移植到原生 Linux 版本**。在安装了 Leader Pass 的 Windows/macOS 上创建的存档包含这些条目，而 Linux 二进制程序拒绝加载它们——在“加载游戏”界面中以红色显示这些 DLC 名称（显示为德语，因为该二进制程序无法解析本地化键）。

`scripts/strip_leader_pass.py` 工具通过以下方式移除这些条目：
1. 找出所有带有 Leader Pass 键（`GREAT_BUILDERS`、`RULERS_OF_ENGLAND`、`GREAT_NEGOTIATORS`、`RULERS_OF_CHINA`、`RULERS_OF_THE_SAHARA`、`GREAT_WARLORDS`）的 DLC 块
2. 从 6 份文件头拷贝中各自切除该块的字节
3. 将每份拷贝中的计数字段递减（例如 23 → 17）

这样每个存档减少约 5.8KB，并使存档可以在原生 Linux 上加载，且不影响游戏玩法。

## 存档文件中没有的内容

存档存储的是**累计计数器和快照**，而不是事件日志：

- **没有逐回合的行动日志**：单个单位的移动、逐个地块的决策以及研究顺序的变更都没有被记录。只存在累计计数（训练的单位、获得的科技）。
- **没有战斗细节**：总战斗次数和击杀数有统计，但没有哪些单位在哪里交战，也没有造成的伤害。
- **没有外交事件历史**：没有友谊、联盟或战争何时开始的记录——只有当前状态。
- **没有生产队列历史**：只有每个城市建成了什么，没有顺序，也没有被换掉的内容。

### 对专家对局数据库的意义

要构建一个专家人类对局的数据库，仅靠存档文件是不够的。你能得到：
- **宏观曲线**：产出、得分、科技、市政在 215 个回合中如何增长
- **建成了什么**：每一个单位、建筑、区域、奇观——以及是哪个城市生产的
- **战略里程碑**：科技/市政完成、奇观建成、营地清除、战争的准确回合
- **政体选择**：采用了哪些政体以及何时采用

你得不到：
- **微观决策**：单位移动、地块改良顺序、战斗战术
- **原因**：没有推理或决策背景
- **研究路径**：只有完成的回合，没有排入队列或被切换的内容

要获得完整的行动级数据，你需要以下之一：
1. 在实时游玩过程中记录 MCP 工具调用（我们的日记系统就是这么做的）
2. 挂接游戏自身的 Lua 事件系统，实时记录行动
3. 解析多个连续的自动存档，对比游戏状态的变化
