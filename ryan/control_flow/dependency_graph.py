from ast_to_cfg import ASTToCFG, FunctionCFG, CFGNode
from typing import Dict, Set
from cpp_parser import Token, Variable
from collections import deque

def create_def_use_pairs(cfg: FunctionCFG) -> Dict[CFGNode, Dict[str, Set[Variable]]]:
    """Maps every node in CFG to a dictionary containing a def, use pair"""
    def_use_pairs = dict()
    queue = deque(cfg.entry_block)
    seen = set()

    while queue:
        cur = queue.popleft()

        if cur in seen:
            continue

        cur_type = cur.get_type()
        block_def_use = {"def": set(), "use": set()}

        if cur_type == "entry":
            block_def_use["def"].update(cur.function_arguments)
        elif cur_type == "basic":
            statement = get_statement_tokens(cur.token)
            lhs = get_LHS_from_statement(statement)
            rhs = get_RHS_from_statement(statement)

            if lhs:
                block_def_use["def"].update(get_vars_from_statement(lhs))
            
            block_def_use["use"].update(get_vars_from_statement(rhs))
        elif cur_type == "conditional":
            block_def_use["use"].update(get_vars_from_statement(get_statement_tokens(cur.condition)))
        elif cur_type == "join":
            pass
        elif cur_type == "empty":
            pass
        elif cur_type == "exit":
            pass

        for next_node in cur.next:
            queue.append(next_node)

        seen.add(cur)
        def_use_pairs[cur] = block_def_use

    return def_use_pairs

def reach_definitions(cfg: FunctionCFG):
    reach_out = dict()
    reach = dict()
    for n in cfg.nodes:
        reach_out[n] = set()
        reach[n] = set()

    def_use_pairs = create_def_use_pairs(cfg)

    queue = deque(cfg.nodes)
    while queue:
        cur = queue.pop()
        old_reach_out = reach_out[cur]

        for prev in cur.previous:
            reach[cur].update(reach_out[prev])
        
        gen = (cur, def_use_pairs[cur]["def"])
        kill = gen[1]

        new_reach_out = {gen}
        for node, variable in reach[cur]:
            if variable not in kill:
                new_reach_out.add((node, variable))

        reach_out[cur] = new_reach_out
        if (new_reach_out != old_reach_out):
            queue.extend(cur.next)

    return reach
        
