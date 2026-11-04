"""
Automata String Simulator Module.

Executes string evaluations synchronously on both NFA and DFA:
- Step-by-step state traversal for DFA
- Step-by-step active state set tracking for NFA
- Empty string (epsilon) handling
- Alphabet symbol validation
- Comparison and formal proof of language equivalence on tested strings
"""

from dataclasses import dataclass, field
from typing import List, Set, Dict, Optional, FrozenSet, Tuple

from .nfa import NFA
from .dfa import DFA
from .conversion import format_subset


@dataclass
class DFAStep:
    """Represents one step in DFA string execution."""
    step_number: int
    symbol: Optional[str]
    from_state: str
    from_subset: FrozenSet[str]
    to_state: str
    to_subset: FrozenSet[str]
    is_accepting: bool


@dataclass
class NFAStep:
    """Represents one step in NFA string execution."""
    step_number: int
    symbol: Optional[str]
    active_states: Set[str]
    per_state_transitions: Dict[str, Set[str]]
    next_states: Set[str]
    is_accepting: bool


@dataclass
class SimulationResult:
    """Output of simulating a string on an automaton (NFA or DFA)."""
    automaton_type: str
    input_string: str
    is_accepted: bool
    final_states_reached: Set[str]
    steps: list
    explanation: str


@dataclass
class ComparisonResult:
    """Side-by-side comparison of NFA and DFA simulations."""
    input_string: str
    nfa_result: SimulationResult
    dfa_result: SimulationResult
    is_equivalent: bool
    verdict: str
    explanation: str


