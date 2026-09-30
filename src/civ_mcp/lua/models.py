"""All dataclasses for Lua query responses and game state."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ScoreEntry:
    player_id: int
    civ_name: str
    score: int


@dataclass
class RivalSnapshot:
    """Per-turn stats for a rival civ, for diary power curves."""

    id: int
    name: str
    score: int
    cities: int
    pop: int
    sci: float
    cul: float
    gold: float
    mil: int
    techs: int
    civics: int
    faith: float
    sci_vp: int
    diplo_vp: int
    stockpiles: dict[str, int] = field(default_factory=dict)


@dataclass
class PlayerRow:
    """One row per player per turn for diary JSONL (long format)."""

    pid: int
    civ: str
    leader: str
    is_agent: bool
    # Score & yields
    score: int
    cities: int
    pop: int
    science: float
    culture: float
    gold: float
    gold_per_turn: float
    faith: float
    faith_per_turn: float
    favor: int
    favor_per_turn: int
    # Military
    military: int = 0
    units_total: int = 0
    units_military: int = 0
    units_civilian: int = 0
    units_support: int = 0
    unit_composition: dict[str, int] = field(default_factory=dict)
    # Progress
    techs_completed: int = 0
    civics_completed: int = 0
    techs: list[str] = field(default_factory=list)
    civics: list[str] = field(default_factory=list)
    current_research: str = "NONE"
    current_civic: str = "NONE"
    # Infrastructure
    districts: int = 0
    wonders: int = 0
    great_works: int = 0
    territory: int = 0
    improvements: int = 0
    exploration_pct: int = 0
    # Governance
    era: str = ""
    era_score: int = 0
    age: str = "NORMAL"
    government: str = "NONE"
    policies: list[str] = field(default_factory=list)
    pantheon: str = "NONE"
    religion: str = "NONE"
    religion_beliefs: list[str] = field(default_factory=list)
    # Victory
    sci_vp: int = 0
    diplo_vp: int = 0
    tourism: int = 0
    staycationers: int = 0
    # Resources
    stockpiles: dict[str, int] = field(default_factory=dict)
    luxuries: dict[str, int] = field(default_factory=dict)
    religion_cities: int = 0


@dataclass
class CityRow:
    """One row per city per turn for diary JSONL."""

    pid: int
    city_id: int
    city: str
    pop: int
    food: float
    production: float
    gold: float
    science: float
    culture: float
    faith: float
    housing: float
    amenities: int
    amenities_needed: int
    districts: str  # comma-separated short names
    producing: str
    loyalty: float
    loyalty_per_turn: float
    # Power (Gathering Storm). `power_required` is what the city's power-load buildings draw each
    # turn (Research Lab 3, Stock Exchange 3, Factory 2, ...) and `power_available` what its own
    # free and temporary sources supply; `powered` is the game's own yes/no, because a city is
    # either fully powered or living with reduced building effects - there is no partial state.
    # Defaults are the "not reported" reading (0 required, powered), so a row written by a server
    # that predates these fields never looks like a deficit.
    power_required: float = 0.0
    power_available: float = 0.0
    powered: bool = True


@dataclass
class AgentExtras:
    """Agent-only data not recorded for AI players."""

    diplo_states: dict[str, dict] = field(default_factory=dict)
    suzerainties: int = 0
    envoys_available: int = 0
    envoys_sent: dict[str, int] = field(default_factory=dict)
    gp_points: dict[str, int] = field(default_factory=dict)
    governors: list[dict] = field(default_factory=list)
    trade_capacity: int = 0
    trade_active: int = 0
    trade_domestic: int = 0
    trade_international: int = 0


@dataclass
class DiarySnapshot:
    """Complete per-turn diary snapshot — players, cities, agent extras."""

    players: list[PlayerRow] = field(default_factory=list)
    cities: list[CityRow] = field(default_factory=list)
    agent: AgentExtras = field(default_factory=AgentExtras)


@dataclass
class ReligionInfo:
    """Religion founded by a civilization."""

    player_id: int
    civ_name: str
    religion_name: str  # e.g. "Eastern Orthodoxy"


@dataclass
class GameOverview:
    turn: int
    player_id: int
    civ_name: str
    leader_name: str
    gold: float
    gold_per_turn: float
    science_yield: float
    culture_yield: float
    faith: float
    current_research: str
    current_civic: str
    num_cities: int
    num_units: int
    score: int = 0
    diplomatic_favor: int = 0
    favor_per_turn: int = 0
    explored_land: int = 0
    total_land: int = 0
    rankings: list[ScoreEntry] | None = None
    # Religion slot tracking
    religions_founded: int = 0
    religions_max: int = 0
    our_religion: str | None = None  # religion name if we founded one
    founded_religions: list[ReligionInfo] | None = None
    # Era score tracking
    total_population: int = 0
    era_name: str = ""
    era_score: int = 0
    era_dark_threshold: int = 0
    era_golden_threshold: int = 0
    max_turns: int = 0  # 0 = unlimited / not set
    difficulty: str = ""  # e.g. "King", "Emperor"
    # Gold breakdown
    gold_income: float = 0.0  # gross gold yield before maintenance
    total_maintenance: float = 0.0  # total maintenance cost
    unit_maintenance: int = 0  # maintenance from units specifically
    # Unit type breakdown
    unit_breakdown: dict[str, int] | None = None  # e.g. {"Builder": 45}
    # Game speed
    game_speed: str = ""  # e.g. "GAMESPEED_QUICK"
    game_speed_name: str = ""  # e.g. "Quick"
    speed_cost_multiplier: int = 100  # 67 for Quick, 100 for Standard, etc.
    # Victory conditions (empty = all enabled)
    enabled_victories: set[str] = field(default_factory=set)


@dataclass
class UnitInfo:
    unit_id: int
    unit_index: int
    name: str
    unit_type: str
    x: int
    y: int
    moves_remaining: float
    max_moves: float
    health: int
    max_health: int
    combat_strength: int = 0
    ranged_strength: int = 0
    build_charges: int = 0
    targets: list[str] = field(default_factory=list)
    needs_promotion: bool = False
    can_upgrade: bool = False
    upgrade_target: str = ""
    upgrade_cost: int = 0
    valid_improvements: list[str] = field(default_factory=list)
    religion: str = ""


@dataclass
class SpyInfo:
    unit_id: int  # composite ID (use with spy_action)
    unit_index: int  # per-player index (unit_id % 65536)
    name: str  # e.g. "Artimpasa"
    x: int
    y: int
    rank: int  # 1=Recruit, 2=Agent, 3=Special Agent, 4=Senior Agent
    xp: int
    moves: int
    city_name: str  # city at current position, or "none"
    city_owner: int  # player ID of city owner, or -1
    available_ops: list[str]  # e.g. ["TRAVEL", "COUNTERSPY"]
    current_mission: str = "none"  # active mission e.g. "COUNTERSPY", or "none"
    is_escaping: bool = False  # True if spy is caught and needs escape route
    status: str = "idle"  # "idle", "in_transit", "on_mission", "escaping"


@dataclass
class CityInfo:
    city_id: int
    name: str
    x: int
    y: int
    population: int
    food: float
    production: float
    gold: float
    science: float
    culture: float
    faith: float
    housing: float
    amenities: int
    turns_to_grow: int
    food_surplus: float = 0.0
    food_stored: float = 0.0
    growth_threshold: int = 0
    currently_building: str = "NONE"
    production_turns_left: int = 0
    defense_strength: int = 0
    garrison_hp: int = 0
    garrison_max_hp: int = 0
    wall_hp: int = 0
    wall_max_hp: int = 0
    attack_targets: list[str] = field(default_factory=list)
    pillaged_districts: list[str] = field(default_factory=list)
    pillaged_buildings: list[str] = field(default_factory=list)
    districts: list[str] = field(default_factory=list)
    loyalty: float = 100.0
    loyalty_max: float = 100.0
    loyalty_per_turn: float = 0.0
    turns_to_loyalty_flip: int = 0
    loyalty_outcome: str = ""  # GAINING_LOYALTY / LOSING_LOYALTY / STABLE (see `losing_loyalty`)
    garrison_unit: str = ""
    unimproved_resources: list[str] = field(
        default_factory=list
    )  # e.g. ["HORSES@5,10"]
    pillaged_improvements: list[str] = field(default_factory=list)  # e.g. ["MINE@6,11"]
    buildings: list[str] = field(
        default_factory=list
    )  # completed buildings (BUILDING_ prefix stripped)
    # Power (Gathering Storm). `-1` / "" is the "the server did not report it" reading - a build
    # without the expansion, or a server started before these fields existed - and the rules that
    # look at power switch off on it rather than reading a missing field as a deficit. The numbers
    # are the same table the game's own city panel reads (`City:GetPower()`, CityPanelPower.lua):
    # required is the load of this city's power-hungry buildings, free is what its renewable
    # sources and dams supply, temporary is what an active project supplies.
    power_required: float = -1.0
    power_free: float = -1.0
    power_temporary: float = -1.0
    power_fully_powered: str = ""  # "yes" / "no" / "" when unreported
    power_advice: str = ""  # City:GetPowerAdvice(), the game's own recommendation

    @property
    def power_reported(self) -> bool:
        """True when the server answered the power question at all."""
        return self.power_required >= 0.0 and self.power_fully_powered != ""

    @property
    def power_available(self) -> float:
        """Free plus temporary power: what this city generates for itself, fuel excluded."""
        return max(self.power_free, 0.0) + max(self.power_temporary, 0.0)

    @property
    def unpowered(self) -> bool:
        """A city that needs power and whose own sources do not cover it.

        The game's word decides it (`IsFullyPowered`) - a city is either fully powered or its
        power-load buildings work at reduced strength, so there is no third state to compute.
        """
        return self.power_required > 0.0 and self.power_fully_powered.lower() == "no"

    @property
    def losing_loyalty(self) -> bool:
        """Which way the pool is moving - and therefore what ``turns_to_loyalty_flip`` means.

        ``GetTurnsToConversion()`` is a revolt countdown only while the city is losing loyalty;
        while it gains, the same figure counts turns to a full pool. The game's own word decides
        when we have it; without it, the sign of the pressure is the best reading available.
        """
        outcome = (self.loyalty_outcome or "").upper()
        if outcome.endswith("LOSING_LOYALTY"):
            return True
        if outcome.endswith("GAINING_LOYALTY"):
            return False
        return self.loyalty_per_turn < 0


@dataclass
class ProductionOption:
    category: str  # "UNIT", "BUILDING", "DISTRICT"
    item_name: str  # "UNIT_WARRIOR", "BUILDING_MONUMENT"
    cost: int  # production cost
    turns: int = 0  # estimated turns to produce
    gold_cost: int = -1  # gold purchase cost (-1 = not purchasable)
    is_repair: bool = False  # True if repairing a pillaged district/building
    repair_x: int | None = None  # district repair X coordinate
    repair_y: int | None = None  # district repair Y coordinate


@dataclass
class TileInfo:
    x: int
    y: int
    terrain: str
    feature: str | None
    resource: str | None
    is_hills: bool
    is_river: bool
    is_coastal: bool
    improvement: str | None
    owner_id: int
    visibility: str = "visible"  # "visible", "revealed", or "unexplored"
    is_fresh_water: bool = False
    yields: tuple[int, ...] | None = None  # (food, prod, gold, science, culture, faith)
    units: list[str] | None = None  # visible foreign units, e.g. ["Barbarian WARRIOR"]
    own_units: list[str] | None = (
        None  # player's own units on this tile, e.g. ["WARRIOR", "BUILDER"]
    )
    resource_class: str | None = None  # "strategic", "luxury", "bonus"
    is_pillaged: bool = False
    district: str | None = None  # e.g. "DISTRICT_CAMPUS", None if no district
    owner_name: str | None = (
        None  # resolved name, e.g. "Vatican City" (with :CS suffix for city-states)
    )
    route_type: int = (
        -1
    )  # -1=none, 0=ancient, 1=medieval, 2=industrial, 3=modern, 4=railroad
    movement_cost: int = 1  # base movement cost for land units


@dataclass
class DiplomacyModifier:
    score: int
    text: str


@dataclass
class VisibleCity:
    name: str
    x: int
    y: int
    population: int
    loyalty: float = 100.0
    loyalty_per_turn: float = 0.0
    has_walls: bool = False
    wall_max: int = 0
    defense_strength: int = 0


@dataclass
class AgendaInfo:
    """Leader agenda (historical or hidden random)."""

    category: str  # "HISTORICAL" or "HIDDEN"
    name: str  # localized name, or "???" if hidden
    description: str  # localized description


@dataclass
class CivInfo:
    player_id: int
    civ_name: str
    leader_name: str
    has_met: bool
    is_at_war: bool
    diplomatic_state: str = "UNKNOWN"  # FRIENDLY, NEUTRAL, UNFRIENDLY, etc.
    relationship_score: int = 0
    modifiers: list[DiplomacyModifier] | None = None
    grievances: int = 0
    access_level: int = 0  # 0=None, higher=more visibility
    has_delegation: bool = False
    has_embassy: bool = False
    they_have_delegation: bool = False
    they_have_embassy: bool = False
    available_actions: list[str] | None = None  # actions we can take
    alliance_type: str | None = None
    alliance_level: int = 0
    defensive_pacts: list[int] = field(
        default_factory=list
    )  # player IDs with defensive pacts
    military_strength: int = 0  # their military strength
    num_cities: int = 0  # number of cities they own
    visible_cities: list[VisibleCity] = field(default_factory=list)
    agendas: list[AgendaInfo] = field(default_factory=list)


@dataclass
class LockedCivic:
    name: str
    civic_type: str
    missing_prereqs: list[str]  # localized names of unmet prerequisites
    era: str = ""  # e.g. "ERA_MODERN"
    boosted: bool = False
    boost_desc: str = ""  # trigger description


@dataclass
class LockedTech:
    name: str
    tech_type: str
    missing_prereqs: list[str]  # localized names of unmet prerequisites
    era: str = ""  # e.g. "ERA_MODERN"
    boosted: bool = False
    boost_desc: str = ""  # trigger description


@dataclass
class TechOption:
    """An available technology for research."""

    name: str
    tech_type: str  # e.g. "TECHNOLOGY_MINING"
    cost: int
    progress_pct: int  # 0-100
    turns: int
    boosted: bool
    boost_desc: str  # trigger description, empty if none
    unlocks: str  # comma-separated unlock names
    prereqs: str = ""  # comma-separated prereq tech type names
    era: str = ""  # e.g. "ERA_ANCIENT"


@dataclass
class CivicOption:
    """An available civic for progression."""

    name: str
    civic_type: str  # e.g. "CIVIC_CODE_OF_LAWS"
    cost: int
    progress_pct: int  # 0-100
    turns: int
    boosted: bool
    boost_desc: str  # trigger description, empty if none
    prereqs: str = ""  # comma-separated prereq civic type names
    era: str = ""  # e.g. "ERA_MEDIEVAL"


@dataclass
class TechCivicStatus:
    current_research: str
    current_research_turns: int
    current_civic: str
    current_civic_turns: int
    available_techs: list[TechOption]
    available_civics: list[CivicOption]
    completed_tech_count: int = 0
    completed_civic_count: int = 0
    locked_civics: list[LockedCivic] | None = None
    locked_techs: list[LockedTech] | None = None


@dataclass
class DiplomacyChoice:
    key: str  # e.g. "CHOICE_POSITIVE", "CHOICE_EXIT"
    text: str  # localized display text


@dataclass
class DiplomacySession:
    session_id: int
    other_player_id: int
    other_civ_name: str
    other_leader_name: str
    choices: list[DiplomacyChoice]
    dialogue_text: str = ""  # leader's spoken text (from UI controls)
    reason_text: str = ""  # agenda/reason subtext
    buttons: str = (
        ""  # semicolon-separated visible button labels; "GOODBYE" if goodbye phase
    )
    deal_summary: str = ""  # human-readable deal content when AI proposes a deal (e.g. "They offer: Research Alliance (25 turns)")
    is_at_war: bool = (
        False  # True if this player declared war (session is war declaration)
    )


@dataclass
class CitySnapshot:
    """Minimal city state for diffing between turns."""

    city_id: int
    name: str
    population: int
    currently_building: str
    # City-centre coordinates. The check engine needs them to tell a garrison (a unit standing
    # on the city tile) from a unit that is merely near a city.
    x: int = 0
    y: int = 0
    food_surplus: float = 0.0
    turns_to_grow: int = 0
    loyalty: float = 100.0
    loyalty_per_turn: float = 0.0


@dataclass
class TurnSnapshot:
    """Full game state snapshot taken before/after end_turn."""

    turn: int
    units: dict[int, UnitInfo]  # keyed by unit_id
    cities: dict[int, CitySnapshot]  # keyed by city_id
    current_research: str
    current_civic: str
    stockpiles: list[ResourceStockpile] = field(default_factory=list)


@dataclass
class TurnEvent:
    """An event detected by diffing two snapshots."""

    priority: int  # 1=critical, 2=important, 3=info
    category: str  # "unit", "city", "research", "civic"
    message: str


@dataclass
class GameNotification:
    """An active notification from NotificationManager."""

    type_name: str
    message: str
    turn: int
    x: int
    y: int
    is_action_required: bool = False
    resolution_hint: str | None = None


@dataclass
class CombatEstimate:
    """Predicted combat outcome."""

    attacker_type: str
    defender_type: str
    attacker_cs: int
    defender_cs: int
    is_ranged: bool
    modifiers: list[str]  # ["fortified +6", "hills +3"]
    est_damage_to_defender: int
    est_damage_to_attacker: int  # 0 for ranged
    defender_hp: int
    attacker_hp: int
    # Name of the city on the target tile, "" when the tile holds none. When it
    # is set, the named defender is a unit standing in that city and the CITY is
    # what actually takes the damage.
    target_city: str = ""
    # The defender's domain as the game defines it (`DOMAIN_LAND`, `DOMAIN_SEA`, `DOMAIN_AIR`), or
    # "" when the target is a city or the game did not say. It is what lets the estimate refuse a
    # melee attack on a unit at sea (manual:723) instead of printing a damage number for it.
    defender_domain: str = ""


@dataclass
class PathingEstimate:
    """Estimated turns for a unit to reach a destination."""

    turns: int
    total_tiles: int
    reachable_this_turn: int
    waypoints: list[str] = field(default_factory=list)  # ["(x,y)", ...]


@dataclass
class StagingRingTile:
    """One tile of the target city's ring, at distance 1 (melee/adjacent) or 2 (shooting)."""

    x: int
    y: int
    distance: int
    blocked: bool = False
    water: bool = False


