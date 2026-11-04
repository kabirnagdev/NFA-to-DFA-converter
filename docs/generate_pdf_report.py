"""
PDF Report Generator for NFA to DFA Conversion Simulator.
Uses ReportLab Platypus to generate a publication-quality academic report.
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Preformatted,
    KeepTogether,
    HRFlowable,
)
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to add 'Page X of Y' footers and running headers."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#475569"))

        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(
                36,
                758,
                "NFA to DFA Conversion Simulator — System Documentation & Technical Report",
            )
            self.drawRightString(
                576,
                758,
                "B.Tech CSE / Automata Theory",
            )
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(36, 752, 576, 752)

        # Footer
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(36, 42, 576, 42)

        self.drawString(
            36,
            30,
            "Author: Kabir Nagdev | https://github.com/kabirnagdev/NFA-to-DFA-converter",
        )
        self.drawRightString(
            576,
            30,
            f"Page {self._pageNumber} of {page_count}",
        )
        self.restoreState()


def build_pdf(output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    primary_color = colors.HexColor("#1E3A8A")
    dark_slate = colors.HexColor("#0F172A")
    body_color = colors.HexColor("#1E293B")
    accent_teal = colors.HexColor("#0D9488")

    title_style = ParagraphStyle(
        "CoverTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=primary_color,
        spaceAfter=4,
    )

    subtitle_style = ParagraphStyle(
        "CoverSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#334155"),
        spaceAfter=12,
    )

    h1_style = ParagraphStyle(
        "SectionH1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=primary_color,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True,
    )

    h2_style = ParagraphStyle(
        "SectionH2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=14,
        textColor=dark_slate,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11.5,
        textColor=body_color,
        spaceAfter=6,
    )

    bullet_style = ParagraphStyle(
        "ReportBullet",
        parent=body_style,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=3,
    )

    code_style = ParagraphStyle(
        "CodeBlock",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=7,
        leading=8.5,
        textColor=colors.HexColor("#0F172A"),
    )

    table_cell = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=9.5,
        textColor=body_color,
    )

    table_header = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9.5,
        textColor=colors.white,
    )

    story = []

    # Title & Metadata Banner
    story.append(Paragraph("NFA TO DFA CONVERSION SIMULATOR", title_style))
    story.append(
        Paragraph(
            "<b>Comprehensive System Specification, Architecture, Algorithmic Analysis & Validation Report</b>",
            subtitle_style,
        )
    )

    meta_table_data = [
        [
            Paragraph("<b>Target Course:</b> Automata Theory / Theory of Computation", table_cell),
            Paragraph("<b>Author:</b> Kabir Nagdev", table_cell),
        ],
        [
            Paragraph("<b>Technology Stack:</b> Python 3.13, Streamlit, Graphviz, Pytest", table_cell),
            Paragraph("<b>Repository:</b> github.com/kabirnagdev/NFA-to-DFA-converter", table_cell),
        ],
    ]
    meta_table = Table(meta_table_data, colWidths=[270, 270])
    meta_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ])
    )
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # =========================================================================
    # SECTION 1: EXISTING-TOOL ANALYSIS
    # =========================================================================
    story.append(Paragraph("1. Existing-Tool Analysis & Comparative Evaluation", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=primary_color, spaceAfter=6))

    story.append(
        Paragraph(
            "Undergraduate computer science instruction in Formal Languages and Automata Theory has traditionally "
            "relied on desktop utilities or basic client-side scripts. To establish design goals, four representative tools were evaluated:",
            body_style,
        )
    )

    tools_text = [
        "<b>JFLAP 7.1 (Duke University)</b>: Extensive theoretical scope across Turing machines, grammars, and PDAs. However, it requires a local Java JRE runtime, suffers from dated multi-window modal dialogs, and exhibits UI scaling flaws on high-DPI displays.",
        "<b>Cyberzhg Automata Simulator (cyberzhg.github.io)</b>: Provides instant browser-based execution via Vis.js, but operates as a <i>black box</i>—converting NFAs directly into DFAs without revealing the step-by-step subset unions, omitting explicit dead state self-loops, and lacking dual synchronous traces.",
        "<b>Automata-lib / FSMView (Python Package Ecosystem)</b>: High algorithmic correctness, but lacks any graphical user interface, making it unsuited for classroom interaction or non-programmer evaluation.",
        "<b>Stanford Automata Applets</b>: Simple interactive canvas, but unmaintained, restricted to fixed alphabet sizes, and lacking automated testing.",
    ]
    for tt in tools_text:
        story.append(Paragraph(f"• {tt}", bullet_style))

    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>Table 1.1: Feature Comparison Matrix</b>", h2_style))

    cmp_matrix = [
        [
            Paragraph("<b>Dimension</b>", table_header),
            Paragraph("<b>JFLAP 7.1</b>", table_header),
            Paragraph("<b>Cyberzhg Web</b>", table_header),
            Paragraph("<b>automata-lib</b>", table_header),
            Paragraph("<b>Our Simulator</b>", table_header),
        ],
        [
            Paragraph("<b>Delivery</b>", table_cell),
            Paragraph("Java App (.jar)", table_cell),
            Paragraph("Client JS / Web", table_cell),
            Paragraph("Python CLI / Lib", table_cell),
            Paragraph("<b>Streamlit Web App</b>", table_cell),
        ],
        [
            Paragraph("<b>Input Interface</b>", table_cell),
            Paragraph("Drag-and-drop nodes", table_cell),
            Paragraph("Raw text / Canvas", table_cell),
            Paragraph("Python code / Dict", table_cell),
            Paragraph("<b>Interactive Data Grid</b>", table_cell),
        ],
        [
            Paragraph("<b>Derivation Trace</b>", table_cell),
            Paragraph("Step dialogs", table_cell),
            Paragraph("Black-box output", table_cell),
            Paragraph("None (Programmatic)", table_cell),
            Paragraph("<b>Granular BFS Union Trace</b>", table_cell),
        ],
        [
            Paragraph("<b>Trap State (∅)</b>", table_cell),
            Paragraph("Implicit", table_cell),
            Paragraph("Often omitted", table_cell),
            Paragraph("Standard", table_cell),
            Paragraph("<b>Explicit ∅ Self-Loops</b>", table_cell),
        ],
        [
            Paragraph("<b>String Simulation</b>", table_cell),
            Paragraph("Single trace stepper", table_cell),
            Paragraph("Final boolean only", table_cell),
            Paragraph("Programmatic eval", table_cell),
            Paragraph("<b>Dual Synchronous Trace</b>", table_cell),
        ],
        [
            Paragraph("<b>Automated Tests</b>", table_cell),
            Paragraph("None", table_cell),
            Paragraph("None", table_cell),
            Paragraph("Pytest available", table_cell),
            Paragraph("<b>18 Pytest Tests (100%)</b>", table_cell),
        ],
    ]
    comp_table = Table(cmp_matrix, colWidths=[80, 110, 110, 110, 130])
    comp_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), primary_color),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ("TOPPADDING", (0, 0), (-1, -1), 2.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ])
    )
    story.append(comp_table)
    story.append(Spacer(1, 8))

    # =========================================================================
    # SECTION 2: SYSTEM ARCHITECTURE & UML
    # =========================================================================
    story.append(Paragraph("2. System Architecture & UML Specifications", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=primary_color, spaceAfter=6))

    story.append(
        Paragraph(
            "The simulator employs a decoupled, modular 3-tier architecture separating presentation, controller state, and automata domain logic:",
            body_style,
        )
    )

    arch_points = [
        "<b>Presentation Layer</b>: Built using Streamlit, comprising 6 dedicated pages (Overview, NFA Setup, NFA Graph, DFA Result, Step Trace, String Tester). Custom CSS provides crisp academic styling.",
        "<b>Controller & State Layer</b>: Manages multi-step session persistence and safe deferred navigation (<code>nav_target</code>) to prevent widget instantiation conflicts across reruns.",
        "<b>Core Domain & Algorithmic Engine</b>: Contains <code>NFA</code>, <code>DFA</code>, <code>SubsetConstructionEngine</code>, <code>NFAValidator</code>, and <code>AutomataSimulator</code>.",
        "<b>Visualization Layer</b>: Generates standard Graphviz DOT definitions rendering initial start arrows, double circles for final states, and consolidated transition labels.",
    ]
    for ap in arch_points:
        story.append(Paragraph(f"• {ap}", bullet_style))

    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>2.1 Class Model & Component Interactions</b>", h2_style))

    uml_text = """+---------------------------------------------------------------------------------------------------+
