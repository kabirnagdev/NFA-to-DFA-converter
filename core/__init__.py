"""
Core automata theory package for NFA to DFA simulator.
Contains NFA, DFA data structures, subset construction algorithm,
validation routines, and simulation engines.
"""

from .nfa import NFA
from .dfa import DFA
from .conversion import SubsetConstructionEngine, ConversionStep, ConversionResult
from .validation import NFAValidator, ValidationResult
from .simulator import (
    AutomataSimulator,
    SimulationResult,
    DFAStep,
    NFAStep,
    ComparisonResult,
)

__all__ = [
    "NFA",
    "DFA",
    "SubsetConstructionEngine",
    "ConversionStep",
    "ConversionResult",
    "NFAValidator",
    "ValidationResult",
    "AutomataSimulator",
    "SimulationResult",
    "DFAStep",
    "NFAStep",
    "ComparisonResult",
]
