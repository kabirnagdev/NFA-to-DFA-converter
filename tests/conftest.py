"""
Shared pytest fixtures for all test modules.
Provides common NFA / DFA instances for reuse across test files.
"""

import pytest
from core.nfa import NFA, EPSILON
from core.conversion import SubsetConstructionEngine


@pytest.fixture
def nfa_ends_with_01():
    """Standard course example: binary strings ending in '01'."""
    return NFA(
        states=["q0", "q1", "q2"],
        alphabet=["0", "1"],
        initial_state="q0",
        final_states=["q2"],
        transitions={
            ("q0", "0"): {"q0", "q1"},
            ("q0", "1"): {"q0"},
            ("q1", "1"): {"q2"},
        },
    )


@pytest.fixture
def dfa_ends_with_01(nfa_ends_with_01):
    """DFA produced from the 'ends with 01' NFA."""
    return SubsetConstructionEngine(nfa_ends_with_01).convert().dfa


@pytest.fixture
def nfa_with_trap():
    """NFA that necessarily generates a trap (dead) state."""
    return NFA(
        states=["q0", "q1"],
        alphabet=["0", "1"],
        initial_state="q0",
        final_states=["q1"],
        transitions={
            ("q0", "0"): {"q1"},
            ("q1", "0"): {"q1"},
            ("q1", "1"): {"q1"},
        },
    )


@pytest.fixture
def epsilon_nfa_a_star_b_star():
    """ε-NFA recognizing L = a*b*."""
    return NFA(
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
