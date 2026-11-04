# NFA to DFA Conversion Simulator

An interactive, educational web application designed for undergraduate **Automata Theory** and **Theory of Computation** (B.Tech Computer Science & Engineering) course evaluations.

The application allows students, educators, and researchers to formally specify a Non-deterministic Finite Automaton (NFA), validate its structural constraints, convert it into an equivalent Deterministic Finite Automaton (DFA) using the **Subset Construction Algorithm (Rabin-Scott)**, inspect the mathematical derivation step by step, and simulate string acceptance synchronously across both automata.

---

## 1. Problem Statement

In Automata Theory, Non-deterministic Finite Automata (NFAs) allow a system to transition into multiple concurrent states or zero states on a given input symbol. While NFAs simplify formal design and regular expression conversion, physical hardware and software lexical analyzers (like compilers and tokenizers) require deterministic execution where each step is uniquely determined in $O(|w|)$ time.

The **Subset Construction Algorithm** proves that NFAs and DFAs have identical expressive power: for every NFA $M$, there exists an equivalent DFA $M'$ such that $L(M) = L(M')$. However, students often struggle to visualize the powerset exploration, set-union transitions, and trap-state generation. This simulator bridges that gap by providing complete algorithmic transparency, rigorous validation, and side-by-side execution verification.

---

## 2. Key Features

- **Formal NFA Definition**: Full 5-tuple specification ($Q, \Sigma, q_0, F, \delta$) with multi-target transitions.
- **Interactive Transition Table Editor**: Intuitive grid editor using Streamlit data tables supporting single and multi-state targets (e.g. `q0, q1`) or empty transitions (`∅` / `-`).
- **Comprehensive Validation Suite**:
  - Detection of undeclared states or symbols
  - Verification of initial state and accepting states
  - Prevention of malformed or empty definitions
  - Graceful treatment of empty transitions as the empty set ($\emptyset$), not an error
- **Subset Construction Engine**:
  - Breadth-First Search (BFS) using Python's `collections.deque`
  - Reachable-state generation only (avoids $2^{|Q|}$ unnecessary states)
  - Explicit trap state ($\emptyset$) handling with deterministic self-loops for all symbols
  - Set and frozenset representation preventing duplicate subsets
  - Consistent state labeling ($A, B, C, \dots$)
- **Step-by-Step Conversion Derivation**:
  - Detailed table showing Current DFA subset, input symbol, individual transitions $\delta(q, a)$, set unions, and destination DFA state
  - State discovery indicators: *New State Discovered* vs *Existing State Visited*
- **Visual State Diagrams**:
  - Graphviz-rendered directed multigraphs for both NFA and DFA
  - Initial state incoming start arrows
  - Double-circle nodes for accepting states
  - Merged multi-symbol transition edges
- **Synchronous String Simulator**:
  - Test custom input strings or use one-click test suites
  - Simulates both automata simultaneously
  - Displays DFA deterministic traversal path alongside NFA active state sets
  - Formal proof and verification of language equivalence
  - Handles the empty string ($\epsilon$) and flags symbols outside $\Sigma$
- **State Complexity Analysis**:
  - Matplotlib visualization comparing $|Q|$ vs $|Q'|$ vs theoretical powerset bound $2^{|Q|}$.

---

## 3. Technology Stack

- **Language**: Python 3.13 / 3.x
- **Frontend / UI**: Streamlit (Reactive web framework, session-state persistence)
- **Automata Representation**: Python `set`, `frozenset`, `dict`, and `dataclasses`
- **Graph Traversal**: `collections.deque` (FIFO Breadth-First Search)
- **Automata Diagrams**: Graphviz (DOT language generation and rendering)
- **Supporting Visualization**: Matplotlib
- **Testing**: `pytest`
- **Data Tables**: `pandas`

---

## 4. Mathematical Model

### NFA Formal Specification
An NFA is a 5-tuple:
$$M = (Q, \Sigma, \delta, q_0, F)$$
where:
1. $Q$ is a finite non-empty set of states.
2. $\Sigma$ is a finite input alphabet.
3. $\delta: Q \times \Sigma \to 2^Q$ is the transition function mapping a state and symbol to a subset of $Q$.
4. $q_0 \in Q$ is the initial start state.
5. $F \subseteq Q$ is the set of final / accepting states.

### DFA Formal Specification
The equivalent DFA is a 5-tuple:
$$M' = (Q', \Sigma, \delta', q'_0, F')$$
where:
1. $Q' \subseteq 2^Q$ is the set of reachable subsets of $Q$.
2. $\Sigma$ is the identical input alphabet.
3. $q'_0 = \{q_0\}$ is the initial DFA state.
4. $\delta': Q' \times \Sigma \to Q'$ is the deterministic transition function defined as:
   $$\delta'(S, a) = \bigcup_{q \in S} \delta(q, a) \quad \text{for } S \in Q', a \in \Sigma$$
5. $F' = \{S \in Q' \mid S \cap F \neq \emptyset\}$ is the set of accepting DFA states.

---

## 5. Built-in Demonstration Example

The simulator includes a standard benchmark NFA accepting all binary strings ending in `"01"`:

- $Q = \{q_0, q_1, q_2\}$
- $\Sigma = \{0, 1\}$
- $q_0 = q_0$
- $F = \{q_2\}$

**Transition Function ($\delta$):**
- $\delta(q_0, 0) = \{q_0, q_1\}$
- $\delta(q_0, 1) = \{q_0\}$
- $\delta(q_1, 0) = \emptyset$
- $\delta(q_1, 1) = \{q_2\}$
- $\delta(q_2, 0) = \emptyset$
- $\delta(q_2, 1) = \emptyset$

