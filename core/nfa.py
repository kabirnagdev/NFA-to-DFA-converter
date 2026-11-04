"""
NFA (Non-deterministic Finite Automaton) Model.

Formal Definition:
M = (Q, Sigma, delta, q0, F)
where:
  Q     : Finite set of states
  Sigma : Finite input alphabet
  delta : Transition function: Q x Sigma -> 2^Q (powerset of Q)
  q0    : Initial / start state in Q
  F     : Set of final / accepting states (F subset of Q)
"""

from typing import Set, Dict, Tuple, Iterable, Any, Optional


class NFA:
    """Represents a standard Non-deterministic Finite Automaton without epsilon transitions."""

    def __init__(
        self,
        states: Iterable[str],
        alphabet: Iterable[str],
        initial_state: str,
        final_states: Iterable[str],
        transitions: Optional[Dict[Tuple[str, str], Set[str]]] = None,
    ):
        self.states: Set[str] = {str(s).strip() for s in states if str(s).strip()}
        self.alphabet: Set[str] = {str(a).strip() for a in alphabet if str(a).strip()}
        self.initial_state: str = str(initial_state).strip()
        self.final_states: Set[str] = {str(f).strip() for f in final_states if str(f).strip()}
        
        # transitions mapping (state, symbol) -> set of next states
        self.transitions: Dict[Tuple[str, str], Set[str]] = {}
        if transitions:
            for (state, sym), next_states in transitions.items():
                s_state = str(state).strip()
                s_sym = str(sym).strip()
                s_next = {str(ns).strip() for ns in next_states if str(ns).strip()}
                if s_next:
                    self.transitions[(s_state, s_sym)] = s_next

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
        """Return alphabet symbols in consistent sorted order."""
        return sorted(list(self.alphabet))

    @property
    def sorted_final_states(self) -> list[str]:
        """Return final states in consistent sorted order."""
        def sort_key(s: str):
            digits = "".join(filter(str.isdigit, s))
            prefix = "".join(filter(str.isalpha, s))
            return (prefix, int(digits) if digits else 0, s)

        return sorted(list(self.final_states), key=sort_key)

    def get_transitions(self, state: str, symbol: str) -> Set[str]:
        """Get set of next states for given state and input symbol. Empty set if none."""
        return self.transitions.get((state, symbol), set())

    def set_transitions(self, state: str, symbol: str, next_states: Iterable[str]) -> None:
        """Set the transition targets for (state, symbol)."""
        cleaned = {str(ns).strip() for ns in next_states if str(ns).strip()}
        if cleaned:
            self.transitions[(state, symbol)] = cleaned
        else:
            self.transitions.pop((state, symbol), None)

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
        return (
            f"NFA(Q={len(self.states)} states, Sigma={self.sorted_alphabet}, "
            f"q0={self.initial_state}, F={self.sorted_final_states})"
        )
