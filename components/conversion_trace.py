"""
Live Interactive Conversion Simulator & Trace Component.

Provides:
- Playback controls: Play, Pause, Next Step, Previous Step, Reset, Speed control
- Current Execution Panel (step, state, subset, symbol, operation, status)
- BFS Queue Visualization (processed, current, pending, newly discovered, empty at end)
- Dynamic Mathematical Breakdown (with separate ε-closure breakdown for ε-NFAs)
- Synchronized Animated NFA & Partial DFA Diagrams
- Continuously Updating Live DFA Transition Table
- Full Step Summary Table (collapsible, preserving Milestone 1 overview)
"""

import time
import html
import streamlit as st
import pandas as pd
from typing import List, Set, Tuple

from core.nfa import NFA
from core.conversion import (
    ConversionStep,
    ConversionSnapshot,
    ConversionResult,
    format_subset,
)
from components.transition_table import render_live_dfa_table
from visualization.automata_graph import (
    generate_nfa_dot,
    generate_partial_dfa_dot_with_finals,
)


# ---------------------------------------------------------------------------
# Session state helpers
# ---------------------------------------------------------------------------

def _ensure_sim_state(total_snapshots: int):
    """Initialize or clamp simulator playback state."""
    if "sim_step" not in st.session_state:
        st.session_state["sim_step"] = 0
    if "sim_playing" not in st.session_state:
        st.session_state["sim_playing"] = False
    if "sim_speed" not in st.session_state:
        st.session_state["sim_speed"] = 1.2

    # Clamp step index safely
    if total_snapshots > 0:
        st.session_state["sim_step"] = max(
            0, min(st.session_state["sim_step"], total_snapshots - 1)
        )
    else:
        st.session_state["sim_step"] = 0


# ---------------------------------------------------------------------------
# Main Live Simulator Entry Point
# ---------------------------------------------------------------------------

