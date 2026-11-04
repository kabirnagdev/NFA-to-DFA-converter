"""
NFA Input Form Component.

Provides a clean, human-friendly interface for:
- State definitions (Q)
- Alphabet definition (Sigma)
- Start state (q0)
- Accepting states (F)
- Tabular interactive transition editor
- Preset selection, validation, and reset actions
"""

import streamlit as st
import pandas as pd
from typing import Dict, Tuple, Set, Optional

from core.nfa import NFA
from core.conversion import SubsetConstructionEngine
from core.validation import NFAValidator, ValidationResult


# Educational presets
PRESETS = {
    "Demo: Strings ending in '01'": {
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
    "Strings containing '010'": {
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
    "Second symbol is 'a'": {
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
    """Load selected preset into session state and immediately initialize NFA & DFA."""
    preset = PRESETS[preset_name]
    st.session_state["input_states"] = preset["states"]
    st.session_state["input_alphabet"] = preset["alphabet"]
    st.session_state["input_initial"] = preset["initial"]
    st.session_state["input_finals"] = preset["finals"]
    st.session_state["nfa_trans_dict"] = dict(preset["transitions"])
    st.session_state.pop("trans_editor_table", None)
    st.session_state["validation_result"] = None

    raw_states = [s.strip() for s in preset["states"].split(",") if s.strip()]
    raw_alphabet = [a.strip() for a in preset["alphabet"].split(",") if a.strip()]
    raw_initial = preset["initial"].strip()
    raw_finals = [f.strip() for f in preset["finals"].split(",") if f.strip()]
    trans_map = {}
    for (s, a), targets_str in preset["transitions"].items():
        if targets_str:
            trans_map[(s, a)] = {t.strip() for t in targets_str.split(",") if t.strip()}

    nfa_obj = NFA(raw_states, raw_alphabet, raw_initial, raw_finals, trans_map)
    st.session_state["current_nfa"] = nfa_obj
    st.session_state["conversion_result"] = SubsetConstructionEngine(nfa_obj).convert()


def reset_to_empty():
    """Reset configuration to blank defaults."""
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
    st.session_state.pop("trans_editor_table", None)
    st.session_state["validation_result"] = None
    st.session_state["conversion_result"] = None
    st.session_state["current_nfa"] = None


def build_transition_table_df(states: list[str], alphabet: list[str], trans_map: dict) -> pd.DataFrame:
    """Build a clean dataframe: Current State, Symbol, Next States."""
    rows = []
    for s in states:
        for a in alphabet:
            val = trans_map.get((s, a), "")
            rows.append({
                "Current State": s,
                "Symbol": a,
                "Next States": val,
            })
    return pd.DataFrame(rows)


def render_nfa_input_controls() -> Optional[NFA]:
    """Renders the NFA input UI and returns the validated NFA."""
    if "input_states" not in st.session_state:
        load_preset_into_state("Demo: Strings ending in '01'")

    # Preset selection
    preset_col, btn_load, btn_reset = st.columns([3, 1, 1])
    with preset_col:
        selected_preset = st.selectbox(
            "Load Example Preset",
            options=list(PRESETS.keys()),
            key="preset_dropdown",
        )
    with btn_load:
        st.write("")
        st.write("")
        if st.button("Load Preset", key="btn_load_preset", use_container_width=True):
            load_preset_into_state(selected_preset)
            st.rerun()
    with btn_reset:
        st.write("")
        st.write("")
        if st.button("Reset", key="btn_reset_all", use_container_width=True):
            reset_to_empty()
            st.rerun()

    # Form inputs
    st.markdown("### Automaton Setup")
    col1, col2 = st.columns(2)
    with col1:
        states_input = st.text_input(
            "States (Q):",
            value=st.session_state.get("input_states", "q0, q1, q2"),
            key="input_states",
            placeholder="q0, q1, q2",
        )
        initial_input = st.text_input(
            "Start State (q0):",
            value=st.session_state.get("input_initial", "q0"),
            key="input_initial",
            placeholder="q0",
        )
    
    with col2:
        alphabet_input = st.text_input(
            "Alphabet (Σ):",
            value=st.session_state.get("input_alphabet", "0, 1"),
            key="input_alphabet",
            placeholder="0, 1",
        )
        finals_input = st.text_input(
            "Accepting States (F):",
            value=st.session_state.get("input_finals", "q2"),
            key="input_finals",
            placeholder="q2",
        )

    raw_states = [s.strip() for s in states_input.split(",") if s.strip()]
    raw_alphabet = [a.strip() for a in alphabet_input.split(",") if a.strip()]
    raw_initial = initial_input.strip()
    raw_finals = [f.strip() for f in finals_input.split(",") if f.strip()]

    st.markdown("### Transition Table (δ)")
    st.caption("Specify next states for each pair. Separate multiple states with commas (e.g. `q0, q1`). Leave blank for no transition.")

    current_trans_map = st.session_state.get("nfa_trans_dict", {})
    trans_df = build_transition_table_df(raw_states, raw_alphabet, current_trans_map)

    edited_df = st.data_editor(
        trans_df,
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        column_config={
            "Current State": st.column_config.TextColumn(disabled=True),
            "Symbol": st.column_config.TextColumn(disabled=True),
            "Next States": st.column_config.TextColumn(
                help="Type target states like 'q0, q1' or leave blank",
            ),
        },
        key="trans_editor_table",
    )

    updated_trans: Dict[Tuple[str, str], Set[str]] = {}
    stored_dict: Dict[Tuple[str, str], str] = {}
    for _, row in edited_df.iterrows():
        st_val = str(row["Current State"]).strip()
        sym_val = str(row["Symbol"]).strip()
        raw_targets = str(row["Next States"]).strip()
        stored_dict[(st_val, sym_val)] = raw_targets
        
        if raw_targets and raw_targets != "-" and raw_targets != "∅" and raw_targets != "None":
            targets = {t.strip() for t in raw_targets.split(",") if t.strip()}
            updated_trans[(st_val, sym_val)] = targets
        else:
            updated_trans[(st_val, sym_val)] = set()

    st.session_state["nfa_trans_dict"] = stored_dict

    col_act1, col_act2, _ = st.columns([1.2, 1.8, 3])
    validate_clicked = col_act1.button("Validate", key="btn_validate_nfa", use_container_width=True)
    convert_clicked = col_act2.button("Convert to DFA", key="btn_convert_dfa", type="primary", use_container_width=True)

    validation_res = NFAValidator.validate_raw(
        states=raw_states,
        alphabet=raw_alphabet,
        initial_state=raw_initial,
        final_states=raw_finals,
        transitions=updated_trans,
    )

    if validate_clicked or "validation_result" in st.session_state:
        st.session_state["validation_result"] = validation_res

    if st.session_state.get("validation_result"):
        val_res: ValidationResult = st.session_state["validation_result"]
        if val_res.is_valid:
            st.success("NFA is valid and ready for conversion.")
            if val_res.has_warnings:
                for w in val_res.warnings:
                    st.warning(f"Note: {w}")
        else:
            for err in val_res.errors:
                st.error(f"Error: {err}")

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
            engine = SubsetConstructionEngine(nfa_obj)
            st.session_state["conversion_result"] = engine.convert()
            st.session_state["nav_selection"] = "4. DFA Result"
            st.rerun()

        return nfa_obj

    return None
