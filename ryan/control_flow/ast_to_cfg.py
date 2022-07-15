from __future__ import annotations
from cpp_parser import CppcheckData, Token, Scope
from cpp_utils import get_statement_tokens, tokens_to_str, token_to_stmt_str
from dump_to_ast import DumpToAST, FunctionDeclaration, Statement
from typing import List, Union, Set, Tuple
from abc import ABC, abstractmethod
from collections import deque
import attr


# TODO: Create CFG class

# Output to json/yaml
# pip-env

class CFGNode(ABC):
    next: Union[Set[CFGNode], None] # IDK if this is how you do abstract attributes
    previous: Union[Set[CFGNode], None] # Empty set instead of None

    @abstractmethod
    def get_type(self):
        raise NotImplementedError

class FunctionCFG:
    def __init__(self, function_declaration: FunctionDeclaration, entry_block: EntryBlock):
        self.function_declaration = function_declaration
        self.entry_block = entry_block
        self.nodes = set()

        queue = deque()
        queue.append(entry_block)

        while queue:
            cur = queue.pop()
            if cur in self.nodes:
                pass
            
            self.nodes.add(cur)

            for next_node in cur.next:
                queue.append(next_node)


class EntryBlock(CFGNode):
    """Entry block for a function"""    
    def __init__(self, function_declaration: FunctionDeclaration):
        self.type = "entry"
        self.next = set()
        self.previous = set()
        self.function_declaration = function_declaration
        self.function_arguments = list(function_declaration.function.argument.values())

    def get_type(self):
        return "entry"

    def __repr__(self):
        return f"EntryBlock(function_name={self.function_declaration.name})"

@attr.s(eq=False, repr=False)
class ExitBlock(CFGNode):
    """Exit block for a function"""
    function_declaration: FunctionDeclaration = attr.ib()
    next: Set[CFGNode] = attr.ib(factory=set)
    previous: Set[CFGNode] = attr.ib(factory=set)

    def get_type(self):
        return "exit"

    def __repr__(self):
        return f"ExitBlock(function_name={self.function_declaration.name})"

@attr.s(eq=False, repr=False)
class BasicBlock(CFGNode):
    """Node for a basic block"""
    token: Token = attr.ib()
    next: Set[CFGNode] = attr.ib(factory=set)
    previous: Set[CFGNode] = attr.ib(factory=set)

    def get_type(self):
        return "basic"

    def __repr__(self):
        return f"BasicBlock(token='{' '.join(token_to_stmt_str(self.token))}')"


@attr.s(eq=False, repr=False)
class ConditionalBlock(CFGNode):
    """Node for condition block"""
    condition: Token = attr.ib()
    condition_true: CFGNode = attr.ib()
    condition_false: CFGNode = attr.ib()
    next: Set[CFGNode] = attr.ib(factory=set)
    previous: Set[CFGNode] = attr.ib(factory=set)

    def get_type(self):
        return "conditional"

    def __repr__(self):
        return f"ConditionalBlock(condition={token_to_stmt_str(self.condition)}"


@attr.s(eq=False, repr=False)
class JoinBlock(CFGNode):
    next: Set[CFGNode] = attr.ib()
    previous: Set[CFGNode] = attr.ib(factory=set)

    def get_type(self):
        return "join"
    
    def __repr__(self):
        repr_str = "JoinBlock("

        prev_repr_str = []
        for p in self.previous:
            prev_repr_str.append(repr(p))
        
        repr_str = repr_str + ", ".join(prev_repr_str) + ")"
        return repr_str

@attr.s(eq=False, repr=False)
class EmptyBlock(CFGNode):
    next: Set[CFGNode] = attr.ib(factory=set)
    previous: Set[CFGNode] = attr.ib(factory=set)

    def get_type(self):
        return "empty"

    def __repr__(self):
        return "EmptyBlock()"

