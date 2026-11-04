"""
NFA TO DFA CONVERSION SIMULATOR
=====================================================
Interactive Automata Theory Tool.
Python 3 | Streamlit | Graphviz | Matplotlib
"""

import os
import streamlit as st
import matplotlib.pyplot as plt

from core.nfa import NFA
from core.dfa import DFA
from core.conversion import SubsetConstructionEngine, ConversionResult, format_subset
from core.validation import NFAValidator, ValidationResult
from core.simulator import AutomataSimulator
from visualization.automata_graph import (
    generate_nfa_dot,
    generate_dfa_dot,
    generate_state_distribution_chart,
)
from components.transition_table import render_nfa_table, render_dfa_table
from components.conversion_trace import render_conversion_steps
from components.input_form import render_nfa_input_controls, load_preset_into_state


# ---------------------------------------------------------------------------
# Page Configuration & CSS
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="NFA to DFA Converter",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

def load_css():
    """Inject custom stylesheet."""
    css_path = os.path.join(os.path.dirname(__file__), "assets", "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            css_content = f.read()
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)

load_css()


# ---------------------------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------------------------
def init_default_automata():
    """Load default demonstration NFA."""
    if "current_nfa" not in st.session_state or st.session_state["current_nfa"] is None:
        builtin_nfa = NFA(
            states=["q0", "q1", "q2"],
            alphabet=["0", "1"],
            initial_state="q0",
            final_states=["q2"],
            transitions={
                ("q0", "0"): {"q0", "q1"},
                ("q0", "1"): {"q0"},
                ("q1", "1"): {"q2"},
            },
        )
        st.session_state["current_nfa"] = builtin_nfa
        engine = SubsetConstructionEngine(builtin_nfa)
        st.session_state["conversion_result"] = engine.convert()

init_default_automata()

if st.session_state.get("trigger_conversion", False):
    st.session_state["trigger_conversion"] = False
    current_nfa: NFA = st.session_state.get("current_nfa")
    if current_nfa:
        st.session_state["conversion_result"] = SubsetConstructionEngine(current_nfa).convert()


# ---------------------------------------------------------------------------
# Sidebar Navigation
# ---------------------------------------------------------------------------
st.sidebar.title("NFA → DFA Converter")

navigation_items = [
    "1. Overview",
    "2. NFA Setup",
    "3. NFA Graph",
    "4. DFA Result",
    "5. Step-by-Step Trace",
    "6. String Tester",
]

if "nav_page" not in st.session_state:
    st.session_state["nav_page"] = "1. Overview"

# Ensure stored nav_page is valid
if st.session_state["nav_page"] not in navigation_items:
    st.session_state["nav_page"] = "1. Overview"

selected_page = st.sidebar.radio(
    "Navigation",
    options=navigation_items,
    index=navigation_items.index(st.session_state["nav_page"]),
    key="nav_selection",
)
st.session_state["nav_page"] = selected_page

st.sidebar.markdown("---")

current_nfa: NFA = st.session_state.get("current_nfa")
conv_result: ConversionResult = st.session_state.get("conversion_result")

if current_nfa:
    st.sidebar.markdown(f"**NFA:** `{len(current_nfa.states)}` states &nbsp;|&nbsp; Σ = `{{{', '.join(current_nfa.sorted_alphabet)}}}`")
    st.sidebar.markdown(f"**Start:** `{current_nfa.initial_state}` &nbsp;|&nbsp; **Final:** `{', '.join(current_nfa.sorted_final_states) or '∅'}`")

if conv_result:
    st.sidebar.markdown(f"**DFA:** `{len(conv_result.dfa.states)}` reachable states")