@dataclass
class StagingUnit:
    """One of our fighting units, with the movement it has left.

    ``role`` is ``siege`` / ``ranged`` / ``short-ranged`` / ``melee`` / ``recon``. Recon is its
    own role because a Scout has Combat 10: a test that only asks "is Combat > 0" files it as
    melee and the plan sends it to a tile adjacent to a city, where it dies for nothing.
    """

    unit_type: str
    unit_id: int
    x: int
    y: int
    # Movement the game reports, which can be fractional: a unit holding 1.5 of 3
    # points is normal (measured 2026-09-27), and parsing it as an int is what
    # killed `get_staging_plan` on the Alexandria assault.
    moves: float
    role: str = "melee"  # siege / ranged / short-ranged / melee / recon
    distance: int = 0  # tiles to the target city
    strength: int = 0  # combat strength, for ordering units within a role
    hp: int = 0
    max_hp: int = 0

    @property
    def wounded(self) -> bool:
        """Half health or worse: a front-line unit in this state is a casualty waiting to happen.

        Measured over this war: a 55 HP Horseman attacking a walled city was destroyed outright
        (T154), and a Knight went 52 -> 6 in one blow from a single Man-at-Arms (T151). Relieving
        it is how the ring keeps a screen without paying for a replacement unit.
        """
        return self.max_hp > 0 and self.hp * 2 <= self.max_hp


