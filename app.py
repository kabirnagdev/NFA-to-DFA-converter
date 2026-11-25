"""
NFA TO DFA CONVERSION SIMULATOR (Milestone 2)
=====================================================
Interactive Automata Theory Educational Simulator.
Python 3 | Streamlit | Graphviz | Matplotlib
"""

import os
import time
import streamlit as st

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
from components.conversion_trace import render_live_simulator
from components.input_form import (
    render_nfa_input_controls,
    load_preset_into_state,
    reset_simulator_playback,
)


# ---------------------------------------------------------------------------
# Page Configuration & CSS
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="NFA to DFA Simulator",
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
# Navigation Helper
# ---------------------------------------------------------------------------
NAVIGATION_ITEMS = [
    "1. Overview",
    "2. NFA Setup",
    "3. NFA Graph",
    "4. DFA Result",
    "5. Live Simulator",
    "6. String Tester",
    "7. How the Algorithm Works",
]


def navigate_to(page_name: str):
    """Safely change pages via nav_target before widget instantiation."""
    st.session_state["nav_target"] = page_name
    st.rerun()


# ---------------------------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------------------------
def init_default_automata():
    """Ensure default demonstration NFA and DFA are available."""
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


# ---------------------------------------------------------------------------
# Sidebar Navigation
# ---------------------------------------------------------------------------
st.sidebar.title("NFA → DFA Simulator")

if "nav_target" in st.session_state:
    st.session_state["nav_selection"] = st.session_state.pop("nav_target")

if "nav_selection" not in st.session_state or st.session_state["nav_selection"] not in NAVIGATION_ITEMS:
    st.session_state["nav_selection"] = "1. Overview"

selected_page = st.sidebar.radio(
    "Navigation Menu",
    options=NAVIGATION_ITEMS,
    key="nav_selection",
)

st.sidebar.markdown("---")

current_nfa: NFA = st.session_state.get("current_nfa")
conv_result: ConversionResult = st.session_state.get("conversion_result")

if current_nfa:
    eps_tag = " (ε-NFA)" if current_nfa.has_epsilon_transitions else ""
    st.sidebar.markdown(
        f"**NFA{eps_tag}:** `{len(current_nfa.states)}` states &nbsp;|&nbsp; "
        f"Σ = `{{{', '.join(current_nfa.sorted_alphabet)}}}`"
    )
    st.sidebar.markdown(
        f"**Start:** `{current_nfa.initial_state}` &nbsp;|&nbsp; "
        f"**Final:** `{', '.join(current_nfa.sorted_final_states) or '∅'}`"
    )

if conv_result:
    st.sidebar.markdown(f"**DFA:** `{len(conv_result.dfa.states)}` reachable states")


# ---------------------------------------------------------------------------
# PAGE 1: OVERVIEW
# ---------------------------------------------------------------------------
if selected_page == "1. Overview":
    st.title("NFA to DFA Interactive Simulator")
    st.markdown(
        "Convert Non-deterministic Finite Automata (including ε-NFAs) into equivalent "
        "Deterministic Finite Automata using the **Rabin–Scott Subset Construction Algorithm**."
    )

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("Launch Live Simulator ▶", key="btn_home_live", type="primary", use_container_width=True):
            reset_simulator_playback()
            navigate_to("5. Live Simulator")
    with col2:
        if st.button("Demo: Ends with '01'", key="btn_load_demo", use_container_width=True):
            load_preset_into_state("Demo: Strings ending in '01'")
            navigate_to("5. Live Simulator")
    with col3:
        if st.button("Demo: ε-NFA (a*b*)", key="btn_load_eps_demo", use_container_width=True):
            load_preset_into_state("ε-NFA: a* followed by b*")
            navigate_to("5. Live Simulator")
    with col4:
        if st.button("Test Input Strings →", key="btn_home_test", use_container_width=True):
            navigate_to("6. String Tester")

    st.markdown("---")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("### 1. Build NFA / ε-NFA")
        st.write(
            "Specify states, alphabet, optional ε-transitions, start/accepting states, "
            "and transition table — or load an educational preset."
        )
    with c2:
        st.markdown("### 2. Watch Live BFS")
        st.write(
            "Step through Subset Construction with Play/Pause/Prev/Next controls, "
            "live BFS queue tracking, mathematical derivations, and updating graphs/tables."
        )
    with c3:
        st.markdown("### 3. Verify Equivalence")
        st.write(
            "Animate input strings simultaneously on both the NFA and converted DFA "
            "to verify identical language acceptance."
        )

    st.markdown("---")
    st.markdown("### Quick Concept Reference")
    q1, q2 = st.columns(2)
    with q1:
        st.markdown("**NFA (Non-deterministic)**")
        st.write(
            "A state can have multiple transitions, no transitions, or ε-transitions. "
            "Execution branches across a set of active states simultaneously."
        )
    with q2:
        st.markdown("**DFA (Deterministic)**")
        st.write(
            "Every state has exactly one transition for each alphabet symbol. "
            "Execution follows a single deterministic path in $O(|w|)$ time."
        )


