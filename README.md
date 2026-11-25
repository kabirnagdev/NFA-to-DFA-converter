# NFA to DFA Interactive Simulator — Milestone 2

An interactive, educational web application for undergraduate **Automata Theory** and **Theory of Computation** courses. It converts Non-deterministic Finite Automata (including ε-NFAs) to equivalent Deterministic Finite Automata using the **Rabin–Scott Subset Construction Algorithm**, with live animated step-by-step visualization.

---

## Milestone 2 Highlights

| Feature | Status |
| :--- | :---: |
| Rabin–Scott Subset Construction (BFS + `frozenset` + `deque`) | ✅ Complete |
| Live animated step-by-step simulator (Play / Pause / Next / Prev / Reset / Speed) | ✅ Complete |
| BFS queue visualization (current / pending / newly discovered / processed) | ✅ Complete |
| Dynamic mathematical breakdown (δ-union formula per step) | ✅ Complete |
| Continuously updating live DFA transition table (pending cells + highlight) | ✅ Complete |
| Animated NFA + partial DFA Graphviz diagrams (synchronized with step) | ✅ Complete |
| ε-NFA support (ε-closure, ε-NFA conversion, separate closure trace) | ✅ Complete |
| String Tester (animated NFA + DFA side-by-side, equivalence verification) | ✅ Complete |
| **63 pytest tests** (27 existing + 36 new edge-case tests) | ✅ 63 / 63 Pass |
| Comprehensive technical documentation | ✅ Complete |
| Educational presets (5 built-in examples including ε-NFA) | ✅ Complete |

---

## 1. Problem Statement

In Automata Theory, NFAs allow multiple concurrent transitions or zero transitions on a single input symbol. While NFAs simplify formal design, deterministic execution requires a DFA. The **Subset Construction Algorithm** proves that for every NFA $M$, there exists an equivalent DFA $M'$ such that $L(M) = L(M')$.

This simulator makes that proof visible: it records `ConversionSnapshot` objects at each BFS micro-step and replays them so users can watch exactly how the algorithm works, step by step.

---

## 2. Features

### Core Algorithm
- Rabin–Scott Subset Construction with BFS (`collections.deque`)
- `frozenset` subset identity guaranteeing zero duplicate states
- Explicit `∅` trap state with self-loops on all symbols
- Epsilon-closure for ε-NFAs: initial state = ε-closure({q₀})
- Complete deterministic DFA from any NFA or ε-NFA input

### Live Simulator (Page 5)
- **Play / Pause** auto-advance with configurable speed (0.4s – 2.5s per step)
- **Next Step / Previous Step** for manual control (true undo via snapshot replay)
- **Reset** to step 1; **End** to jump to the final step
- **Current Execution Panel**: DFA state, NFA subset, input symbol, operation, formula, result, discovery status
- **BFS Queue Visualization**: color-coded chips for current / pending / newly discovered / processed states
- **Mathematical Breakdown**: live `δ(q, a)` individual transitions + union + ε-closure display
- **Live DFA Transition Table**: amber highlight for active row/cell, blue for new states, green for accepting
- **Animated DFA Graph**: partial graph growing step-by-step in real time

### ε-NFA Support
- Checkbox to enable ε-transitions in the input form
- ε-closure computation (iterative BFS, handles cycles)
- Separate ε-closure steps displayed in the mathematical breakdown
- 2 ε-NFA presets: `a*b*` and ε-chain

### String Tester (Page 6)
- Animated character-by-character traversal on both NFA and DFA graphs
- Side-by-side comparison with ACCEPTED / REJECTED banner
- Quick test presets adapted to the current alphabet
- Full execution trace tables for DFA path and NFA active state sets
- Equivalence verification per string

### Algorithm Guide (Page 7)
- NFA and DFA formal definitions
- Transition function formula: $\delta'(S, a) = \bigcup_{q \in S} \delta(q, a)$
- Interactive subset-to-DFA-state example with adjustable multiselect
- Explanations of BFS, frozenset, trap states, and 2ⁿ complexity

---

## 3. Technology Stack

| Component | Technology |
| :--- | :--- |
| Language | Python 3.13 |
| UI Framework | Streamlit ≥ 1.30 |
| Automata Graph | Graphviz 0.21 |
| Supporting Plots | Matplotlib ≥ 3.7 |
| Data Tables | Pandas ≥ 2.0 |
| Testing | pytest ≥ 8.0 |

---

## 4. Mathematical Model

### NFA Formal Specification
$$M = (Q, \Sigma, \delta, q_0, F)$$

### DFA Formal Specification
$$M' = (Q', \Sigma, \delta', q'_0, F')$$

### Transition Function
$$\delta'(S, a) = \bigcup_{q \in S} \delta(q, a)$$

For ε-NFAs:
$$\delta'(S, a) = \varepsilon\text{-closure}\!\left(\bigcup_{q \in S} \delta(q, a)\right)$$

### Accepting States
$$F' = \{ S \in Q' \mid S \cap F \neq \emptyset \}$$

### Complexity
- **Worst case**: $\Theta(2^n)$ DFA states for an $n$-state NFA.
- **BFS exploration**: Only reachable subsets are ever constructed, so $|R| \ll 2^n$ in practice.
- **Time**: $O(|R| \cdot |\Sigma| \cdot n)$ where $|R|$ = reachable DFA states.

---

## 5. Built-in Demonstration Presets

