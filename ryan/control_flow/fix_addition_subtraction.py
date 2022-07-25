from __future__ import annotations

import json
from collections import deque
from typing import Dict, List, Set, Union

import attr

from ast_to_cfg import ASTToCFG, CFGNode, FunctionCFG
from cpp_utils import get_LHS_from_statement, get_RHS_from_statement, get_statement_tokens, get_vars_from_statement, token_to_stmt_str
from dependency_graph import CFGToDependencyGraph, DependencyGraph
from phys_fix import Error, PhysVar, get_error_dependency_node, get_token_unit_map


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


def unit_diff(u1: Dict[str, Union[int, float]], u2: Dict[str, Union[int, float]]):
    """Calculates the unit that u1 would have to be multiplied by to get u2"""
    diff = {}

    for unit_name, unit_expt in u2.items():
        if unit_name in u1:
            diff[unit_name] = unit_expt - u1[unit_name]
        else:
            diff[unit_name] = unit_expt

    return unit_diff


def inverse_unit(lhs_unit, token, phys_var_map: Dict[str, PhysVar], token_unit_map: Dict[str, Dict]):
    error_correct_unit = lhs_unit

    cur = token
    while cur.astParent:
        print(cur.str)
        parent = cur.astParent
        if parent.str == "*":
            other_operand = parent.astOperand1 if parent.astOperand2 == cur else parent.astOperand1

            if other_operand.variable:
                error_correct_unit = multiply_units(error_correct_unit, phys_var_map[other_operand.Id].units)
            else:
                error_correct_unit = multiply_units(error_correct_unit, token_unit_map[other_operand.Id].units)
        elif parent.str == "/":
            other_operand = parent.astOperand1 if parent.astOperand2 == cur else parent.astOperand1

            if other_operand.variable:
                error_correct_unit = divide_units(error_correct_unit, phys_var_map[other_operand.Id].units)
            else:
                error_correct_unit = divide_units(error_correct_unit, token_unit_map[other_operand.Id].units)
        elif parent.str == "(":
            if parent.astOperand1.str == "sqrt":
                error_correct_unit = expt_units(error_correct_unit, 2)
            # Maybe consider pow function in the future?

        cur = parent
    
    return error_correct_unit

def fix_addition_subtraction(error: Error, phys_var_map: Dict[str, PhysVar], token_unit_map: Dict[str, Dict]):
    """Make sure to run get_error_dependency_node on error before this"""
    error_tokens = get_statement_tokens(error.root_token)
    lhs_tokens = get_LHS_from_statement(error_tokens)
    rhs_tokens = get_RHS_from_statement(error_tokens)
    
    # Assume LHS only has one variable
    lhs_var = get_vars_from_statement(lhs_tokens)[0]
    lhs_unit = phys_var_map[lhs_var.Id].units[0]

    # Walk from error token to root token and do inverse operations to find what unit the error var should have
    error_token = error.error_token
    error_correct_unit = inverse_unit(lhs_unit, error_token, phys_var_map, token_unit_map)
    return error_correct_unit
    
    error_left_token = error_token.astOperand1
    error_right_token = error_token.astOperand2
    
    error_left_unit = None
    if error_left_token.variable:
        error_left_unit = phys_var_map[error_left_token.variable.Id].units[0]
    else:
        error_left_unit = token_unit_map[error_left_token.str].units[0]

    error_right_unit = None
    if error_right_token.variable:
        error_right_unit = phys_var_map[error_right_token.variable.Id].units[0]
    else:
        error_right_unit = token_unit_map[error_right_token.str].units[0]

    token_to_fix = error_left_token if error_left_unit != error_correct_unit else error_right_token

    
    

if __name__ == "__main__":
    output = "/home/rewong/phys/src/test_19_output.json"
    dump = "/home/rewong/phys/ryan/control_flow/dump_to_ast_test/test_19.cpp.dump"

    cfgs = ASTToCFG().convert(dump)
    d_graphs = [CFGToDependencyGraph().create_dependency_graph(c) for c in cfgs]

    e = Error.from_dict(output)
    # print(e)
    e_dependency = get_error_dependency_node(e[0], d_graphs)
    phys_vars = PhysVar.from_dict(output)
    var_unit_map = PhysVar.create_unit_map(phys_vars)
    token_unit_map = get_token_unit_map(output)
    g = fix_addition_subtraction(e[0], var_unit_map, token_unit_map)
    print(g)
    # print(var_unit_map)