# ---------------------------------------------------------------------------
# PAGE 2: NFA SETUP
# ---------------------------------------------------------------------------
elif selected_page == "2. NFA Setup":
    st.title("NFA Configuration")
    configured_nfa = render_nfa_input_controls()

    active_nfa = configured_nfa or current_nfa

    if active_nfa:
        st.markdown("---")
        mcol1, mcol2, mcol3, mcol4 = st.columns(4)
        mcol1.metric("States (|Q|)", len(active_nfa.states))
        mcol2.metric("Alphabet (|Σ|)", len(active_nfa.alphabet))
        mcol3.metric("Start State", active_nfa.initial_state)
        mcol4.metric("Accept States", len(active_nfa.final_states))

        b1, b2, b3 = st.columns([1.5, 1.5, 1.5])
        with b1:
            if st.button("View NFA Graph →", key="btn_view_nfa_graph", use_container_width=True):
                navigate_to("3. NFA Graph")
        with b2:
            if st.button("Launch Live Simulator ▶", key="btn_setup_live", type="primary", use_container_width=True):
                st.session_state["conversion_result"] = SubsetConstructionEngine(active_nfa).convert()
                reset_simulator_playback()
                navigate_to("5. Live Simulator")
        with b3:
            if st.button("View Final DFA →", key="btn_view_dfa_result", use_container_width=True):
                st.session_state["conversion_result"] = SubsetConstructionEngine(active_nfa).convert()
                navigate_to("4. DFA Result")


# ---------------------------------------------------------------------------
# PAGE 3: NFA GRAPH
# ---------------------------------------------------------------------------
elif selected_page == "3. NFA Graph":
    st.title("NFA Diagram")

    if not current_nfa:
        st.warning("Please configure an NFA in 'NFA Setup' first.")
    else:
        nav_col1, nav_col2, nav_col3 = st.columns([1.5, 1.5, 1.5])
        with nav_col1:
            if st.button("← Back to Setup", key="btn_nfa_back_setup", use_container_width=True):
                navigate_to("2. NFA Setup")
        with nav_col2:
            if st.button("Launch Live Simulator ▶", key="btn_nfa_to_live", type="primary", use_container_width=True):
                st.session_state["conversion_result"] = SubsetConstructionEngine(current_nfa).convert()
                reset_simulator_playback()
                navigate_to("5. Live Simulator")
        with nav_col3:
            if st.button("View Final DFA →", key="btn_nfa_to_dfa", use_container_width=True):
                st.session_state["conversion_result"] = SubsetConstructionEngine(current_nfa).convert()
                navigate_to("4. DFA Result")

        st.markdown("---")
        col_graph, col_meta = st.columns([3, 2])

        with col_graph:
            dot_code = generate_nfa_dot(current_nfa)
            st.graphviz_chart(dot_code, use_container_width=True)

        with col_meta:
            st.markdown("#### Transition Table")
            render_nfa_table(current_nfa)
            st.caption(
                f"Q = {{{', '.join(current_nfa.sorted_states)}}}, "
                f"Σ = {{{', '.join(current_nfa.sorted_alphabet)}}}, "
                f"start = {current_nfa.initial_state}, "
                f"F = {{{', '.join(current_nfa.sorted_final_states)}}}"
            )


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

        b_col1, b_col2, _ = st.columns([1.8, 1.8, 2.4])
        with b_col1:
            if st.button("Launch Live Simulator ▶", key="btn_dfa_to_trace", type="primary", use_container_width=True):
                reset_simulator_playback()
                navigate_to("5. Live Simulator")
        with b_col2:
            if st.button("Test Input Strings →", key="btn_dfa_to_sim", use_container_width=True):
                navigate_to("6. String Tester")

        st.markdown("---")

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
                    "Type": "Accepting (*)" if is_acc else ("Trap (∅)" if not subset else "Normal"),
                })
            st.dataframe(mapping_data, use_container_width=True, hide_index=True)

            st.subheader("State Count Comparison")
            fig = generate_state_distribution_chart(conv_result.nfa_state_count, conv_result.dfa_state_count)
            st.pyplot(fig, use_container_width=True)

        st.markdown("---")
        st.subheader("DFA Transition Table")
        render_dfa_table(dfa)


