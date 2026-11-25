"""
Automata Graph Visualization Module.

Generates Graphviz DOT representations and graphs for both NFAs and DFAs.
Supports:
- Full static NFA/DFA graphs
- Partial DFA graphs (for live simulator, showing only discovered states)
- Highlighted graphs (active state/edge highlighted for string tester)

Follows formal automata theory visual standards:
- Initial state indicated by an incoming arrow from an invisible source node
- Final states designated with double circles
- Normal states designated with single circles
- Merged transition labels for multi-symbol edges
- Academic color scheme (deep navy, slate, light backgrounds)
"""

from typing import Dict, List, Set, Tuple, Optional, FrozenSet
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from core.nfa import NFA, EPSILON
from core.dfa import DFA
from core.conversion import format_subset, ConversionSnapshot


# ---------------------------------------------------------------------------
# Color constants (academic palette)
# ---------------------------------------------------------------------------
_COL_BORDER_DEFAULT = "#1E3A8A"       # navy blue
_COL_FILL_NORMAL = "#F8FAFC"          # near-white
_COL_FILL_ACCEPT = "#F0FDF4"          # light green
_COL_BORDER_ACCEPT = "#15803D"        # dark green
_COL_EDGE = "#334155"                 # slate
_COL_EDGE_FONT = "#1E293B"            # near-black
_COL_HIGHLIGHT_STATE = "#FEF9C3"      # amber yellow fill (current)
_COL_HIGHLIGHT_BORDER = "#B45309"     # amber border (current)
_COL_NEW_STATE_FILL = "#EFF6FF"       # light blue (newly discovered)
_COL_NEW_STATE_BORDER = "#2563EB"     # blue border
_COL_HIGHLIGHT_EDGE = "#DC2626"       # red (active transition edge)
_COL_PENDING_FILL = "#F1F5F9"         # light grey (queued but unprocessed)
_COL_PENDING_BORDER = "#64748B"       # grey border


# ---------------------------------------------------------------------------
# Full NFA graph
# ---------------------------------------------------------------------------

def generate_nfa_dot(
    nfa: NFA,
    highlight_states: Optional[Set[str]] = None,
    highlight_edges: Optional[Set[Tuple[str, str, str]]] = None,  # (from, to, sym)
) -> str:
    """
    Generate Graphviz DOT string for an NFA.

    Args:
        nfa: NFA instance.
        highlight_states: States to highlight (e.g. active states during simulation).
        highlight_edges: (from_state, to_state, symbol) edges to color red.
    """
    highlight_states = highlight_states or set()
    highlight_edges = highlight_edges or set()

    lines: List[str] = [
        'digraph NFA {',
        '    rankdir=LR;',
        '    bgcolor="transparent";',
        '    node [fontname="Helvetica, Arial, sans-serif", fontsize=11];',
        '    edge [fontname="Helvetica, Arial, sans-serif", fontsize=10, '
        f'color="{_COL_EDGE}", fontcolor="{_COL_EDGE_FONT}"];',
        '',
        '    // Invisible start anchor',
        '    __start [shape=none, label="", width=0, height=0];',
    ]

    final_states = set(nfa.final_states)

    for state in nfa.sorted_states:
        is_final = state in final_states
        is_highlighted = state in highlight_states

        if is_highlighted:
            shape = "doublecircle" if is_final else "circle"
            fill = _COL_HIGHLIGHT_STATE
            border = _COL_HIGHLIGHT_BORDER
            pw = "2.5"
        elif is_final:
            shape = "doublecircle"
            fill = _COL_FILL_ACCEPT
            border = _COL_BORDER_ACCEPT
            pw = "2.0"
        else:
            shape = "circle"
            fill = _COL_FILL_NORMAL
            border = _COL_BORDER_DEFAULT
            pw = "1.5"

        lines.append(
            f'    "{state}" [shape={shape}, style="filled", '
            f'fillcolor="{fill}", color="{border}", penwidth={pw}];'
        )

    lines.append('')
    if nfa.initial_state:
        lines.append(
            f'    __start -> "{nfa.initial_state}" '
            f'[label="start", color="{_COL_BORDER_DEFAULT}", '
            f'fontcolor="{_COL_BORDER_DEFAULT}", penwidth=1.5];'
        )

    lines.append('')
    # Group transitions by (from_state, to_state) -> list of symbols
    edge_map: Dict[Tuple[str, str], List[str]] = {}
    for (from_st, sym), targets in nfa.transitions.items():
        for to_st in targets:
            edge_map.setdefault((from_st, to_st), []).append(sym)

    for (from_st, to_st), symbols in sorted(edge_map.items()):
        symbols_label = ", ".join(sorted(symbols))
        # Check if any of these (from, to, sym) combos are highlighted
        is_active = any((from_st, to_st, s) in highlight_edges for s in symbols)
        edge_color = _COL_HIGHLIGHT_EDGE if is_active else _COL_EDGE
        edge_pw = "2.5" if is_active else "1.0"
        lines.append(
            f'    "{from_st}" -> "{to_st}" '
            f'[label="{symbols_label}", color="{edge_color}", penwidth={edge_pw}];'
        )

    lines.append('}')
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Full DFA graph
# ---------------------------------------------------------------------------