# ---------------------------------------------------------------------------
# PAGE 1: OVERVIEW
# ---------------------------------------------------------------------------
if selected_page == "1. Overview":
    st.title("NFA to DFA Converter")
    st.markdown(
        "Convert Non-deterministic Finite Automata into equivalent Deterministic Finite Automata "
        "using the **Subset Construction Algorithm**."
    )

    col1, col2, _ = st.columns([1.5, 1.5, 3])
    with col1:
        if st.button("Load Demo: Ends with '01'", type="primary", use_container_width=True):
            load_preset_into_state("Demo: Strings ending in '01'")
            builtin_nfa = NFA(
                states=["q0", "q1", "q2"],
                alphabet=["0", "1"],
                initial_state="q0",
                final_states=["q2"],
                transitions={
                    ("q0", "0"): {"q0", "q1"},
                    ("q0", "1"): {"q0"},
                    ("q1", "1"): {"q2"},
                },
            )
            st.session_state["current_nfa"] = builtin_nfa
            st.session_state["conversion_result"] = SubsetConstructionEngine(builtin_nfa).convert()
            st.session_state["nav_page"] = "2. NFA Setup"
            st.rerun()

    with col2:
        if st.button("Open Custom Setup →", use_container_width=True):
            st.session_state["nav_page"] = "2. NFA Setup"
            st.rerun()

    st.markdown("---")

    # Clean 3-step cards
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("### 1. Build NFA")
        st.write("Specify your states, alphabet, initial state, and transition table — or load a ready-made preset.")
    with c2:
        st.markdown("### 2. Subset Construction")
        st.write("BFS explores reachable state combinations (subsets) and groups them into unique DFA states.")
    with c3:
        st.markdown("### 3. Test Strings")
        st.write("Simulate inputs across both automata to verify identical acceptance behavior.")

    st.markdown("---")
    st.markdown("### Quick Concept Reference")
    q1, q2 = st.columns(2)
    with q1:
        st.markdown("**NFA (Non-deterministic)**")
        st.write("A state can have multiple transitions or no transitions on the same symbol. Can branch across multiple paths.")
    with q2:
        st.markdown("**DFA (Deterministic)**")
        st.write("Every state has exactly one transition for each alphabet symbol. Execution is deterministic and runs in $O(|w|)$ time.")


# ---------------------------------------------------------------------------
# PAGE 2: NFA SETUP
# ---------------------------------------------------------------------------
elif selected_page == "2. NFA Setup":
    st.title("NFA Configuration")
    configured_nfa = render_nfa_input_controls()

    if configured_nfa:
        st.markdown("---")
        mcol1, mcol2, mcol3, mcol4 = st.columns(4)
        mcol1.metric("States (|Q|)", len(configured_nfa.states))
        mcol2.metric("Alphabet (|Σ|)", len(configured_nfa.alphabet))
        mcol3.metric("Start State", configured_nfa.initial_state)
        mcol4.metric("Accept States", len(configured_nfa.final_states))

        b1, b2, _ = st.columns([1.5, 1.5, 3])
        with b1:
            if st.button("View NFA Graph →", use_container_width=True):
                st.session_state["nav_page"] = "3. NFA Graph"
                st.rerun()
        with b2:
            if st.button("View DFA Result →", type="primary", use_container_width=True):
                st.session_state["conversion_result"] = SubsetConstructionEngine(configured_nfa).convert()
                st.session_state["nav_page"] = "4. DFA Result"
                st.rerun()


# ---------------------------------------------------------------------------
# PAGE 3: NFA GRAPH
# ---------------------------------------------------------------------------
elif selected_page == "3. NFA Graph":
    st.title("NFA Diagram")
    
    if not current_nfa:
        st.warning("Please configure an NFA in 'NFA Setup' first.")
    else:
        col_graph, col_meta = st.columns([3, 2])

        with col_graph:
            dot_code = generate_nfa_dot(current_nfa)
            st.graphviz_chart(dot_code, use_container_width=True)

        with col_meta:
            st.markdown("#### Transition Table")
            render_nfa_table(current_nfa)
            st.caption(f"Q = {{{', '.join(current_nfa.sorted_states)}}}, Σ = {{{', '.join(current_nfa.sorted_alphabet)}}}, start = {current_nfa.initial_state}, F = {{{', '.join(current_nfa.sorted_final_states)}}}")


# ---------------------------------------------------------------------------
# PAGE 4: DFA RESULT
# ---------------------------------------------------------------------------
elif selected_page == "4. DFA Result":
    st.title("Converted DFA")

    if not current_nfa:
        st.warning("No NFA configured. Please setup an NFA first.")
    else:
        if not conv_result:
            conv_result = SubsetConstructionEngine(current_nfa).convert()
            st.session_state["conversion_result"] = conv_result

        dfa = conv_result.dfa

        # Metrics
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("NFA States", conv_result.nfa_state_count)
        c2.metric("Reachable DFA States", conv_result.dfa_state_count)
        c3.metric("Powerset Max (2^|Q|)", 2 ** conv_result.nfa_state_count)
        c4.metric("DFA Accept States", len(dfa.final_states))

        st.markdown("---")

        col_dfa_graph, col_dfa_table = st.columns([3, 2])

        with col_dfa_graph:
            st.subheader("DFA State Diagram")
            dfa_dot = generate_dfa_dot(dfa)
            st.graphviz_chart(dfa_dot, use_container_width=True)

        with col_dfa_table:
            st.subheader("State Mapping")
            mapping_data = []
            for label, subset, is_acc in conv_result.reachable_subsets:
                mapping_data.append({
                    "DFA State": label,
                    "NFA Subset": format_subset(subset),
                    "Type": "Accepting (*)" if is_acc else "Normal",
                })
            st.dataframe(mapping_data, use_container_width=True, hide_index=True)

            st.subheader("State Count Comparison")
            fig = generate_state_distribution_chart(conv_result.nfa_state_count, conv_result.dfa_state_count)
            st.pyplot(fig, use_container_width=True)

        st.markdown("---")
        st.subheader("DFA Transition Table")
        render_dfa_table(dfa)