# ---------------------------------------------------------------------------
# PAGE 5: LIVE SIMULATOR
# ---------------------------------------------------------------------------
elif selected_page == "5. Live Simulator":
    st.title("Live Subset Construction Simulator")
    st.caption(
        "Watch the Rabin–Scott Subset Construction algorithm explore reachable NFA subsets "
        "using BFS (collections.deque), compute transition unions, and build the DFA in real time."
    )

    if not current_nfa:
        st.warning("Please configure an NFA first.")
    else:
        if not conv_result:
            conv_result = SubsetConstructionEngine(current_nfa).convert()
            st.session_state["conversion_result"] = conv_result

        t_col1, t_col2, _ = st.columns([1.5, 1.5, 3])
        with t_col1:
            if st.button("← Edit NFA Setup", key="btn_live_to_setup", use_container_width=True):
                navigate_to("2. NFA Setup")
        with t_col2:
            if st.button("Test Input Strings →", key="btn_trace_to_sim", use_container_width=True):
                navigate_to("6. String Tester")

        st.markdown("---")
        render_live_simulator(current_nfa, conv_result)


# ---------------------------------------------------------------------------
# PAGE 6: STRING TESTER (WITH ANIMATED EXECUTION)
# ---------------------------------------------------------------------------
elif selected_page == "6. String Tester":
    st.title("String Tester & Equivalence Verifier")
    st.write("Test and animate any input string synchronously on both the original NFA and converted DFA.")

    if not current_nfa or not conv_result:
        st.warning("Please configure an NFA and run conversion first.")
    else:
        dfa = conv_result.dfa
        alphabet_str = ", ".join(current_nfa.sorted_alphabet)
        st.caption(f"Valid alphabet Σ: {{{alphabet_str}}}. Leave empty for the empty string (ε).")

        # Quick test buttons adapted to current alphabet
        st.write("**Quick Test Presets:**")
        if current_nfa.alphabet == {"0", "1"}:
            quick_strings = ["01", "101", "001", "10", "111", "010", ""]
            button_labels = ["01", "101", "001", "10", "111", "010", "ε (Empty)"]
        else:
            syms = current_nfa.sorted_alphabet
            s0 = syms[0]
            s1 = syms[1] if len(syms) > 1 else syms[0]
            quick_strings = [s0, s1, s0 + s1, s0 * 2 + s1, s1 + s0, ""]
            button_labels = [x if x else "ε (Empty)" for x in quick_strings]

        qb_cols = st.columns(len(quick_strings))
        for i, (q_str, q_lbl) in enumerate(zip(quick_strings, button_labels)):
            if qb_cols[i].button(q_lbl, key=f"quick_btn_{i}", use_container_width=True):
                st.session_state["sim_input_target"] = q_str
                st.session_state["str_sim_step"] = 0
                st.session_state["str_sim_playing"] = False
                st.rerun()

        if "sim_input_target" in st.session_state:
            st.session_state["sim_input_text"] = st.session_state.pop("sim_input_target")
        elif "sim_input_text" not in st.session_state:
            st.session_state["sim_input_text"] = quick_strings[0]

        sim_input_col, run_btn_col = st.columns([4, 1])
        with sim_input_col:
            sim_str = st.text_input(
                "Input String:",
                key="sim_input_text",
                placeholder="e.g. 0101 (leave blank for ε)",
            )
        with run_btn_col:
            st.write("")
            st.write("")
            if st.button("Run Test", key="btn_run_test", type="primary", use_container_width=True):
                st.session_state["str_sim_step"] = 0
                st.session_state["str_sim_playing"] = False

        is_valid_str, err_msg = AutomataSimulator.validate_string(current_nfa.alphabet, sim_str)

        if not is_valid_str:
            st.error(f"Invalid string: {err_msg}")
        else:
            cmp_res = AutomataSimulator.compare(current_nfa, dfa, sim_str)

            # Result banner
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

            # Animated step-by-step string playback
            st.markdown("---")
            st.subheader("Animated String Execution")

            total_str_steps = len(cmp_res.dfa_result.steps)
            if "str_sim_step" not in st.session_state:
                st.session_state["str_sim_step"] = 0
            if "str_sim_playing" not in st.session_state:
                st.session_state["str_sim_playing"] = False

            cur_s = max(0, min(st.session_state["str_sim_step"], total_str_steps - 1))
            st.session_state["str_sim_step"] = cur_s

            sc1, sc2, sc3, sc4, sc5 = st.columns([1, 1, 1, 1, 2])
            if sc1.button("⏮ Start", key="str_btn_reset", use_container_width=True):
                st.session_state["str_sim_step"] = 0
                st.session_state["str_sim_playing"] = False
                st.rerun()
            if sc2.button("◀ Prev", key="str_btn_prev", disabled=(cur_s == 0), use_container_width=True):
                st.session_state["str_sim_playing"] = False
                st.session_state["str_sim_step"] = cur_s - 1
                st.rerun()
            if st.session_state["str_sim_playing"]:
                if sc3.button("⏸ Pause", key="str_btn_pause", type="primary", use_container_width=True):
                    st.session_state["str_sim_playing"] = False
                    st.rerun()
            else:
                if sc3.button("▶ Animate", key="str_btn_play", type="primary", disabled=(cur_s >= total_str_steps - 1), use_container_width=True):
                    st.session_state["str_sim_playing"] = True
                    st.rerun()
            if sc4.button("Next ▶", key="str_btn_next", disabled=(cur_s >= total_str_steps - 1), use_container_width=True):
                st.session_state["str_sim_playing"] = False
                st.session_state["str_sim_step"] = cur_s + 1
                st.rerun()

            cur_dfa_step = cmp_res.dfa_result.steps[cur_s]
            cur_nfa_step = cmp_res.nfa_result.steps[cur_s]

            with sc5:
                sym_lbl = f"Read '{cur_dfa_step.symbol}'" if cur_dfa_step.symbol is not None else "Initial (Step 0)"
                st.metric("Execution Step", f"{cur_s} / {total_str_steps - 1} ({sym_lbl})")

            # Highlighted side-by-side diagrams
            g_left, g_right = st.columns(2)
            with g_left:
                st.markdown(f"**NFA Active States:** `{format_subset(frozenset(cur_nfa_step.next_states))}`")
                nfa_edges = set()
                if cur_nfa_step.symbol is not None:
                    for src, tgts in cur_nfa_step.per_state_transitions.items():
                        for tgt in tgts:
                            nfa_edges.add((src, tgt, cur_nfa_step.symbol))
                st.graphviz_chart(
                    generate_nfa_dot(
                        current_nfa,
                        highlight_states=set(cur_nfa_step.next_states),
                        highlight_edges=nfa_edges,
                    ),
                    use_container_width=True,
                )

            with g_right:
                st.markdown(
                    f"**DFA Current State:** `{cur_dfa_step.to_state}` = "
                    f"`{format_subset(cur_dfa_step.to_subset)}`"
                )
                dfa_edge = (
                    (cur_dfa_step.from_state, cur_dfa_step.to_state, cur_dfa_step.symbol)
                    if cur_dfa_step.symbol is not None
                    else None
                )
                st.graphviz_chart(
                    generate_dfa_dot(
                        dfa,
                        highlight_state=cur_dfa_step.to_state,
                        highlight_edge=dfa_edge,
                    ),
                    use_container_width=True,
                )

            st.markdown("---")
            st.subheader("Full Execution Trace")

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

            if st.session_state["str_sim_playing"]:
                if cur_s < total_str_steps - 1:
                    time.sleep(1.0)
                    st.session_state["str_sim_step"] = cur_s + 1
                    st.rerun()
                else:
                    st.session_state["str_sim_playing"] = False
                    st.rerun()


