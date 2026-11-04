"""
NFA Input Form Component.

Provides configuration interfaces for:
- State definitions (Q)
- Alphabet definition (Sigma)
- Initial state (q0)
- Final / accepting states (F)
- Tabular interactive transition editor (st.data_editor)
- Preset loading, validation triggers, and reset actions
"""

import streamlit as st
import pandas as pd
from typing import Dict, Tuple, Set, Optional

from core.nfa import NFA
from core.validation import NFAValidator, ValidationResult


# Preset definitions
PRESETS = {
    "Built-in: Strings ending in '01' (Default)": {
        "states": "q0, q1, q2",
        "alphabet": "0, 1",
        "initial": "q0",
        "finals": "q2",
        "transitions": {
            ("q0", "0"): "q0, q1",
            ("q0", "1"): "q0",
            ("q1", "0"): "",
            ("q1", "1"): "q2",
            ("q2", "0"): "",
            ("q2", "1"): "",
        },
    },
    "Example 2: Strings containing substring '010'": {
        "states": "q0, q1, q2, q3",
        "alphabet": "0, 1",
        "initial": "q0",
        "finals": "q3",
        "transitions": {
            ("q0", "0"): "q0, q1",
            ("q0", "1"): "q0",
            ("q1", "0"): "",
            ("q1", "1"): "q2",
            ("q2", "0"): "q3",
            ("q2", "1"): "",
            ("q3", "0"): "q3",
            ("q3", "1"): "q3",
        },
    },
    "Example 3: Strings with 'a' at 2nd position": {
        "states": "q0, q1, q2",
        "alphabet": "a, b",
        "initial": "q0",
        "finals": "q2",
        "transitions": {
            ("q0", "a"): "q1",
            ("q0", "b"): "q1",
            ("q1", "a"): "q2",
            ("q1", "b"): "",
            ("q2", "a"): "q2",
            ("q2", "b"): "q2",
        },
    },
}


def load_preset_into_state(preset_name: str):
    """Load selected preset into session state."""
    preset = PRESETS[preset_name]
    st.session_state["input_states"] = preset["states"]
    st.session_state["input_alphabet"] = preset["alphabet"]
    st.session_state["input_initial"] = preset["initial"]
    st.session_state["input_finals"] = preset["finals"]
    st.session_state["nfa_trans_dict"] = dict(preset["transitions"])
    st.session_state["validation_result"] = None
    st.session_state["conversion_result"] = None


def reset_to_empty():
    """Reset configuration to empty."""
    st.session_state["input_states"] = "q0, q1"
    st.session_state["input_alphabet"] = "0, 1"
    st.session_state["input_initial"] = "q0"
    st.session_state["input_finals"] = "q1"
    st.session_state["nfa_trans_dict"] = {
        ("q0", "0"): "",
        ("q0", "1"): "",
        ("q1", "0"): "",
        ("q1", "1"): "",
    }
    st.session_state["validation_result"] = None
    st.session_state["conversion_result"] = None


def build_transition_table_df(states: list[str], alphabet: list[str], trans_map: dict) -> pd.DataFrame:
    """Build a tabular dataframe with columns: [Current State, Input Symbol, Next States]."""
    rows = []
    for s in states:
        for a in alphabet:
            val = trans_map.get((s, a), "")
            rows.append({
                "Current State": s,
                "Input Symbol": a,
                "Next States (comma-separated or empty)": val,
            })
    return pd.DataFrame(rows)


