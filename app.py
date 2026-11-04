"""
NFA TO DFA CONVERSION SIMULATOR
=====================================================
A clean, modular, and academic web application built for
Automata Theory / Theory of Computation courses.

Author: Antigravity Agent
Technology: Python 3, Streamlit, Graphviz, Matplotlib
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
# Page Configuration & CSS Injection
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="NFA to DFA Conversion Simulator",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

def load_css():
    """Inject custom academic stylesheet."""
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
    """Ensure session state contains the built-in demonstration example."""
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


# Check if conversion trigger was activated from input form
if st.session_state.get("trigger_conversion", False):
    st.session_state["trigger_conversion"] = False
    current_nfa: NFA = st.session_state.get("current_nfa")
    if current_nfa:
        engine = SubsetConstructionEngine(current_nfa)
        st.session_state["conversion_result"] = engine.convert()


# ---------------------------------------------------------------------------
# Sidebar Navigation
# ---------------------------------------------------------------------------
st.sidebar.title("Automata Simulator")
st.sidebar.caption("Theory of Computation & Automata Theory")

navigation_items = [
    "1. Introduction",
    "2. NFA Configuration",
    "3. NFA Visualization",
    "4. NFA to DFA Conversion",
    "5. Conversion Steps",
    "6. String Simulator",
]

# Set default navigation selection or read from session_state
if "nav_page" not in st.session_state:
    st.session_state["nav_page"] = "1. Introduction"

selected_page = st.sidebar.radio(
    "Navigation Menu",
    options=navigation_items,
    index=navigation_items.index(st.session_state["nav_page"]),
    key="nav_selection",
)
st.session_state["nav_page"] = selected_page

st.sidebar.markdown("---")
st.sidebar.subheader("Automaton Status")

current_nfa: NFA = st.session_state.get("current_nfa")
conv_result: ConversionResult = st.session_state.get("conversion_result")

if current_nfa:
    st.sidebar.text(f"NFA States (|Q|): {len(current_nfa.states)}")
    st.sidebar.text(f"Alphabet (Σ): {', '.join(current_nfa.sorted_alphabet)}")
    st.sidebar.text(f"Start State (q0): {current_nfa.initial_state}")
    st.sidebar.text(f"Final States (F): {', '.join(current_nfa.sorted_final_states) or '∅'}")
else:
    st.sidebar.info("No NFA configured.")

if conv_result:
    st.sidebar.markdown("---")
    st.sidebar.text(f"DFA States (|Q'|): {len(conv_result.dfa.states)}")
    st.sidebar.text(f"DFA Final States: {', '.join(conv_result.dfa.sorted_final_states) or '∅'}")
    st.sidebar.success("Conversion: Ready")
else:
    st.sidebar.warning("Conversion: Pending")


# ---------------------------------------------------------------------------
# PAGE 1: INTRODUCTION
# ---------------------------------------------------------------------------
if selected_page == "1. Introduction":
    st.title("NFA to DFA Conversion Simulator")
    st.markdown(
        "An educational platform designed for undergraduate **Automata Theory** and "
        "**Theory of Computation** courses to demonstrate the **Subset Construction Algorithm** "
        "(Rabin-Scott Powersets Construction) with complete algorithmic transparency."
    )

    col_btn1, col_btn2, _ = st.columns([1.5, 1.5, 3])
    with col_btn1:
        if st.button("Load Built-in Example (01)", type="primary", use_container_width=True):
            load_preset_into_state("Built-in: Strings ending in '01' (Default)")
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
            st.session_state["nav_page"] = "2. NFA Configuration"
            st.rerun()

    with col_btn2:
        if st.button("Go to Conversion Engine", use_container_width=True):
            st.session_state["nav_page"] = "4. NFA to DFA Conversion"
            st.rerun()

    st.markdown("---")

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("### What is an NFA?")
        st.markdown(
            """
            A **Non-deterministic Finite Automaton (NFA)** is defined by a 5-tuple:
            $$M = (Q, \\Sigma, \\delta, q_0, F)$$
            - **$Q$**: Finite non-empty set of states
            - **$\\Sigma$**: Finite input alphabet
            - **$\\delta$**: Transition function $\\delta: Q \\times \\Sigma \\to 2^Q$ (maps a state and symbol to a **set of next states**)
            - **$q_0$**: Initial / start state ($q_0 \\in Q$)
            - **$F$**: Set of final / accepting states ($F \\subseteq Q$)

            Because $\\delta(q, a)$ can yield zero, one, or multiple states, an NFA may branch across multiple computation paths simultaneously.
            """
        )

        st.markdown("### What is a DFA?")
        st.markdown(
            """
            A **Deterministic Finite Automaton (DFA)** is defined by:
            $$M' = (Q', \\Sigma, \\delta', q'_0, F')$$
            - **$\\delta'$**: Transition function $\\delta': Q' \\times \\Sigma \\to Q'$
            - For **every** state $S \\in Q'$ and symbol $a \\in \\Sigma$, there is **exactly one** unique destination state.
            - Guarantees deterministic, linear-time string evaluation: $O(|w|)$.
            """
        )

    with col_right:
        st.markdown("### Subset Construction Algorithm")
        st.markdown(
            """
            Every NFA has an equivalent DFA that recognizes the exact same formal language ($L(M) = L(M')$). 
            The **Subset Construction Algorithm** builds the DFA systematically:

            1. **Initial DFA State:**
               $$q'_0 = \\{q_0\\}$$
            2. **Transition Function:**
               For any reachable subset $S \\subseteq Q$ and symbol $a \\in \\Sigma$:
               $$\\delta'(S, a) = \\bigcup_{q \\in S} \\delta(q, a)$$
            3. **Accepting DFA States:**
               Any subset containing at least one original NFA final state:
               $$F' = \\{S \\in Q' \\mid S \\cap F \\neq \\emptyset\\}$$
            4. **Reachability:**
               Explored via **Breadth-First Search (BFS)** using `collections.deque` so only reachable subsets are generated.
            """
        )

    st.markdown("---")
    st.subheader("Key Application Features")
    
    fcol1, fcol2, fcol3 = st.columns(3)
    with fcol1:
        st.markdown(
            """
            **1. Formal Configuration & Validation**
            - Interactive matrix & list transition editor
            - Theoretical constraint validation
            - Automatic detection of undeclared symbols/states
            """
        )
    with fcol2:
        st.markdown(
            """
            **2. Step-by-Step Mathematical Trace**
            - Granular record of every BFS transition
            - Individual transition breakdowns $\\delta(q, a)$
            - Set unions and discovery markers
            """
        )
    with fcol3:
        st.markdown(
            """
            **3. Dual Automata String Simulation**
            - Simultaneous string execution on NFA & DFA
            - Path traversal and active state tracking
            - Mathematical proof of equivalence
            """
        )


# ---------------------------------------------------------------------------
# PAGE 2: NFA CONFIGURATION
# ---------------------------------------------------------------------------
elif selected_page == "2. NFA Configuration":
    st.title("NFA Input & Configuration")
    st.write(
        "Define your Non-deterministic Finite Automaton using the formal 5-tuple input fields below. "
        "Transitions can be edited in the interactive table."
    )

    configured_nfa = render_nfa_input_controls()

    if configured_nfa:
        st.markdown("---")
        st.subheader("Current Validated NFA Summary")
        mcol1, mcol2, mcol3, mcol4 = st.columns(4)
        mcol1.metric("Total States (|Q|)", len(configured_nfa.states))
        mcol2.metric("Alphabet Size (|Σ|)", len(configured_nfa.alphabet))
        mcol3.metric("Initial State", configured_nfa.initial_state)
        mcol4.metric("Accepting States (|F|)", len(configured_nfa.final_states))

        col_nav1, col_nav2 = st.columns([1, 1])
        with col_nav1:
            if st.button("View NFA Graph →", use_container_width=True):
                st.session_state["nav_page"] = "3. NFA Visualization"
                st.rerun()
        with col_nav2:
            if st.button("Convert to DFA & View Trace →", type="primary", use_container_width=True):
                st.session_state["conversion_result"] = SubsetConstructionEngine(configured_nfa).convert()
                st.session_state["nav_page"] = "4. NFA to DFA Conversion"
                st.rerun()


# ---------------------------------------------------------------------------
# PAGE 3: NFA VISUALIZATION
# ---------------------------------------------------------------------------
elif selected_page == "3. NFA Visualization":
    st.title("NFA Visualization")
    
    if not current_nfa:
        st.warning("Please configure an NFA first in the 'NFA Configuration' section.")
    else:
        st.write(
            "Graphviz diagram representing the original NFA. "
            "Double circles represent accepting states, while incoming arrows mark the initial state."
        )

        col_graph, col_meta = st.columns([3, 2])

        with col_graph:
            st.subheader("Automaton State Graph")
            dot_code = generate_nfa_dot(current_nfa)
            st.graphviz_chart(dot_code, use_container_width=True)

        with col_meta:
            st.subheader("Transition Matrix Table")
            render_nfa_table(current_nfa)

            st.markdown("##### Formal Specification")
            st.markdown(
                f"- **States $Q$:** `{', '.join(current_nfa.sorted_states)}`\n"
                f"- **Alphabet $\\Sigma$:** `{', '.join(current_nfa.sorted_alphabet)}`\n"
                f"- **Initial State $q_0$:** `{current_nfa.initial_state}`\n"
                f"- **Final States $F$:** `{', '.join(current_nfa.sorted_final_states) or '∅'}`"
            )


# ---------------------------------------------------------------------------
# PAGE 4: NFA TO DFA CONVERSION
# ---------------------------------------------------------------------------
elif selected_page == "4. NFA to DFA Conversion":
    st.title("Converted DFA (Deterministic Finite Automaton)")

    if not current_nfa:
        st.warning("No NFA configured. Please configure an NFA first.")
    else:
        if not conv_result:
            conv_result = SubsetConstructionEngine(current_nfa).convert()
            st.session_state["conversion_result"] = conv_result

        dfa = conv_result.dfa

        # Metric Tiles
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("NFA States (|Q|)", conv_result.nfa_state_count)
        c2.metric("Reachable DFA States (|Q'|)", conv_result.dfa_state_count)
        powerset_max = 2 ** conv_result.nfa_state_count
        c3.metric("Powerset Max (2^|Q|)", powerset_max)
        c4.metric("DFA Final States (|F'|)", len(dfa.final_states))

        st.markdown("---")

        col_dfa_graph, col_dfa_table = st.columns([3, 2])

        with col_dfa_graph:
            st.subheader("DFA State Transition Diagram")
            st.caption("Each node displays the DFA state label along with its underlying constituent NFA subset.")
            dfa_dot = generate_dfa_dot(dfa)
            st.graphviz_chart(dfa_dot, use_container_width=True)

        with col_dfa_table:
            st.subheader("DFA State Mapping & Subsets")
            mapping_data = []
            for label, subset, is_acc in conv_result.reachable_subsets:
                mapping_data.append({
                    "DFA State": label,
                    "NFA Subset": format_subset(subset),
                    "Type": "Accepting (*)" if is_acc else "Normal",
                })
            st.dataframe(mapping_data, use_container_width=True, hide_index=True)

            st.subheader("Complexity Comparison")
            fig = generate_state_distribution_chart(conv_result.nfa_state_count, conv_result.dfa_state_count)
            st.pyplot(fig, use_container_width=True)

        st.markdown("---")
        st.subheader("DFA Complete Transition Table")
        render_dfa_table(dfa)


# ---------------------------------------------------------------------------
# PAGE 5: CONVERSION STEPS
# ---------------------------------------------------------------------------
elif selected_page == "5. Conversion Steps":
    st.title("Step-by-Step Conversion Derivation")

    if not conv_result:
        if current_nfa:
            conv_result = SubsetConstructionEngine(current_nfa).convert()
            st.session_state["conversion_result"] = conv_result
        else:
            st.warning("Please configure an NFA first.")

    if conv_result:
        render_conversion_steps(conv_result)


# ---------------------------------------------------------------------------
# PAGE 6: STRING SIMULATOR
# ---------------------------------------------------------------------------
elif selected_page == "6. String Simulator":
    st.title("Input String Simulator & Equivalence Verifier")
    st.write(
        "Simulate string acceptance synchronously on both the **original NFA** and the **converted DFA**. "
        "Verify that both automata yield identical formal decisions and state set evaluations."
    )

    if not current_nfa or not conv_result:
        st.warning("Please configure an NFA and execute conversion first.")
    else:
        dfa = conv_result.dfa
        alphabet_str = ", ".join(current_nfa.sorted_alphabet)
        st.caption(f"Valid Input Alphabet Σ: {{{alphabet_str}}}. Empty string 'ε' is represented by leaving input blank.")

        # Quick test buttons
        st.write("##### Quick Test Examples:")
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
            "Enter string to test:",
            value=st.session_state.get("sim_input_val", "01"),
            key="sim_input_text",
            help="Symbols must belong to the declared alphabet.",
        )

        is_valid_str, err_msg = AutomataSimulator.validate_string(current_nfa.alphabet, sim_str)

        if not is_valid_str:
            st.error(f"Validation Error: {err_msg}")
        else:
            cmp_res = AutomataSimulator.compare(current_nfa, dfa, sim_str)

            # High-visibility Result Banner
            if cmp_res.verdict == "ACCEPTED":
                st.markdown(
                    f'<div class="accepted-banner">RESULT: ACCEPTED &nbsp; | &nbsp; '
                    f'Both NFA and DFA accepted the string \'{sim_str or "ε"}\'.</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div class="rejected-banner">RESULT: REJECTED &nbsp; | &nbsp; '
                    f'Both NFA and DFA rejected the string \'{sim_str or "ε"}\'.</div>',
                    unsafe_allow_html=True,
                )

            st.info(cmp_res.explanation)

            st.markdown("---")
            st.subheader("Execution Path Comparison")

            col_dfa_trace, col_nfa_trace = st.columns(2)

            with col_dfa_trace:
                st.markdown("#### Deterministic DFA Path")
                dfa_trace_rows = []
                for s in cmp_res.dfa_result.steps:
                    dfa_trace_rows.append({
                        "Step": s.step_number,
                        "Symbol": s.symbol if s.symbol is not None else "(start)",
                        "Current State": s.from_state,
                        "Next State": s.to_state,
                        "Underlying Subset": format_subset(s.to_subset),
                        "Accepting": "Yes (*)" if s.is_accepting else "No",
                    })
                st.dataframe(dfa_trace_rows, use_container_width=True, hide_index=True)
                st.caption(f"Halted in state: {list(cmp_res.dfa_result.final_states_reached)[0]}")

            with col_nfa_trace:
                st.markdown("#### Non-deterministic NFA Active State Set")
                nfa_trace_rows = []
                for s in cmp_res.nfa_result.steps:
                    nfa_trace_rows.append({
                        "Step": s.step_number,
                        "Symbol": s.symbol if s.symbol is not None else "(start)",
                        "Active States": format_subset(frozenset(s.active_states)),
                        "Next Active States": format_subset(frozenset(s.next_states)),
                        "Accepting": "Yes (*)" if s.is_accepting else "No",
                    })
                st.dataframe(nfa_trace_rows, use_container_width=True, hide_index=True)
                st.caption(f"Active state set at termination: {format_subset(frozenset(cmp_res.nfa_result.final_states_reached))}")
