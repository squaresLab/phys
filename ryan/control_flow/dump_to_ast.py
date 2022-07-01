from __future__ import annotations
from abc import ABC, abstractmethod
from cpp_parser import *
from cpp_utils import *
from typing import *
from control_flow import *


class ScopeNode:
    def __init__(self, scope_obj: Scope):
        """Node for a tree of Scopes"""
        self.scope_id: str = scope_obj.Id
        self.scope_obj: Scope = scope_obj
        self.children: List[ScopeNode] = []
        self.parent: Union[ScopeNode, None] = None

    def remove_by_id(self, scope_id: str) -> Bool:
        """Remove subtree where the root has Id == scope_id
        by scope ID

        Returns:
            bool : Whether the node was removed
        """
        for i in range(len(self.children)):
            if self.children[i].scope_id == scope_id:
                self.children.pop(i)
                return True
            
            res = self.children[i].remove_by_id(scope_id)
            if res:
                return True

        return False

    def find_by_id(self, scope_id: str) -> Union[ScopeNode, None]:
        """Finds node by scope_id"""
        if scope_id == self.scope_id:
            return self
        
        for node in self.children:
            res = node.find_by_id(scope_id)

            if res:
                return res

    def find_by_obj(self, scope_obj: Scope) -> Union[ScopeNode, None]:
        """Finds node by scope_obj"""
        return self.find_by_id(scope_obj.scope_id)


    @staticmethod
    def make_scope_tree(cppcheck_config: Configuration, scope_obj: Scope):
        """Creates a scope tree using scopes in cppcheck_config where the 
        root is the scope_obj
        """
        if not scope_obj:
            return None
        
        scope_node = ScopeNode(scope_obj)
        scope_children = []
        # Find nested children
        for i in range(len(cppcheck_config.scopes)):
            s = cppcheck_config.scopes[i]
            if s == scope_node.scope_obj:
                continue

            # Remove try scopes and change the "Else" scope to have the "Try" scope_id
            if s.type == "Else":
                s.Id = cppcheck_config.scopes[i + 1].Id
                cppcheck_config.scopes[i + 1].nestedInId = "-1"

            # If a scope is nested inside of the root node (is a child of root)
            if s.nestedInId == scope_node.scope_id:
                # Recurse
                scope_node_child = ScopeNode.make_scope_tree(cppcheck_config, s)
                if scope_node_child:
                    scope_node_child.parent = scope_obj
                    scope_children.append(scope_node_child)

        scope_node.children = scope_children
        return scope_node

    def copy(self) -> ScopeNode:
        """Creates a deep copy of self"""
        scope_node_copy = ScopeNode(self.scope_obj)

        if scope_node_copy.parent:
            scope_node_copy.parent = self.parent.copy()
        copy_children = []

        for node in self.children:
            copy_children.append(node.copy())
        scope_node_copy.children = copy_children

        return scope_node_copy

class Statement(ABC):
    @abstractmethod
    def get_type(self) -> str:
        return ""

class BlockStatement(Statement):
    def __init__(self, root_token: Token):
        """Class for a single block statement"""
        self.type: str = "block"
        self.root_token: Token = root_token

    def get_type(self) -> str:
        return self.type

class IfStatement(Statement):
    def __init__(self, condition: Token, condition_true: List[Token], 
    condition_false: List[Token]):
        """Class for an if statement"""
        self.type: str = "if"
        self.condition: Token = condition
        self.condition_false: List[Statement] = condition_false
        self.condition_true: List[Statement] = condition_true

    def get_type(self) -> str:
        return self.type

class WhileStatement(Statement):
    def __init__(self, condition: Token, condition_true: List[Token]):
        """Class for a while statement"""
        self.type: str = "while"
        self.condition: Token = condition
        self.condition_true: List[Statement] = condition_true

    def get_type(self) -> str:
        return self.type
        
class ForStatement:
    def __init__(self, condition: Token, condition_true: List[Token]):
        """Class for a for loop"""
        self.type: str = "for"
        self.condition: Token = condition
        self.condition_true: List[Statement] = condition_true

    def for_to_while(self) -> List[BlockStatement, WhileStatement]:
        """Desugars for loop into a while loop"""

        # E.g. int i = 0
        initialize_expr: Token = self.condition.astOperand1
        # E.g. i < 10
        condition_expr: Token = self.condition.astOperand2.astOperand1
        # E.g. i++
        update_expr: token = self.condition.astOperand2.astOperand2

        blocks = []
        blocks.append(BlockStatement(initialize_expr))
        blocks.append(WhileStatement(condition_expr, self.condition_true + [BlockStatement(update_expr)]))

        return blocks

class FunctionDeclaration:
    def __init__(self, name: str, token_start: Token, token_end: Token, scope_obj: Scope, scope_tree: ScopeNode,
    function: str):
        """Class for a function"""
        self.name: str = name
        self.token_start: Token = token_start
        self.token_end: Token = token_end
        self.scope_obj: Scope = scope_obj
        self.scope_tree: ScopeNode = scope_tree
        self.function: str = function
        self.body: List[Statement] = []

class DumpToAST:
    def __init__(self):
        """Class for parsing an Cppcheck XML dump into an AST tree"""
        pass

    @staticmethod
    def convert(dump_file_path: str):
        cpp_check = CppcheckData(dump_file_path)
        cppcheck_config = cpp_check.configurations[0]

        function_declaration_objs = []
        # Loop through all functions in file
        for f in get_functions(cppcheck_config).values():
            func_obj = FunctionDeclaration(f["name"], f["token_start"], f["token_end"], 
            f["scopeObject"], ScopeNode.make_scope_tree(cppcheck_config, f["scopeObject"]),
            f["function"])

            # Get root tokens for all statements inside of function
            root_tokens = get_root_tokens(func_obj.token_start, func_obj.token_end)
            print([tokens_to_str(get_statement_tokens(t)) for t in root_tokens])
            # Parse into AST
            # func_obj.body = parse(root_tokens, func_obj.scope_tree.copy())
            function_declaration_objs.append(func_obj)

        return function_declaration_objs


