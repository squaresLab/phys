from cpp_parser import *
from cpp_utils import *
from typing import *
from control_flow import *


class ScopeNode:
    def __init__(self, scope_obj: Scope):
        self.scope_id = scope_obj.Id
        self.scope_obj = scope_obj
        self.children = []
        self.parent = None

    def remove(self, scope_id: str) -> None:
        for i in range(len(self.children)):
            if self.children[i].scope_id == scope_id:
                self.children.pop(i)
                return True
            
            res = self.children[i].remove(scope_id)
            if res:
                return True

        return False

    def find_by_id(self, scope_id: str):
        if scope_id == self.scope_id:
            return self
        
        for node in self.children:
            res = node.find_by_id(scope_id)

            if res:
                return res

    def find_by_obj(self, scope_obj: Scope):
        return self.find_by_id(scope_obj.scope_id)


    @staticmethod
    def make_scope_tree(cppcheck_config: Configuration, scope_obj: Scope):
        if not scope_obj:
            return None
        
        scope_node = ScopeNode(scope_obj)
        scope_children = {}
        for i in range(len(cppcheck_config.scopes)):
            s = cppcheck_config.scopes[i]
            # All Else scopes should have a Try scope directly following that is functionally the same
            if s.type == "Else":
                s.Id = cppcheck_config.scopes[i + 1].Id

            if s.nestedInId == scope_node.scope_id:
                scope_node_child = make_scope_tree(cppcheck_config, s)

                if scope_node_child:
                    scope_node_child.parent = scope_obj
                    scope_children[scope_node_child.scope_id] = scope_node
        
        return scope_node

    def copy(self):
        scope_node_copy = ScopeNode(self.scope_obj)

        if scope_node_copy.parent:
            scope_node_copy.parent = self.parent.copy()
        copy_children = []

        for node in self.children:
            copy_children.append(node.copy())
        scope_node_copy.children = copy_children

        return scope_node_copy


class BlockStatement:
    def __init__(self, root_token: Token):
        self.root_token = root_token

class IfStatement:
    def __init__(self, condition: Token, condition_false: List[Token], 
    condition_true: List[Token]):
        self.condition = condition
        self.condition_false = condition_false
        self.condition_true = condition_true
        

class FunctionDeclaration:
    def __init__(self, name, token_start, token_end, scope_obj, scope_tree,
    function):
        self.name = name
        self.token_start = token_start
        self.token_end = token_end
        self.scope_obj = scope_obj
        self.scope_tree = scope_tree
        self.function = function
        self.body = []

class DumpToAST:
    def __init__(self):
        pass

    @staticmethod
    def convert(dump_file_path: str):
        cpp_check = CppcheckData(dump_file_path)
        cppcheck_config = cpp_check.configurations[0]

        function_declaration_objs = []
        for f in get_functions(cppcheck_config).values():
            func_obj = FunctionDeclaration(f["name"], f["token_start"], f["token_end"], 
            f["scopeObject"], ScopeNode.make_scope_tree(cppcheck_config, f["scopeObject"]),
            f["function"])

            root_tokens = get_root_tokens(func_obj.token_start, func_obj.token_end)
            func_obj.body = parse(root_tokens, func_obj.scope_tree.copy())
            function_declaration_objs.append(func_obj)

        return function_declaration_objs


def parse(root_tokens, scope_tree):
    blocks = []

    while root_tokens:
        t = root_tokens.pop(0)

        # If block
        if t.astOperand1 and t.astOperand1.str == "if":
            if_scope = scope_tree.find_by_id(t.scopeId)
            scope_tree.remove(if_scope)
            if_scope_end = if_scope.scope_obj.classEnd
            conditional_tokens = t.astOperand2

            # Get code for true case
            condition_true_root_tokens = []
            while root_tokens and root_tokens[0].Id <= if_scope_end.Id:
                condition_true_root_tokens.append(root_tokens.pop(0))
                
            condition_true = parse(condition_true_root_tokens, if_scope)

            if scope_tree.children[0].scope_obj.type == "Else":
                else_scope = scope_tree.find_by_id(scope_tree.children[0].scope_id)
                else_scope_end = else_scope.scope_obj.classEnd

                condition_false_root_tokens = []
                while root_tokens and root_tokens[0].Id <= else_scope_end:
                    condition_false_root_tokens.append(root_tokens.pop(0))
            
            condition_false = parse(condition_false_root_tokens, else_scope)
        # Regular statement
        else:
            blocks.append(BlockStatement(t))

    return blocks

if __name__ == "__main__":
    test_path = "/home/rewong/phys/ryan/control_flow/dump_to_ast_test/test_1.cpp.dump"
    parsed = DumpToAST.convert(test_path)
    print(parsed[0].body)

    for b in parsed[0].body:
        print(tokens_to_str(get_statement_tokens(b.root_token)))



    