|                                            NFA (core/nfa.py)                                      |
+---------------------------------------------------------------------------------------------------+
| - states: Set[str]                - initial_state: str                - final_states: Set[str]     |
| - alphabet: Set[str]              - transitions: Dict[Tuple[str, str], Set[str]]                  |
+---------------------------------------------------------------------------------------------------+
| + get_transitions(state, symbol) -> Set[str]       + to_dict() / from_dict(data)                   |
+---------------------------------------------------------------------------------------------------+
                                                  ^
                                                  | processes
+-------------------------------------------------+-------------------------------------------------+
|                                SubsetConstructionEngine (core/conversion.py)                      |
+---------------------------------------------------------------------------------------------------+
| - nfa: NFA                                                                                        |
| + convert() -> ConversionResult (dfa: DFA, steps: List[ConversionStep], state_mapping: Dict)      |
+---------------------------------------------------------------------------------------------------+
                                                  | produces
                                                  v
+---------------------------------------------------------------------------------------------------+
|                                            DFA (core/dfa.py)                                      |
+---------------------------------------------------------------------------------------------------+
| - states: Set[str]                - initial_state: str                - final_states: Set[str]     |
| - alphabet: Set[str]              - transitions: Dict[Tuple[str, str], str]                       |
| - state_subsets: Dict[str, FrozenSet[str]]                            - subset_to_label: Dict     |
+---------------------------------------------------------------------------------------------------+
| + get_transition(state, symbol) -> str             + is_final(state) -> bool                      |
| + get_subset_str(state) -> str                     + to_dict() / from_dict(data)                  |
+---------------------------------------------------------------------------------------------------+"""
    story.append(Preformatted(uml_text, code_style))
    story.append(Spacer(1, 8))

    # =========================================================================
    # SECTION 3: UI MOCK-UPS & WIREFRAMES
    # =========================================================================
    story.append(Paragraph("3. User Interface Mock-Ups & Layout Specifications", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=primary_color, spaceAfter=6))

    story.append(
        Paragraph(
            "The user interface emphasizes clean information hierarchy, readable typography, and accessible controls. Below are the structural wireframes:",
            body_style,
        )
    )

    wf_text = """[Wireframe 3.1: NFA Setup & Transition Editor]
