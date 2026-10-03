"""The World Congress gate must not block a turn it has nothing to collect.

`execute_end_turn` registers a vote handler before ACTION_ENDTURN, because a World Congress
session opens and closes synchronously inside it. The gate that guards that had a second
condition - `and not wc_status.is_in_session` - and it defeated its own escape:

  * `is_in_session` is true for a World Congress that is *opening* this turn with an empty
    resolution list, not only for one that is genuinely open with resolutions to cast;
  * the free-vote fallback is built **from the resolutions**, so with zero resolutions it is
    empty, `if fallback:` is false, and the handler is never registered;
  * the gate therefore returned the same "call end_turn() again" message on every call.

Measured T293 in the china--1894041591 run: 0 resolutions, `is_in_session` true, and `end`
printed the identical block three times while the turn stood still. `dismiss_popup` found no
popups and `.tools/whats-on-screen.py` showed the ordinary map, so the block was in this
condition and not in a dialog.

The rule is now a named function with no `is_in_session` in it, because the resolution count is
what actually separates the two cases.
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from civ_mcp.end_turn import wc_gate_blocks_end_turn  # noqa: E402


def test_a_session_with_resolutions_is_worth_blocking_for():
    """The case the gate exists for: there are votes to register, so end_turn must wait."""
    assert wc_gate_blocks_end_turn(1) is True
    assert wc_gate_blocks_end_turn(4) is True


def test_a_session_with_nothing_to_vote_on_never_blocks():
    """The regression. Blocking here cannot register a handler (the fallback list is built from
    the resolutions and is therefore empty), so it returns the same message forever."""
    assert wc_gate_blocks_end_turn(0) is False


def test_the_gate_does_not_consult_is_in_session():
    """`is_in_session` is true for both cases, so a gate that reads it cannot tell them apart.
    This is the assertion that would have caught the original bug: the decision is a function of
    the resolution count alone."""
    import inspect

    source = inspect.getsource(wc_gate_blocks_end_turn)
    body = source.split('"""', 2)[-1]
    assert "is_in_session" not in body, (
        "the gate must decide on the resolution count - `is_in_session` is true for an empty "
        "session too, which is exactly the state that used to hang the turn"
    )