@dataclass
class StagingOption:
    """A unit's path to one ring tile: turns to arrive, and whether it arrives this turn."""

    unit_id: int
    x: int
    y: int
    turns: int
    this_turn: bool = False
    path_len: int = 0


@dataclass
class StagingPlan:
    """The raw material of a staging plan: the ring, the units, and every option.

    ``next_ring`` / ``next_options`` are the same thing for the *next* objective, when the caller
    named one — surplus units advance toward it rather than idling (human instruction 2026-09-26:
    多余部队还可以向下一个城市目标/蛮族营地集结推进).

    ``camp`` says the target tile holds a **barbarian camp** rather than an enemy city: the ring,
    the paths and the assignments are the same, but a camp has no HP, no walls and no supply line,
    so only the last step (one unit walks onto the tile) and the closing line change. The flag is
    read from the game (`Cities.GetCityInPlot`) and not inferred from the tile's improvement.
    """

    target: str = ""
    ring: list[StagingRingTile] = field(default_factory=list)
    units: list[StagingUnit] = field(default_factory=list)
    options: list[StagingOption] = field(default_factory=list)
    # The **assembly** ring: tiles at distance 3, outside the city's two-tile strike, where a unit
    # forms up before stepping onto the firing ring. Nothing is ever assigned to them (they are not
    # firing tiles); they exist so the plan can print `RALLY x,y d3 T+n`, which is the leg the
    # doctrine asks for and the one the measured failures were about - 底比斯 opened with 2 of 3
    # shooters in place, 亚历山大 with 2 of 5. Empty when the server predates the rally ring.
    rally_ring: list[StagingRingTile] = field(default_factory=list)
    rally_options: list[StagingOption] = field(default_factory=list)
    next_ring: list[StagingRingTile] = field(default_factory=list)
    next_options: list[StagingOption] = field(default_factory=list)
    camp: bool = False
    # A unit to eliminate (in practice a missionary): the ring around it is the job, because a
    # religious unit dies to one attack — the work is getting adjacent and blocking its escape.
    kill_ring: list[StagingRingTile] = field(default_factory=list)
    kill_options: list[StagingOption] = field(default_factory=list)