def render_live_simulator(nfa: NFA, result: ConversionResult):
    """Render the full interactive, animated Subset Construction simulator."""
    snapshots: List[ConversionSnapshot] = result.snapshots
    if not snapshots:
        st.info("No conversion steps recorded.")
        return

    total = len(snapshots)
    _ensure_sim_state(total)

    cur_idx: int = st.session_state["sim_step"]
    snap: ConversionSnapshot = snapshots[cur_idx]
    step: ConversionStep = snap.step
    is_finished = (cur_idx == total - 1) and not snap.queue_pending

    # -----------------------------------------------------------------------
    # 1. Playback Controls Bar
    # -----------------------------------------------------------------------
    ctrl_cols = st.columns([1, 1, 1.1, 1.1, 1, 1.8, 1.4])

    with ctrl_cols[0]:
        if st.button("⏮ Reset", key="sim_btn_reset", use_container_width=True):
            st.session_state["sim_step"] = 0
            st.session_state["sim_playing"] = False
            st.rerun()

    with ctrl_cols[1]:
        if st.button(
            "◀ Prev",
            key="sim_btn_prev",
            disabled=(cur_idx == 0),
            use_container_width=True,
        ):
            st.session_state["sim_playing"] = False
            st.session_state["sim_step"] = max(0, cur_idx - 1)
            st.rerun()

    with ctrl_cols[2]:
        if st.session_state["sim_playing"]:
            if st.button("⏸ Pause", key="sim_btn_pause", type="primary", use_container_width=True):
                st.session_state["sim_playing"] = False
                st.rerun()
        else:
            if st.button(
                "▶ Play",
                key="sim_btn_play",
                type="primary",
                disabled=(cur_idx >= total - 1),
                use_container_width=True,
            ):
                st.session_state["sim_playing"] = True
                st.rerun()

    with ctrl_cols[3]:
        if st.button(
            "Next ▶",
            key="sim_btn_next",
            disabled=(cur_idx >= total - 1),
            use_container_width=True,
        ):
            st.session_state["sim_playing"] = False
            st.session_state["sim_step"] = min(total - 1, cur_idx + 1)
            st.rerun()

    with ctrl_cols[4]:
        if st.button(
            "⏭ End",
            key="sim_btn_end",
            disabled=(cur_idx >= total - 1),
            use_container_width=True,
        ):
            st.session_state["sim_playing"] = False
            st.session_state["sim_step"] = total - 1
            st.rerun()

    with ctrl_cols[5]:
        speed = st.select_slider(
            "Step Delay (s)",
            options=[0.4, 0.8, 1.2, 1.8, 2.5],
            value=st.session_state.get("sim_speed", 1.2),
            key="sim_speed_slider",
            label_visibility="collapsed",
        )
        st.session_state["sim_speed"] = speed
        st.caption(f"Speed: {speed}s / step")

    with ctrl_cols[6]:
        st.metric("Step", f"{cur_idx + 1} / {total}")

    # Progress bar
    st.progress((cur_idx + 1) / total)

    # -----------------------------------------------------------------------
    # 2. Current Execution Panel & BFS Queue Visualization
    # -----------------------------------------------------------------------
    panel_col, queue_col = st.columns([1.35, 1])

    with panel_col:
        _render_execution_panel(snap, is_finished)

    with queue_col:
        _render_queue_panel(snap, is_finished)

    st.markdown("---")

    # -----------------------------------------------------------------------
    # 3. Mathematical Breakdown + Live DFA Transition Table
    # -----------------------------------------------------------------------
    math_col, table_col = st.columns([1, 1.4])

    with math_col:
        st.subheader("Mathematical Breakdown")
        _render_math_breakdown(snap)

    with table_col:
        st.subheader("Live DFA Transition Table")
        render_live_dfa_table(
            snapshot=snap,
            alphabet=nfa.sorted_alphabet,
            nfa_final_states=nfa.final_states,
            initial_label=result.dfa.initial_state,
        )
        st.caption(
            "Amber = active row/cell | Blue = newly discovered state | "
            "Green = accepting state (*)"
        )

    st.markdown("---")

    # -----------------------------------------------------------------------
    # 4. Synchronized NFA & Partial DFA Diagrams
    # -----------------------------------------------------------------------
    st.subheader("Animated Automata Diagrams")
    g_nfa_col, g_dfa_col = st.columns(2)

    with g_nfa_col:
        st.markdown("**Original NFA** *(active subset highlighted)*")
        active_nfa_states: Set[str] = set(step.current_subset)
        active_nfa_edges: Set[Tuple[str, str, str]] = set()
        for src, targets in step.individual_transitions.items():
            for tgt in targets:
                active_nfa_edges.add((src, tgt, step.symbol))
        nfa_dot = generate_nfa_dot(
            nfa,
            highlight_states=active_nfa_states,
            highlight_edges=active_nfa_edges,
        )
        st.graphviz_chart(nfa_dot, use_container_width=True)

    with g_dfa_col:
        st.markdown("**Constructed DFA** *(updating live)*")
        dfa_dot = generate_partial_dfa_dot_with_finals(
            snapshot=snap,
            nfa_final_states=nfa.final_states,
        )
        st.graphviz_chart(dfa_dot, use_container_width=True)

    # -----------------------------------------------------------------------
    # 5. Full Step Summary (Collapsible, preserves Milestone 1 table)
    # -----------------------------------------------------------------------
    with st.expander("View Complete Step Summary Table", expanded=False):
        render_conversion_steps(result)

    # -----------------------------------------------------------------------
    # 6. Auto-advance when Playing
    # -----------------------------------------------------------------------
    if st.session_state["sim_playing"]:
        if cur_idx < total - 1:
            time.sleep(st.session_state["sim_speed"])
            st.session_state["sim_step"] = cur_idx + 1
            st.rerun()
        else:
            st.session_state["sim_playing"] = False
            st.rerun()


# ---------------------------------------------------------------------------
# Sub-panels
# ---------------------------------------------------------------------------

