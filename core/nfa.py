"""
NFA (Non-deterministic Finite Automaton) Model.

Formal Definition:
M = (Q, Sigma, delta, q0, F)
where:
  Q     : Finite set of states
  Sigma : Finite input alphabet
  delta : Transition function: Q x (Sigma ∪ {ε}) -> 2^Q (powerset of Q)
  q0    : Initial / start state in Q
  F     : Set of final / accepting states (F subset of Q)

Epsilon transitions are supported via the special symbol EPSILON = "ε".
Ordinary NFAs (without epsilon transitions) continue working unchanged.
"""

from typing import Set, Dict, Tuple, Iterable, Any, Optional

EPSILON = "ε"  # Epsilon / lambda transition symbol


class NFA:
    """
    Represents a Non-deterministic Finite Automaton.
    Supports both ordinary NFAs and epsilon-NFAs (ε-NFAs).

    Epsilon transitions are stored with the symbol EPSILON ("ε").
    Use has_epsilon_transitions to detect whether this NFA requires
    epsilon-closure computation during subset construction.
    """

    def __init__(
        self,
        states: Iterable[str],
        alphabet: Iterable[str],
        initial_state: str,
        final_states: Iterable[str],
        transitions: Optional[Dict[Tuple[str, str], Set[str]]] = None,
    ):
        self.states: Set[str] = {str(s).strip() for s in states if str(s).strip()}
        # Alphabet does NOT include epsilon — epsilon is a meta-symbol
        self.alphabet: Set[str] = {
            str(a).strip()
            for a in alphabet
            if str(a).strip() and str(a).strip() != EPSILON
        }
        self.initial_state: str = str(initial_state).strip()
        self.final_states: Set[str] = {str(f).strip() for f in final_states if str(f).strip()}

        # transitions mapping (state, symbol) -> set of next states
        # symbol may be EPSILON for epsilon transitions
        self.transitions: Dict[Tuple[str, str], Set[str]] = {}
        if transitions:
            for (state, sym), next_states in transitions.items():
                s_state = str(state).strip()
                s_sym = str(sym).strip()
                s_next = {str(ns).strip() for ns in next_states if str(ns).strip()}
                if s_next:
                    self.transitions[(s_state, s_sym)] = s_next

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def sorted_states(self) -> list[str]:
        """Return states in consistent natural order (e.g. q0, q1, q2)."""
        def sort_key(s: str):
            digits = "".join(filter(str.isdigit, s))
            prefix = "".join(filter(str.isalpha, s))
            return (prefix, int(digits) if digits else 0, s)

        return sorted(list(self.states), key=sort_key)

    @property
    def sorted_alphabet(self) -> list[str]:
        """Return alphabet symbols in consistent sorted order (epsilon excluded)."""
        return sorted(list(self.alphabet))

    @property
    def sorted_final_states(self) -> list[str]:
        """Return final states in consistent sorted order."""
        def sort_key(s: str):
            digits = "".join(filter(str.isdigit, s))
            prefix = "".join(filter(str.isalpha, s))
            return (prefix, int(digits) if digits else 0, s)

        return sorted(list(self.final_states), key=sort_key)

    @property
    def has_epsilon_transitions(self) -> bool:
        """True if any epsilon transition is defined."""
        return any(sym == EPSILON for (_, sym) in self.transitions)

    # ------------------------------------------------------------------
    # Transition access
    # ------------------------------------------------------------------

    def get_transitions(self, state: str, symbol: str) -> Set[str]:
        """Get set of next states for given state and input symbol. Empty set if none."""
        return self.transitions.get((state, symbol), set())

    def get_epsilon_transitions(self, state: str) -> Set[str]:
        """Get set of states reachable from state via a single epsilon transition."""
        return self.transitions.get((state, EPSILON), set())

    def set_transitions(self, state: str, symbol: str, next_states: Iterable[str]) -> None:
        """Set the transition targets for (state, symbol)."""
        cleaned = {str(ns).strip() for ns in next_states if str(ns).strip()}
        if cleaned:
            self.transitions[(state, symbol)] = cleaned
        else:
            self.transitions.pop((state, symbol), None)

    # ------------------------------------------------------------------
    # Epsilon closure
    # ------------------------------------------------------------------

    def epsilon_closure(self, states: Iterable[str]) -> frozenset:
        """
        Compute the epsilon-closure of a set of states.

        ε-closure(S) = all states reachable from any state in S
                       using zero or more epsilon transitions.

        Uses BFS / iterative set expansion.
        Returns a frozenset for use as a dictionary key.
        """
        closure: Set[str] = set(states)
        worklist: list[str] = list(closure)

        while worklist:
            current = worklist.pop()
            eps_targets = self.get_epsilon_transitions(current)
            for t in eps_targets:
                if t not in closure:
                    closure.add(t)
                    worklist.append(t)

        return frozenset(closure)

    def epsilon_closure_of_set(self, states: Iterable[str]) -> frozenset:
        """Alias for epsilon_closure — provided for semantic clarity in traces."""
        return self.epsilon_closure(states)

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Serialize NFA to a plain dictionary (useful for Streamlit session_state)."""
        trans_list = [
            {"from": state, "symbol": sym, "to": sorted(list(targets))}
            for (state, sym), targets in self.transitions.items()
        ]
        return {
            "states": self.sorted_states,
            "alphabet": self.sorted_alphabet,
            "initial_state": self.initial_state,
            "final_states": self.sorted_final_states,
            "transitions": trans_list,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NFA":
        """Reconstruct NFA from a dictionary."""
        transitions: Dict[Tuple[str, str], Set[str]] = {}
        for entry in data.get("transitions", []):
            transitions[(entry["from"], entry["symbol"])] = set(entry.get("to", []))
        return cls(
            states=data.get("states", []),
            alphabet=data.get("alphabet", []),
            initial_state=data.get("initial_state", ""),
            final_states=data.get("final_states", []),
            transitions=transitions,
        )

    def __repr__(self) -> str:
        eps_note = " [ε-NFA]" if self.has_epsilon_transitions else ""
        return (
            f"NFA(Q={len(self.states)} states, Sigma={self.sorted_alphabet}, "
            f"q0={self.initial_state}, F={self.sorted_final_states}){eps_note}"
        )