@dataclass
class SettleCandidate:
    """A candidate location for founding a city."""

    x: int
    y: int
    score: float
    total_food: int
    total_prod: int
    water_type: str  # "fresh", "coast", "none"
    resources: list[str]  # classified: ["S:IRON", "L:DIAMONDS", "B:WHEAT"]
    defense_score: int = 0
    luxury_count: int = 0
    strategic_count: int = 0
    loyalty_pressure: float = (
        0.0  # approx loyalty/turn from population pressure, negative = bad
    )


@dataclass
class FogBoundary:
    """Fog-of-war boundary distances from a city in 6 hex directions."""

    city_name: str
    city_x: int
    city_y: int
    fog_distances: list[int]  # NE,E,SE,SW,W,NW — -1 means all explored


@dataclass
class UnclaimedResource:
    """A luxury or strategic resource on revealed, unowned land."""

    resource_type: str
    x: int
    y: int
    resource_class: str  # "RESOURCECLASS_LUXURY" or "RESOURCECLASS_STRATEGIC"


@dataclass
class StrategicMapData:
    """Strategic map overview: fog boundaries and unclaimed resources."""

    fog_boundaries: list[FogBoundary]
    unclaimed_resources: list[UnclaimedResource]


@dataclass
class ResourceStockpile:
    """Strategic resource stockpile info."""

    name: str
    amount: int
    cap: int
    per_turn: int  # accumulation per turn
    demand: int  # unit upkeep demand per turn
    imported: int  # from trade deals


@dataclass
class OwnedResource:
    """A resource on a tile owned by the player."""

    name: str
    resource_class: str  # "strategic", "luxury", "bonus"
    improved: bool
    x: int
    y: int


@dataclass
class NearbyResource:
    """An unclaimed resource near one of the player's cities."""

    name: str
    resource_class: str
    x: int
    y: int
    nearest_city: str
    distance: int


@dataclass
class SiegePosture:
    """Where one of our siege units stands relative to the enemy.

    Distances are the game's own (``Map.GetPlotDistance``): ``enemy_distance`` to the nearest
    visible enemy unit, ``screen_enemy_distance`` to the nearest enemy of the friendly front
    line unit that is closest to this siege unit (999 when there is no screen at all), and
    ``city_distance`` to the nearest visible enemy city.
    """

    unit_type: str
    x: int
    y: int
    enemy_distance: int = 999
    screen_distance: int = 999
    screen_enemy_distance: int = 999
    city_distance: int = 999
    city_name: str = ""

    @property
    def exposed(self) -> bool:
        """Within enemy reach with nothing *closer* to the enemy than itself.

        Strictly closer: a screen standing exactly as close as the siege unit is not between it
        and the enemy, so it does not count as cover.
        """
        return self.enemy_distance <= 2 and self.screen_enemy_distance >= self.enemy_distance