def _render_execution_panel(snap: ConversionSnapshot, is_finished: bool):
    """Display current step metadata, operation, formula, and discovery status."""
    step = snap.step
    status_text = (
        f"New DFA state '{step.target_label}' discovered and enqueued"
        if step.is_new_state
        else f"Existing DFA state '{step.target_label}' reused"
    )
    status_cls = "status-new" if step.is_new_state else "status-reused"
    op_desc = (
        f"Computing δ'({step.current_label}, {step.symbol}) via "
        + ("ε-closure of transition union" if snap.is_epsilon_nfa else "transition union")
    )
    if not step.current_subset:
        op_desc = f"Trap state {step.current_label} = ∅ self-loop on '{step.symbol}'"

    formula_expr = (
        f"δ'({step.current_label}, {step.symbol}) = "
        + (f"ε-closure({format_subset(step.raw_union)}) = " if snap.is_epsilon_nfa and step.raw_union else "")
        + f"{step.formatted_union_result} = {step.target_label}"
    )

    done_banner = (
        '<div class="exec-complete">Conversion Complete: BFS queue is empty. '
        "All reachable DFA states have been explored.</div>"
        if is_finished
        else ""
    )

    panel_html = f"""
    <div class="exec-panel">
        <div class="exec-panel-title">Current Execution Panel — Step {step.step_number} of {snap.total_snapshots}</div>
        <div class="exec-grid">
            <div><span class="exec-lbl">Current DFA State:</span> <code>{html.escape(step.current_label)}</code></div>
            <div><span class="exec-lbl">NFA Subset:</span> <code>{html.escape(step.formatted_current_subset)}</code></div>
            <div><span class="exec-lbl">Input Symbol:</span> <code>{html.escape(step.symbol)}</code></div>
            <div><span class="exec-lbl">Result State:</span> <code>{html.escape(step.target_label)} = {html.escape(step.formatted_union_result)}</code></div>
        </div>
        <div class="exec-row"><strong>Operation:</strong> {html.escape(op_desc)}</div>
        <div class="exec-row"><strong>Expression:</strong> <code>{html.escape(formula_expr)}</code></div>
        <div class="exec-row"><strong>Status:</strong> <span class="{status_cls}">{html.escape(status_text)}</span></div>
        {done_banner}
    </div>
    """
    st.markdown(panel_html, unsafe_allow_html=True)


def _render_queue_panel(snap: ConversionSnapshot, is_finished: bool):
    """Display the FIFO BFS queue state: current, pending, newly discovered, processed."""
    step = snap.step

    # Current state chip
    cur_chip = (
        f'<span class="q-chip q-chip-current">{html.escape(step.current_label)} '
        f'= {html.escape(step.formatted_current_subset)}</span>'
    )

    # Pending queue chips
    new_set = {lbl for lbl, _ in snap.queue_just_discovered}
    if snap.queue_pending:
        pending_chips = " ".join(
            f'<span class="q-chip {"q-chip-new" if lbl in new_set else "q-chip-pending"}">'
            f'{html.escape(lbl)} = {html.escape(format_subset(sub))}</span>'
            for lbl, sub in snap.queue_pending
        )
    else:
        pending_chips = '<span class="q-empty">∅ (Queue is empty)</span>'

    # Processed chips
    if snap.queue_processed:
        proc_chips = " ".join(
            f'<span class="q-chip q-chip-done">{html.escape(lbl)}</span>'
            for lbl, _ in snap.queue_processed
        )
    else:
        proc_chips = '<span class="q-empty">None yet</span>'

    queue_status = (
        "Queue empty — BFS terminated."
        if is_finished
        else f"{len(snap.queue_pending)} state(s) waiting in FIFO queue."
    )

    queue_html = f"""
    <div class="queue-panel">
        <div class="exec-panel-title">BFS Queue Visualization (collections.deque)</div>
        <div class="q-section">
            <div class="q-label">Currently Processing (dequeued):</div>
            <div class="q-chips">{cur_chip}</div>
        </div>
        <div class="q-section">
            <div class="q-label">Pending in FIFO Queue (blue = newly enqueued):</div>
            <div class="q-chips">{pending_chips}</div>
        </div>
        <div class="q-section">
            <div class="q-label">Already Processed:</div>
            <div class="q-chips">{proc_chips}</div>
        </div>
        <div class="q-footer">{html.escape(queue_status)}</div>
    </div>
    """
    st.markdown(queue_html, unsafe_allow_html=True)