# ---------------------------------------------------------------------------
# PAGE 5: STEP-BY-STEP TRACE
# ---------------------------------------------------------------------------
elif selected_page == "5. Step-by-Step Trace":
    st.title("Conversion Steps")

    if not conv_result:
        if current_nfa:
            conv_result = SubsetConstructionEngine(current_nfa).convert()
            st.session_state["conversion_result"] = conv_result
        else:
            st.warning("Please configure an NFA first.")

    if conv_result:
        render_conversion_steps(conv_result)


# ---------------------------------------------------------------------------
# PAGE 6: STRING TESTER
# ---------------------------------------------------------------------------
elif selected_page == "6. String Tester":
    st.title("String Tester")
    st.write("Test any input string synchronously on both the original NFA and converted DFA.")

    if not current_nfa or not conv_result:
        st.warning("Please configure an NFA and run conversion first.")
    else:
        dfa = conv_result.dfa
        alphabet_str = ", ".join(current_nfa.sorted_alphabet)
        st.caption(f"Valid alphabet Σ: {{{alphabet_str}}}. Leave empty for the empty string (ε).")

        # Quick test buttons
        st.write("**Quick Test Presets:**")
        qb_cols = st.columns(7)
        quick_strings = ["01", "101", "001", "10", "111", "010", ""]
        button_labels = ["01", "101", "001", "10", "111", "010", "ε (Empty)"]

        selected_quick = None
        for i, (q_str, q_lbl) in enumerate(zip(quick_strings, button_labels)):
            if qb_cols[i].button(q_lbl, use_container_width=True):
                selected_quick = q_str

        if selected_quick is not None:
            st.session_state["sim_input_val"] = selected_quick

        sim_str = st.text_input(
            "Input String:",
            value=st.session_state.get("sim_input_val", "01"),
            key="sim_input_text",
            placeholder="e.g. 0101",
        )

        is_valid_str, err_msg = AutomataSimulator.validate_string(current_nfa.alphabet, sim_str)

        if not is_valid_str:
            st.error(f"Invalid string: {err_msg}")
        else:
            cmp_res = AutomataSimulator.compare(current_nfa, dfa, sim_str)

            # Clean result pill
            if cmp_res.verdict == "ACCEPTED":
                st.markdown(
                    f'<div class="accepted-banner">RESULT: ACCEPTED &nbsp;•&nbsp; '
                    f'Both NFA and DFA accepted \'{sim_str or "ε"}\'.</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div class="rejected-banner">RESULT: REJECTED &nbsp;•&nbsp; '
                    f'Both NFA and DFA rejected \'{sim_str or "ε"}\'.</div>',
                    unsafe_allow_html=True,
                )

            st.caption(cmp_res.explanation)

            st.markdown("---")
            st.subheader("Execution Trace")

            col_dfa_trace, col_nfa_trace = st.columns(2)

            with col_dfa_trace:
                st.markdown("#### DFA Traversal")
                dfa_trace_rows = []
                for s in cmp_res.dfa_result.steps:
                    dfa_trace_rows.append({
                        "Step": s.step_number,
                        "Symbol": s.symbol if s.symbol is not None else "(start)",
                        "Current": s.from_state,
                        "Next": s.to_state,
                        "Subset": format_subset(s.to_subset),
                        "Accepting?": "Yes (*)" if s.is_accepting else "No",
                    })
                st.dataframe(dfa_trace_rows, use_container_width=True, hide_index=True)
                st.caption(f"Halted in state: {list(cmp_res.dfa_result.final_states_reached)[0]}")

            with col_nfa_trace:
                st.markdown("#### NFA Active States")
                nfa_trace_rows = []
                for s in cmp_res.nfa_result.steps:
                    nfa_trace_rows.append({
                        "Step": s.step_number,
                        "Symbol": s.symbol if s.symbol is not None else "(start)",
                        "Active States": format_subset(frozenset(s.active_states)),
                        "Next Active": format_subset(frozenset(s.next_states)),
                        "Accepting?": "Yes (*)" if s.is_accepting else "No",
                    })
                st.dataframe(nfa_trace_rows, use_container_width=True, hide_index=True)
                st.caption(f"Final active set: {format_subset(frozenset(cmp_res.nfa_result.final_states_reached))}")