@dataclass
class CaptureReadiness:
    """An enemy city we can see, with the numbers that decide whether it can be taken now.

    ``hp`` is the city's own HP pool (the city centre's garrison pool - walls are a separate
    pool and are damaged first). ``melee_adjacent`` counts our capture-capable units next to the
    city and ``melee_within_2`` those one tile further out: only a melee-class unit can take a
    city, and only from the city's own tile, so those two numbers *are* the answer to "is this
    city takeable this turn".
    """

    city_name: str
    x: int
    y: int
    hp: int = 0
    max_hp: int = 0
    wall_hp: int = 0
    wall_max: int = 0
    melee_adjacent: int = 0
    melee_within_2: int = 0
    melee_unit: str = ""
    # Supply line: how many of the city's adjacent hexes are cut (one of our military units is on
    # them or beside them). The manual's rule is that a city heals while **any** adjacent hex is
    # outside our zone of control, so `supply_open` decides whether an assault has to out-damage a
    # heal at all - cutting the last open hex is a lever the army can pull.
    supply_covered: int = 0
    supply_total: int = 0
    # Our fighting units within three tiles that still have movement. The supply lever is only
    # pullable if somebody can walk onto the open hexes, and this is that count - measured over
    # the T139-T159 war, the cities that healed back were exactly the ones whose ring stayed at
    # 1/6 or 3/6 cut while spare units sat queued in the corridor.
    idle_within_3: int = 0
    # The open hexes themselves, as "x,y" strings. The count above says a city is healing; this
    # says *where to walk*, which is the difference between a metric and an order (measured
    # T215: 亚历山大 sat at `supply line 3/6 cut` and healed 20 a turn while the report named no
    # hex at all).
    supply_open_hexes: list[str] = field(default_factory=list)

    @property
    def supply_open(self) -> int:
        """Adjacent hexes still feeding the city; zero means it is not healing."""
        return max(0, self.supply_total - self.supply_covered)

    @property
    def supplied(self) -> bool:
        """Still has a supply line, so it still heals about twenty points a turn."""
        return self.supply_total > 0 and self.supply_open > 0

    @property
    def down(self) -> bool:
        """A city whose HP pool is empty: the next melee attack takes it."""
        return self.max_hp > 0 and self.hp <= 0

    @property
    def takeable(self) -> bool:
        """Down, with one of our melee units already next to it."""
        return self.down and self.melee_adjacent > 0


@dataclass
class CityLoyalty:
    """One of our cities' loyalty, and what is holding it up.

    ``loyalty`` is the 0-100 pool, ``loyalty_per_turn`` the current pressure (negative means the
    city is falling) and ``conversion_outcome`` the game's own word for which way it is going
    (``GAINING_LOYALTY`` / ``LOSING_LOYALTY`` / ``STABLE``). ``turns_to_flip`` is
    ``GetTurnsToConversion()`` verbatim, which **is not a revolt countdown on its own**: the game
    reads it together with the outcome (`CityBannerManager.lua:2355-2358` warns only when
    ``LOSING_LOYALTY and nTurns < 20``), and while a city gains, the same figure counts turns to a
    full pool. Use ``turns_to_revolt`` for the revolt reading, ``losing`` for the direction, and
    ``transfer_name`` (only set while losing) for who takes it. ``advice`` is the game's own
    localized recommendation, which is worth more than our guess at the fix.

    Why this exists: a city captured far from home revolts. Live, Moscow was taken at T112 with
    pop 3, no governor and no garrison, appeared as a Free City in the logs at T116, and was
    retaken at T121 - 9 attacks and four turns of the campaign spent on a city we already owned.
    Live again at T121 the same city stood at 50/100, +15/turn, ``turns=4`` and
    ``GAINING_LOYALTY``: recovered in four turns, which a bare countdown calls a revolt in four.
    """

    city_id: int
    city_name: str
    x: int
    y: int
    population: int = 0
    loyalty: float = 100.0
    loyalty_max: float = 100.0
    loyalty_per_turn: float = 0.0
    turns_to_flip: int = 0
    governor: str = ""
    garrison: int = 0
    advice: str = ""
    conversion_outcome: str = ""
    transfer_to: int = -1
    transfer_name: str = ""
    # Power (Gathering Storm), read on the same pass as loyalty so the check path pays no extra
    # round trip: `power_required` is this city's load and `power_available` what its own free and
    # temporary sources give it, fuel excluded (a Coal Power Plant's 1 coal -> 4 power is a fuel
    # question, read from `get_empire_resources`). `powered` is the game's own IsFullyPowered, and
    # defaults to True when a server does not report it, so a pre-power build never reports a
    # deficit it cannot see.
    power_required: float = 0.0
    power_available: float = 0.0
    powered: bool = True

    @property
    def unpowered(self) -> bool:
        """The city needs power and its own sources do not cover it."""
        return self.power_required > 0.0 and not self.powered

    @property
    def losing(self) -> bool:
        """The loyalty pool is draining - the only state in which a countdown means a revolt.

        The game's own word wins when we have it (it is the same call the banner makes); without
        it, the sign of the pressure is the best available reading.
        """
        outcome = (self.conversion_outcome or "").upper()
        if outcome.endswith("LOSING_LOYALTY"):
            return True
        if outcome.endswith("GAINING_LOYALTY"):
            return False
        return self.loyalty_per_turn < 0

    @property
    def turns_to_revolt(self) -> int:
        """Turns until this city becomes a Free City, or 0 when it is not draining."""
        return self.turns_to_flip if self.losing else 0

    @property
    def falling(self) -> bool:
        """Loyalty is going down this turn."""
        return self.losing

    @property
    def low(self) -> bool:
        """Below the point where a revolt is a matter of when, not if."""
        return self.loyalty_max > 0 and self.loyalty < 50

    @property
    def unsupported(self) -> bool:
        """Low loyalty with no governor in the city and no military unit on its tile."""
        return self.low and not self.governor and self.garrison <= 0


