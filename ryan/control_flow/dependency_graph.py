from __future__ import annotations

from collections import deque
from typing import Dict, List, Optional, Set

import attr

from ast_to_cfg import ASTToCFG, CFGNode, FunctionCFG
from cpp_parser import Variable
from cpp_utils import (get_LHS_from_statement, get_RHS_from_statement,
                       get_statement_tokens, get_vars_from_statement)

# Create dataclass for def-use pair

@attr.s(eq=False)
class DefUsePair:
    """Variables defined/used in a cfg Node"""

    cfgNode: CFGNode = attr.ib()
    define: Set[Variable] = attr.ib(factory=set)
    use: Set[Variable] = attr.ib(factory=set)

def create_def_use_pairs(cfg: FunctionCFG) -> Dict[CFGNode, DefUsePair]:
    """Maps every node in CFG to a dictionary containing a def, use pair"""
    def_use_pairs = {}
    queue = deque([cfg.entry_block])
    seen = set()

    while queue:
        cur = queue.popleft()

        if cur in seen:
            continue

        cur_type = cur.get_type()
        block_def_use = DefUsePair(cur)

        if cur_type == "entry":
            block_def_use.define.update(cur.function_arguments)
        elif cur_type == "basic":
            statement = get_statement_tokens(cur.token)
            lhs = get_LHS_from_statement(statement)
            rhs = get_RHS_from_statement(statement)

            if lhs:
                block_def_use.define.update(get_vars_from_statement(lhs))

            block_def_use.use.update(get_vars_from_statement(rhs))
        elif cur_type == "conditional":
            block_def_use.use.update(get_vars_from_statement(get_statement_tokens(cur.condition)))

        for next_node in cur.next:
            queue.append(next_node)

        seen.add(cur)
        def_use_pairs[cur] = block_def_use

    return def_use_pairs


@attr.s()
class ReachDef:
    """Data class of a variable dn the CFGNode which defines it"""
    def_node: CFGNode = attr.ib()
    variable: Variable = attr.ib()


def reach_definitions(cfg: FunctionCFG) -> Dict[CFGNode, Set[ReachDef]]:
    """Calculates variables that reach a node for all nodes in CFG. Returns a mapping 
    between CFGNodes and ReachNodes.
    """
    reach_out: Dict[CFGNode, Set[ReachDef]] = {}
    reach: Dict[CFGNode, Set[ReachDef]] = {}
    for n in cfg.nodes:
        reach_out[n] = set()
        reach[n] = set()

    def_use_pairs: Dict[CFGNode, DefUsePair] = create_def_use_pairs(cfg)

    queue = deque(cfg.nodes)

    while queue:
        cur: CFGNode = queue.pop()
        old_reach_out: Set[ReachDef] = reach_out[cur]

        reach[cur] = set()
        for prev in cur.previous:
            reach[cur].update(reach_out[prev])

        gen: Set[ReachDef] = set()
        kill: Set[Variable] = set()
        new_reach_out: Dict[CFGNode, Set[ReachDef]] = set()
        if def_use_pairs[cur].define:
            for def_var in def_use_pairs[cur].define:
                gen.add(ReachDef(cur, def_var))
                kill.add(def_var)

            new_reach_out.update(gen)
            for node, variable in reach[cur]:
                if variable not in kill:
                    new_reach_out.add(ReachDef(node, variable))
        else:  # If nothing is defined then then kill and gen are empty sets
            new_reach_out = reach[cur]

        reach_out[cur] = new_reach_out

        if new_reach_out != old_reach_out:
            queue.extend(cur.next)

    return reach


@attr.s()
class DependencyNode:
    cfgnode: CFGNode = attr.ib()
    variable: Variable = attr.ib()
    next: Set[DependencyNode] = attr.ib(factory=set)
    previous: Set[DependencyNode] = attr.ib(factory=set)


def create_dependency_graph(reach_definitions: Dict[CFGNode, Set[ReachDef]], 
                            def_use_pairs: Dict[CFGNode, DefUsePair]) -> List[DependencyNode]:
    # Maps CFGNode to set of ReachDef which represent variables which are used to define other variables
    # in CFGNode
    node_dependency_mapping: Dict[CFGNode, Set[ReachDef]] = {}
    
    # Get all variables which are used to define other variables in each node
    for cur_node, reach_def in reach_definitions.items():
        cur_def = def_use_pairs[cur_node].define
        cur_use = def_use_pairs[cur_node].use
        remove = set()

        if not cur_def:
            continue

        for r in reach_def:
            reach_var = r.variable
            # If the variable is killed by the statement or if variable isn't used in statement
            if reach_var in cur_def or reach_var not in cur_use:
                remove.add(reach_def)

        reach_definitions[cur_node] -= remove

        node_dependency_mapping[cur_node] = reach_definitions[cur_node]

    cfg_dependency_node_mapping = {}  # Maps CFGNode to set of DependencyNodes
    dependency_graph_nodes = []  # All DependencyNodes
    # Create all nodes of dependency graph for all variables in each node
    for cur_node, reach_def in node_dependency_mapping.items():
        cfg_dependency_node_mapping[cur_node] = set()
        cur_def = def_use_pairs[cur_node].define

        for def_var in cur_def:
            d_node = DependencyNode(cur_node, def_var)
            dependency_graph_nodes.append(d_node)
            cfg_dependency_node_mapping[cur_node].add(d_node)

    # Set previous and next nodes for all dependency nodes
    for d in dependency_graph_nodes:
        reach_def = node_dependency_mapping[d.cfgnode]

        for r in reach_def:
            prev = cfg_dependency_node_mapping[r.def_node]
            d.previous.add(prev)
            prev.next = d

    return dependency_graph_nodes


if __name__ == "__main__":
    cfg = ASTToCFG.convert("/home/rewong/phys/ryan/control_flow/data_dependency_tests/test_1.cpp.dump")
    p = create_def_use_pairs(cfg[0])
    # for k, v in p.items():
    #     if k.get_type() == "basic":
    #         print(token_to_stmt_str(k.token))
    #         print(f"def {[x.nameToken.str for x in v['def']]}")
    #         print(f"use {[x.nameToken.str for x in v['use']]}")

    r = reach_definitions(cfg[0])
    # print(r)
    for k, v in r.items():
        print("___")
        print(f"{k}:")
        for (n, var) in v:
            print(n, var)
    # for k, v in r.items():
    #     if k.get_type() == "basic":
    #         print("____")
    #         print(token_to_stmt_str(k.token))
            
    #         for n, var in v:
    #             if n.get_type() == "basic":
    #                 print(f"{token_to_stmt_str(n.token)}: {var.nameToken.str}")
    #             elif n.get_type() == "entry":
    #                 print(f"Entry: {var.nameToken.str}")

        