| Preset | Language | Type |
| :--- | :--- | :--- |
| **Demo: Strings ending in '01'** | $\{w \in \{0,1\}^* \mid w \text{ ends with } 01\}$ | Ordinary NFA |
| **Second symbol is 'a'** | $\{w \in \{a,b\}^* \mid |w| \geq 2 \wedge w[1] = a\}$ | Ordinary NFA |
| **Strings containing '010'** | $\{w \in \{0,1\}^* \mid 010 \in w\}$ | Ordinary NFA (4 states) |
| **ε-NFA: a\* followed by b\*** | $a^* b^*$ | ε-NFA |
| **ε-NFA: ε-chain** | All strings over `{a,b}` | ε-NFA (ε-closure demo) |

---

## 6. Project Architecture

```
nfa-dfa-simulator/
│
├── app.py                      # Streamlit page controller (7 pages)
├── requirements.txt            # Dependencies
├── README.md                   # This file
│
├── core/                       # Algorithmic engine (pure Python, no UI)
│   ├── nfa.py                  # NFA model, epsilon_closure()
│   ├── dfa.py                  # DFA model, state_subsets mapping
│   ├── conversion.py           # SubsetConstructionEngine, ConversionStep, ConversionSnapshot
│   ├── validation.py           # NFAValidator, ValidationResult
│   └── simulator.py            # AutomataSimulator: NFA/DFA string simulation & comparison
│
├── visualization/
│   └── automata_graph.py       # Graphviz DOT generators (NFA, DFA, partial DFA)
│
├── components/
│   ├── input_form.py           # NFA 5-tuple form, presets, validation triggers
│   ├── transition_table.py     # NFA/DFA tables + live HTML DFA table
│   └── conversion_trace.py     # Live simulator: controls, panels, math, graphs
│
├── tests/
│   ├── conftest.py             # Shared pytest fixtures
│   ├── test_conversion.py      # 9 core algorithm tests
│   ├── test_epsilon.py         # 4 ε-NFA tests (incl. 63-string bounded equivalence)
│   ├── test_simulator.py       # 5 string simulation tests (incl. 127-string exhaustive)
│   ├── test_validation.py      # 9 validation boundary tests
│   └── test_edge_cases.py      # 36 Milestone 2 edge-case tests
│
├── docs/
│   └── SYSTEM_DOCUMENTATION.md  # Full academic report
│
└── assets/
    └── style.css               # Academic UI styling (navy + white + blue)
```

---

## 7. Installation & Setup

### Prerequisites
- Python 3.9+ (tested on 3.13)
- Graphviz (Streamlit renders DOT natively — optional system install)

### Quick Start
```bash
# 1. Clone repository
git clone https://github.com/kabirnagdev/NFA-to-DFA-converter
cd NFA-to-DFA-converter

# 2. Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
streamlit run app.py
```

The application opens at `http://localhost:8501`.

---

## 8. Running Tests

```bash
python -m pytest tests/ -v
```

**Expected output: 63 tests, 100% pass rate.**

| Test File | Tests | Coverage |
| :--- | :---: | :--- |
| `test_conversion.py` | 9 | Core algorithm, trap state, unreachable states, label generation, snapshots |
| `test_epsilon.py` | 4 | ε-closure chains/cycles, ε-NFA conversion, 63-string bounded equivalence |
| `test_simulator.py` | 5 | String tests, invalid symbols, 127-string exhaustive equivalence |
| `test_validation.py` | 9 | Missing states, undeclared symbols, empty definitions |
| `test_edge_cases.py` | 36 | Multiple transitions, trap state, duplicate subsets, accepting states, alphabet sizes, snapshot integrity, 5-state NFA |

> **Note on exhaustive testing**: Equivalence between NFA and DFA is verified on *all* strings up to a stated length, not just selected examples. For the standard NFA (3 states, binary alphabet), all 255 binary strings up to length 7 are tested. For ε-NFA (`a*b*`), all 63 strings over `{a,b}` up to length 5 are tested.

---

## 9. How to Use (Demo Guide)

1. **Overview page** — Click "Demo: Ends with '01'" to load the standard example.
2. **Live Simulator (Page 5)** — Press ▶ Play and watch the BFS algorithm execute:
   - Current Execution Panel shows the exact operation being computed.
   - BFS Queue updates after each step.
   - Mathematical Breakdown shows each `δ(q, a)` individually.
   - Live DFA Table adds rows and fills cells as they are computed.
   - DFA Graph grows state by state.
3. **String Tester (Page 6)** — Enter `101` and press Run Test to see side-by-side animated traversal.
4. **NFA Setup (Page 2)** — Build a custom NFA or load any of the 5 presets.
5. **How the Algorithm Works (Page 7)** — Interactive math reference for viva preparation.

---

## 10. Viva Reference

**What is a trap state?**
When the union $\bigcup_{q \in S} \delta(q, a) = \emptyset$, the NFA has no valid successor. In a DFA every transition must be defined, so $\emptyset$ becomes an explicit non-accepting state that loops to itself on every symbol.

**Why `frozenset`?**
A Python `frozenset` is immutable and hashable, allowing $O(1)$ average-time lookup in the `subset_to_label` dictionary to detect whether a subset has already been assigned a DFA state label.

**Why BFS (`collections.deque`)?**
BFS explores reachable subsets level by level from $\{q_0\}$, avoiding the full $2^n$ powerset enumeration. In practice only reachable subsets $R \subseteq \mathcal{P}(Q)$ are ever created.

**Why can the DFA reach $2^n$ states?**
Every subset of $Q$ can in principle become a reachable DFA state. The classical worst case is the language of binary strings whose $n$-th symbol from the end is `1`.