@dataclass
class ThreatInfo:
    """A hostile military unit spotted near our empire."""

    unit_type: str
    x: int
    y: int
    hp: int
    max_hp: int
    combat_strength: int
    ranged_strength: int
    distance: int
    owner_id: int = 63
    owner_name: str = "Barbarian"
    is_city_state: bool = False
    unit_id: int = 0
    # PROMOTION_CLASS_* - the game's own rock/paper/scissors axis (MELEE, RANGED,
    # LIGHT_CAVALRY, HEAVY_CAVALRY, ANTI_CAVALRY, SIEGE, RECON, NAVAL_*).
    promotion_class: str = ""
    # Distance to the nearest of our units, cities excluded (999 when we have no units).
    unit_distance: int = 999
    # How many of our *military* units sit within two tiles / adjacent to this enemy. The
    # difference between a lone unit trading blows and a force that can actually kill is this
    # count, so the check engine asks the game for it rather than guessing from coordinates.
    friendly_within_2: int = 0
    friendly_within_1: int = 0


@dataclass
class VictoryPlayerProgress:
    """Victory progress for a single civilization."""

    player_id: int
    name: str  # "Unmet" if not met
    score: int
    science_vp: int  # space race VP (0-50)
    science_vp_needed: int
    diplomatic_vp: int  # need 20 to win
    tourism: int
    military_strength: int
    techs_researched: int
    civics_completed: int
    religion_cities: int  # cities following their religion
    # Culture dominance (only for our civ)
    staycationers: int = 0  # domestic tourists
    # Religion details (only meaningful if they founded one)
    has_religion: bool = False
    # Rival intel
    num_cities: int = 0
    science_yield: float = 0.0
    culture_yield: float = 0.0
    gold_yield: float = 0.0
    # Space race
    spaceports: int = 0
    space_progress: str = ""  # e.g. "3/20"


@dataclass
class DemographicEntry:
    """A single demographics metric (mirrors in-game Demographics panel)."""

    rank: int  # 1-based (1 = best)
    value: float  # our value
    best: float
    average: float
    worst: float


@dataclass
class VictoryProgress:
    """Full victory progress snapshot."""

    players: list[VictoryPlayerProgress]
    # Culture victory details (our perspective)
    our_tourists_from: dict[str, int] = field(
        default_factory=dict
    )  # civ_name -> tourists
    their_staycationers: dict[str, int] = field(
        default_factory=dict
    )  # civ_name -> domestic tourists
    # Domination: who holds their original capital?
    capitals_held: dict[str, bool] = field(
        default_factory=dict
    )  # civ_name -> still_holds_own_capital
    # Religion majority per civ
    religion_majority: dict[str, str] = field(
        default_factory=dict
    )  # civ_name -> religion name
    # Religion slot tracking
    religion_founded_names: dict[str, str] = field(
        default_factory=dict
    )  # civ_name -> religion display name
    religions_founded: int = 0
    religions_max: int = 0
    # Demographics (anonymized aggregates for all civs, mirrors in-game panel)
    demographics: dict[str, DemographicEntry] = field(default_factory=dict)
    # Space race project detail (our player only)
    space_projects: list[SpaceProject] = field(default_factory=list)
    # Which victory types are enabled (empty = all enabled / unknown)
    enabled_victories: set[str] = field(default_factory=set)


@dataclass
class SpaceProject:
    """Status of a single space race project."""

    project_type: str  # e.g. "PROJECT_LAUNCH_EARTH_SATELLITE"
    name: str  # localized name
    status: str  # "completed" / "building" / "available" / "locked"
    progress_pct: int = 0  # 0-100, only if building
    turns_remaining: int = 0  # only if building
    cost: int = 0  # speed-adjusted production cost
    tech_prereq: str = ""  # e.g. "TECH_ROCKETRY"
    has_tech: bool = False
    city_name: str = ""  # city building it (if status=building)


@dataclass
class DealItem:
    """A single item in a trade deal."""

    from_player_id: int
    from_player_name: str
    item_type: str  # "GOLD", "RESOURCE", "AGREEMENT", "FAVOR", "CITY", "GREAT_WORK"
    name: str  # human-readable: "Gold", "Tobacco", "Open Borders"
    amount: int
    duration: int  # 0 = lump sum, >0 = per-turn
    is_from_us: bool


@dataclass
class PendingDeal:
    """A trade deal offered by another civilization."""

    other_player_id: int
    other_player_name: str
    other_leader_name: str
    items_from_them: list[DealItem] = field(default_factory=list)
    items_from_us: list[DealItem] = field(default_factory=list)


@dataclass
class TradeableCity:
    city_id: int
    name: str
    population: int
    is_capital: bool


@dataclass
class DealOptions:
    """What's available to trade with a civilization."""

    other_player_id: int
    other_civ_name: str
    our_gold: int = 0
    our_gpt: int = 0
    our_favor: int = 0
    their_gold: int = 0
    their_gpt: int = 0
    their_favor: int = 0
    our_luxuries: list[str] = field(default_factory=list)
    our_strategics: list[str] = field(default_factory=list)
    their_luxuries: list[str] = field(default_factory=list)
    their_strategics: list[str] = field(default_factory=list)
    our_cities: list[TradeableCity] = field(default_factory=list)
    their_cities: list[TradeableCity] = field(default_factory=list)
    has_open_borders: bool = False
    alliance_eligible: bool = False
    current_alliance: str | None = None


@dataclass
class TestTradeItem:
    side: str  # "US" or "THEM"
    item_type: str  # GOLD, RESOURCE, AGREEMENT, FAVOR, CITY, GREAT_WORK
    amount: int
    duration: int
    value_id: str  # e.g. "YIELD_GOLD", "RESOURCE_HORSES"
    subtype_id: str  # e.g. "DIPLOACTION_OPEN_BORDERS"


@dataclass
class TestTradeResult:
    other_player_id: int
    other_civ_name: str
    proposed: list[TestTradeItem] = field(default_factory=list)
    counter: list[TestTradeItem] = field(default_factory=list)
    rejected: bool = False


@dataclass
class PolicySlot:
    """A government policy slot with its current policy."""

    slot_index: int
    slot_type: (
        str  # "SLOT_MILITARY", "SLOT_ECONOMIC", "SLOT_DIPLOMATIC", "SLOT_WILDCARD"
    )
    current_policy: str | None
    current_policy_name: str | None


@dataclass
class PolicyInfo:
    """An available (unlocked) policy."""

    policy_type: str  # e.g. "POLICY_AGOGE"
    name: str
    description: str
    slot_type: str  # compatible slot type


