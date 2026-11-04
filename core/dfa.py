"""
DFA (Deterministic Finite Automaton) Model.

Formal Definition:
M' = (Q', Sigma, delta', q'0, F')
where:
  Q'     : Finite set of DFA states (subsets of NFA states)
  Sigma  : Finite input alphabet (identical to NFA alphabet)
  delta' : Transition function: Q' x Sigma -> Q' (deterministic mapping)
  q'0    : Initial DFA state in Q' (closure/subset containing NFA q0)
  F'     : Set of final / accepting DFA states (states containing >= 1 NFA final state)
"""

from typing import Set, Dict, Tuple, Iterable, Any, Optional, FrozenSet


class DFA:
    """Represents a Deterministic Finite Automaton produced by Subset Construction."""

    def __init__(
        self,
        states: Iterable[str],
        alphabet: Iterable[str],
        initial_state: str,
        final_states: Iterable[str],
        transitions: Dict[Tuple[str, str], str],
        state_subsets: Optional[Dict[str, FrozenSet[str]]] = None,
    ):
        self.states: Set[str] = {str(s).strip() for s in states if str(s).strip()}
        self.alphabet: Set[str] = {str(a).strip() for a in alphabet if str(a).strip()}
        self.initial_state: str = str(initial_state).strip()
        self.final_states: Set[str] = {str(f).strip() for f in final_states if str(f).strip()}
        
        # transitions mapping (state_label, symbol) -> next_state_label
        self.transitions: Dict[Tuple[str, str], str] = {
            (str(st).strip(), str(sym).strip()): str(nxt).strip()
            for (st, sym), nxt in transitions.items()
        }

        # mapping from state label (e.g. 'A') to the underlying NFA state frozenset
        self.state_subsets: Dict[str, FrozenSet[str]] = state_subsets or {}
        self.subset_to_label: Dict[FrozenSet[str], str] = {
            subset: label for label, subset in self.state_subsets.items()
        }

    @property
    def sorted_states(self) -> list[str]:
        """Return states in alphabetical or natural order."""
        return sorted(list(self.states))

    @property
    def sorted_alphabet(self) -> list[str]:
        """Return alphabet symbols in sorted order."""
        return sorted(list(self.alphabet))

    @property
    def sorted_final_states(self) -> list[str]:
        """Return final states in sorted order."""
        return sorted(list(self.final_states))

    def get_transition(self, state: str, symbol: str) -> Optional[str]:
        """Return the unique next state for (state, symbol)."""
        return self.transitions.get((state, symbol))

    def is_final(self, state: str) -> bool:
        """Check if a given DFA state is an accepting state."""
        return state in self.final_states

    def get_subset_str(self, state: str) -> str:
        """Return formatted string of underlying NFA subset, e.g. '{q0, q1}' or '∅'."""
        subset = self.state_subsets.get(state)
        if subset is None:
            return "{}"
        if not subset:
            return "∅"
        
        def state_sort_key(s: str):
            digits = "".join(filter(str.isdigit, s))
            prefix = "".join(filter(str.isalpha, s))
            return (prefix, int(digits) if digits else 0, s)

        sorted_items = sorted(list(subset), key=state_sort_key)
        return "{" + ", ".join(sorted_items) + "}"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize DFA to a plain dictionary."""
        trans_list = [
            {"from": st, "symbol": sym, "to": nxt}
            for (st, sym), nxt in self.transitions.items()
        ]
        subsets_dict = {
            st: sorted(list(subset))
            for st, subset in self.state_subsets.items()
        }
        return {
            "states": self.sorted_states,
            "alphabet": self.sorted_alphabet,
            "initial_state": self.initial_state,
            "final_states": self.sorted_final_states,
            "transitions": trans_list,
            "state_subsets": subsets_dict,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DFA":
        """Reconstruct DFA from dictionary."""
        transitions: Dict[Tuple[str, str], str] = {}
        for entry in data.get("transitions", []):
            transitions[(entry["from"], entry["symbol"])] = entry["to"]
        
        state_subsets = {
            st: frozenset(sub_list)
            for st, sub_list in data.get("state_subsets", {}).items()
        }
        return cls(
            states=data.get("states", []),
            alphabet=data.get("alphabet", []),
            initial_state=data.get("initial_state", ""),
            final_states=data.get("final_states", []),
            transitions=transitions,
            state_subsets=state_subsets,
        )

    def __repr__(self) -> str:
        return (
            f"DFA(Q'={len(self.states)} states, Sigma={self.sorted_alphabet}, "
            f"q'0={self.initial_state}, F'={self.sorted_final_states})"
        )
