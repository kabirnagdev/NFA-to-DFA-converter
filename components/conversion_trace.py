"""
Conversion Trace Display Component.

Renders granular step-by-step subset construction traces:
- Overview table summarizing every state transition evaluation
- Expandable step-by-step breakdown highlighting individual transitions,
  union calculations, and discovery status.
"""

import streamlit as st
import pandas as pd
from typing import List

from core.conversion import ConversionStep, ConversionResult


def render_conversion_steps(result: ConversionResult):
    """
    Renders the subset construction steps in both tabular and expandable formats.
    """
    steps: List[ConversionStep] = result.steps
    
    if not steps:
        st.info("No conversion steps recorded.")
        return

    st.subheader("Step-by-Step Subset Construction Trace")
    st.write(
        "Below is the exact execution trace of the **Subset Construction Algorithm** "
        "using Breadth-First Search (BFS). Each row details how transitions are computed "
        "by taking the union of individual NFA transitions."
    )

    # 1. Summary Table
    table_data = []
    for s in steps:
        table_data.append({
            "Step": s.step_number,
            "Current State": f"{s.current_label} = {s.formatted_current_subset}",
            "Input Symbol": s.symbol,
            "NFA Transition Formula": s.formula_breakdown,
            "Target Subset (Union)": s.formatted_union_result,
            "Target DFA State": s.target_label,
            "Status": "✨ New State" if s.is_new_state else "Existing State",
        })

    summary_df = pd.DataFrame(table_data)
    st.dataframe(
        summary_df,
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("---")
    st.subheader("Detailed Step Breakdown")
    
    # Step selector / filter for detailed inspection
    step_options = [
        f"Step {s.step_number}: δ'({s.current_label}, {s.symbol}) → {s.target_label}"
        for s in steps
    ]
    
    view_mode = st.radio(
        "Detailed View Mode:",
        ["Show All Expanders", "Inspect Specific Step"],
        horizontal=True,
    )

    if view_mode == "Inspect Specific Step":
        selected_idx = st.selectbox(
            "Select Step to Inspect:",
            range(len(steps)),
            format_func=lambda i: step_options[i],
        )
        render_single_step_card(steps[selected_idx])
    else:
        for s in steps:
            with st.expander(
                f"Step {s.step_number}: δ'({s.current_label}, {s.symbol}) = {s.target_label} = {s.formatted_union_result} "
                f"({'New State' if s.is_new_state else 'Existing'})",
                expanded=(s.step_number == 1),
            ):
                render_single_step_card(s)


def render_single_step_card(step: ConversionStep):
    """Render a clean academic card detailing a single conversion step."""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"**Current DFA State:** `{step.current_label}`")
        st.markdown(f"**Current Subset:** `{step.formatted_current_subset}`")
    
    with col2:
        st.markdown(f"**Input Symbol:** `{step.symbol}`")
        st.markdown(
            f"**Discovery Status:** {'`New State Discovered`' if step.is_new_state else '`Already Visited`'}"
        )

    with col3:
        st.markdown(f"**Target DFA State:** `{step.target_label}`")
        st.markdown(f"**Target Subset:** `{step.formatted_union_result}`")

    st.markdown("##### Mathematical Derivation:")
    
    if not step.current_subset:
        st.code(f"δ'({step.current_label}, {step.symbol}) = δ'(∅, {step.symbol}) = ∅ (Trap State)", language="text")
    else:
        deriv_lines = []
        for q, targets in sorted(step.individual_transitions.items()):
            t_str = "{" + ", ".join(sorted(targets)) + "}" if targets else "∅"
            deriv_lines.append(f"δ({q}, {step.symbol}) = {t_str}")
        
        target_str = step.formatted_union_result
        deriv_lines.append(f"Union = {target_str}")
        deriv_lines.append(f"Resulting DFA State = {step.target_label} = {target_str}")
        
        st.code("\n".join(deriv_lines), language="text")

    st.info(step.explanation)


def render_step_details(steps: List[ConversionStep]):
    """Helper wrapper for external calls."""
    for s in steps:
        render_single_step_card(s)