@dataclass
class GovernmentStatus:
    """Current government and policy configuration."""

    government_name: str
    government_type: str
    slots: list[PolicySlot] = field(default_factory=list)
    available_policies: list[PolicyInfo] = field(default_factory=list)


@dataclass
class GovernorInfo:
    """An available governor type."""

    governor_type: str
    name: str
    title: str
    description: str = ""
    base_ability: str = ""  # name of the base (level 0) promotion
    base_ability_desc: str = ""  # description of the base promotion
    promotions: list["GovernorPromotion"] = field(default_factory=list)


@dataclass
class GovernorPromotion:
    """A promotion available for a governor."""

    promotion_type: str
    name: str
    description: str
    level: int = 0  # 0 = base ability, 1-3 = promotion tiers
    column: int = 0  # position in the promotion tree


@dataclass
class AppointedGovernor:
    """A governor the player has appointed."""

    governor_type: str
    name: str
    assigned_city_id: int  # -1 = unassigned
    assigned_city_name: str  # "Unassigned" if not placed
    is_established: bool
    turns_to_establish: int = 0
    available_promotions: list[GovernorPromotion] = field(default_factory=list)


@dataclass
class GovernorStatus:
    """Full governor status for the player."""

    points_available: int
    points_spent: int
    can_appoint: bool
    appointed: list[AppointedGovernor] = field(default_factory=list)
    available_to_appoint: list[GovernorInfo] = field(default_factory=list)


@dataclass
class PromotionOption:
    """A promotion available for a unit."""

    promotion_type: str
    name: str
    description: str


@dataclass
class UnitPromotionStatus:
    """Promotions available for a specific unit."""

    unit_id: int
    unit_index: int
    unit_type: str
    promotions: list[PromotionOption] = field(default_factory=list)
    xp: int = 0
    xp_needed: int = 0
    promotion_count: int = 0


@dataclass
class CityStateInfo:
    """A known city-state with envoy info."""

    player_id: int
    name: str
    city_state_type: str  # "Scientific", "Industrial", "Trade", etc.
    envoys_sent: int  # envoys we've sent
    suzerain_id: int  # player ID of suzerain (-1 = none)
    suzerain_name: str  # "None" or civ name
    can_send_envoy: bool


@dataclass
class EnvoyStatus:
    """Full envoy status for the player."""

    tokens_available: int
    city_states: list[CityStateInfo] = field(default_factory=list)


@dataclass
class BeliefInfo:
    """A pantheon belief available for selection."""

    belief_type: str  # e.g. "BELIEF_DANCE_OF_THE_AURORA"
    name: str
    description: str


@dataclass
class PantheonStatus:
    """Current pantheon status and available beliefs."""

    has_pantheon: bool
    current_belief: str | None  # belief type if has pantheon
    current_belief_name: str | None
    faith_balance: float
    available_beliefs: list[BeliefInfo] = field(default_factory=list)


@dataclass
class UnitUpgradeInfo:
    """Info about a unit's upgrade path."""

    unit_id: int
    current_type: str
    upgrade_type: str  # e.g. "UNIT_ARCHER"
    upgrade_name: str
    gold_cost: int
    can_upgrade: bool
    reason: str = ""  # failure reason if can't upgrade


@dataclass
class DedicationChoice:
    """A dedication/commemoration available for selection."""

    index: int
    name: str  # e.g. "COMMEMORATION_SCIENTIFIC"
    normal_desc: str  # bonus in Normal age
    golden_desc: str  # bonus in Golden/Heroic age
    dark_desc: str  # bonus in Dark age


@dataclass
class DedicationStatus:
    """Current dedication/commemoration state."""

    age_type: str  # "Normal", "Golden", "Dark", "Heroic"
    era: int
    era_score: int
    dark_threshold: int
    golden_threshold: int
    selections_allowed: int
    active: list[str] = field(default_factory=list)
    choices: list[DedicationChoice] = field(default_factory=list)


@dataclass
class DistrictPlacement:
    """A valid tile for placing a district, with adjacency bonuses."""

    x: int
    y: int
    adjacency: dict[str, int]  # yield_type -> bonus (e.g. {"science": 3})
    total_adjacency: int
    terrain_desc: str  # e.g. "Plains Hills"


@dataclass
class WonderPlacement:
    """A valid tile for placing a wonder, ranked by displacement cost."""

    x: int
    y: int
    terrain: str  # e.g. "TERRAIN_GRASS_HILLS"
    feature: str  # e.g. "FEATURE_JUNGLE" or "none"
    has_river: bool
    is_coastal: bool
    resource: str  # e.g. "RESOURCE_IRON" or "none"
    improvement: str  # e.g. "IMPROVEMENT_FARM" or "none"
    displacement_score: (
        int  # 0 = empty bare tile (best), higher = more valuable yields lost
    )


@dataclass
class PurchasableTile:
    """A tile that can be purchased with gold."""

    x: int
    y: int
    cost: int
    terrain: str
    resource: str | None
    resource_class: str | None  # "strategic", "luxury", "bonus"


@dataclass
class StaticMapTile:
    """Per-tile static terrain data from full map dump."""

    terrain: int  # TerrainType index
    feature: int  # FeatureType index (-1 = none)
    hills: bool
    river: bool
    coastal: bool
    resource: int  # ResourceType index (-1 = none)


@dataclass
class StaticMapDump:
    """Full static terrain dump of the game map."""

    grid_w: int
    grid_h: int
    tiles: list[StaticMapTile]  # row-major: index = y * grid_w + x
    initial_owners: list[int]  # one per tile, -1 = unowned
    initial_routes: list[int]  # one per tile, -1 = none
    initial_cities: list[tuple[int, int, int, int, str]]  # (x, y, pid, pop, name)
    players: list[tuple[int, str, str | None]]  # (pid, civ_type, cs_type)


@dataclass
class OwnershipDelta:
    """Per-turn ownership/road changes + city snapshot."""

    owner_changes: list[tuple[int, int]]  # (tile_idx, new_owner)
    road_changes: list[tuple[int, int]]  # (tile_idx, route_type)
    cities: list[tuple[int, int, int, int, str]]  # (x, y, pid, pop, name)