def generate_dfa_dot(
    dfa: DFA,
    highlight_state: Optional[str] = None,
    highlight_edge: Optional[Tuple[str, str, str]] = None,  # (from, to, sym)
    new_states: Optional[Set[str]] = None,
) -> str:
    """
    Generate Graphviz DOT string for a DFA.
    Includes both state label (A, B, C...) and the underlying NFA subset.

    Args:
        dfa: DFA instance.
        highlight_state: DFA state label to highlight as 'current'.
        highlight_edge: (from_label, to_label, symbol) edge to highlight.
        new_states: Labels of newly discovered states to colour distinctly.
    """
    highlight_state = highlight_state or ""
    highlight_edge = highlight_edge or ("", "", "")
    new_states = new_states or set()

    lines: List[str] = [
        'digraph DFA {',
        '    rankdir=LR;',
        '    bgcolor="transparent";',
        '    node [fontname="Helvetica, Arial, sans-serif", fontsize=10];',
        '    edge [fontname="Helvetica, Arial, sans-serif", fontsize=10, '
        f'color="{_COL_EDGE}", fontcolor="{_COL_EDGE_FONT}"];',
        '',
        '    // Invisible start anchor',
        '    __start [shape=none, label="", width=0, height=0];',
    ]

    final_states = set(dfa.final_states)

    for s in dfa.sorted_states:
        subset = dfa.state_subsets.get(s, frozenset())
        subset_str = format_subset(subset)
        label_text = f"{s}\\n{subset_str}"
        is_final = s in final_states
        is_current = s == highlight_state
        is_new = s in new_states

        if is_current:
            shape = "doublecircle" if is_final else "circle"
            fill = _COL_HIGHLIGHT_STATE
            border = _COL_HIGHLIGHT_BORDER
            pw = "2.5"
        elif is_new:
            shape = "doublecircle" if is_final else "circle"
            fill = _COL_NEW_STATE_FILL
            border = _COL_NEW_STATE_BORDER
            pw = "2.0"
        elif is_final:
            shape = "doublecircle"
            fill = _COL_FILL_ACCEPT
            border = _COL_BORDER_ACCEPT
            pw = "2.0"
        else:
            shape = "circle"
            fill = _COL_FILL_NORMAL
            border = _COL_BORDER_DEFAULT
            pw = "1.5"

        lines.append(
            f'    "{s}" [shape={shape}, style="filled", '
            f'fillcolor="{fill}", color="{border}", penwidth={pw}, label="{label_text}"];'
        )

    lines.append('')
    if dfa.initial_state:
        lines.append(
            f'    __start -> "{dfa.initial_state}" '
            f'[label="start", color="{_COL_BORDER_DEFAULT}", '
            f'fontcolor="{_COL_BORDER_DEFAULT}", penwidth=1.5];'
        )

    lines.append('')
    edge_map: Dict[Tuple[str, str], List[str]] = {}
    for (from_st, sym), to_st in dfa.transitions.items():
        edge_map.setdefault((from_st, to_st), []).append(sym)

    for (from_st, to_st), symbols in sorted(edge_map.items()):
        symbols_label = ", ".join(sorted(symbols))
        h_from, h_to, h_sym = highlight_edge
        is_active = (from_st == h_from and to_st == h_to and h_sym in symbols)
        edge_color = _COL_HIGHLIGHT_EDGE if is_active else _COL_EDGE
        edge_pw = "2.5" if is_active else "1.0"
        lines.append(
            f'    "{from_st}" -> "{to_st}" '
            f'[label="{symbols_label}", color="{edge_color}", penwidth={edge_pw}];'
        )

    lines.append('}')
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Partial DFA graph (for live simulator)
# ---------------------------------------------------------------------------

