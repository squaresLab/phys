from __future__ import annotations

import json
from collections import deque
from typing import Dict, List, Set, Union
import uuid

import attr

from cpp_parser import Token
from ast_to_cfg import ASTToCFG, CFGNode, FunctionCFG
from cpp_utils import get_LHS_from_statement, get_RHS_from_statement, get_statement_tokens, get_vars_from_statement, token_to_stmt_str, tokens_to_str
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
            if unit_expt - u1[unit_name] != 0:
                diff[unit_name] = unit_expt - u1[unit_name]
        else:
            diff[unit_name] = unit_expt

    return diff


def inverse_unit(lhs_unit, token, phys_var_map: Dict[str, PhysVar], token_unit_map: Dict[str, Dict]):
    error_correct_unit = lhs_unit

    cur = token
    while cur.astParent:
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


def make_arithmetic_token(arithmetic_op) -> Token:
    new_token = Token(None)
    new_token.str = arithmetic_op
    new_token.Id = str(uuid.uuid4())
    new_token.isArithmeticalOp = True

    return new_token

def copy_variable_token(var: Variable) -> Token:
    new_token = Token(None)
    new_token.str = var.nameToken.str
    new_token.Id = str(uuid.uuid4())
    new_token.varId = var.Id
    new_token.variableId = var.Id
    new_token.variable = var

    return new_token