@dataclass
class GreatPersonInfo:
    """Info about an available or claimed Great Person."""

    class_name: str  # e.g. "Great Scientist"
    individual_name: str  # e.g. "Hypatia"
    era_name: str
    cost: int  # great person points needed to recruit
    claimant: str  # civ name or "Unclaimed"
    player_points: int  # our points toward this class
    ability: str = ""  # the individual's own action: for a General/Admiral this
    #                    is a RETIREMENT and `activate` consumes the unit
    passive: str = ""  # aura the unit grants while alive; only Great Generals and
    #                    Great Admirals have one, and activating throws it away
    gold_cost: int = 0  # gold patronize cost
    faith_cost: int = 0  # faith patronize cost
    can_recruit: bool = False  # have enough GP points
    individual_id: int = 0  # GameInfo index for recruit/patronize actions


@dataclass
class GPAdvisorCity:
    """A candidate city for Great Person activation."""

    city_name: str
    city_id: int
    district_x: int
    district_y: int
    can_activate: bool  # GP can activate here right now
    distance: int  # hex distance from GP's current position
    city_yield: int = 0  # city's total yield for the relevant type
    slots_free: int = -1  # empty great work slots (-1 = N/A)
    slots_total: int = -1  # total great work slots (-1 = N/A)


@dataclass
class GPAdvisorResult:
    """Result of GP placement advisor query."""

    gp_name: str
    gp_class: str
    target_district: str
    gp_x: int
    gp_y: int
    charges: int
    cities: list[GPAdvisorCity]


@dataclass
class TradeDestination:
    """A valid trade route destination city."""

    city_name: str
    owner_name: str  # civ/city-state name, or "Domestic"
    x: int
    y: int
    is_domestic: bool
    is_city_state: bool = False
    has_quest: bool = False  # city-state wants a trade route
    has_trading_post: bool = False  # established trading post (bonus yields)
    origin_yields: str = ""  # e.g. "Food:3 Prod:2 Gold:4"
    dest_yields: str = ""  # food+prod for domestic routes
    pressure_out: float = 0.0  # our religion → destination
    religion_out: str = ""  # our majority religion name
    pressure_in: float = 0.0  # their religion → our city
    religion_in: str = ""  # destination's majority religion name


@dataclass
class TraderInfo:
    """A trader unit with its route status."""

    unit_id: int
    x: int
    y: int
    has_moves: bool
    on_route: bool = False
    route_origin: str = ""  # origin city name
    route_dest: str = ""  # destination city name
    route_owner: str = ""  # civ/city-state name
    is_domestic: bool = False
    origin_yields: str = ""  # e.g. "Food:3 Prod:2 Gold:4"
    dest_yields: str = ""
    pressure_out: float = 0.0  # our religion → destination
    religion_out: str = ""
    pressure_in: float = 0.0  # their religion → our city
    religion_in: str = ""
    has_quest: bool = False
    is_city_state: bool = False


@dataclass
class TradeRouteStatus:
    """Trade route capacity and trader status."""

    capacity: int
    active_count: int
    traders: list[TraderInfo] = field(default_factory=list)
    ghost_count: int = 0  # ghost route records inflating engine count


@dataclass
class CongressResolution:
    """A resolution to vote on or that has been passed."""

    resolution_type: str  # e.g. "WC_RES_MERCENARY_COMPANIES"
    resolution_hash: int  # e.g. -1027166762
    name: str  # e.g. "Mercenary Companies"
    target_kind: str  # e.g. "YIELD", "RELIGION", "PLAYER"
    effect_a: str  # description of option A
    effect_b: str  # description of option B
    possible_targets: list[str]  # ["Production", "Gold", ...] or player names etc.
    is_passed: bool = False
    winner: int = -1  # 0=A won, 1=B won
    chosen_thing: str = ""  # target that was chosen


@dataclass
class CongressProposal:
    """A discussion proposal to vote on."""

    sender_id: int
    sender_name: str
    target_id: int
    target_name: str
    proposal_type: int
    description: str


@dataclass
class WorldCongressStatus:
    """Full World Congress state."""

    is_in_session: bool
    turns_until_next: int
    favor: int
    max_votes: int
    favor_costs: list[int]  # [0, 10, 30, 60, 100, 150]
    resolutions: list[CongressResolution]
    proposals: list[CongressProposal]


# --- Scattered dataclasses (originally defined mid-file near their builders) ---


@dataclass
class GameOverStatus:
    is_game_over: bool
    is_defeat: bool  # True = we lost, False = we won
    winner_name: str
    winner_leader: str
    victory_type: str  # e.g. "VICTORY_RELIGIOUS", "VICTORY_SCIENCE"
    player_alive: bool


@dataclass
class ReligionBeliefOption:
    """A belief available for selection when founding/enhancing a religion."""

    belief_class: str  # BELIEF_CLASS_FOLLOWER, BELIEF_CLASS_FOUNDER, etc.
    belief_type: str  # e.g. BELIEF_WORK_ETHIC
    name: str
    description: str


@dataclass
class ReligionFoundingStatus:
    """Religion founding status and available options."""

    has_religion: bool
    religion_type: str | None  # e.g. RELIGION_HINDUISM
    religion_name: str | None
    pantheon_index: int
    faith_balance: float
    available_religions: list[tuple[str, str]] = field(
        default_factory=list
    )  # (type, name) pairs
    beliefs_by_class: dict[str, list[ReligionBeliefOption]] = field(
        default_factory=dict
    )


@dataclass
class CityReligionInfo:
    player_id: int
    civ_name: str
    city_name: str
    majority_religion: str  # display name or "none"
    population: int
    followers: dict[str, int]  # religion_name -> follower count


@dataclass
class ReligionSummary:
    religion_name: str
    civs_with_majority: int
    total_majors: int


@dataclass
class ReligionStatus:
    cities: list[CityReligionInfo]
    summary: list[ReligionSummary]


@dataclass
class BuilderTask:
    priority: str  # "urgent", "high", "normal"
    x: int
    y: int
    improvement: str  # e.g. "IMPROVEMENT_MINE"
    resource: str  # e.g. "IRON", "" for non-resource tiles
    resource_class: str  # "strategic", "luxury", "bonus", "pillaged", ""
    city_name: str
    nearest_builder_id: int = -1
    distance: int = 999


@dataclass
class BuilderInfo:
    unit_id: int  # composite ID
    unit_index: int
    x: int
    y: int
    charges: int
    moves: float
