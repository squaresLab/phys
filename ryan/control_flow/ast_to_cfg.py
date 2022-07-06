from cpp_parser import *
from cpp_utils import *
from typing import *
from dump_to_ast import *
from abc import ABC, abstractmethod


class CFGNode(ABC):
    next: Union[List[CFGNode], None] # IDK if this is how you do abstract attributes
    previous: Union[List[CFGNode], None]

    @abstractmethod
    def get_type:
        raise NotImplementedError

class EntryBlock(CFGNode):
    def __init__(self, function_declaration: FunctionDeclaration):
        """Entry block for a function"""
        self.type = "entry"
        self.function_declaration: function_declaration
        self.next = []
        self.previous = []

class ExitBlock(CFGNode):
    def __init__(self, previous: List[CFGNode]):
        """Entry block for a function"""
        self.type = "exit"
        self.function_declaration: function_declaration
        self.next = []
        self.previous = []

class BasicBlock(CFGNode):
    def __init__(self, root_token: Token):
        """Node for a basic block"""
        self.type = "basic"
        self.tokens = tokens
        self.previous = []
        self.next = []

class ConditionalBlock(CFGNode):
    def __init__(self, condition: Token, condition_true: CFGNode,
    condition_false: CFGNode):
        self.type = "conditional"
        self.condition = condition
        self.condition_true: condition_true
        self.condition_false = condition_false
        self.previous = []
        self.next = []

class JoinBlock(CFGNode):
    def __init__(self, previous: List[CFGNode]):
        self.type = "join"
        self.previous = previous
        self.next = []

class ASTToCFG:
    def __init__(self):
        """Class for converting AST into CFG"""
        pass
    
    @staticmethod
    def convert_statements(statements: List[Statement], call_tree: List[Tuple[str, Statement, Statement]]) -> EntryBlock:
        """
        
        call_tree is order of block calls and each item is tuple of the call + start block of call + the exit/join block of that call
        """
        start = BasicBlock(None) # Sentinel node
        cur = start # Cur node in graph

        for stmt in function_declaration.body:
            if stmt.get_type() == "block": # Block statement -> BasicBlock
                # Make basic block, connect to cur, advance cur
                basic_block = BasicBlock(stmt.root_token)
                basic_block.previous.append(cur)
                cur.next.append(basic_block)
                cur = basic_block
                
                # Walk through AST to check for break/return/continue
                for t in get_statement_tokens(stmt.root_token):
                    if t.str == "break":
                        assert call_tree

                        # Find where to break out of
                        last_while = None
                        for i in range(len(call_tree), -1, -1):
                            if call_tree[i][0] == "while":
                                last_while = call_tree[i]
                                break
                        
                        assert last_while, "Attempted to break with no while"

                        cur.next.append(last_while[2])
                        last_while[2].previous.append(cur)
                        return start
                    elif t.str == "return":
                        assert call_tree
                        block_type, block_exit = call_tree[0]
                        assert block_type == "function", "Attempted to return outside a function"

                        # Connect return statement to function exit block
                        cur.next.append(block_exit)
                        block_exit.previous.append(cur)
                        return start
                    elif t.str == "continue":
                        assert call_tree

                        # Find where to continue to
                        last_while = None
                        for i in range(len(call_tree), -1, -1):
                            if call_tree[i][0] == "while":
                                last_while = call_tree[i]
                                break
                        
                        assert last_while, "Attempted to continue with no while"

                        cur.next.append(last_while[1])
                        last_while[1].previous.append(cur)
                        return start

            elif stmt.get_type() == "if":
                cond_block = ConditionalBlock(smt.condition, None, None)
                join_block = JoinBlock([])
                
                # Recursively get true/false nodes
                condition_true = ASTToCFG.convert_statements(stmt.condition_true, path + [("if", cond_block, join_block)])
                condition_false = ASTToCFG.convert_statements(stmt.condition_false, path + [("if", cond_block, join_block)])
                cond_block.condition_true = condition_true
                cond_block.condition_false = condition_false    
                
                # Advance true/false nodes until the end
                condition_true_end = traverse_until(condition_true, lambda x: x.next == [])
                condition_false_end = traverse_until(condition_false, lambda x: x.next == [])

                # Connect condition to true/false nodes
                condition_true.previous.append(cond_block)
                condition_false.previous.append(cond_block)
                cond_block.next.append(condition_true, condition_false)
                
                # Connect true/false nodes to join node
                join_block.previous.append([condition_true_end, condition_false_end])
                condition_true_end.next.append(join_block)
                condition_false_end.next.append(join_block)
                
                cur = join_block
            elif stmt.get_type() == "while":
                cond_block = ConditionalBlock(smt.condition, None, None)
                join_block = JoinBlock([])
                
                # Recursively get true/false nodes
                condition_true = ASTToCFG.convert_statements(stmt.condition_true, path + [("while", cond_block, join_block)])
                condition_false = ASTToCFG.convert_statements(stmt.condition_false, path + [("while", cond_block, join_block)])
                cond_block.condition_true = condition_true
                cond_block.condition_false
                
                
                # Advance true/false nodes until the end
                condition_true_end = traverse_until(condition_true, lambda x: x.next == [])
                condition_false_end = traverse_until(condition_false, lambda x: x.next == [])

                # Connect condition to true/false nodes
                condition_true.previous.append(cond_block)
                condition_false.previous.append(cond_block)
                cond_block.next.append(condition_true, condition_false)
                
                # Connect true node back to conditional
                condition_true_end.next.append(cond_block)
                cond_block.previous.append(condition_true_end)

                # Connect false node back to join
                join_block.previous.append(cond_false_end)
                condition_false_end.next.append(join_block)
                
                cur = join_block
            else:
                raise Error(f"Unexpected statement: {smt.get_type()}")

        if path and path[0][0] == "function": # If we're in the top level function block
            function_exit_block = path[0][2]
            cur.next.append(function_exit_block)
            function_exit_block.previous.append(cur)

        return start.next


    @staticmethod
    def convert(dump_file_path: str) -> List[EntryBlock]:
        """Takes a dump file path and creates a CFG for each function"""
        function_declaration_objs = DumpToAST().convert(dump_file_path)
        function_CFG = []

        for f in function_declaration_objs:
            entry_block = EntryBlock(f)
            exit_block = ExitBlock([])

            cfg = convert_statements(f.body, [(f.get_type(), exit_block)])
            entry_block.next.append(cfg)

            if cfg:
                cfg.previous.append(entry_block)

            function_CFG.append(entry_block)

        return function_CFG