def apply_unit_multiplication(token: Token, cur_unit: Dict, target_unit: Dict, phys_var_map, dependency_node, dependency_graph,
                              depth=5):
    """Given a token (t) with a current unit, attempt to transform t to have the target unit by 
    applying the rules t -> t * x or t -> t / x, where x is a variable which reaches t
    """
    # token_unit_diff = unit_diff(target_unit, cur_unit)
    reach_defs = dependency_graph.reach_definition[dependency_node.cfgnode]
    candidate_change_tuples = []

    q = []
    q.append(([], [], cur_unit))  # Tuple of vars to multiply by, vars to divide by, and the current unit difference
    print(cur_unit, target_unit)
    for _ in range(depth):
        new_q = []
        for mult_vars, div_vars, units in q:
            if units == target_unit:
                candidate_change_tuples.append((mult_vars, div_vars))

            for r in reach_defs:
                reach_var = r.variable

                if reach_var.Id not in phys_var_map:
                    continue
                
                reach_units = phys_var_map[reach_var.Id].units[0]

                if not reach_units:
                    continue
                

                if reach_var not in div_vars:
                    multiplication_units = multiply_units(units, reach_units)
                    new_q.append((mult_vars + [reach_var], div_vars, multiplication_units))

                if reach_var not in mult_vars:
                    division_units = divide_units(units, reach_units) 
                    new_q.append((mult_vars, div_vars + [reach_var], division_units))
        
        q = new_q

    for c in candidate_change_tuples:
        print(c)

    # Change tuples into a list of tokens which can be made into a tree later
    symbols_list = []

    for mult_vars, div_vars in candidate_change_tuples:
        symbols = []
        if token.variableId:
            symbols.extend([token.copy(), make_arithmetic_token("*")])

            # Append multiplication symbols
            for i in range(len(mult_vars) - 1):
                symbols.extend([copy_variable_token(mult_vars[i]), make_arithmetic_token("*")])
            
            symbols.append(copy_variable_token(mult_vars[-1]))

            # Append division symbols
            for _, var in enumerate(div_vars):
                symbols.extend([make_arithmetic_token("/"), copy_variable_token(var)])
        else:
            for _, var in enumerate(mult_vars):
                symbols.extend([copy_variable_token(var), make_arithmetic_token("*")])
            
            symbols.extend(get_statement_tokens(token.copy()))

            for _, var in enumerate(div_vars):
                symbols.extend([make_arithmetic_token("/"), copy_variable_token(var)])

        symbols_list.append(symbols)
        print(tokens_to_str(symbols))

    return candidate_change_tuples
    def construct_change_tree(mult_vars, div_vars):
        tree, left, right = None, None, None
        if mult_vars:
            tree = make_arithmetic_token("*")
            left = copy_variable_token(mult_vars[0])
            right = construct_change_tree(mult_vars[1:], div_vars) 
        else:
            tree = make_arithmetic_token("/")
            left = copy_variable_token(div_vars[0])
            right = construct_change_tree(mult_vars[0], div_vars[1:]) 

        tree.astOperand1 = left
        tree.astOperand1Id = left.Id
        left.astParent = tree
        left.astParentId = tree.Id

        
        tree.astOperand2 = right
        tree.astOperand2Id = right.Id
        right.astParent = tree.astParent
        right.astParentId = tree.Id

        return tree

    token_copy = token.copy()
    candidate_changes = []

    for mult_vars, div_vars in candidate_change_tuples:
        # t, a /b -> t * a / b
        if token.varibleId:
            root = make_arithmetic_token("*")
            left = token_copy
            right = construct_change_tree(mult_vars, div_vars)

            root.astOperand1 = left
            root.astOperand1Id = left.Id
            left.astParent = root
            left.astParentId = root.Id

            
            root.astOperand2 = right
            root.astOperand2Id = right.Id
            right.astParent = root.astParent
            right.astParentId = root.Id

            candidate_changes.append(root)
        else:
            root = None
            # t1 * t2, a / b -> t1 * t2 * a / b
            if token.str == "*":
                root = token_copy
                temp_right = token_copy.astOperand2
                right = make_arithmetic_token("*")
                right_right = construct_change_tree(mult_vars, div_vars)

                right.astOperand1 = temp_right
                right.astOperand1Id = temp_right

                temp_right.astParent = right
                temp_right.astParentId = right

                right.astOperand2 = right_right
                right.astOperand2Id = right_right

                right_right.astParent = right
                right_right.astParentId = right.Id

                root.astOperand2 = right
                root.astOperand2 = right.Id

                right.astParent = root
                right.astParentId = root.Id
            # t1 / t2, a / b -> t1 * a / t2 / b
            elif token.str == "/":
                root = make_arithmetic_token("*")
                root_right = construct_change_tree(mult_vars)
                root_left = token_copy.astOperand1

                root.astOperand1 = root_left
                root.astOperand1Id = root_left
                root_left.astParent = root
                root_left.astParentId = root.Id

                root.astOperand2 = root_right
                root.astOperand2Id = root_right.Id
                root_right.astParent = root
                root_right.astParentId = root.Id

                cur = root
                while cur.astOperand2.isArithmeticalOp:
                    cur = cur.astOperand2
                
                temp_right = cur.astOperand2
                right = make_arithmetic_token("*")

                cur.astOperand2 = right
                cur.astOperand2Id = right.Id
                
                right.astOperand1 = temp_right
                right.astOperand1Id = temp_right.Id

                temp_right.astParent = right
                temp_right.astParentId = right.Id
                
                cur = right
                right = make_arithmetic_token("/")
                cur.astOperand2 = right
                cur.astOperand2Id = right.Id

                right.astParent = cur
                right.astParentId = right.Id

                cur = right
                left = token_copy.astOperand2
                right = construct_change_tree(div_vars)

                cur.astOperand1 = left
                cur.astOperand1Id = left.Id
                
                left.astParent = cur
                left.astParentId = cur.Id

                cur.astOperand2 = right
                cur.astOperand2Id = right.Id

                right.astParent = cur
                right.astParentId = cur.Id

            # f(t1), a / b -> f(t1) * a / b
            elif token.str == "(":
                root = construct_change_tree(mult_vars)
                cur = root
                while cur.astOperand2:
                    cur = cur.astOperand2

                left = token_copy()
                right = construct_change_tree(div_vars)

                cur.astOperand1 = left
                cur.astOperand1Id = left.Id
                
                left.astParent = cur
                left.astParentId = cur.Id

                cur.astOperand2 = right
                cur.astOperand2Id = right.Id

                right.astParent = cur
                right.astParentId = cur.Id
            else:
                raise ValueError(f"Unexpecte token {token.str}")

            candidate_changes.append(root)

    return candidate_changes


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
    
    error_left_token = error_token.astOperand1
    error_right_token = error_token.astOperand2
    
    error_left_unit = None
    if error_left_token.variable:
        error_left_unit = phys_var_map[error_left_token.variable.Id].units[0]
    else:
        error_left_unit = token_unit_map[error_left_token.Id]

    error_right_unit = None
    if error_right_token.variable:
        error_right_unit = phys_var_map[error_right_token.variable.Id].units[0]
    else:
        error_right_unit = token_unit_map[error_right_token.Id]

    # Assumes that only one unit is incorrect
    token_to_fix = None
    token_to_fix_unit = None

    cur_token = None
    direction = None
    if error_right_unit != error_correct_unit:
        cur_token = error_right_token
        token_to_fix_unit = error_right_unit
        direction = "left"
    else:
        cur_token = error_left_token
        token_to_fix_unit = error_left_unit
        direction = "right"

    while True:
        if cur_token.varId:
            token_to_fix = cur_token
            break
        elif cur_token.str == "(":
            token_to_fix = cur_token
            break
        elif cur_token.str in ["*", "/"]:
            token_to_fix = cur_token
            break
        elif cur_token.str in ["+", "-"]:
            if direction == "left":
                cur_token = cur_token.astOperand1
            else:
                cur_token = cur_token.astOperand2
        
    # print(token_to_fix)
    apply_unit_multiplication(token_to_fix, token_to_fix_unit, error_correct_unit, phys_var_map, error.dependency_node,
    error.dependency_graph)


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
    # print(g)
    # print(var_unit_map)
