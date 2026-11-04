"""
Automata Graph Visualization Module.

Generates Graphviz DOT representations and graphs for both NFAs and DFAs.
Follows formal automata theory visual standards:
- Initial state indicated by an incoming arrow from an invisible source node
- Final states designated with double circles
- Normal states designated with single circles
- Merged transition labels for multi-symbol edges
- Crisp academic color scheme (deep navy, slate, soft light backgrounds)
"""

from typing import Dict, List, Set, Tuple, Optional
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from core.nfa import NFA
from core.dfa import DFA
from core.conversion import format_subset


def generate_nfa_dot(nfa: NFA) -> str:
    """
    Generate clean Graphviz DOT language string for an NFA.
    """
    lines: List[str] = [
        'digraph NFA {',
        '    rankdir=LR;',
        '    bgcolor="transparent";',
        '    node [fontname="Helvetica, Arial, sans-serif", fontsize=11];',
        '    edge [fontname="Helvetica, Arial, sans-serif", fontsize=10, color="#334155", fontcolor="#1E293B"];',
        '',
        '    // Invisible start anchor node',
        '    __start [shape=none, label="", width=0, height=0];',
    ]

    # Partition states into final and non-final
    final_states = sorted(list(nfa.final_states))
    non_final_states = [s for s in nfa.sorted_states if s not in nfa.final_states]

    # Declare final states with doublecircle
    if final_states:
        f_nodes = " ".join(f'"{s}"' for s in final_states)
        lines.append(
            f'    node [shape=doublecircle, style="filled", fillcolor="#F0FDF4", color="#15803D", penwidth=2.0]; {f_nodes};'
        )

    # Declare non-final states with circle
    if non_final_states:
        nf_nodes = " ".join(f'"{s}"' for s in non_final_states)
        lines.append(
            f'    node [shape=circle, style="filled", fillcolor="#F8FAFC", color="#1E3A8A", penwidth=1.5]; {nf_nodes};'
        )

    lines.append('')
    # Incoming arrow to initial state
    if nfa.initial_state:
        lines.append(f'    __start -> "{nfa.initial_state}" [label="start", color="#1E3A8A", fontcolor="#1E3A8A", penwidth=1.5];')

    lines.append('')
    # Group transitions by (from_state, to_state) -> list of symbols
    edge_map: Dict[Tuple[str, str], List[str]] = {}
    for (from_st, sym), targets in nfa.transitions.items():
        for to_st in targets:
            edge_map.setdefault((from_st, to_st), []).append(sym)

    for (from_st, to_st), symbols in sorted(edge_map.items()):
        symbols_label = ", ".join(sorted(symbols))
        lines.append(f'    "{from_st}" -> "{to_st}" [label="{symbols_label}"];')

    lines.append('}')
    return "\n".join(lines)


def generate_dfa_dot(dfa: DFA) -> str:
    """
    Generate clean Graphviz DOT language string for a DFA.
    Includes both the state label (A, B, C...) and the underlying NFA subset.
    """
    lines: List[str] = [
        'digraph DFA {',
        '    rankdir=LR;',
        '    bgcolor="transparent";',
        '    node [fontname="Helvetica, Arial, sans-serif", fontsize=10];',
        '    edge [fontname="Helvetica, Arial, sans-serif", fontsize=10, color="#334155", fontcolor="#1E293B"];',
        '',
        '    // Invisible start anchor node',
        '    __start [shape=none, label="", width=0, height=0];',
    ]

    final_states = sorted(list(dfa.final_states))
    non_final_states = [s for s in dfa.sorted_states if s not in dfa.final_states]

    # Define final states with doublecircle
    for s in final_states:
        subset = dfa.state_subsets.get(s, frozenset())
        subset_str = format_subset(subset)
        label_text = f"{s}\\n{subset_str}"
        lines.append(
            f'    "{s}" [shape=doublecircle, style="filled", fillcolor="#F0FDF4", color="#15803D", penwidth=2.0, label="{label_text}"];'
        )

    # Define non-final states with circle
    for s in non_final_states:
        subset = dfa.state_subsets.get(s, frozenset())
        subset_str = format_subset(subset)
        label_text = f"{s}\\n{subset_str}"
        lines.append(
            f'    "{s}" [shape=circle, style="filled", fillcolor="#F8FAFC", color="#1E3A8A", penwidth=1.5, label="{label_text}"];'
        )

    lines.append('')
    # Incoming arrow to initial state
    if dfa.initial_state:
        lines.append(f'    __start -> "{dfa.initial_state}" [label="start", color="#1E3A8A", fontcolor="#1E3A8A", penwidth=1.5];')

    lines.append('')
    # Group transitions by (from_state, to_state) -> list of symbols
    edge_map: Dict[Tuple[str, str], List[str]] = {}
    for (from_st, sym), to_st in dfa.transitions.items():
        edge_map.setdefault((from_st, to_st), []).append(sym)

    for (from_st, to_st), symbols in sorted(edge_map.items()):
        symbols_label = ", ".join(sorted(symbols))
        lines.append(f'    "{from_st}" -> "{to_st}" [label="{symbols_label}"];')

    lines.append('}')
    return "\n".join(lines)


def render_nfa_graph(nfa: NFA):
    """
    Returns a Graphviz Digraph object or DOT source for the NFA.
    """
    return generate_nfa_dot(nfa)


def render_dfa_graph(dfa: DFA):
    """
    Returns a Graphviz Digraph object or DOT source for the DFA.
    """
    return generate_dfa_dot(dfa)


def generate_state_distribution_chart(nfa_count: int, dfa_count: int) -> Figure:
    """
    Generate an academic Matplotlib chart comparing state spaces:
    NFA States vs Reachable DFA States vs Theoretical Powerset Bound (2^|Q|).
    """
    fig, ax = plt.subplots(figsize=(6, 3.2), dpi=100)
    
    categories = ['NFA States (|Q|)', 'Reachable DFA (|Q\'|)', 'Powerset Bound (2^|Q|)']
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
    ax.set_title('Automata State Complexity Comparison', fontsize=11, fontweight='bold', color='#0F172A', pad=12)
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
