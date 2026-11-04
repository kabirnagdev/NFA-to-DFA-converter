"""
Unit tests for NFA Validation Module (core/validation.py).
"""

import pytest
from core.validation import NFAValidator


def test_valid_nfa_passes():
    """Verify that a well-defined NFA passes validation cleanly."""
    res = NFAValidator.validate_raw(
        states=["q0", "q1", "q2"],
        alphabet=["0", "1"],
        initial_state="q0",
        final_states=["q2"],
        transitions={
            ("q0", "0"): ["q0", "q1"],
            ("q0", "1"): ["q0"],
            ("q1", "1"): ["q2"],
        },
    )
    assert res.is_valid is True
    assert len(res.errors) == 0


def test_missing_initial_state():
    """Validation must fail if initial state is blank."""
    res = NFAValidator.validate_raw(
        states=["q0", "q1"],
        alphabet=["0", "1"],
        initial_state="",
        final_states=["q1"],
    )
    assert res.is_valid is False
    assert any("Initial state" in e for e in res.errors)


def test_undeclared_initial_state():
    """Validation must fail if initial state is not in Q."""
    res = NFAValidator.validate_raw(
        states=["q0", "q1"],
        alphabet=["0", "1"],
        initial_state="q_unknown",
        final_states=["q1"],
    )
    assert res.is_valid is False
    assert any("q_unknown" in e for e in res.errors)


def test_undeclared_final_state():
    """Validation must fail if final states contain undeclared states."""
    res = NFAValidator.validate_raw(
        states=["q0", "q1"],
        alphabet=["0", "1"],
        initial_state="q0",
        final_states=["q1", "q_fake"],
    )
    assert res.is_valid is False
    assert any("q_fake" in e for e in res.errors)


def test_empty_states_definition():
    """Validation must fail if states set is empty."""
    res = NFAValidator.validate_raw(
        states=[],
        alphabet=["0", "1"],
        initial_state="q0",
        final_states=["q0"],
    )
    assert res.is_valid is False
    assert any("State set Q cannot be empty" in e for e in res.errors)


def test_empty_alphabet_definition():
    """Validation must fail if alphabet is empty."""
    res = NFAValidator.validate_raw(
        states=["q0"],
        alphabet=[],
        initial_state="q0",
        final_states=["q0"],
    )
    assert res.is_valid is False
    assert any("Alphabet Σ cannot be empty" in e for e in res.errors)


def test_undeclared_state_in_transitions():
    """Validation must fail if transition references undeclared state."""
    res = NFAValidator.validate_raw(
        states=["q0", "q1"],
        alphabet=["0", "1"],
        initial_state="q0",
        final_states=["q1"],
        transitions={
            ("q0", "0"): ["q99"],  # q99 undeclared
        },
    )
    assert res.is_valid is False
    assert any("q99" in e for e in res.errors)


def test_undeclared_symbol_in_transitions():
    """Validation must fail if transition uses an undeclared symbol."""
    res = NFAValidator.validate_raw(
        states=["q0", "q1"],
        alphabet=["0", "1"],
        initial_state="q0",
        final_states=["q1"],
        transitions={
            ("q0", "2"): ["q1"],  # '2' not in {'0', '1'}
        },
    )
    assert res.is_valid is False
    assert any("symbol '2'" in e for e in res.errors)


def test_empty_transitions_treated_as_empty_set():
    """Empty transitions must be accepted as valid empty set (∅), not an error."""
    res = NFAValidator.validate_raw(
        states=["q0", "q1"],
        alphabet=["0", "1"],
        initial_state="q0",
        final_states=["q1"],
        transitions={
            ("q0", "0"): [],
            ("q0", "1"): set(),
            ("q1", "0"): None,
            ("q1", "1"): ["q1"],
        },
    )
    assert res.is_valid is True
    assert len(res.errors) == 0
