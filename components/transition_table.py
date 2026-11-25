"""
Transition Table Display Components.

Renders clean tabular views for NFA and DFA transitions,
including the live continuously updating DFA transition table
used during step-by-step algorithm animation.
"""

import html
import streamlit as st
import pandas as pd
from typing import Dict, Any, List, Set, FrozenSet

from core.nfa import NFA, EPSILON
from core.dfa import DFA
from core.conversion import format_subset, ConversionSnapshot


def get_nfa_matrix_df(nfa: NFA) -> pd.DataFrame:
    """Generate a clean pandas DataFrame for NFA transitions in matrix form."""
    symbols = list(nfa.sorted_alphabet)
    if nfa.has_epsilon_transitions:
        symbols.append(EPSILON)

    rows = []
    for state in nfa.sorted_states:
        row: Dict[str, Any] = {"State": state}
        for sym in symbols:
            targets = nfa.get_transitions(state, sym)
            row[sym] = "{" + ", ".join(sorted(targets)) + "}" if targets else "∅"
        rows.append(row)
    return pd.DataFrame(rows)


def render_nfa_table(nfa: NFA):
    """Render NFA transition table in Streamlit."""
    df = get_nfa_matrix_df(nfa)

    def format_state_col(state_name: str) -> str:
        prefix = ""
        if state_name == nfa.initial_state:
            prefix += "→ "
        if state_name in nfa.final_states:
            prefix += "* "
        return f"{prefix}{state_name}"

    display_df = df.copy()
    display_df["State"] = display_df["State"].apply(format_state_col)

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )
    st.caption("→ Start State &nbsp;|&nbsp; * Accepting State &nbsp;|&nbsp; ∅ No Transition")


def get_dfa_matrix_df(dfa: DFA) -> pd.DataFrame:
    """Generate a clean pandas DataFrame for DFA transitions with subset annotations."""
    rows = []
    for label in dfa.sorted_states:
        subset = dfa.state_subsets.get(label, frozenset())
        subset_str = format_subset(subset)

        status_flags = []
        if label == dfa.initial_state:
            status_flags.append("Start (→)")
        if label in dfa.final_states:
            status_flags.append("Accept (*)")
        if not subset:
            status_flags.append("Trap (∅)")
        if not status_flags:
            status_flags.append("Normal")

        row: Dict[str, Any] = {
            "DFA State": label,
            "NFA Subset": subset_str,
        }
        for sym in dfa.sorted_alphabet:
            target = dfa.get_transition(label, sym)
            target_subset = dfa.state_subsets.get(target, frozenset()) if target else frozenset()
            row[f"Input {sym}"] = f"{target} ({format_subset(target_subset)})" if target else "—"
        row["Type"] = ", ".join(status_flags)
        rows.append(row)
    return pd.DataFrame(rows)


def render_dfa_table(dfa: DFA):
    """Render DFA transition table in Streamlit."""
    df = get_dfa_matrix_df(dfa)
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
    )
    st.caption("A DFA state is accepting (*) if its subset contains any NFA accepting state.")


# ---------------------------------------------------------------------------
# Live Continuously Updating DFA Transition Table
# ---------------------------------------------------------------------------

def render_live_dfa_table(
    snapshot: ConversionSnapshot,
    alphabet: List[str],
    nfa_final_states: Set[str],
    initial_label: str = "A",
):
    """
    Render a live HTML transition table reflecting ONLY the states and
    transitions discovered up to `snapshot`.

    - Current row being processed is highlighted in amber.
    - Newly discovered state rows are highlighted in soft blue.
    - Active transition cell (current_label, symbol) is highlighted in bold blue/amber.
    - Unprocessed transitions are clearly marked as '… (pending)'.
    """
    step = snapshot.step
    known_states = snapshot.known_states            # frozenset -> label
    partial_trans = snapshot.partial_transitions    # (from_label, sym) -> to_label
    label_to_subset: Dict[str, FrozenSet[str]] = {v: k for k, v in known_states.items()}
    new_labels = {lbl for lbl, _ in snapshot.queue_just_discovered}

    # Sort labels in discovery order (A, B, ..., Z, AA, ...)
    def label_sort_key(lbl: str):
        return (len(lbl), lbl)

    ordered_labels = sorted(label_to_subset.keys(), key=label_sort_key)

    # Build HTML table
    header_cells = ["<th>DFA State</th>", "<th>NFA Subset</th>"]
    for sym in alphabet:
        header_cells.append(f"<th>Input {html.escape(sym)}</th>")
    header_cells.append("<th>Type</th>")

    rows_html: List[str] = []
    for lbl in ordered_labels:
        subset = label_to_subset[lbl]
        subset_str = html.escape(format_subset(subset))
        is_current = (lbl == step.current_label)
        is_new = (lbl in new_labels)
        is_accepting = bool(subset.intersection(nfa_final_states))

        flags = []
        if lbl == initial_label:
            flags.append("Start (→)")
        if is_accepting:
            flags.append("Accept (*)")
        if not subset:
            flags.append("Trap (∅)")
        if not flags:
            flags.append("Normal")
        type_str = html.escape(", ".join(flags))

        row_cls = ""
        if is_current:
            row_cls = ' class="live-row-current"'
        elif is_new:
            row_cls = ' class="live-row-new"'
        elif is_accepting:
            row_cls = ' class="live-row-accept"'

        badge = ""
        if is_current:
            badge = ' <span class="tbl-badge tbl-badge-cur">ACTIVE</span>'
        elif is_new:
            badge = ' <span class="tbl-badge tbl-badge-new">NEW</span>'

        cells = [
            f"<td><strong>{html.escape(lbl)}</strong>{badge}</td>",
            f"<td><code>{subset_str}</code></td>",
        ]

        for sym in alphabet:
            target = partial_trans.get((lbl, sym))
            is_active_cell = is_current and (sym == step.symbol)
            cell_cls = ' class="live-cell-active"' if is_active_cell else ""

            if target is not None:
                tgt_subset = label_to_subset.get(target, frozenset())
                tgt_str = html.escape(f"{target} ({format_subset(tgt_subset)})")
                cells.append(f"<td{cell_cls}><strong>{tgt_str}</strong></td>")
            else:
                cells.append(f'<td{cell_cls}><span class="live-pending">… pending</span></td>')

        cells.append(f"<td>{type_str}</td>")
        rows_html.append(f"<tr{row_cls}>{''.join(cells)}</tr>")

    table_html = (
        '<div class="live-table-wrap">'
        '<table class="live-dfa-table">'
        f"<thead><tr>{''.join(header_cells)}</tr></thead>"
        f"<tbody>{''.join(rows_html)}</tbody>"
        "</table>"
        "</div>"
    )
    st.markdown(table_html, unsafe_allow_html=True)