class ASTToCFG:
    def __init__(self):
        """Class for converting AST into CFG"""
        pass

    @staticmethod
    def convert_traverse(node: CFGNode) -> List[CFGNode]:
        """Traverses nodes of a CFG"""
        if not node:
            return None

        # print("____")

        def traverse(path):
            # print(path)
            if path[-1].next == set():
                return path

            for next_node in path[-1].next:
                if next_node in path:
                    continue

                skip_node = False
                if next_node.get_type() == "basic":
                    # print(tokens_to_str(get_statement_tokens(next_node.token)))
                    for t in tokens_to_str(get_statement_tokens(next_node.token)):
                        if t in ["return", "break", "continue"]:
                            skip_node = True
                            # print("??")
                            break

                if skip_node:
                    continue

                res = traverse(path + [next_node])
                if res:
                    return res

        return traverse([node])
    
    @staticmethod
    def convert_statements(statements: List[Statement], call_tree: List[Tuple[str, Statement, Statement]]) -> EntryBlock:
        """
        
        call_tree is order of block calls and each item is tuple of the call + start block of call + the exit/join block of that call
        """
        sentinel = EmptyBlock() # Sentinel node
        cur = sentinel # Cur node in graph

        # print("____")
        # print(statements)

        for stmt in statements:
            if stmt.get_type() == "block": # Block statement -> BasicBlock
                # Make basic block, connect to cur, advance cur
                basic_block = BasicBlock(stmt.root_token)
                basic_block.previous.add(cur)
                cur.next.add(basic_block)
                cur = basic_block

                # print(tokens_to_str(get_statement_tokens(stmt.root_token)))
                
                # Walk through AST to check for break/return/continue
                for t in get_statement_tokens(stmt.root_token):
                    if t.str == "break":
                        assert call_tree, "No call tree"

                        # Find where to break out of
                        last_while = None
                        for i in range(len(call_tree) - 1, -1, -1):
                            if call_tree[i][0] == "while":
                                last_while = call_tree[i]
                                break
                        
                        assert last_while, "Attempted to break with no while"

                        cur.next.add(last_while[2])
                        last_while[2].previous.add(cur)

                        start = sentinel.next.pop()
                        start.previous.pop()
                        return start
                    elif t.str == "return":
                        assert call_tree, "No call tree"
                        block_type, block_start, block_exit = call_tree[0]
                        assert block_type == "function", "Attempted to return outside a function"

                        # Connect return statement to function exit block
                        cur.next.add(block_exit)
                        block_exit.previous.add(cur)

                        start = sentinel.next.pop()
                        start.previous.pop()
                        return start
                    elif t.str == "continue":
                        assert call_tree, "No call tree"

                        # Find where to continue to
                        last_while = None
                        for i in range(len(call_tree) - 1, -1, -1):
                            if call_tree[i][0] == "while":
                                last_while = call_tree[i]
                                break
                        
                        assert last_while, "Attempted to continue with no while"

                        cur.next.add(last_while[1])
                        last_while[1].previous.add(cur)

                        start = sentinel.next.pop()
                        start.previous.pop()
                        return start

            elif stmt.get_type() == "if":
                cond_block = ConditionalBlock(stmt.condition, None, None)
                cur.next.add(cond_block)
                cond_block.previous.add(cur)
                join_block = JoinBlock(set())

                # Recursively get true/false nodes
                condition_true = ASTToCFG.convert_statements(stmt.condition_true, call_tree + [("if", cond_block, join_block)])
                condition_false = ASTToCFG.convert_statements(stmt.condition_false, call_tree + [("if", cond_block, join_block)])

                cond_block.condition_true = condition_true
                cond_block.next.add(condition_true)
                condition_true.previous.add(cond_block)

                condition_true_end = ASTToCFG.convert_traverse(condition_true)
                if condition_true_end is not None: # is False when breaking/returning
                    condition_true_end = condition_true_end[-1]
                    condition_true_end.next.add(join_block)
                    join_block.previous.add(condition_true_end)

                cond_block.condition_false = condition_false
                cond_block.next.add(condition_false)
                condition_false.previous.add(cond_block)

                condition_false_end = ASTToCFG.convert_traverse(condition_false)
                if condition_false_end is not None:                
                    condition_false_end = condition_false_end[-1]
                    condition_false_end.next.add(join_block)
                    join_block.previous.add(condition_false_end)
                
                cur = join_block
            elif stmt.get_type() == "while":
                cond_block = ConditionalBlock(stmt.condition, None, None)
                cur.next.add(cond_block)
                cond_block.previous.add(cur)
                join_block = JoinBlock(set())

                # Recursively get true/false nodes
                condition_true = ASTToCFG.convert_statements(stmt.condition_true, call_tree + [("while", cond_block, join_block)])
                condition_false = EmptyBlock()

                # Connect true/false to conditional
                cond_block.condition_true = condition_true
                cond_block.next.add(condition_true)
                condition_true.previous.add(cond_block)
                cond_block.condition_false = condition_false
                cond_block.next.add(condition_false)
                condition_false.previous.add(cond_block)

                # Traverse to end of conditionals
                condition_true_end = ASTToCFG.convert_traverse(condition_true)

                if condition_true_end:
                    condition_true_end = condition_true_end[-1]
                    condition_true_end.next.add(cond_block)
                    cond_block.previous.add(condition_true_end)

                condition_false_end = condition_false # End of empty block is just the empty block
                
                # Connect false to join
                condition_false_end.next.add(join_block)
                join_block.previous.add(condition_false_end)

                cur = join_block
            else:
                raise Error(f"Unexpected statement: {smt.get_type()}")

        if call_tree and len(call_tree) == 1 and call_tree[0][0] == "function": # If we're in the top level function block
            function_exit_block = call_tree[0][2]
            cur.next.add(function_exit_block)
            function_exit_block.previous.add(cur)

        if sentinel.next:
            assert len(sentinel.next) == 1, "Too many nodes"

            start = sentinel.next.pop()
            start.previous.pop()
            return start
        
        return EmptyBlock()


    @staticmethod
    def convert(dump_file_path: str) -> List[FunctionCFG]:
        """Takes a dump file path and creates a CFG for each function"""
        function_declaration_objs = DumpToAST().convert(dump_file_path)
        function_CFG = []

        for f in function_declaration_objs:
            entry_block = EntryBlock(f)
            exit_block = ExitBlock(f)

            cfg = ASTToCFG.convert_statements(f.body, [(f.get_type(), entry_block, exit_block)])
            entry_block.next.add(cfg)

            if cfg:
                cfg.previous.add(entry_block)

            function_CFG.append(FunctionCFG(f, entry_block))

        return function_CFG