def traverse_until(node: CFGNode, stop_condition=lambda x: False) -> List[CFGNode]:
    """Traverses nodes of a CFG until stop_condition is met"""
    def traverse(path):
        if stop_condition(path[-1]):
            return path

        for next_node in node.next:
            if next_node in path:
                continue

            res = traverse(path + [next_node])
            if res:
                return res
    
    return traverse([node])
        



if __name__ == "__main__":
    filename = "/home/rewong/phys/data/FrenchVanilla/src/turtlebot_example/src/turtlebot_example_node.cpp.dump"
    d = CppcheckData(filename)
    w = list(get_functions(d.configurations[0]).values())[0]
    print([tokens_to_str([t.astOperand1, t, t.astOperand2]) for t in w["root_tokens"]])
    # print(get_function_statements(w["start_token"], w["end_token"], w["root_tokens"]))
    # z = [tokens_to_str(t) for t in get_function_statements(w["token_start"], w["token_end"], w["root_tokens"])]
    # z = [tokens_to_str(get_statement_tokens(t)) for t in w["root_tokens"]]
    for a in z:
        print(a)
    # print(z)
    # y = construct_function_cfg(w)
    # print(tokens_to_str(y.next.next.next.next.next.tokens))
    # t = []
    # for i in range(15):
    #     t.append(w)
    #     w = w.next
    # print(tokens_to_str(t))
    # for root_t in list(get_functions(d.configurations[0]).values())[0]["root_tokens"]:
    #     print(tokens_to_str(get_statement_tokens(root_t)))
    # print(tokens_to_str(get_statement_tokens(list(get_functions(d.configurations[0]).values())[0]["root_tokens"][0])))