def parse(root_tokens: List[Token], scope_tree: ScopeNode) -> List[Statement]:
    """Parses root tokens into AST Statement objects"""
    blocks: List[Statement] = []

    while root_tokens:
        t: Token = root_tokens.pop(0)

        # If block
        if t.astOperand1 and t.astOperand1.str == "if":
            # Grab the scope from scope tree
            if_scope = scope_tree.children[0]
            assert if_scope.scope_obj.type == "If"
            # Remove scope from tree so it isn't reused
            scope_tree.remove_by_id(if_scope.scope_id)
            # Find end of scope (denoted by '}')
            if_scope_end = if_scope.scope_obj.classEnd
            # Grab if statement conditional
            conditional_root_token = t.astOperand2

            # Get tokens for true case
            condition_true_root_tokens = []
            # Get tokens that are before the scope end (token Ids are in lexigraphical order)
            while root_tokens and root_tokens[0].Id <= if_scope_end.Id:
                condition_true_root_tokens.append(root_tokens.pop(0))

            # Recursively parse tokens    
            condition_true = parse(condition_true_root_tokens, if_scope)
            
            # Get tokens for false/else case
            condition_false_root_tokens = []
            # Check if Else scope exists and directly follows If scope
            if scope_tree.children and scope_tree.children[0].scope_obj.type == "Else":
                else_scope = scope_tree.children[0]
                else_scope_end = else_scope.scope_obj.classEnd
                scope_tree.remove_by_id(if_scope.scope_id)

                condition_false_root_tokens = []
                while root_tokens and root_tokens[0].Id <= else_scope_end.Id:
                    condition_false_root_tokens.append(root_tokens.pop(0))

            condition_false = []
            if condition_false_root_tokens:
                condition_false = parse(condition_false_root_tokens, else_scope)
            
            blocks.append(IfStatement(conditional_root_token, condition_true, condition_false))
        # While statement
        elif t.astOperand1 and t.astOperand1.str == "while":
            # Grab while scope from tree
            while_scope = scope_tree.children[0]
            assert while_scope.scope_obj.type == "While"
            # Remove while scope from tree
            scope_tree.remove_by_id(while_scope.scope_id)
            # Get end of while scope
            while_scope_end = while_scope.scope_obj.classEnd
            # Get while conditional
            conditional_root_token = t.astOperand2

            # Get code for true case
            condition_true_root_tokens = []
            while root_tokens and root_tokens[0].Id <= while_scope_end.Id:
                condition_true_root_tokens.append(root_tokens.pop(0))
            
            # Parse true case
            condition_true = parse(condition_true_root_tokens, while_scope)

            blocks.append(WhileStatement(conditional_root_token, condition_true))
        # For statement
        elif t.astOperand1 and t.astOperand1.str == "for":
            for_scope = scope_tree.children[0]
            assert for_scope.scope_obj.type == "For"
            scope_tree.remove_by_id(for_scope.scope_id)
            for_scope_end = for_scope.scope_obj.classEnd
            conditional_root_token = t.astOperand2

            # Get code for true case
            condition_true_root_tokens = []
            while root_tokens and root_tokens[0].Id <= for_scope_end.Id:
                condition_true_root_tokens.append(root_tokens.pop(0))
                
            condition_true = parse(condition_true_root_tokens, for_scope)
            for_statement = ForStatement(conditional_root_token, condition_true)
            # Convert for statement into while format
            desugared_for = for_statement.for_to_while()
            blocks.extend(desugared_for)
        # Regular statement
        else:
            blocks.append(BlockStatement(t))

    return blocks


def print_AST(function_body):
    for b in function_body:
        print("_____")
        if b.type == "block":
            print(tokens_to_str(get_statement_tokens(b.root_token)))
        elif b.type == "if":
            print("IF:")
            print(tokens_to_str(get_statement_tokens(b.condition)))
            print("IF TRUE:")
            print_AST(b.condition_true)
            print("IF FALSE:")
            print_AST(b.condition_false)
        elif b.type == "while":
            print("WHILE:")
            print(tokens_to_str(get_statement_tokens(b.condition)))
            print("IF TRUE:")
            print_AST(b.condition_true)
        elif b.type == "for":
            print("FOR:")
            print(tokens_to_str(get_statement_tokens(b.condition)))
            print("DO:")
            print_AST(b.condition_true)

if __name__ == "__main__":
    test_path = "/home/rewong/phys/ryan/control_flow/dump_to_ast_test/test_9.cpp.dump"
    parsed = DumpToAST.convert(test_path)
    # print([x.scope_obj.type for x in parsed[0].scope_tree.children])

    # cur = [parsed[0].scope_tree]
    # while cur:
    #     x = cur.pop(0)
    #     print(x.scope_id)
    #     print([z.scope_id for z in x.children])
    #     cur.extend(x.children)

    # print_AST(parsed[0].body)
    # for b in parsed[0].body:
    #     print("_____")
    #     if b.type == "block":
    #         print(tokens_to_str(get_statement_tokens(b.root_token)))
    #     elif b.type == "if":
    #         print(tokens_to_str(get_statement_tokens(b.condition)))
    #         print(b.condition_true)
            # print(tokens_to_str(get_statement_tokens(b.condition_true)))
            # print(tokens_to_str(get_statement_tokens(b.condition_false)))



    