+---------------------------------------------------------------------------------------------------+
| NFA Configuration                                                                                 |
| Select Preset: [ Demo: Strings ending in '01' (v) ]          [ Load Preset ]  [ Reset ]           |
|                                                                                                   |
| States (Q): [ q0, q1, q2                 ]       Alphabet (Σ): [ 0, 1                            ]|
| Start State: [ q0                        ]       Accept States: [ q2                             ]|
|                                                                                                   |
| Transition Table (δ):                                                                             |
| +-------------------------+-------------------------+-------------------------------------------+ |
| | Current State           | Symbol                  | Next States (comma-separated or blank)    | |
| +-------------------------+-------------------------+-------------------------------------------+ |
| | q0                      | 0                       | q0, q1                                    | |
| | q0                      | 1                       | q0                                        | |
| | q1                      | 0                       |                                           | |
| | q1                      | 1                       | q2                                        | |
| | q2                      | 0                       |                                           | |
| | q2                      | 1                       |                                           | |
| +-------------------------+-------------------------+-------------------------------------------+ |
| [ Validate ]   [ Convert to DFA (Primary) ]                                                       |
| Status: [✓] NFA is valid and ready for conversion.                                                |
| [ View NFA Graph -> ]   [ View DFA Result -> ]                                                    |
+---------------------------------------------------------------------------------------------------+