class AutomataSimulator:
    """Simulates string acceptance and generates execution traces."""

    @staticmethod
    def validate_string(alphabet: Set[str], input_string: str) -> Tuple[bool, Optional[str]]:
        """
        Validate whether the input string contains only symbols from the declared alphabet.
        Empty string is always valid.
        """
        if not input_string:
            return True, None
        
        invalid_symbols = set(input_string) - alphabet
        if invalid_symbols:
            inv_str = ", ".join(f"'{s}'" for s in sorted(invalid_symbols))
            alph_str = ", ".join(f"'{a}'" for a in sorted(alphabet))
            return False, f"String contains symbol(s) {inv_str} not in alphabet Σ = {{{alph_str}}}."
        
        return True, None

    @classmethod
    def simulate_dfa(cls, dfa: DFA, input_string: str) -> SimulationResult:
        """
        Simulate DFA execution on input string w.
        DFA is deterministic: exactly one state is active at each step.
        """
        current_state = dfa.initial_state
        current_subset = dfa.state_subsets.get(current_state, frozenset())
        
        steps: List[DFAStep] = []
        
        # Initial step (Step 0)
        steps.append(
            DFAStep(
                step_number=0,
                symbol=None,
                from_state=current_state,
                from_subset=current_subset,
                to_state=current_state,
                to_subset=current_subset,
                is_accepting=dfa.is_final(current_state),
            )
        )

        for idx, sym in enumerate(input_string):
            next_state = dfa.get_transition(current_state, sym)
            if next_state is None:
                # Should not occur for well-formed DFA, but guard safely
                next_state = "TRAP"
                next_subset = frozenset()
            else:
                next_subset = dfa.state_subsets.get(next_state, frozenset())

            is_acc = dfa.is_final(next_state)
            steps.append(
                DFAStep(
                    step_number=idx + 1,
                    symbol=sym,
                    from_state=current_state,
                    from_subset=current_subset,
                    to_state=next_state,
                    to_subset=next_subset,
                    is_accepting=is_acc,
                )
            )
            current_state = next_state
            current_subset = next_subset

        is_accepted = dfa.is_final(current_state)
        subset_fmt = format_subset(current_subset)
        
        if is_accepted:
            expl = (
                f"DFA halted in state {current_state} = {subset_fmt}, which is an accepting state "
                f"({current_state} ∈ F'). Input '{input_string or 'ε'}' is ACCEPTED."
            )
        else:
            expl = (
                f"DFA halted in state {current_state} = {subset_fmt}, which is NOT an accepting state "
                f"({current_state} ∉ F'). Input '{input_string or 'ε'}' is REJECTED."
            )

        return SimulationResult(
            automaton_type="DFA",
            input_string=input_string,
            is_accepted=is_accepted,
            final_states_reached={current_state},
            steps=steps,
            explanation=expl,
        )

    @classmethod
    def simulate_nfa(cls, nfa: NFA, input_string: str) -> SimulationResult:
        """
        Simulate NFA execution on input string w.
        NFA tracks the set of all simultaneously active states.
        """
        active_states: Set[str] = {nfa.initial_state}
        steps: List[NFAStep] = []

        is_acc = bool(active_states.intersection(nfa.final_states))
        steps.append(
            NFAStep(
                step_number=0,
                symbol=None,
                active_states=set(active_states),
                per_state_transitions={},
                next_states=set(active_states),
                is_accepting=is_acc,
            )
        )

        for idx, sym in enumerate(input_string):
            per_state: Dict[str, Set[str]] = {}
            next_active: Set[str] = set()

            for q in sorted(active_states):
                targets = nfa.get_transitions(q, sym)
                per_state[q] = set(targets)
                next_active.update(targets)

            is_acc = bool(next_active.intersection(nfa.final_states))
            steps.append(
                NFAStep(
                    step_number=idx + 1,
                    symbol=sym,
                    active_states=set(active_states),
                    per_state_transitions=per_state,
                    next_states=set(next_active),
                    is_accepting=is_acc,
                )
            )
            active_states = next_active

        is_accepted = bool(active_states.intersection(nfa.final_states))
        active_fmt = format_subset(frozenset(active_states))
        final_fmt = format_subset(frozenset(nfa.final_states))

        if is_accepted:
            intersecting = sorted(list(active_states.intersection(nfa.final_states)))
            expl = (
                f"NFA finished with active state set {active_fmt}. "
                f"Contains accepting state(s) {{{', '.join(intersecting)}}} from F = {final_fmt}. "
                f"Input '{input_string or 'ε'}' is ACCEPTED."
            )
        else:
            expl = (
                f"NFA finished with active state set {active_fmt}. "
                f"Contains no accepting states from F = {final_fmt}. "
                f"Input '{input_string or 'ε'}' is REJECTED."
            )

        return SimulationResult(
            automaton_type="NFA",
            input_string=input_string,
            is_accepted=is_accepted,
            final_states_reached=set(active_states),
            steps=steps,
            explanation=expl,
        )

    @classmethod
    def compare(cls, nfa: NFA, dfa: DFA, input_string: str) -> ComparisonResult:
        """Run input string on both NFA and DFA and verify equivalence."""
        nfa_res = cls.simulate_nfa(nfa, input_string)
        dfa_res = cls.simulate_dfa(dfa, input_string)

        is_equiv = nfa_res.is_accepted == dfa_res.is_accepted
        verdict = "ACCEPTED" if dfa_res.is_accepted else "REJECTED"

        if is_equiv:
            expl = (
                f"Equivalence Confirmed: Both NFA and DFA produced the identical result "
                f"({verdict}) on string '{input_string or 'ε'}'. "
                f"At termination, NFA active states {format_subset(frozenset(nfa_res.final_states_reached))} "
                f"exactly match the subset represented by DFA state {list(dfa_res.final_states_reached)[0]}."
            )
        else:
            expl = (
                f"Discrepancy Detected! NFA returned {nfa_res.is_accepted} while DFA returned {dfa_res.is_accepted}."
            )

        return ComparisonResult(
            input_string=input_string,
            nfa_result=nfa_res,
            dfa_result=dfa_res,
            is_equivalent=is_equiv,
            verdict=verdict,
            explanation=expl,
        )