if __name__ == "__main__":
    e_count = 0
    # test_path = f"/home/rewong/phys/data/romeo_grasper/src/modeledobject.cpp.dump"
    # parsed = ASTToCFG.convert(test_path)
    with open("dump_files.txt") as f:
        for idx, l in enumerate(f.readlines()):
            print(idx)
            try:
                test_path = f"/home/rewong/{l.rstrip()}"
                parsed = ASTToCFG.convert(test_path)
            except Exception as e:
                print(test_path)
                print(e)
                e_count += 1
    
    print(e_count)
    # x = parsed[0].next.pop().next.pop().condition_false.next.pop().previous
    # x = list(list(parsed[0].next)[0].next)[0].condition_true.condition_false.next.pop().next
    # y = list(list(list(parsed[0].next)[0].next)[0].condition_false.next)[0]
    # print(tokens_to_str(get_statement_tokens(x.condition)))
    # print(x)
    # for i in x:
    #     if i.get_type() == "conditional":
    #         for j in i.next:
    #             print(j.next.pop().next.pop().previous, j.get_type())
    # print(tokens_to_str(get_statement_tokens(parsed[0].next.pop().next.pop().next.pop().next.pop().next.pop().next)))

    # print([x.scope_obj.type for x in parsed[0].scope_tree.children])

    # cur = [parsed[0].scope_tree]
    # while cur:
    #     x = cur.pop(0)
    #     print(x.scope_id)
    #     print([z.scope_id for z in x.children])
    #     cur.extend(x.children)

    # print_AST(parsed[0].body)
    # print(parsed[0].body[-1].condition_true[2])
    # print_AST(parsed[0].body[-1].match_true[-1].match_true)
    # for b in parsed[0].body:
    #     print("_____")
    #     if b.type == "block":
    #         print(tokens_to_str(get_statement_tokens(b.root_token)))
    #     elif b.type == "if":
    #         print(tokens_to_str(get_statement_tokens(b.condition)))
    #         print(b.condition_true)
            # print(tokens_to_str(get_statement_tokens(b.condition_true)))
            # print(tokens_to_str(get_statement_tokens(b.condition_false)))
