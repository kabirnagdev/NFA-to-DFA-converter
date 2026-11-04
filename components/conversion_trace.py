"""
Conversion Trace Display Component.

Renders step-by-step subset construction trace:
- Overview summary table
- Expandable step-by-step breakdown
"""

import streamlit as st
import pandas as pd
from typing import List

from core.conversion import ConversionStep, ConversionResult


def render_conversion_steps(result: ConversionResult):
    """Renders subset construction steps in tabular and card formats."""
    steps: List[ConversionStep] = result.steps
    
    if not steps:
        st.info("No conversion steps recorded.")
        return

    st.subheader("Step-by-Step Subset Construction")
    st.caption("How each DFA state and transition was derived via subset construction.")

    # Summary Table
    table_data = []
    for s in steps:
        table_data.append({
            "Step": s.step_number,
            "Current State": f"{s.current_label} = {s.formatted_current_subset}",
            "Symbol": s.symbol,
            "NFA Derivation": s.formula_breakdown,
            "Union": s.formatted_union_result,
            "DFA Target": s.target_label,
            "Discovery": "New State" if s.is_new_state else "Existing",
        })

    summary_df = pd.DataFrame(table_data)
    st.dataframe(
        summary_df,
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("---")
    st.subheader("Inspect Specific Step")
    
    step_options = [
        f"Step {s.step_number}: δ'({s.current_label}, {s.symbol}) → {s.target_label}"
        for s in steps
    ]
    
    selected_idx = st.selectbox(
        "Select step to inspect:",
        range(len(steps)),
        format_func=lambda i: step_options[i],
    )
    render_single_step_card(steps[selected_idx])


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


def render_step_details(steps: List[ConversionStep]):
    """Helper wrapper for external calls."""
    for s in steps:
        render_single_step_card(s)