[Wireframe 3.2: String Tester & Dual Equivalence Verification]
+---------------------------------------------------------------------------------------------------+
| String Tester & Equivalence Verifier                                                              |
| Quick Presets: [ 01 ] [ 101 ] [ 001 ] [ 10 ] [ 111 ] [ 010 ] [ ε (Empty) ]                        |
| Input String: [ 101                       ]   [ Run Test ]                                        |
|                                                                                                   |
| [✓] RESULT: ACCEPTED  •  Both NFA and DFA accepted string '101'.                                  |
| Explanation: Both agree: '101' is ACCEPTED. NFA active states {q0, q2} match DFA state C.         |
|                                                                                                   |
| DFA Traversal Path:                              | NFA Active State Sets:                         |
| +------+--------+---------+------+-------+       | +------+--------+---------------+----------+   |
| | Step | Symbol | Current | Next | Acc.? |       | | Step | Symbol | Active States | Next Act.|   |
| +------+--------+---------+------+-------+       | +------+--------+---------------+----------+   |
| | 0    | (start)| A       | A    | No    |       | | 0    | (start)| {q0}          | {q0}     |   |
| | 1    | 1      | A       | A    | No    |       | | 1    | 1      | {q0}          | {q0}     |   |
| | 2    | 0      | A       | B    | No    |       | | 2    | 0      | {q0}          | {q0, q1} |   |
| | 3    | 1      | B       | C    | Yes(*)|       | | 3    | 1      | {q0, q1}      | {q0, q2}*|   |
| +------+--------+---------+------+-------+       | +------+--------+---------------+----------+   |
+---------------------------------------------------------------------------------------------------+"""
    story.append(Preformatted(wf_text, code_style))
    story.append(Spacer(1, 8))

    # =========================================================================
    # SECTION 4: FORMAL ALGORITHM & PSEUDOCODE
    # =========================================================================
    story.append(Paragraph("4. Formal Algorithm Specification & Complexity", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=primary_color, spaceAfter=6))

    story.append(
        Paragraph(
            "<b>Definition (Rabin-Scott Powersets)</b>: Given an NFA M = (Q, Σ, δ, q0, F), the equivalent DFA "
            "M' = (Q', Σ, δ', q'0, F') is constructed such that q'0 = {q0}, δ'(S, a) = ⋃_{q ∈ S} δ(q, a), "
            "and F' = {S ∈ Q' | S ∩ F ≠ ∅}. The BFS algorithm below explores reachable states only:",
            body_style,
        )
    )

    pseudo_text = """Algorithm: SUBSET_CONSTRUCTION
