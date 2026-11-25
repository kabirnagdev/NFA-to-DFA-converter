"""
Subset Construction Engine (NFA to DFA Conversion).

Implements the standard Rabin-Scott Subset Construction algorithm:
- Uses collections.deque for BFS exploration of reachable DFA states.
- Uses frozenset for subsets to ensure uniqueness and hashability.
- Supports ordinary NFAs and epsilon-NFAs (ε-NFAs).
- Captures granular ConversionStep records for pedagogical breakdown.
- Builds a list of ConversionSnapshot objects so the UI can replay
  the algorithm one micro-step at a time without corrupting state.
"""

from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, FrozenSet, Optional, Deque

from .nfa import NFA, EPSILON
from .dfa import DFA


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Step record (one transition calculation)
# ---------------------------------------------------------------------------

@dataclass
class ConversionStep:
    """Detailed record of a single transition calculation in subset construction."""
    step_number: int
    current_label: str
    current_subset: FrozenSet[str]
    symbol: str
    individual_transitions: Dict[str, Set[str]]
    # For epsilon-NFAs: pre-closure raw union before epsilon closure is applied
    raw_union: FrozenSet[str]
    # Epsilon closure steps: state -> epsilon-reachable set (empty if not ε-NFA)
    epsilon_closure_steps: Dict[str, Set[str]]
    union_result: FrozenSet[str]       # = epsilon_closure(raw_union)
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
        """Academic mathematical breakdown: δ'(S, a) = ε-closure(⋃ δ(q, a))."""
        if not self.current_subset:
            return f"δ'({self.current_label}, {self.symbol}) = δ'(∅, {self.symbol}) = ∅"

        parts = []
        for q, targets in sorted(self.individual_transitions.items()):
            t_str = "{" + ", ".join(sorted(targets)) + "}" if targets else "∅"
            parts.append(f"δ({q}, {self.symbol}) = {t_str}")
        return ", ".join(parts)


# ---------------------------------------------------------------------------
# Snapshot (algorithm state at a specific micro-step, used for playback)
# ---------------------------------------------------------------------------

@dataclass
class ConversionSnapshot:
    """
    Captures the complete observable state of the BFS algorithm
    at one micro-step (one symbol processed for one DFA state).

    The UI replays these snapshots to animate the algorithm without
    re-running or corrupting the actual computation.
    """
    snapshot_index: int           # 0-based index in the snapshots list
    total_snapshots: int          # filled in after all snapshots are built

    # What is happening at this micro-step
    step: ConversionStep          # the transition being computed

    # Queue state at this point in the algorithm
    # (after dequeuing current_subset, before enqueuing any new discoveries)
    queue_pending: List[Tuple[str, FrozenSet[str]]]  # [(label, subset), ...]
    queue_just_discovered: List[Tuple[str, FrozenSet[str]]]  # newly found this step
    queue_processed: List[Tuple[str, FrozenSet[str]]]  # already fully processed

    # Partial DFA state at this point: subset_to_label map built so far
    known_states: Dict[FrozenSet[str], str]  # frozenset -> label

    # Partial DFA transitions confirmed so far: (from_label, symbol) -> to_label
    partial_transitions: Dict[Tuple[str, str], str]

    # Whether epsilon-NFA mode is active
    is_epsilon_nfa: bool


# ---------------------------------------------------------------------------
# Full result
# ---------------------------------------------------------------------------