def render_nfa_input_controls() -> Optional[NFA]:
    """
    Renders the complete NFA input UI and returns the constructed NFA if valid.
    """
    # Initialize session state if not already set
    if "input_states" not in st.session_state:
        load_preset_into_state("Built-in: Strings ending in '01' (Default)")

    st.subheader("1. Automaton Formal Definition")
    st.caption("Specify the 5-tuple components: Q, Σ, q0, F, and δ.")

    # Preset selection bar
    preset_col, btn_load, btn_reset = st.columns([3, 1, 1])
    with preset_col:
        selected_preset = st.selectbox(
            "Select Example Preset:",
            options=list(PRESETS.keys()),
            key="preset_dropdown",
        )
    with btn_load:
        st.write("")
        st.write("")
        if st.button("Load Preset", use_container_width=True):
            load_preset_into_state(selected_preset)
            st.rerun()
    with btn_reset:
        st.write("")
        st.write("")
        if st.button("Reset All", use_container_width=True):
            reset_to_empty()
            st.rerun()

    # Form inputs
    col1, col2 = st.columns(2)
    with col1:
        states_input = st.text_input(
            "Set of States (Q) [comma-separated]:",
            value=st.session_state.get("input_states", "q0, q1, q2"),
            key="input_states",
            help="E.g., q0, q1, q2",
        )
        initial_input = st.text_input(
            "Initial State (q0):",
            value=st.session_state.get("input_initial", "q0"),
            key="input_initial",
            help="Must be one of the states declared in Q.",
        )
    
    with col2:
        alphabet_input = st.text_input(
            "Input Alphabet (Σ) [comma-separated]:",
            value=st.session_state.get("input_alphabet", "0, 1"),
            key="input_alphabet",
            help="E.g., 0, 1 or a, b",
        )
        finals_input = st.text_input(
            "Final / Accepting States (F) [comma-separated]:",
            value=st.session_state.get("input_finals", "q2"),
            key="input_finals",
            help="E.g., q2 or q1, q2",
        )

    # Parse inputs into lists
    raw_states = [s.strip() for s in states_input.split(",") if s.strip()]
    raw_alphabet = [a.strip() for a in alphabet_input.split(",") if a.strip()]
    raw_initial = initial_input.strip()
    raw_finals = [f.strip() for f in finals_input.split(",") if f.strip()]

    st.subheader("2. Transition Function (δ) Editor")
    st.write(
        "Edit the next states for each pair `(Current State, Input Symbol)`. "
        "Separate multiple target states with commas (e.g. `q0, q1`). "
        "Leave blank or enter `-` for no transition (empty set ∅)."
    )

    current_trans_map = st.session_state.get("nfa_trans_dict", {})
    trans_df = build_transition_table_df(raw_states, raw_alphabet, current_trans_map)

    edited_df = st.data_editor(
        trans_df,
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        column_config={
            "Current State": st.column_config.TextColumn(disabled=True),
            "Input Symbol": st.column_config.TextColumn(disabled=True),
            "Next States (comma-separated or empty)": st.column_config.TextColumn(
                help="Type states e.g. 'q0, q1' or leave empty for ∅",
            ),
        },
        key="trans_editor_table",
    )

    # Convert edited_df back to dictionary
    updated_trans: Dict[Tuple[str, str], Set[str]] = {}
    stored_dict: Dict[Tuple[str, str], str] = {}
    for _, row in edited_df.iterrows():
        st_val = str(row["Current State"]).strip()
        sym_val = str(row["Input Symbol"]).strip()
        raw_targets = str(row["Next States (comma-separated or empty)"]).strip()
        stored_dict[(st_val, sym_val)] = raw_targets
        
        if raw_targets and raw_targets != "-" and raw_targets != "∅":
            targets = {t.strip() for t in raw_targets.split(",") if t.strip()}
            updated_trans[(st_val, sym_val)] = targets
        else:
            updated_trans[(st_val, sym_val)] = set()

    st.session_state["nfa_trans_dict"] = stored_dict

    # Action buttons
    col_act1, col_act2, _ = st.columns([1.5, 1.5, 3])
    validate_clicked = col_act1.button("Validate NFA", use_container_width=True)
    convert_clicked = col_act2.button("Convert to DFA", type="primary", use_container_width=True)

    # Perform validation
    validation_res = NFAValidator.validate_raw(
        states=raw_states,
        alphabet=raw_alphabet,
        initial_state=raw_initial,
        final_states=raw_finals,
        transitions=updated_trans,
    )

    if validate_clicked or "validation_result" in st.session_state:
        st.session_state["validation_result"] = validation_res

    # Display validation feedback
    if st.session_state.get("validation_result"):
        val_res: ValidationResult = st.session_state["validation_result"]
        if val_res.is_valid:
            st.success("NFA definition is valid and meets theoretical constraints.")
            if val_res.has_warnings:
                for w in val_res.warnings:
                    st.warning(f"Notice: {w}")
        else:
            for err in val_res.errors:
                st.error(f"Validation Error: {err}")

    # Build and store NFA object
    if validation_res.is_valid:
        nfa_obj = NFA(
            states=raw_states,
            alphabet=raw_alphabet,
            initial_state=raw_initial,
            final_states=raw_finals,
            transitions=updated_trans,
        )
        st.session_state["current_nfa"] = nfa_obj

        if convert_clicked:
            st.session_state["trigger_conversion"] = True
        return nfa_obj

    return None
