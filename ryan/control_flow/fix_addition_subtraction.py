from __future__ import annotations

import json
from collections import deque
from typing import Dict, List, Set, Union

import attr

from ast_to_cfg import ASTToCFG, CFGNode, FunctionCFG
from cpp_utils import get_LHS_from_statement, get_RHS_from_statement, get_statement_tokens, get_vars_from_statement, token_to_stmt_str
from dependency_graph import CFGToDependencyGraph, DependencyGraph
from phys_fix import Error, PhysVar


def multiply_units(u1: Dict[str, Union[int, float]], u2: Dict[str, Union[int, float]]):
    new_unit = u1.copy()

    for unit_name, unit_expt in u2.items():
        if unit_name in new_unit:
            new_unit[unit_name] += unit_expt
        else:
            new_unit[unit_name] = unit_expt

    return new_unit


def divide_units(u1: Dict[str, Union[int, float]], u2: Dict[str, Union[int, float]]):
    new_unit = u1.copy()

    for unit_name, unit_expt in u2.items():
        if unit_name in new_unit:
            new_unit[unit_name] -= unit_expt
        else:
            new_unit[unit_name] = -1 * unit_expt

    return new_unit


def expt_units(u1: Dict[str, Union[int, float]], power: Union[int, float]):
    new_unit = u1.copy()

    for unit_name in new_unit:
        new_unit[unit_name] *= power

    return new_unit

def fix_addition_subtraction(error: Error, phys_var_map: Dict[str, PhysVar], token_unit_map: Dict[str, Di]):
    error_tokens = get_statement_tokens(error.root_token)
    lhs_tokens = get_LHS_from_statement(error_tokens)
    rhs_tokens = get_RHS_from_statement(error_tokens)
    # 
