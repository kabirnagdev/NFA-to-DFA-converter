"""
NFA Validation Module.

Validates the formal components of an NFA definition according to
Automata Theory principles before conversion or visualization:
- Non-empty states set and alphabet
- Declared initial state within state set
- Final states subset of declared state set
- Transitions refer strictly to declared states and alphabet symbols
- Treatment of empty transitions as empty set (∅), not an error
"""

from dataclasses import dataclass, field
from typing import List, Set, Dict, Tuple, Iterable, Any, Optional


@dataclass
class ValidationResult:
    """Encapsulates the validation outcome for an NFA."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0


class NFAValidator:
    """Validates NFA configuration inputs against theoretical constraints."""

    @staticmethod
    def validate_raw(
        states: Iterable[str],
        alphabet: Iterable[str],
        initial_state: str,
        final_states: Iterable[str],
        transitions: Optional[Dict[Tuple[str, str], Iterable[str]]] = None,
    ) -> ValidationResult:
        """
        Validate raw string/collection inputs before constructing an NFA object.
        """
        errors: List[str] = []
        warnings: List[str] = []

        clean_states: Set[str] = {str(s).strip() for s in states if str(s).strip()}
        clean_alphabet: Set[str] = {str(a).strip() for a in alphabet if str(a).strip()}
        clean_initial: str = str(initial_state).strip()
        clean_final: Set[str] = {str(f).strip() for f in final_states if str(f).strip()}

        # 1. State set validation
        if not clean_states:
            errors.append("State set Q cannot be empty. Please declare at least one state (e.g. q0).")

        # 2. Alphabet validation
        if not clean_alphabet:
            errors.append("Alphabet Σ cannot be empty. Please declare at least one input symbol (e.g. 0, 1).")
        
        # Check for whitespace/comma delimiters inside symbols
        for sym in clean_alphabet:
            if " " in sym or "," in sym:
                errors.append(f"Alphabet symbol '{sym}' contains invalid delimiters (spaces or commas).")

        # 3. Initial state validation
        if not clean_initial:
            errors.append("Initial state q0 is required and cannot be blank.")
        elif clean_states and clean_initial not in clean_states:
            errors.append(
                f"Initial state '{clean_initial}' is not declared in the set of states Q: {sorted(list(clean_states))}."
            )

        # 4. Final states validation
        if clean_states:
            undeclared_finals = clean_final - clean_states
            if undeclared_finals:
                errors.append(
                    f"Final state(s) {sorted(list(undeclared_finals))} are not in declared states Q."
                )

        if not clean_final:
            warnings.append(
                "No final states declared. The language accepted by this automaton will be empty (∅)."
            )

        # 5. Transition table validation
        if transitions:
            for (st, sym), targets in transitions.items():
                s_st = str(st).strip()
                s_sym = str(sym).strip()
                
                # Check origin state
                if clean_states and s_st not in clean_states:
                    errors.append(
                        f"Transition origin state '{s_st}' is not in declared states Q."
                    )
                
                # Check symbol
                if clean_alphabet and s_sym not in clean_alphabet:
                    errors.append(
                        f"Transition symbol '{s_sym}' is not in declared alphabet Σ."
                    )
                
                # Check target states
                if targets:
                    for t in targets:
                        clean_t = str(t).strip()
                        if clean_t and clean_t not in clean_states and clean_states:
                            errors.append(
                                f"Transition δ({s_st}, {s_sym}) targets undeclared state '{clean_t}'."
                            )

        is_valid = len(errors) == 0
        return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)

    @classmethod
    def validate_nfa(cls, nfa_obj: Any) -> ValidationResult:
        """Validate an already instantiated NFA object."""
        return cls.validate_raw(
            states=nfa_obj.states,
            alphabet=nfa_obj.alphabet,
            initial_state=nfa_obj.initial_state,
            final_states=nfa_obj.final_states,
            transitions=nfa_obj.transitions,
        )
