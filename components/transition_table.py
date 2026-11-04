"""
Transition Table Display Components.

Renders high-clarity tabular representations of NFA and DFA transition functions:
- NFA transition list and matrix views
- DFA state subset mapping and transition table with acceptance status markers
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any

from core.nfa import NFA
from core.dfa import DFA
from core.conversion import format_subset


def get_nfa_matrix_df(nfa: NFA) -> pd.DataFrame:
    """Generate a clean pandas DataFrame for NFA transitions in matrix form."""
    rows = []
    for state in nfa.sorted_states:
        row: Dict[str, Any] = {"State": state}
        for sym in nfa.sorted_alphabet:
            targets = nfa.get_transitions(state, sym)
            row[sym] = "{" + ", ".join(sorted(targets)) + "}" if targets else "∅"
        rows.append(row)
    return pd.DataFrame(rows)


def render_nfa_table(nfa: NFA):
    """Render NFA transition table in Streamlit."""
    df = get_nfa_matrix_df(nfa)
    
    # Add indicators for initial and final states
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
    st.caption("Legend: → Initial State | * Final / Accepting State | ∅ Empty set (no transition)")


def get_dfa_matrix_df(dfa: DFA) -> pd.DataFrame:
    """Generate a clean pandas DataFrame for DFA transitions with subset annotations."""
    rows = []
    for label in dfa.sorted_states:
        subset = dfa.state_subsets.get(label, frozenset())
        subset_str = format_subset(subset)
        
        status_flags = []
        if label == dfa.initial_state:
            status_flags.append("Initial (→)")
        if label in dfa.final_states:
            status_flags.append("Final (*)")
        if not status_flags:
            status_flags.append("Normal")

        row: Dict[str, Any] = {
            "DFA State": label,
            "NFA Subset": subset_str,
            "Status": ", ".join(status_flags),
        }
        for sym in dfa.sorted_alphabet:
            target = dfa.get_transition(label, sym)
            target_subset = dfa.state_subsets.get(target, frozenset()) if target else frozenset()
            row[f"δ'({sym})"] = f"{target} ({format_subset(target_subset)})" if target else "—"
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
    st.caption("A DFA state is accepting (*) if its constituent NFA subset contains at least one NFA final state.")
