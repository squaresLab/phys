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
    def convert_statements(statements: List[Statement]) -> EntryBlock:
        start = BasicBlock(None)
        cur = start

        for stmt in function_declaration.body:
            if stmt.get_type() == "block": # Block statement -> BasicBlock
                basic_block = BasicBlock(stmt.root_token)
                basic_block.previous = [cur]
                cur.next = [basic_block]
                cur = basic_block
            elif stmt.get_type() == "if":
                # Recursively get true/false nodes
                condition_true = ASTToCFG.convert_statements(stmt.condition_true)
                condition_false = ASTToCFG.convert_statements(stmt.condition_false)
                cond_block = ConditionalBlock(smt.condition, condition_true, condition_false)
                
                # Advance true/false nodes until the end
                condition_true_end = traverse_until(condition_true, lambda x: x.next == [])
                condition_false_end = traverse_until(condition_false, lambda x: x.next == [])

                # Connect condition to true/false nodes
                condition_true.previous = [cond_block]
                condition_false.previous = [cond_block]
                cond_block.next = [condition_true, condition_false]
                
                # Connect true/false nodes to join node
                join_block = JoinBlock([condition_true_end, condition_false_end])
                condition_true_end.next = join_block
                condition_false_end.next = join_block
                
                cur = join_block
            elif stmt.get_type() == "while":
                pass
            else:
                raise Error(f"Unexpected statement: {smt.get_type()}")




        return start.next


    @staticmethod
    def convert(dump_file_path: str):
        function_declaration_objs = DumpToAST().convert(dump_file_path)


def traverse_until(node: CFGNode, stop_condition) -> CFGNode:
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