# ---------------------------------------------------------------------------
# PAGE 7: HOW THE ALGORITHM WORKS (VIVA / EDUCATIONAL GUIDE)
# ---------------------------------------------------------------------------
elif selected_page == "7. How the Algorithm Works":
    st.title("How the Subset Construction Algorithm Works")
    st.markdown(
        "A concise theoretical reference explaining every mechanism behind "
        "**Rabin–Scott Subset Construction**."
    )

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### What is an NFA?")
        st.write(
            "A **Non-deterministic Finite Automaton (NFA)** $M = (Q, \\Sigma, \\delta, q_0, F)$ "
            "allows a state to transition to **zero, one, or multiple** states on a single input symbol "
            "(or spontaneously via $\\varepsilon$-transitions). An input string is accepted if **at least one** "
            "computational path ends in an accepting state."
        )
    with c2:
        st.markdown("### What is a DFA?")
        st.write(
            "A **Deterministic Finite Automaton (DFA)** $M' = (Q', \\Sigma, \\delta', q'_0, F')$ "
            "has **exactly one** next state for every $(q, a) \\in Q' \\times \\Sigma$. "
            "Because there is no branching, a DFA is directly executable in $O(|w|)$ time."
        )

    st.markdown("---")
    st.markdown("### Mathematical Transition Function")
    st.latex(r"\delta'(S, a) = \bigcup_{q \in S} \delta(q, a)")
    st.write(
        "For **ε-NFAs**, we first take the initial state's closure $q'_0 = \\varepsilon\\text{-closure}(\\{q_0\\})$, "
        "and apply $\\varepsilon$-closure after every transition union:"
    )
    st.latex(r"\delta'(S, a) = \varepsilon\text{-closure}\!\left(\bigcup_{q \in S} \delta(q, a)\right)")

    st.markdown("---")
    k1, k2 = st.columns(2)
    with k1:
        st.markdown("#### Why Powerset Construction?")
        st.write(
            "At any point while reading a string, an NFA is simultaneously in a **subset** $S \\subseteq Q$ "
            "of its states. By treating each reachable subset $S$ as a **single DFA state**, "
            "we eliminate non-determinism."
        )
        st.markdown("#### Why BFS (`collections.deque`)?")
        st.write(
            "Instead of generating all $2^n$ subsets upfront, Breadth-First Search starts from $\\{q_0\\}$ "
            "and explores **only reachable subsets** level by level using a FIFO queue."
        )
        st.markdown("#### Why `frozenset`?")
        st.write(
            "A Python `frozenset` is **immutable and hashable**, so it can be used directly as a dictionary key "
            "(`subset_to_label[T]`) to detect duplicates in $O(1)$ average time."
        )
    with k2:
        st.markdown("#### Accepting States ($F'$)")
        st.write(
            "A DFA state representing subset $S$ is accepting if and only if $S \\cap F \\neq \\emptyset$ "
            "(i.e., $S$ contains at least one NFA accepting state)."
        )
        st.markdown("#### What is a Trap State ($\\emptyset$)?")
        st.write(
            "If $\\bigcup_{q \\in S} \\delta(q, a) = \\emptyset$, the NFA has no valid transitions. "
            "In a DFA, every transition must be defined, so $\\emptyset$ becomes an explicit non-accepting **trap (dead) state** "
            "that loops to itself on every symbol."
        )
        st.markdown("#### Worst-Case $2^n$ Complexity")
        st.write(
            "An NFA with $n = |Q|$ states has $2^n$ possible subsets in its powerset $\\mathcal{P}(Q)$. "
            "In the worst case (e.g., recognizing the $n$-th symbol from the end), all $2^n$ states are reachable."
        )

    st.markdown("---")
    st.markdown("### Interactive Example: One Subset Becoming a DFA State")
    st.write("Adjust the NFA transitions below to see how a single subset $S = \\{q_0, q_1\\}$ computes $\\delta'(S, 0)$:")

    ex_c1, ex_c2 = st.columns(2)
    with ex_c1:
        t_q0 = st.multiselect("δ(q0, 0) =", options=["q0", "q1", "q2"], default=["q0", "q1"], key="guide_q0")
    with ex_c2:
        t_q1 = st.multiselect("δ(q1, 0) =", options=["q0", "q1", "q2"], default=["q2"], key="guide_q1")

    union_ex = frozenset(t_q0) | frozenset(t_q1)
    q0_fmt = format_subset(frozenset(t_q0))
    q1_fmt = format_subset(frozenset(t_q1))
    u_fmt = format_subset(union_ex)
    is_acc_ex = "q2" in union_ex

    st.code(
        f"Current DFA state: A = {{q0, q1}}\n"
        f"Input symbol:      0\n\n"
        f"δ(q0, 0) = {q0_fmt}\n"
        f"δ(q1, 0) = {q1_fmt}\n\n"
        f"Union = {q0_fmt} ∪ {q1_fmt} = {u_fmt}\n"
        f"Therefore: δ'(A, 0) = {u_fmt} → DFA State B\n"
        f"Accepting? {'Yes (contains q2 ∈ F)' if is_acc_ex else ('No (Trap state ∅)' if not union_ex else 'No')}",
        language="text",
    )
