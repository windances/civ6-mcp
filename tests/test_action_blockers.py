"""Every deliberate write clears the popup layer first.

The failure this exists for (live T103): a stack of 22 popups - a cinematic camera, a
natural-disaster screen and a run of invites - sat in front of the game while
`set_city_production` reported success. It is not that the call errored: the Lua returned
`PRODUCING`, and the readback said the engine had not persisted anything
(`SILENT_FAILURE|... NOT_SET|current=nil|expected=BUILDING_ETEMENANKI`), three times in a row.
After `dismiss_popup` emptied the layer the identical call landed on the first attempt.

`move_unit` and `attack_unit` carried that guard inline because the same thing had been measured
on them; the rest of the writes did not, so a popup could silently eat a policy change, a
promotion or a purchase exactly the way it ate that wonder. `clears_blockers` puts the guard on
all of them, and these tests hold it there - a method that loses its decorator is a method that
can start lying again without any test noticing.
"""

from __future__ import annotations

import asyncio
import inspect
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from civ_mcp.game_state import GameState, clears_blockers  # noqa: E402

# The verbs that change the game. Naming them one by one is the point: a new write method that
# is not listed here is a method the popup layer can eat in silence.
WRITES = (
    "move_unit",
    "attack_unit",
    "city_attack",
    "resolve_city_capture",
    "found_city",
    "condemn_heretic",
    "pillage_tile",
    "fortify_unit",
    "skip_unit",
    "skip_remaining_units",
    "automate_explore",
    "heal_unit",
    "alert_unit",
    "sleep_unit",
    "delete_unit",
    "improve_tile",
    "remove_feature",
    "repair_improvement",
    "remove_improvement",
    "sacrifice_builder_charges",
    "set_city_production",
    "purchase_item",
    "set_research",
    "set_civic",
    "diplomacy_respond",
    "send_diplomatic_action",
    "respond_to_deal",
    "propose_trade",
    "propose_peace",
    "form_alliance",
    "set_policies",
    "appoint_governor",
    "assign_governor",
    "promote_governor",
    "promote_unit",
    "send_envoy",
    "choose_pantheon",
    "found_religion",
    "upgrade_unit",
    "choose_dedication",
    "purchase_tile",
    "change_government",
    "recruit_great_person",
    "patronize_great_person",
    "reject_great_person",
    "make_trade_route",
    "activate_great_person",
    "spread_religion",
    "teleport_to_city",
    "vote_world_congress",
    "submit_congress",
    "queue_wc_votes",
    "set_city_focus",
    "spy_travel",
    "spy_mission",
)

# Recovery paths rather than turn actions: a popup in front of a load is a different situation,
# and `docs/game-recovery.md` owns what to do about it.
NOT_WRITES = ("dismiss_popup", "end_turn", "load_save", "load_game_save")


class TestTheGuardIsOnEveryWrite:
    def test_every_named_write_carries_the_decorator(self):
        missing = [
            name
            for name in WRITES
            if not getattr(getattr(GameState, name), "_clears_blockers", False)
        ]
        assert missing == [], f"these writes let a popup eat them silently: {missing}"

    def test_the_recovery_paths_are_deliberately_not_wrapped(self):
        wrapped = [
            name
            for name in NOT_WRITES
            if getattr(getattr(GameState, name), "_clears_blockers", False)
        ]
        assert wrapped == []

    def test_the_list_covers_every_mutating_method_on_the_class(self):
        """A new write method must be classified, not forgotten.

        Reads are told apart by their prefix; anything else that does not start with an
        underscore is a write this test expects to see in `WRITES`.
        """
        reads = ("get_", "check_", "narrate_", "parse_", "list_", "is_", "has_", "find_", "build_")
        reads += ("staging_plan", "target_report", "reinforcements", "visible_foreign_cities")
        reads += ("unused_attacks", "siege_posture", "capture_readiness", "city_loyalty")
        reads += ("test_trade", "execute_lua", "dismiss_popup")
        unclassified = []
        for name, member in vars(GameState).items():
            if not inspect.iscoroutinefunction(member) or name.startswith("_"):
                continue
            if name in WRITES or name in NOT_WRITES or name.startswith(reads):
                continue
            unclassified.append(name)
        assert unclassified == [], (
            f"new method(s) {unclassified} are neither a read nor in WRITES - decide whether a "
            "popup can eat them"
        )


class _Recorder:
    """Records the order of the popup clear and the write it guards."""

    def __init__(self):
        self.order = []

    async def execute_write(self, lua):
        self.order.append("write")
        return ["OK:FORTIFIED|1 fortified"]

    async def execute_read(self, lua):
        self.order.append("read")
        return ["OK:SKIPPED|1 units"]


def _gs() -> GameState:
    gs = GameState.__new__(GameState)
    gs.conn = _Recorder()

    async def _popup():
        gs.conn.order.append("dismiss")
        return "DISMISSED|NaturalDisasterPopup"

    gs.dismiss_popup = _popup
    return gs


class TestItRunsBeforeTheAction:
    def test_the_dismiss_lands_before_the_first_write(self):
        gs = _gs()
        asyncio.run(gs.fortify_unit(0))
        assert gs.conn.order[0] == "dismiss"
        assert "write" in gs.conn.order

    def test_a_dismiss_that_throws_does_not_fail_the_action(self):
        """A layer the game will not let us clear is a reason to try anyway, not to refuse."""

        class _Broken(_Recorder):
            async def execute_write(self, lua):
                return ["OK:FORTIFIED|1 fortified"]

        gs = GameState.__new__(GameState)
        gs.conn = _Broken()

        async def _boom():
            raise RuntimeError("tuner busy")

        gs.dismiss_popup = _boom
        assert asyncio.run(gs.fortify_unit(0)) == "FORTIFIED|1 fortified"

    def test_the_helper_itself_swallows_and_reports_empty(self):
        gs = GameState.__new__(GameState)

        async def _boom():
            raise RuntimeError("tuner busy")

        gs.dismiss_popup = _boom
        assert asyncio.run(gs._clear_action_blockers()) == ""


def test_the_decorator_preserves_the_wrapped_signature():
    """The MCP schema is generated from the signature - a `*args` wrapper would flatten it."""

    @clears_blockers
    async def sample(self, city_id: int, item_type: str) -> str:
        return "ok"

    params = list(inspect.signature(sample).parameters)
    assert params == ["self", "city_id", "item_type"], params