def generate_partial_dfa_dot(snapshot: ConversionSnapshot) -> str:
    """
    Generate a DFA DOT graph showing only the states and transitions
    discovered so far at the given snapshot index.

    - Current DFA state being processed: amber highlight
    - Newly discovered state: blue highlight
    - Pending (queued) states: grey
    - Already processed states: normal colours
    - Active transition edge being computed: red
    """
    step = snapshot.step
    known = snapshot.known_states           # frozenset -> label
    partial_trans = snapshot.partial_transitions  # (label, sym) -> label

    # Invert known map for label lookups
    label_to_subset: Dict[str, FrozenSet[str]] = {v: k for k, v in known.items()}

    # Collect labels of pending states (in queue now)
    pending_labels = {lbl for lbl, _ in snapshot.queue_pending}
    new_labels = {lbl for lbl, _ in snapshot.queue_just_discovered}
    processed_labels = {lbl for lbl, _ in snapshot.queue_processed}
    current_label = step.current_label

    # We need DFA final states: any subset intersecting NFA final states.
    # We don't have the NFA here directly, but we can infer from step data.
    # We'll mark accepting states via the subset; we pass final detection downstream.
    # For the graph we colour but don't use doublecircle logic without NFA ref.
    # NOTE: accepting detection is done by the caller who has conv_result.
    # We embed a __ACCEPT__ marker in the label for caller to handle,
    # or we let generate_partial_dfa_dot_with_finals take the final_states set.
    # For simplicity: accept all labels where subset ∩ nfa_finals != ∅ — but
    # we don't have nfa_finals here. We pass an optional parameter.

    lines: List[str] = [
        'digraph DFA {',
        '    rankdir=LR;',
        '    bgcolor="transparent";',
        '    node [fontname="Helvetica, Arial, sans-serif", fontsize=10];',
        '    edge [fontname="Helvetica, Arial, sans-serif", fontsize=10, '
        f'color="{_COL_EDGE}", fontcolor="{_COL_EDGE_FONT}"];',
        '',
        '    __start [shape=none, label="", width=0, height=0];',
    ]

    # Sort labels for deterministic rendering
    all_labels = sorted(label_to_subset.keys())
    # Initial label is always the first discovered (label A)
    initial_label = min(all_labels, key=lambda lbl: len(lbl) * 100 + ord(lbl[0]))

    for lbl in all_labels:
        subset = label_to_subset[lbl]
        subset_str = format_subset(subset)
        label_text = f"{lbl}\\n{subset_str}"

        is_current = lbl == current_label
        is_new = lbl in new_labels
        is_pending = lbl in pending_labels and lbl != current_label
        is_processed = lbl in processed_labels

        if is_current:
            shape = "circle"
            fill = _COL_HIGHLIGHT_STATE
            border = _COL_HIGHLIGHT_BORDER
            pw = "2.5"
        elif is_new:
            shape = "circle"
            fill = _COL_NEW_STATE_FILL
            border = _COL_NEW_STATE_BORDER
            pw = "2.0"
        elif is_pending:
            shape = "circle"
            fill = _COL_PENDING_FILL
            border = _COL_PENDING_BORDER
            pw = "1.5"
        else:
            # Processed or other known state
            shape = "circle"
            fill = _COL_FILL_NORMAL
            border = _COL_BORDER_DEFAULT
            pw = "1.5"

        lines.append(
            f'    "{lbl}" [shape={shape}, style="filled", '
            f'fillcolor="{fill}", color="{border}", penwidth={pw}, label="{label_text}"];'
        )

    lines.append('')
    if initial_label:
        lines.append(
            f'    __start -> "{initial_label}" '
            f'[label="start", color="{_COL_BORDER_DEFAULT}", '
            f'fontcolor="{_COL_BORDER_DEFAULT}", penwidth=1.5];'
        )

    lines.append('')
    edge_map: Dict[Tuple[str, str], List[str]] = {}
    for (from_lbl, sym), to_lbl in partial_trans.items():
        edge_map.setdefault((from_lbl, to_lbl), []).append(sym)

    active_from = step.current_label
    active_to = step.target_label
    active_sym = step.symbol

    for (from_lbl, to_lbl), symbols in sorted(edge_map.items()):
        symbols_label = ", ".join(sorted(symbols))
        is_active = (from_lbl == active_from and to_lbl == active_to and active_sym in symbols)
        edge_color = _COL_HIGHLIGHT_EDGE if is_active else _COL_EDGE
        edge_pw = "2.5" if is_active else "1.0"
        lines.append(
            f'    "{from_lbl}" -> "{to_lbl}" '
            f'[label="{symbols_label}", color="{edge_color}", penwidth={edge_pw}];'
        )

    lines.append('}')
    return "\n".join(lines)


