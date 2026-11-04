"""
Subset Construction Engine (NFA to DFA Conversion).

Implements the standard Rabin-Scott Powersets / Subset Construction algorithm:
- Uses collections.deque for BFS exploration of reachable DFA states.
- Uses frozenset for subsets to ensure uniqueness and hashability.
- Captures granular trace steps for pedagogical breakdown.
"""

from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple, FrozenSet, Optional

from .nfa import NFA
from .dfa import DFA


def generate_state_label(index: int) -> str:
    """Generate consistent academic state labels: A, B, C, ... Z, AA, AB, etc."""
    label = ""
    idx = index
    while True:
        label = chr(ord('A') + (idx % 26)) + label
        idx = idx // 26 - 1
        if idx < 0:
            break
    return label


def format_subset(subset: FrozenSet[str]) -> str:
    """Format a subset of states for academic display."""
    if not subset:
        return "∅"
    
    def sort_key(s: str):
        digits = "".join(filter(str.isdigit, s))
        prefix = "".join(filter(str.isalpha, s))
        return (prefix, int(digits) if digits else 0, s)

    items = sorted(list(subset), key=sort_key)
    return "{" + ", ".join(items) + "}"


@dataclass
class ConversionStep:
    """Detailed record of a single transition calculation in subset construction."""
    step_number: int
    current_label: str
    current_subset: FrozenSet[str]
    symbol: str
    individual_transitions: Dict[str, Set[str]]
    union_result: FrozenSet[str]
    target_label: str
    is_new_state: bool
    explanation: str

    @property
    def formatted_current_subset(self) -> str:
        return format_subset(self.current_subset)

    @property
    def formatted_union_result(self) -> str:
        return format_subset(self.union_result)

    @property
    def formula_breakdown(self) -> str:
        """Academic mathematical breakdown: delta'(S, a) = Union delta(q, a)."""
        if not self.current_subset:
            return f"δ'({self.current_label}, {self.symbol}) = δ'(∅, {self.symbol}) = ∅"
        
        parts = []
        for q, targets in sorted(self.individual_transitions.items()):
            t_str = "{" + ", ".join(sorted(targets)) + "}" if targets else "∅"
            parts.append(f"δ({q}, {self.symbol}) = {t_str}")
        return ", ".join(parts)


@dataclass
class ConversionResult:
    """Complete output of the subset construction algorithm."""
    dfa: DFA
    steps: List[ConversionStep]
    state_mapping: Dict[str, FrozenSet[str]]
    nfa_state_count: int
    dfa_state_count: int
    reachable_subsets: List[Tuple[str, FrozenSet[str], bool]]  # (label, subset, is_accepting)