def _render_math_breakdown(snap: ConversionSnapshot):
    """Render dynamic step-by-step mathematical derivation for the current step."""
    step = snap.step
    lines: List[str] = [
        f"Current state: {step.current_label} = {step.formatted_current_subset}",
        f"Input symbol:  {step.symbol}",
        "",
    ]

    if not step.current_subset:
        lines.append(f"δ'(∅, {step.symbol}) = ∅  (Trap state self-loop)")
    else:
        for q, targets in sorted(step.individual_transitions.items()):
            t_str = "{" + ", ".join(sorted(targets)) + "}" if targets else "∅"
            lines.append(f"δ({q}, {step.symbol}) = {t_str}")

        raw_str = format_subset(step.raw_union)
        lines.append("")
        lines.append(f"Union = {raw_str}")

        if snap.is_epsilon_nfa and step.raw_union:
            lines.append("")
            lines.append("Epsilon-closure calculation:")
            if step.epsilon_closure_steps:
                for q, added in sorted(step.epsilon_closure_steps.items()):
                    lines.append(
                        f"  ε-closure({{{q}}}) adds {format_subset(frozenset(added))}"
                    )
            else:
                lines.append("  No additional states reachable via ε.")
            lines.append(f"ε-closure({raw_str}) = {step.formatted_union_result}")

        lines.append("")
        lines.append("Therefore:")
        lines.append(
            f"δ'({step.current_label}, {step.symbol}) = "
            f"{step.formatted_union_result} = {step.target_label}"
        )

    lines.append("")
    if step.is_new_state:
        lines.append(f"Status: New state {step.target_label} discovered & enqueued.")
    else:
        lines.append(f"Status: Existing state {step.target_label} reused.")

    st.code("\n".join(lines), language="text")


# ---------------------------------------------------------------------------
# Milestone 1 Summary Table (preserved for compatibility & overview)
# ---------------------------------------------------------------------------

def render_conversion_steps(result: ConversionResult):
    """Renders subset construction steps in tabular and card formats."""
    steps: List[ConversionStep] = result.steps

    if not steps:
        st.info("No conversion steps recorded.")
        return

    table_data = []
    for s in steps:
        table_data.append({
            "Step": s.step_number,
            "Current State": f"{s.current_label} = {s.formatted_current_subset}",
            "Symbol": s.symbol,
            "NFA Derivation": s.formula_breakdown,
            "Union / Result": s.formatted_union_result,
            "DFA Target": s.target_label,
            "Discovery": "New State" if s.is_new_state else "Existing",
        })

    summary_df = pd.DataFrame(table_data)
    st.dataframe(
        summary_df,
        use_container_width=True,
        hide_index=True,
    )


def render_single_step_card(step: ConversionStep):
    """Render a clean card for a single conversion step."""
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"**Current State:** `{step.current_label}` = `{step.formatted_current_subset}`")

    with col2:
        st.markdown(f"**Symbol:** `{step.symbol}`")
        status_badge = "New State Discovered" if step.is_new_state else "Existing State Visited"
        st.markdown(f"**Status:** `{status_badge}`")

    with col3:
        st.markdown(f"**Next State:** `{step.target_label}` = `{step.formatted_union_result}`")

    if not step.current_subset:
        st.code(f"δ'({step.current_label}, {step.symbol}) = ∅ (Trap State)", language="text")
    else:
        deriv_lines = []
        for q, targets in sorted(step.individual_transitions.items()):
            t_str = "{" + ", ".join(sorted(targets)) + "}" if targets else "∅"
            deriv_lines.append(f"δ({q}, {step.symbol}) = {t_str}")

        target_str = step.formatted_union_result
        deriv_lines.append(f"Union = {target_str}")
        deriv_lines.append(f"Next DFA State = {step.target_label} = {target_str}")
        st.code("\n".join(deriv_lines), language="text")