**Resulting Converted DFA:**
- State $A = \{q_0\}$ (Initial)
- State $B = \{q_0, q_1\}$
- State $C = \{q_0, q_2\}$ (Accepting, since $q_2 \in C$)

| DFA State | Subset | On '0' | On '1' | Accepting? |
| :---: | :---: | :---: | :---: | :---: |
| **A** | $\{q_0\}$ | B | A | No |
| **B** | $\{q_0, q_1\}$ | B | C | No |
| **C** | $\{q_0, q_2\}$ | B | A | **Yes (*)** |

**Test String Evaluations:**
- `"01"` $\to$ **Accepted**
- `"101"` $\to$ **Accepted**
- `"001"` $\to$ **Accepted**
- `"10"` $\to$ **Rejected**
- `"111"` $\to$ **Rejected**
- `"010"` $\to$ **Rejected**
- $\epsilon$ (Empty string) $\to$ **Rejected**

---

## 6. Project Architecture

```
nfa-dfa-simulator/
│
├── app.py                      # Main Streamlit application and page controller
├── requirements.txt            # Python dependencies
├── README.md                   # Complete academic documentation
│
├── core/                       # Core automata theory engine
│   ├── __init__.py
│   ├── nfa.py                  # NFA data structure and serialization
│   ├── dfa.py                  # DFA data structure and subset helpers
│   ├── conversion.py           # BFS subset construction engine & trace
│   ├── validation.py           # Formal input validation & error reporting
│   └── simulator.py            # Synchronous string execution & equivalence proof
│
├── visualization/              # Visualization modules
│   ├── __init__.py
│   └── automata_graph.py       # Graphviz DOT generator & Matplotlib plots
│
├── components/                 # Reusable Streamlit UI components
│   ├── __init__.py
│   ├── input_form.py           # NFA 5-tuple input form & transition editor
│   ├── transition_table.py     # Tabular views for NFA and DFA transitions
│   └── conversion_trace.py     # Granular step-by-step conversion tables & cards
│
├── tests/                      # Automated pytest unit test suite
│   ├── test_conversion.py      # Subset construction correctness tests
│   ├── test_validation.py      # Input boundary and error validation tests
│   └── test_simulator.py       # String simulation and 100% equivalence tests
│
└── assets/
    └── style.css               # Clean academic typography & UI styling
```

---

## 7. Installation & Setup

### Prerequisites
- Python 3.9+ (Python 3.11, 3.12, 3.13 supported)
- Graphviz (Optional system package; Streamlit renders DOT diagrams natively)

### Step 1: Clone or Open Project Directory
```bash
cd nfa-dfa-simulator
```

### Step 2: Create a Virtual Environment (Recommended)
```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 8. Running the Application

Launch the Streamlit web application:

```bash
streamlit run app.py
```

The application will automatically open in your default browser at `http://localhost:8501`.

---

## 9. Running Automated Tests

Run the complete automated test suite using `pytest`:

```bash
python -m pytest tests -v
```

All 18 tests cover:
1. Normal subset construction conversion.
2. State label generation ($A, B, \dots$).
3. Multi-branch NFA transitions.
4. Empty subset / trap state self-loop verification.
5. Rejection of undeclared states and symbols in definitions.
6. Acceptance and rejection of test strings across both NFA and DFA.
7. Exhaustive language equivalence verification over 127 generated strings.

---

## 10. Screenshots

*(Placeholders for lab report and presentation evaluations)*

### 1. NFA Configuration & Interactive Transition Editor
```
+-----------------------------------------------------------------------+
|  Set of States (Q): q0, q1, q2     Alphabet (Σ): 0, 1                |
|  Initial State: q0                 Final States (F): q2               |
|                                                                       |
|  Transition Editor Table:                                             |
|  | Current State | Input Symbol | Next States                        |
|  | q0            | 0            | q0, q1                             |
|  | q0            | 1            | q0                                 |
|  | q1            | 0            |                                    |
|  | q1            | 1            | q2                                 |
+-----------------------------------------------------------------------+
```

### 2. Converted DFA Diagram & Step-by-Step Derivation
```
+-----------------------------------------------------------------------+
|  DFA State Transition Diagram:                                        |
|  (start) -> [ A: {q0} ] -- 0 --> [ B: {q0, q1} ]                     |
|                   ^                     |                             |
|                   |-- 1 ----------------+-- 1 --> (( C: {q0, q2} ))   |
|                                                                       |
|  Step 1: δ'(A, 0) = δ(q0, 0) = {q0, q1} = B (New State)               |
|  Step 2: δ'(A, 1) = δ(q0, 1) = {q0}     = A (Existing State)          |
+-----------------------------------------------------------------------+
```

### 3. Dual Automata String Simulator
```
+-----------------------------------------------------------------------+
|  Input String: "101"                                                  |
|  [ RESULT: ACCEPTED - Both NFA and DFA accepted the string ]         |
|                                                                       |
|  DFA Traversal:   A -> A (on 1) -> B (on 0) -> C (on 1) [Accept]      |
|  NFA Active Sets: {q0} -> {q0} -> {q0, q1} -> {q0, q2} [Accept]       |
+-----------------------------------------------------------------------+
```

---

## 11. Current Scope & Future Improvements

### Current Scope (Milestone 1)
- Supports ordinary NFAs without $\epsilon$-transitions.
- Subset Construction with BFS exploration.
- Deterministic DFA generation, state subset mapping, and validation.
- Dual simulation and equivalence testing.

### Planned Milestone 2 Additions
- Support for $\epsilon$-NFAs with $\epsilon$-closure computation.
- DFA state minimization using Hopcroft's or Moore's partitioning algorithm.
- Regular expression to NFA conversion (Thompson's Construction).
- Direct export of converted transition matrices to LaTeX and CSV.
