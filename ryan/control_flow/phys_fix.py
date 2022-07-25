from __future__ import annotations

import json
from collections import deque
from typing import Dict, List, Set

import attr

from ast_to_cfg import ASTToCFG, CFGNode, FunctionCFG
from cpp_utils import get_statement_tokens, token_to_stmt_str
from dependency_graph import CFGToDependencyGraph, DependencyGraph


@attr.s()
class Error:
    root_token_id: str = attr.ib()
    error_token_id: str = attr.ib()
    error_type: str = attr.ib()
    DependencyGraph: FunctionCFG = attr.ib(default=None)
    node: CFGNode = attr.ib(default=None)
    root_token = attr.ib(default=None)
    error_token = attr.ib(default=None)

    @staticmethod
    def from_dict(phys_output_path) -> List[Error]:
        output_dict = {}
        with open(phys_output_path) as f:
            output_dict = json.load(f)
        # print(output_dict)
        error_dict = output_dict["errors"]

        error_objs = []
        for e in error_dict:
            error_objs.append(Error(e["root_token_id"], e["token_id"], e["error_type"]))

        return error_objs

@attr.s()
class PhysVar:
    var_name: str = attr.ib()
    var_id: str = attr.ib()
    units: List[Dict] = attr.ib()  # Units sorted by likelihood by Phys

    @staticmethod
    def from_dict(phys_output_path) -> List[PhysVar]:
        output_dict = {}
        with open(phys_output_path) as f:
            output_dict = json.load(f)
        # print(output_dict)
        var_dict = output_dict["variables"]

        phys_var_objs = []
        for v in var_dict:
            var_name = v["var_name"]
            var_id = v["var_id"]

            units = []
            for u in v["units"]:
                if isinstance(u, list):
                    units.append(u[0])
                elif isinstance(u, dict):
                    units.append(u)

            phys_var_objs.append(PhysVar(var_name, var_id, units))

        return phys_var_objs

    @staticmethod
    def create_unit_map(phys_vars: List[PhysVar]) -> Dict[str, PhysVar]:
        unit_map = {}
        for p in phys_vars:
            unit_map[p.var_id] = p
        
        return unit_map


def get_token_unit_map(phys_output_path):
    output_dict = {}
    with open(phys_output_path) as f:
        output_dict = json.load(f)
    # print(output_dict)
    return output_dict["token_units"] 


def get_error_dependency_node(error: Error, dependency_graphs: List[DependencyGraph]):
    """Takes an error and a list of dependency graphs which compsoes a program and returns
    the dependency graph and node at which the error occurs
    """
    for d in dependency_graphs:
        for n in d.nodes:
            if n.cfgnode.get_type() == "basic":
                if n.cfgnode.token.Id == error.root_token_id:
                    error.root_token = n.cfgnode.token
                    for t in get_statement_tokens(error.root_token):
                        if t.Id == error.error_token_id:
                            error.error_token = t
                            break

                    return (d, n)

def get_connected_errors(errors: List[Error], dependency_graphs: List[DependencyGraph]) -> List[Set[Error]]:
    """Returns list of sets of errors which are connected in the dependency graph"""
    for e in errors:
        (d_graph, d_node) = get_error_dependency_node(errors, dependency_graphs)
        e.dependency_graph = d_graph
        e.node = d_node
    
    connected_errors: List[Set[Error]] = []
    seen = set()

    for e in errors:
        if e in seen:
            continue

        q = deque()
        q.append(e)
        connected = set()
        while q:
            cur = q.pop()

            if cur in connected:
                continue

            connected.add(cur)
            seen.add(cur)
            for n in cur.next:
                q.append(n)
            for n in cur.previous:
                q.append(n)

        connected_errors.append(connected)

    return connected_errors


if __name__ == "__main__":
    phys_output = "/home/rewong/phys/src/turtlebot_example_node_output.json"
    dump = "/home/rewong/phys/data/FrenchVanilla/src/turtlebot_example/src/turtlebot_example_node.cpp.dump"

    cfgs = ASTToCFG().convert(dump)
    d_graphs = [CFGToDependencyGraph().create_dependency_graph(c) for c in cfgs]

    e = Error.from_dict(phys_output)
    # print(e)
    e_dependency = get_error_dependency_node(e[0], d_graphs)
    # print(d_graphs[0])
    print(d_graphs[0].get_node_connected_components(e_dependency[1]))