@dataclass
class ConversionResult:
    """Complete output of the subset construction algorithm."""
    dfa: DFA
    steps: List[ConversionStep]
    state_mapping: Dict[str, FrozenSet[str]]
    nfa_state_count: int
    dfa_state_count: int
    reachable_subsets: List[Tuple[str, FrozenSet[str], bool]]  # (label, subset, is_accepting)
    snapshots: List[ConversionSnapshot] = field(default_factory=list)
    is_epsilon_nfa: bool = False


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class SubsetConstructionEngine:
    """
    Algorithmic engine executing the Rabin-Scott Subset Construction algorithm.

    For ordinary NFAs:
      δ'(S, a) = ⋃ { δ(q, a) | q ∈ S }

    For epsilon-NFAs:
      δ'(S, a) = ε-closure( ⋃ { δ(q, a) | q ∈ S } )
      Initial state = ε-closure({q0})
    """

    def __init__(self, nfa: NFA):
        self.nfa = nfa

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def convert(self) -> ConversionResult:
        """
        Execute subset construction transforming NFA M into equivalent DFA M'.

        Algorithm (ordinary NFA):
        1. q'0 = {q0}
        2. Assign label 'A' to q'0; enqueue it.
        3. While queue not empty:
           a. Dequeue current subset S with label L.
           b. For each symbol a in Σ:
              i.  T = ⋃ { δ(q, a) | q ∈ S }
              ii. If T unseen: assign new label, enqueue.
              iii. Record δ'(L, a) = label(T).
        4. Mark DFA state S accepting iff S ∩ F ≠ ∅.

        For ε-NFA: replace step 1 with ε-closure({q0}),
        and step 3b-i with ε-closure(⋃ δ(q, a)).
        """
        is_eps = self.nfa.has_epsilon_transitions

        # Step 1: Initial subset
        raw_initial = frozenset([self.nfa.initial_state])
        initial_subset = self.nfa.epsilon_closure(raw_initial) if is_eps else raw_initial

        # Mappings: frozenset -> label and label -> frozenset
        subset_to_label: Dict[FrozenSet[str], str] = {}
        label_to_subset: Dict[str, FrozenSet[str]] = {}

        # FIFO queue for BFS
        queue: Deque[FrozenSet[str]] = deque()

        # Assign label to initial state
        label_counter = 0
        initial_label = generate_state_label(label_counter)
        label_counter += 1

        subset_to_label[initial_subset] = initial_label
        label_to_subset[initial_label] = initial_subset
        queue.append(initial_subset)

        dfa_transitions: Dict[Tuple[str, str], str] = {}
        steps: List[ConversionStep] = []
        snapshots: List[ConversionSnapshot] = []
        step_counter = 1

        # Track processing history for snapshot queue visualizations
        processed_labels: List[Tuple[str, FrozenSet[str]]] = []  # fully processed
        # We also need to track queue order: each subset in queue order
        enqueue_order: List[FrozenSet[str]] = [initial_subset]  # order subsets were enqueued
        enqueued_set: Set[FrozenSet[str]] = {initial_subset}

        alphabet = self.nfa.sorted_alphabet

        while queue:
            current_subset = queue.popleft()
            current_label = subset_to_label[current_subset]

            # Mark as currently processing — we snapshot per symbol
            queue_pending_before = [
                (subset_to_label[s], s)
                for s in list(queue)
            ]

            for sym in alphabet:
                individual_trans: Dict[str, Set[str]] = {}
                union_set: Set[str] = set()
                eps_closure_steps: Dict[str, Set[str]] = {}

                if not current_subset:
                    # Trap state: empty subset -> itself for all symbols
                    raw_union_subset = frozenset()
                    target_subset = frozenset()
                else:
                    for q in sorted(current_subset):
                        q_targets = set(self.nfa.get_transitions(q, sym))
                        individual_trans[q] = q_targets
                        union_set.update(q_targets)

                    raw_union_subset = frozenset(union_set)

                    if is_eps and union_set:
                        # Compute epsilon closure of the raw union
                        closed = self.nfa.epsilon_closure(union_set)
                        # Track per-state epsilon contributions for trace display
                        for q in sorted(union_set):
                            eps_reach = self.nfa.epsilon_closure({q})
                            if eps_reach != {q}:  # only record if closure adds states
                                eps_closure_steps[q] = set(eps_reach - {q})
                        target_subset = closed
                    else:
                        target_subset = raw_union_subset

                is_new = False
                just_discovered: List[Tuple[str, FrozenSet[str]]] = []

                if target_subset not in subset_to_label:
                    target_label = generate_state_label(label_counter)
                    label_counter += 1
                    subset_to_label[target_subset] = target_label
                    label_to_subset[target_label] = target_subset
                    queue.append(target_subset)
                    enqueue_order.append(target_subset)
                    enqueued_set.add(target_subset)
                    is_new = True
                    just_discovered = [(target_label, target_subset)]
                else:
                    target_label = subset_to_label[target_subset]

                dfa_transitions[(current_label, sym)] = target_label

                # Build explanation text
                curr_fmt = format_subset(current_subset)
                tgt_fmt = format_subset(target_subset)

                if not current_subset:
                    expl = (
                        f"Trap state {current_label} = ∅ on '{sym}' "
                        f"loops to ∅ ({target_label})."
                    )
                else:
                    new_tag = (
                        f"discovered new state {target_label}"
                        if is_new
                        else f"points to existing state {target_label}"
                    )
                    if is_eps and raw_union_subset != target_subset:
                        expl = (
                            f"δ'({current_label}, {sym}) = "
                            f"ε-closure({format_subset(raw_union_subset)}) = "
                            f"{tgt_fmt} ({new_tag})."
                        )
                    else:
                        expl = (
                            f"δ'({current_label}, {sym}) = {tgt_fmt} ({new_tag})."
                        )

                step = ConversionStep(
                    step_number=step_counter,
                    current_label=current_label,
                    current_subset=current_subset,
                    symbol=sym,
                    individual_transitions=individual_trans,
                    raw_union=raw_union_subset,
                    epsilon_closure_steps=eps_closure_steps,
                    union_result=target_subset,
                    target_label=target_label,
                    is_new_state=is_new,
                    explanation=expl,
                )
                steps.append(step)

                # Build snapshot
                snapshot = ConversionSnapshot(
                    snapshot_index=len(snapshots),
                    total_snapshots=0,  # backfill after
                    step=step,
                    queue_pending=[
                        (subset_to_label[s], s)
                        for s in list(queue)
                        if s != target_subset or not is_new
                    ] + (just_discovered if is_new else []),
                    queue_just_discovered=just_discovered,
                    queue_processed=list(processed_labels),
                    known_states=dict(subset_to_label),
                    partial_transitions=dict(dfa_transitions),
                    is_epsilon_nfa=is_eps,
                )
                snapshots.append(snapshot)

                step_counter += 1

            # This state is fully processed
            processed_labels.append((current_label, current_subset))

        # Backfill total_snapshots
        total = len(snapshots)
        for snap in snapshots:
            snap.total_snapshots = total

        # Determine DFA final states
        dfa_states = set(label_to_subset.keys())
        dfa_final_states: Set[str] = set()
        reachable_summary: List[Tuple[str, FrozenSet[str], bool]] = []

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
            snapshots=snapshots,
            is_epsilon_nfa=is_eps,
        )