class SubsetConstructionEngine:
    """Algorithmic engine executing the Subset Construction algorithm."""

    def __init__(self, nfa: NFA):
        self.nfa = nfa

    def convert(self) -> ConversionResult:
        """
        Execute subset construction to transform NFA M into equivalent DFA M'.
        
        Algorithm Steps:
        1. q'0 = {q0} (Initial DFA state)
        2. Assign initial label 'A' to {q0}
        3. Enqueue initial subset into BFS deque
        4. While queue is not empty:
            a. Dequeue current subset S with label L
            b. For each symbol a in Sigma:
                i. Compute T = Union { delta(q, a) for q in S }
                ii. If T has not been seen, assign new label and enqueue T
                iii. Record delta'(L, a) = label(T)
                iv. Record step-by-step trace
        5. Mark any DFA state S as accepting if S contains at least one NFA final state.
        """
        # Step 1: Initial subset
        initial_subset: FrozenSet[str] = frozenset([self.nfa.initial_state])
        
        # Mappings: frozenset -> label and label -> frozenset
        subset_to_label: Dict[FrozenSet[str], str] = {}
        label_to_subset: Dict[str, FrozenSet[str]] = {}
        
        # FIFO queue for BFS
        queue: deque[FrozenSet[str]] = deque()
        
        # Assign label to initial state
        label_counter = 0
        initial_label = generate_state_label(label_counter)
        label_counter += 1
        
        subset_to_label[initial_subset] = initial_label
        label_to_subset[initial_label] = initial_subset
        queue.append(initial_subset)
        
        dfa_transitions: Dict[Tuple[str, str], str] = {}
        steps: List[ConversionStep] = []
        step_counter = 1

        alphabet = self.nfa.sorted_alphabet

        while queue:
            current_subset = queue.popleft()
            current_label = subset_to_label[current_subset]

            for sym in alphabet:
                individual_trans: Dict[str, Set[str]] = {}
                union_set: Set[str] = set()

                if not current_subset:
                    # Empty subset transitions to itself for all symbols
                    target_subset = frozenset()
                else:
                    for q in sorted(current_subset):
                        q_targets = self.nfa.get_transitions(q, sym)
                        individual_trans[q] = set(q_targets)
                        union_set.update(q_targets)
                    target_subset = frozenset(union_set)

                is_new = False
                if target_subset not in subset_to_label:
                    target_label = generate_state_label(label_counter)
                    label_counter += 1
                    subset_to_label[target_subset] = target_label
                    label_to_subset[target_label] = target_subset
                    queue.append(target_subset)
                    is_new = True
                else:
                    target_label = subset_to_label[target_subset]

                dfa_transitions[(current_label, sym)] = target_label

                # Academic explanation text
                curr_fmt = format_subset(current_subset)
                tgt_fmt = format_subset(target_subset)
                
                if not current_subset:
                    expl = (
                        f"Empty subset {current_label} = ∅ on symbol '{sym}' remains ∅ "
                        f"(Trap State {target_label})."
                    )
                else:
                    trans_parts = [
                        f"δ({q}, {sym}) = {format_subset(frozenset(targets))}"
                        for q, targets in sorted(individual_trans.items())
                    ]
                    unions_str = " ∪ ".join([f"δ({q}, {sym})" for q in sorted(individual_trans.keys())])
                    res_unions = " ∪ ".join([format_subset(frozenset(t)) for _, t in sorted(individual_trans.items())])
                    new_tag = f"Newly discovered DFA state {target_label} = {tgt_fmt}" if is_new else f"Existing DFA state {target_label} = {tgt_fmt}"
                    expl = (
                        f"δ'({current_label}, {sym}) = {unions_str} = {res_unions} = {tgt_fmt}. {new_tag}."
                    )

                step = ConversionStep(
                    step_number=step_counter,
                    current_label=current_label,
                    current_subset=current_subset,
                    symbol=sym,
                    individual_transitions=individual_trans,
                    union_result=target_subset,
                    target_label=target_label,
                    is_new_state=is_new,
                    explanation=expl,
                )
                steps.append(step)
                step_counter += 1

        # Determine DFA final states: any subset that intersects with NFA final states
        dfa_states = set(label_to_subset.keys())
        dfa_final_states: Set[str] = set()
        reachable_summary: List[Tuple[str, FrozenSet[str], bool]] = []

        # Sort DFA states by label for clean deterministic presentation
        for label in sorted(dfa_states):
            subset = label_to_subset[label]
            is_acc = bool(subset.intersection(self.nfa.final_states))
            if is_acc:
                dfa_final_states.add(label)
            reachable_summary.append((label, subset, is_acc))

        dfa = DFA(
            states=dfa_states,
            alphabet=alphabet,
            initial_state=initial_label,
            final_states=dfa_final_states,
            transitions=dfa_transitions,
            state_subsets=label_to_subset,
        )

        return ConversionResult(
            dfa=dfa,
            steps=steps,
            state_mapping=label_to_subset,
            nfa_state_count=len(self.nfa.states),
            dfa_state_count=len(dfa.states),
            reachable_subsets=reachable_summary,
        )
