from ast_to_cfg import ASTToCFG, FunctionCFG, CFGNode
from typing import Dict, Set
from cpp_parser import Token, Variable
from collections import deque
from cpp_utils import get_statement_tokens, tokens_to_str, get_vars_from_statement, get_LHS_from_statement, get_RHS_from_statement, token_to_stmt_str

def create_def_use_pairs(cfg: FunctionCFG) -> Dict[CFGNode, Dict[str, Set[Variable]]]:
    """Maps every node in CFG to a dictionary containing a def, use pair"""
    def_use_pairs = dict()
    queue = deque([cfg.entry_block])
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
    reach_out: Dict[CFGNode, Set[Tuple[CFGNode, Variable]]] = dict()
    reach: Dict[CFGNode, Set[Tuple[CFGNode, Variable]]] = dict()
    for n in cfg.nodes:
        reach_out[n] = set()
        reach[n] = set()

    def_use_pairs: Dict[CFGNode, Dict[str, Set[Variable]]] = create_def_use_pairs(cfg)

    queue = deque(cfg.nodes)
    while queue:
        cur: CFGNode = queue.pop()
        old_reach_out: Set[Tuple(CFGNode, Variable)] = reach_out[cur]

        for prev in cur.previous:
            reach[cur].update(reach_out[prev])
        
        gen = set()
        kill = set()
        new_reach_out = set()
        if def_use_pairs[cur]["def"]:
            for def_var in def_use_pairs[cur]["def"]:
                gen.add((cur, def_var))
                kill.add(def_var.Id)

            new_reach_out.update(gen)
            if cur.get_type() == "basic":
                if token_to_stmt_str(cur.token) == ['vel_y', '=', '20']:
                    print("~~~")
                    print("HERE")
                    print(kill)
                    print(token_to_stmt_str(cur.token))
            for node, variable in reach[cur]:
                if variable.Id not in kill:
                    new_reach_out.add((node, variable))
                else:
                    if cur.get_type() == "basic":
                        if token_to_stmt_str(cur.token) == ['vel_y', '=', '20']:
                            print("THere")
                            print(token_to_stmt_str(node.token))

            if cur.get_type() == "basic":
                if token_to_stmt_str(cur.token) == ['vel_y', '=', '20']:
                    print("Where")
                    for n, var in new_reach_out:
                        if n.get_type() == "basic":
                            print(f"{token_to_stmt_str(n.token)}: {var.nameToken.str}")
                        elif n.get_type() == "entry":
                            print(f"Entry: {var.nameToken.str}")
        reach_out[cur] = new_reach_out
        if (new_reach_out != old_reach_out):
            queue.extend(cur.next)

    return reach


if __name__ == "__main__":
    cfg = ASTToCFG.convert("/home/rewong/phys/ryan/control_flow/data_dependency_tests/test_1.cpp.dump")
    p = create_def_use_pairs(cfg[0])
    # for k, v in p.items():
    #     if k.get_type() == "basic":
    #         print(token_to_stmt_str(k.token))
    #         print(f"def {[x.nameToken.str for x in v['def']]}")
    #         print(f"use {[x.nameToken.str for x in v['use']]}")

    r = reach_definitions(cfg[0])
    for k, v in r.items():
        if k.get_type() == "basic":
            print("____")
            print(token_to_stmt_str(k.token))
            
            for n, var in v:
                if n.get_type() == "basic":
                    print(f"{token_to_stmt_str(n.token)}: {var.nameToken.str}")
                elif n.get_type() == "entry":
                    print(f"Entry: {var.nameToken.str}")

        