def generate_partial_dfa_dot_with_finals(
    snapshot: ConversionSnapshot,
    nfa_final_states: Set[str],
) -> str:
    """
    Like generate_partial_dfa_dot but correctly marks accepting states
    with doublecircle by checking subset ∩ nfa_final_states.
    """
    step = snapshot.step
    known = snapshot.known_states
    partial_trans = snapshot.partial_transitions
    label_to_subset: Dict[str, FrozenSet[str]] = {v: k for k, v in known.items()}

    pending_labels = {lbl for lbl, _ in snapshot.queue_pending}
    new_labels = {lbl for lbl, _ in snapshot.queue_just_discovered}
    current_label = step.current_label

    lines: List[str] = [
        'digraph DFA {',
        '    rankdir=LR;',
        '    bgcolor="transparent";',
        '    node [fontname="Helvetica, Arial, sans-serif", fontsize=10];',
        '    edge [fontname="Helvetica, Arial, sans-serif", fontsize=10, '
        f'color="{_COL_EDGE}", fontcolor="{_COL_EDGE_FONT}"];',
        '',
        '    __start [shape=none, label="", width=0, height=0];',
    ]

    all_labels = sorted(label_to_subset.keys())
    initial_label = min(all_labels, key=lambda lbl: len(lbl) * 100 + ord(lbl[0])) if all_labels else ""

    for lbl in all_labels:
        subset = label_to_subset[lbl]
        subset_str = format_subset(subset)
        label_text = f"{lbl}\\n{subset_str}"

        is_final = bool(subset.intersection(nfa_final_states))
        is_current = lbl == current_label
        is_new = lbl in new_labels
        is_pending = lbl in pending_labels and lbl != current_label
        shape = "doublecircle" if is_final else "circle"

        if is_current:
            fill = _COL_HIGHLIGHT_STATE
            border = _COL_HIGHLIGHT_BORDER
            pw = "2.5"
        elif is_new:
            fill = _COL_NEW_STATE_FILL
            border = _COL_NEW_STATE_BORDER
            pw = "2.0"
        elif is_pending:
            fill = _COL_PENDING_FILL
            border = _COL_PENDING_BORDER
            pw = "1.5"
        elif is_final:
            fill = _COL_FILL_ACCEPT
            border = _COL_BORDER_ACCEPT
            pw = "2.0"
        else:
            fill = _COL_FILL_NORMAL
            border = _COL_BORDER_DEFAULT
            pw = "1.5"

        lines.append(
            f'    "{lbl}" [shape={shape}, style="filled", '
            f'fillcolor="{fill}", color="{border}", penwidth={pw}, label="{label_text}"];'
        )

    lines.append('')
    if initial_label:
        lines.append(
            f'    __start -> "{initial_label}" '
            f'[label="start", color="{_COL_BORDER_DEFAULT}", '
            f'fontcolor="{_COL_BORDER_DEFAULT}", penwidth=1.5];'
        )

    lines.append('')
    edge_map: Dict[Tuple[str, str], List[str]] = {}
    for (from_lbl, sym), to_lbl in partial_trans.items():
        edge_map.setdefault((from_lbl, to_lbl), []).append(sym)

    active_from = step.current_label
    active_to = step.target_label
    active_sym = step.symbol

    for (from_lbl, to_lbl), symbols in sorted(edge_map.items()):
        symbols_label = ", ".join(sorted(symbols))
        is_active = (from_lbl == active_from and to_lbl == active_to and active_sym in symbols)
        edge_color = _COL_HIGHLIGHT_EDGE if is_active else _COL_EDGE
        edge_pw = "2.5" if is_active else "1.0"
        lines.append(
            f'    "{from_lbl}" -> "{to_lbl}" '
            f'[label="{symbols_label}", color="{edge_color}", penwidth={edge_pw}];'
        )

    lines.append('}')
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Compatibility wrappers
# ---------------------------------------------------------------------------

