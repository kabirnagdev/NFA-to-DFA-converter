"""
Unit tests for Epsilon-NFA (ε-NFA) support, epsilon-closure, and equivalence.
"""

import itertools
import pytest

from core.nfa import NFA, EPSILON
from core.conversion import SubsetConstructionEngine
from core.simulator import AutomataSimulator
from core.validation import NFAValidator


def test_epsilon_closure_chain_and_cycle():
    """Verify ε-closure handles multi-hop chains and ε-cycles without infinite loops."""
    nfa = NFA(
        states=["q0", "q1", "q2", "q3"],
        alphabet=["a"],
        initial_state="q0",
        final_states=["q2"],
        transitions={
            ("q0", EPSILON): {"q1"},
            ("q1", EPSILON): {"q2", "q0"},  # cycle back to q0
            ("q2", "a"): {"q3"},
        },
    )
    assert nfa.has_epsilon_transitions is True
    assert nfa.epsilon_closure({"q0"}) == frozenset({"q0", "q1", "q2"})
    assert nfa.epsilon_closure({"q3"}) == frozenset({"q3"})
    assert nfa.epsilon_closure(set()) == frozenset()


def test_epsilon_nfa_validation_allows_epsilon():
    """Validator must accept ε as a transition symbol while excluding it from Σ."""
    res = NFAValidator.validate_raw(
        states=["q0", "q1"],
        alphabet=["a", "b"],
        initial_state="q0",
        final_states=["q1"],
        transitions={
            ("q0", "a"): {"q0"},
            ("q0", EPSILON): {"q1"},
            ("q1", "b"): {"q1"},
        },
    )
    assert res.is_valid is True
    assert res.errors == []


def test_epsilon_nfa_a_star_b_star_conversion_and_equivalence():
    """
    Test ε-NFA recognizing L = a*b*:
      q0 --a--> q0
      q0 --ε--> q1
      q1 --b--> q1
    Initial DFA state A = ε-closure({q0}) = {q0, q1}, which is accepting!
    Bounded exhaustive equivalence: all strings over {a, b} up to length 5 (63 strings).
    """
    nfa = NFA(
        states=["q0", "q1"],
        alphabet=["a", "b"],
        initial_state="q0",
        final_states=["q1"],
        transitions={
            ("q0", "a"): {"q0"},
            ("q0", EPSILON): {"q1"},
            ("q1", "b"): {"q1"},
        },
    )

    result = SubsetConstructionEngine(nfa).convert()
    dfa = result.dfa

    assert result.is_epsilon_nfa is True
    assert dfa.state_subsets["A"] == frozenset({"q0", "q1"})
    assert dfa.is_final("A") is True

    # Bounded exhaustive test up to length 5 (sum_{k=0..5} 2^k = 63 strings)
    all_strings = [""]
    for length in range(1, 6):
        for combo in itertools.product(["a", "b"], repeat=length):
            all_strings.append("".join(combo))

    for w in all_strings:
        cmp_res = AutomataSimulator.compare(nfa, dfa, w)
        assert cmp_res.is_equivalent is True, f"Mismatch on '{w}'"
        # Language a*b*: no 'a' may appear after any 'b'
        expected = ("ba" not in w)
        assert cmp_res.dfa_result.is_accepted == expected, f"Wrong verdict on '{w}'"


def test_epsilon_closure_after_symbol_transition():
    """
    Verify ε-closure is applied AFTER symbol transitions:
      q0 --0--> q1, q1 --ε--> q2 (final).
    String '0' must be accepted.
    """
    nfa = NFA(
        states=["q0", "q1", "q2"],
        alphabet=["0", "1"],
        initial_state="q0",
        final_states=["q2"],
        transitions={
            ("q0", "0"): {"q1"},
            ("q1", EPSILON): {"q2"},
        },
    )
    result = SubsetConstructionEngine(nfa).convert()
    dfa = result.dfa

    for w in ["", "0", "1", "00", "01", "10"]:
        cmp_res = AutomataSimulator.compare(nfa, dfa, w)
        assert cmp_res.is_equivalent is True
        assert cmp_res.dfa_result.is_accepted == (w == "0")