Input    : NFA M = (Q, Σ, δ, q0, F)
Output   : ConversionResult(DFA M', steps, state_mapping)

1:  Let queue be an empty FIFO queue (collections.deque)
2:  Let subset_to_label be an empty hash map (frozenset -> str)
3:  Let label_to_subset be an empty hash map (str -> frozenset)
4:  Let dfa_transitions be an empty hash map ((str, str) -> str)
5:  Let steps be an empty list of ConversionStep records
6:  Let label_counter ← 0
7:  
8:  // Step 1: Initialize Start State
9:  S0 ← frozenset({q0})
10: initial_label ← GENERATE_LABEL(label_counter)  // 'A'
11: label_counter ← label_counter + 1
12: subset_to_label[S0] ← initial_label
13: label_to_subset[initial_label] ← S0
14: queue.ENQUEUE(S0)
15: 
16: // Step 2: BFS Exploration of Reachable Subsets
17: while queue is not empty do
18:     current_subset ← queue.DEQUEUE()
19:     current_label ← subset_to_label[current_subset]
20:     
21:     for each symbol a ∈ SORTED(Σ) do
22:         target_subset ← ∅
23:         individual_trans ← empty dictionary
24:         if current_subset == ∅ then
25:             target_subset ← frozenset()   // Trap state loops to itself
26:         else
27:             for each state q ∈ SORTED(current_subset) do
28:                 targets ← δ(q, a)
29:                 individual_trans[q] ← targets
30:                 target_subset ← target_subset ∪ targets
31:             end for
32:             target_subset ← frozenset(target_subset)
33:         end if
34:         
35:         is_new ← FALSE
36:         if target_subset ∉ subset_to_label then
37:             target_label ← GENERATE_LABEL(label_counter)
38:             label_counter ← label_counter + 1
39:             subset_to_label[target_subset] ← target_label
40:             label_to_subset[target_label] ← target_subset
41:             queue.ENQUEUE(target_subset)
42:             is_new ← TRUE
43:         else
44:             target_label ← subset_to_label[target_subset]
45:         end if
46:         dfa_transitions[(current_label, a)] ← target_label
47:         
48:         // Record step trace for pedagogical breakdown
49:         steps.APPEND(ConversionStep(step=LENGTH(steps)+1, current_label, current_subset,
50:                                     a, individual_trans, target_subset, target_label, is_new))
51:     end for
52: end while
53: 
54: // Step 3: Classify Accepting States
55: dfa_final_states ← { L for L, S in label_to_subset.items() if S ∩ F ≠ ∅ }
56: return DFA(states=KEYS(label_to_subset), Σ, dfa_transitions, initial_label, dfa_final_states)"""
    story.append(Preformatted(pseudo_text, code_style))

    story.append(Spacer(1, 4))
    story.append(
        Paragraph(
            "<b>Complexity Bounds</b>: Worst-case time is O(2^|Q| · |Σ| · |Q|), but BFS explores only reachable subsets "
            "|Q'| ≪ 2^|Q| (e.g. for |Q|=10, 2^10 = 1024, but typical practical recognizers have |Q'| ≤ 20). "
            "String simulation runs in linear O(|w|) time on the DFA and O(|w| · |Q|) on the NFA.",
            body_style,
        )
    )
    story.append(Spacer(1, 8))

    # =========================================================================
    # SECTION 5: MANUALLY SOLVED VALIDATION EXAMPLE
    # =========================================================================
    story.append(Paragraph("5. Manually Solved Validation Example & Trace Verification", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=primary_color, spaceAfter=6))

    story.append(
        Paragraph(
            "<b>Problem Specification</b>: Convert the NFA accepting all binary strings ending with <code>'01'</code> "
            "into an equivalent DFA, and verify acceptance on test strings <code>101</code>, <code>110</code>, and <code>ε</code>.",
            body_style,
        )
    )

    nfa_spec_lines = [
        "<b>States Q</b>: {q0, q1, q2} &nbsp;|&nbsp; <b>Alphabet Σ</b>: {0, 1} &nbsp;|&nbsp; <b>Start</b>: q0 &nbsp;|&nbsp; <b>Final F</b>: {q2}",
        "<b>NFA Transitions δ</b>: δ(q0, 0) = {q0, q1}; δ(q0, 1) = {q0}; δ(q1, 1) = {q2}; others = ∅",
    ]
    for nsl in nfa_spec_lines:
        story.append(Paragraph(nsl, body_style))

    story.append(Paragraph("<b>5.1 Step-by-Step Manual Derivation</b>", h2_style))

    deriv_steps = [
        "<b>Step 0 (Initialization)</b>: Initial state S0 = {q0} ⟹ Label <b>A</b> = {q0}. Queue = [A].",
        "<b>Iteration 1 (Process A = {q0})</b>:<br/>"
        "• On symbol 0: δ'(A, 0) = δ(q0, 0) = {q0, q1}. New subset ⟹ Label <b>B</b> = {q0, q1}. Enqueue B.<br/>"
        "• On symbol 1: δ'(A, 1) = δ(q0, 1) = {q0}. Existing subset ⟹ State <b>A</b>.",
        "<b>Iteration 2 (Process B = {q0, q1})</b>:<br/>"
        "• On symbol 0: δ'(B, 0) = δ(q0, 0) ∪ δ(q1, 0) = {q0, q1} ∪ ∅ = {q0, q1}. Existing subset ⟹ State <b>B</b>.<br/>"
        "• On symbol 1: δ'(B, 1) = δ(q0, 1) ∪ δ(q1, 1) = {q0} ∪ {q2} = {q0, q2}. New subset ⟹ Label <b>C</b> = {q0, q2}. Enqueue C.",
        "<b>Iteration 3 (Process C = {q0, q2})</b>:<br/>"
        "• On symbol 0: δ'(C, 0) = δ(q0, 0) ∪ δ(q2, 0) = {q0, q1} ∪ ∅ = {q0, q1}. Existing subset ⟹ State <b>B</b>.<br/>"
        "• On symbol 1: δ'(C, 1) = δ(q0, 1) ∪ δ(q2, 1) = {q0} ∪ ∅ = {q0}. Existing subset ⟹ State <b>A</b>.<br/>"
        "• Queue is empty. BFS terminates.",
    ]
    for ds in deriv_steps:
        story.append(Paragraph(ds, bullet_style))

    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>5.2 Final Accepting States Classification</b>", h2_style))
    story.append(
        Paragraph(
            "An equivalent DFA state is accepting if its constituent subset intersects with NFA final states F = {q2}:<br/>"
            "• State A = {q0} ⟹ {q0} ∩ {q2} = ∅ ⟹ Non-accepting<br/>"
            "• State B = {q0, q1} ⟹ {q0, q1} ∩ {q2} = ∅ ⟹ Non-accepting<br/>"
            "• State C = {q0, q2} ⟹ {q0, q2} ∩ {q2} = {q2} ≠ ∅ ⟹ <b>Accepting (*)</b><br/>"
            "<b>DFA Final States: F' = {C}</b>",
            body_style,
        )
    )

    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>Table 5.1: Complete Converted DFA Transition Matrix</b>", h2_style))

    dfa_table_data = [
        [
            Paragraph("<b>DFA State</b>", table_header),
            Paragraph("<b>Constituent NFA Subset</b>", table_header),
            Paragraph("<b>Input '0'</b>", table_header),
            Paragraph("<b>Input '1'</b>", table_header),
            Paragraph("<b>Accepting Status</b>", table_header),
        ],
        [
            Paragraph("<b>→ A</b>", table_cell),
            Paragraph("{q0}", table_cell),
            Paragraph("B ({q0, q1})", table_cell),
            Paragraph("A ({q0})", table_cell),
            Paragraph("Non-accepting (Start)", table_cell),
        ],
        [
            Paragraph("<b>B</b>", table_cell),
            Paragraph("{q0, q1}", table_cell),
            Paragraph("B ({q0, q1})", table_cell),
            Paragraph("C ({q0, q2})", table_cell),
            Paragraph("Non-accepting", table_cell),
        ],
        [
            Paragraph("<b>C*</b>", table_cell),
            Paragraph("{q0, q2}", table_cell),
            Paragraph("B ({q0, q1})", table_cell),
            Paragraph("A ({q0})", table_cell),
            Paragraph("<b>Accepting (*)</b>", table_cell),
        ],
    ]
    dfa_mat = Table(dfa_table_data, colWidths=[70, 140, 115, 115, 100])
    dfa_mat.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), primary_color),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ])
    )
    story.append(dfa_mat)
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>5.3 String Execution Verification Traces</b>", h2_style))
    trace_explanations = [
        "<b>String 1: w = 101</b> (Should be ACCEPTED):<br/>"
        "• <i>NFA Active States</i>: {q0} ──1──> {q0} ──0──> {q0, q1} ──1──> {q0, q2}*. Final active set contains q2 ∈ F ⟹ <b>ACCEPTED</b>.<br/>"
        "• <i>DFA Traversal</i>: A ──1──> A ──0──> B ──1──> C*. State C ∈ F' ⟹ <b>ACCEPTED</b>.<br/>"
        "• <b>Result</b>: Both accept. Equivalence verified.",
        "<b>String 2: w = 110</b> (Should be REJECTED):<br/>"
        "• <i>NFA Active States</i>: {q0} ──1──> {q0} ──1──> {q0} ──0──> {q0, q1}. No final state in {q0, q1} ⟹ <b>REJECTED</b>.<br/>"
        "• <i>DFA Traversal</i>: A ──1──> A ──1──> A ──0──> B. State B ∉ F' ⟹ <b>REJECTED</b>.<br/>"
        "• <b>Result</b>: Both reject. Equivalence verified.",
        "<b>String 3: w = ε</b> (Empty string ⟹ Should be REJECTED):<br/>"
        "• <i>NFA</i> halts in {q0} ∉ F ⟹ <b>REJECTED</b>. <i>DFA</i> halts in A ∉ F' ⟹ <b>REJECTED</b>.",
    ]
    for te in trace_explanations:
        story.append(Paragraph(te, bullet_style))

    # Build PDF
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated PDF report at: {output_path}")


if __name__ == "__main__":
    target = os.path.join(os.path.dirname(__file__), "NFA_to_DFA_Simulator_Documentation.pdf")
    build_pdf(target)