def render_nfa_graph(nfa: NFA) -> str:
    """Returns DOT source for the NFA."""
    return generate_nfa_dot(nfa)


def render_dfa_graph(dfa: DFA) -> str:
    """Returns DOT source for the DFA."""
    return generate_dfa_dot(dfa)


# ---------------------------------------------------------------------------
# State distribution chart
# ---------------------------------------------------------------------------

def generate_state_distribution_chart(nfa_count: int, dfa_count: int) -> Figure:
    """
    Generate an academic Matplotlib chart comparing state spaces:
    NFA States vs Reachable DFA States vs Theoretical Powerset Bound (2^|Q|).
    """
    fig, ax = plt.subplots(figsize=(6, 3.2), dpi=100)

    categories = ['NFA States (|Q|)', "Reachable DFA (|Q'|)", 'Powerset Bound (2^|Q|)']
    powerset_bound = 2 ** nfa_count if nfa_count <= 10 else 1024
    values = [nfa_count, dfa_count, powerset_bound]
    colors = ['#1E3A8A', '#0D9488', '#64748B']

    bars = ax.bar(categories, values, color=colors, width=0.48, edgecolor="#0F172A", linewidth=0.8)

    for bar in bars:
        height = bar.get_height()
        ax.annotate(
            f'{height}',
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 4),
            textcoords="offset points",
            ha='center', va='bottom',
            fontsize=10, fontweight='bold', color='#0F172A'
        )

    ax.set_ylabel('Number of States', fontsize=10, fontweight='500', color='#1E293B')
    ax.set_title(
        'Automata State Complexity Comparison',
        fontsize=11, fontweight='bold', color='#0F172A', pad=12
    )
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#CBD5E1')
    ax.spines['bottom'].set_color('#CBD5E1')
    ax.grid(axis='y', linestyle='--', alpha=0.4, color='#94A3B8')
    ax.set_axisbelow(True)
    fig.patch.set_facecolor('#FFFFFF')
    ax.set_facecolor('#F8FAFC')
    plt.tight_layout()
    return fig
