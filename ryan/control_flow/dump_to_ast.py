"""Converting cppcheck dump files into AST Statements objects"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Union, Set, Dict, Optional
import json
import yaml

from cpp_parser import CppcheckData, Token, Scope, Configuration
from cpp_utils import get_statement_tokens, tokens_to_str

import attr


def get_root_tokens(token_start: Token, token_end: Token) -> List[Token]:
    """ Takes the start and end tokens for a function and finds the root tokens
    of all statments in the function.
    """
    root_tokens_set: Set[Token] = set()
    current_token: Union[Token, None] = token_start

    while current_token is not None and current_token != token_end:  #todo: reverse token set exploration to top-down instead of bottom-up
        # HAS A PARENT
        if current_token.astParent: 
            token_parent = current_token.astParent
            has_parent = True
            while has_parent:
                # HAS NO PARENT, THEREFORE IS ROOT
                if not token_parent.astParent:
                    root_tokens_set.add(token_parent)
                    token_parent.isRoot = True  # THIS PROPERTY IS A CUSTOM NEW PROPERTY
                    has_parent = False
                else:
                    token_parent = token_parent.astParent
        current_token = current_token.next

    root_tokens = list(root_tokens_set)
    # SORT NUMERICALLY BY LINE NUMBER
    root_tokens = sorted(root_tokens, key=lambda x: int(x.linenr))
    return root_tokens


# This is needed since not all tokens in a statment are children of the root token for some reason
def get_function_statements(start_token: Token, end_token: Token, root_tokens: List[Token]) -> List[List[Token]]:
    """Takes the start and end tokens of a function and a list of the root tokens
    of the statments in a funciton and returns all of the tokens of each statment.
    """
    function_statements = [get_statement_tokens(t) for t in root_tokens]

    for i, statement in enumerate(function_statements):
        cur = statement[-1].next
        statement_end = None

        if i == len(function_statements) - 1:
            statement_end = end_token.previous
        else:
            statement_end = function_statements[i + 1][0]

        while cur and cur != statement_end:
            statement.append(cur)
            cur = cur.next

    return function_statements


def get_functions(cppcheck_config: Configuration) -> Dict[str, Dict]:
    """Retrieves function information from Cppcheck Config obj."""
    function_dicts: Dict[str, Dict] = {}

    # FIND FUNCTIONS IN "SCOPES" REGION OF DUMP FILE, START AND END TOKENs
    for s in cppcheck_config.scopes:
        if s.type == "Function":
            # SCAN ALL FUNCTIONS UNLESS LIST OF FUNCTIONS SPECIFIED
            function_dicts[s.Id] = {"name": s.className,
                                    "linern": s.classStart.linenr,
                                    "token_start": s.classStart,
                                    "token_end": s.classEnd,
                                    "scopeObject": s,
                                    "scopes": [],
                                    "symbol_table": {},
                                    "function_graph_edges": [],
                                    "function": s.function}
            # CONSTRUCT LIST OF ROOT TOKENS
            function_dicts[s.Id]["root_tokens"] = get_root_tokens(s.classStart, s.classEnd)

    return function_dicts


def get_function_scopes(cppcheck_config: Configuration, function_scope_id: str) -> List[Scope]:
    """Takes a function and returns a list of scopes nested within that function.
    """
    nested_scopes: List[Scope] = []
    for s in cppcheck_config.scopes:
        if s.nestedIn == function_scope_id:
            nested_scopes.append(s)

    return nested_scopes


class ScopeNode:
    """Node for a tree of Scopes"""
    def __init__(self, scope_obj: Scope):
        self.scope_id: str = scope_obj.Id
        self.scope_obj: Scope = scope_obj
        self.children: List[ScopeNode] = []
        self.parent: Union[ScopeNode, None] = None

    def remove_by_id(self, scope_id: str) -> bool:
        """Remove subtree where the root has Id == scope_id
        by scope ID

        Returns:
            bool : Whether the node was removed
        """
        for i, children in enumerate(self.children):
            if children.scope_id == scope_id:
                self.children.pop(i)
                return True

            res = children.remove_by_id(scope_id)
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

        return None

    def find_by_obj(self, scope_obj: Scope) -> Union[ScopeNode, None]:
        """Finds node by scope_obj"""
        return self.find_by_id(scope_obj.Id)

    @staticmethod
    def make_scope_tree(cppcheck_config: Configuration, scope_obj: Scope):
        """Creates a scope tree using scopes in cppcheck_config where the
        root is the scope_obj
        """
        if not scope_obj:
            return None

        scope_node: ScopeNode = ScopeNode(scope_obj)
        scope_children: List[ScopeNode] = []
        # Find nested children
        for i, s in enumerate(cppcheck_config.scopes):
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

        if scope_node_copy.parent is not None:
            scope_node_copy.parent = self.parent.copy()
        copy_children = []

        for node in self.children:
            copy_children.append(node.copy())
        scope_node_copy.children = copy_children

        return scope_node_copy


class Statement(ABC):
    """Abstract base class for AST statements"""

    @abstractmethod
    def get_type(self) -> str:
        """Returns statement type"""
        raise NotImplementedError

    def to_dict(self) -> Dict:
        """Serializes statement to dictionary"""
        raise NotImplementedError

@attr.s(repr=False)
class BlockStatement(Statement):
    """Single block statement"""
    root_token: Token = attr.ib()

    def get_type(self) -> str:
        return "block"

    def to_dict(self) -> Dict:
        return {self.get_type(): repr(self.root_token)}

    def __repr__(self):
        return f"BasicStatement(root_token='{repr(self.root_token)}')"

@attr.s(repr=False)
class IfStatement(Statement):
    """If statement"""
    condition: Token = attr.ib()
    condition_true: List[Statement] = attr.ib()
    condition_false: List[Statement] = attr.ib()

    def get_type(self) -> str:
        return "if"

    def to_dict(self) -> Dict:
        if_dict = {
            self.get_type(): {
                "condition": repr(self.condition),
                "condition_true": [s.to_dict() for s in self.condition_true],
                "condition_false": [s.to_dict() for s in self.condition_false]
            }
        }

        return if_dict

    def __repr__(self):
        return f"IfStatement(condition='{repr(self.condition)}'"

@attr.s(repr=False)
class WhileStatement(Statement):
    """While statement"""
    condition: Token = attr.ib()  # Conditional
    condition_true: List[Statement] = attr.ib()  # While block

    def get_type(self) -> str:
        return "while"

    def to_dict(self) -> Dict:
        while_dict = {
            self.get_type(): {
                "condition": repr(self.condition),
                "condition_true": [s.to_dict() for s in self.condition_true]
            }
        }

        return while_dict

@attr.s()
class ForStatement(Statement):
    """For loop (all for loops should be desugared to while using .desugar)"""
    condition: Token = attr.ib()  # Conditional
    condition_true: List[Statement] = attr.ib()  # For block

    def get_type(self):
        return "for"

    def desugar(self) -> List[Union[BlockStatement, WhileStatement]]:
        """Desugars for loop into a while loop"""

        # E.g. int i = 0
        initialize_expr: Token = self.condition.astOperand1
        # E.g. i < 10
        condition_expr: Token = self.condition.astOperand2.astOperand1
        # E.g. i++
        update_expr: Token = self.condition.astOperand2.astOperand2

        blocks = []
        blocks.append(BlockStatement(initialize_expr))
        blocks.append(WhileStatement(condition_expr, self.condition_true + [BlockStatement(update_expr)]))

        return blocks

    def to_dict(self) -> Dict:
        raise ValueError("Desugar for into while")


@attr.s()
class SwitchStatment(Statement):
    """Switch statements represented as linked list (should be desugared into if statements)"""
    switch_expr: Token = attr.ib()
    match_expr: Token = attr.ib()  # Case for single switch expression
    match_true: List[Statement] = attr.ib()  # Code executed if switch case matches
    has_break: bool = attr.ib(init=False, default=False)  # Whether case terminates with break
    is_default: bool = attr.ib(init=False, default=False)  # Whether this is a default case
    previous: Optional[SwitchStatment] = attr.ib(init=False, default=None)  # Previous node in LL
    next: Optional[SwitchStatment] = attr.ib(init=False, default=None)  # Next node in LL

    def _add_breaks(self):
        """Converts self into switch statements where every node has a break"""
        # Convert switch statements so every switch has a break
        cur_switch: SwitchStatment = self  # Last node in LL
        while cur_switch.next: 
            cur_switch = cur_switch.next

        cur_switch.has_break = True
        cur_switch = cur_switch.previous
        while cur_switch:
            if not cur_switch.has_break:
                cur_switch.match_true.extend(cur_switch.next.match_true)

            cur_switch = cur_switch.previous

    def _switch_to_if_else(self) -> IfStatement:
        """Converts a switch to an if/else. MUST run _add_breaks before"""
        equals_token: Token = Token(None)  # Hopefully this doesn't become a problem
        equals_token.str = "=="
        equals_token.astOperand1 = self.switch_expr
        equals_token.astOperand2 = self.match_expr
        condition_true: List[Statement] = self.match_true[:-1]  # Last token is break/continue/pass which should be excluded
        condition_false = []

        if self.next:
            if self.next.is_default:
                condition_false = self.next.match_true
            else:
                condition_false = [self.next._switch_to_if_else()]

        if_statement = IfStatement(equals_token, condition_true, condition_false)

        return if_statement

    def desugar(self) -> IfStatement:
        """Desugars switch into if/else statements"""
        self._add_breaks()
        return self._switch_to_if_else()

    def get_type(self) -> str:
        return "switch"

    def to_dict(self) -> Dict:
        raise ValueError("Desugar switch to if")


@attr.s()
class FunctionDeclaration(Statement):
    """Function declaration"""
    name: str = attr.ib()
    token_start: Token = attr.ib()
    token_end: Token = attr.ib()
    scope_obj: Scope = attr.ib()
    scope_tree: ScopeNode = attr.ib()
    function: str = attr.ib()
    body: List[Statement] = attr.ib(init=False, factory=list)

    def get_type(self):
        return "function"

    def to_dict(self) -> Dict:
        function_dict = {
            self.get_type(): {
                "name": self.name,
                "body": [s.to_dict() for s in self.body]
            }
        }

        return function_dict


class DumpToAST:
    """Class for parsing an Cppcheck XML dump into an AST tree"""
    def __init__(self):
        pass

    @staticmethod
    def convert(dump_file_path: str) -> List[FunctionDeclaration]:
        """Converts contents of a cppcheck .dump into an AST"""
        cpp_check = CppcheckData(dump_file_path)
        cppcheck_config = cpp_check.configurations[0]

        function_declaration_objs = []
        # Loop through all functions in file
        for f in get_functions(cppcheck_config).values():
            func_obj = FunctionDeclaration(f["name"], f["token_start"], f["token_end"], 
                                           f["scopeObject"], 
                                           ScopeNode.make_scope_tree(cppcheck_config, f["scopeObject"]),
                                           f["function"])

            # Get root tokens for all statements inside of function
            root_tokens = get_root_tokens(func_obj.token_start, func_obj.token_end)
            # print([tokens_to_str(get_statement_tokens(t)) for t in root_tokens])
            # Parse into AST
            func_obj.body = parse(root_tokens, func_obj.scope_tree.copy())
            function_declaration_objs.append(func_obj)

        return function_declaration_objs

    @staticmethod
    def write(function_declaration_objs: List[FunctionDeclaration], file_name: str, serialize_format="yaml"):
        """Serializes FunctionDeclaration objects to yaml/json"""
        objs_dict: List[Dict] = [f.to_dict() for f in function_declaration_objs]

        if serialize_format == "yaml":
            with open(file_name, "w", encoding="utf-8") as f:
                yaml.dump(objs_dict, f)
        elif serialize_format == "json":
            with open(file_name, "w", encoding="utf-8") as f:
                json.dump(objs_dict, f)
        else:
            raise ValueError("Format should be json or yaml")


def parse(root_tokens: List[Token], scope_tree: ScopeNode) -> List[Statement]:
    """Parses root tokens into AST Statement objects"""
    blocks: List[Statement] = []

    while root_tokens:
        t: Token = root_tokens.pop(0)

        # If block
        if t.astOperand1 and t.astOperand1.str == "if":
            # Grab the scope from scope tree
            if_scope: ScopeNode = scope_tree.children[0]
            assert if_scope.scope_obj.type == "If", f"Expected if scope, got {if_scope.scope_obj.type}"
            # Remove scope from tree so it isn't reused
            scope_tree.remove_by_id(if_scope.scope_id)
            # Find end of scope (denoted by '}')
            if_scope_end: Token = if_scope.scope_obj.classEnd
            # Grab if statement conditional
            conditional_root_token = t.astOperand2

            # Get tokens for true case
            condition_true_root_tokens: List[Token] = []

            # Get tokens that are before the scope end
            cur_token: Token = if_scope.scope_obj.classStart
            while root_tokens and cur_token.Id != if_scope_end.Id:
                if cur_token.Id == root_tokens[0].Id:
                    condition_true_root_tokens.append(root_tokens.pop(0))

                cur_token = cur_token.next

            # Recursively parse tokens
            condition_true: List[Statement] = parse(condition_true_root_tokens, if_scope)

            # Check backwards in scope for break/continue
            break_continue_token = None
            cur_token: Token = if_scope_end
            while cur_token and cur_token.scopeId == if_scope_end.scopeId:
                if cur_token.str in ["break", "continue"]:
                    break_continue_token = cur_token
                    break  # Haha get it?

                cur_token = cur_token.previous

            if break_continue_token:
                # Assumed that break/continue is always at the end of a statement
                condition_true.append(BlockStatement(break_continue_token))

            # Get tokens for false/else case
            condition_false_root_tokens: List[Token] = []
            # Check if Else scope exists and directly follows If scope
            if scope_tree.children and scope_tree.children[0].scope_obj.type == "Else":
                else_scope: ScopeNode = scope_tree.children[0]
                else_scope_end: Token = else_scope.scope_obj.classEnd
                scope_tree.remove_by_id(if_scope.scope_id)

                condition_false_root_tokens: List[Token] = []

                cur_token: Token = else_scope.scope_obj.classStart
                while root_tokens and cur_token.Id != else_scope_end.Id:
                    if cur_token.Id == root_tokens[0].Id:
                        condition_false_root_tokens.append(root_tokens.pop(0))

                    cur_token = cur_token.next

                # Check backwards in scope for break/continue
                break_continue_token = None
                cur_token: Token = else_scope_end
                while cur_token and cur_token.scopeId == else_scope_end.scopeId and cur_token.Id != else_scope_end.Id:
                    if cur_token.str in ["break", "continue"]:
                        break_continue_token = cur_token
                        break  # Haha get it?

                    cur_token = cur_token.previous

                if break_continue_token:
                    # Assumed that break/continue is always at the end of a statement
                    condition_false_root_tokens.append(BlockStatement(break_continue_token))

            condition_false: List[Statement] = []
            if condition_false_root_tokens:
                condition_false = parse(condition_false_root_tokens, else_scope)

            blocks.append(IfStatement(conditional_root_token, condition_true, condition_false))
        # While statement
        elif t.astOperand1 and t.astOperand1.str == "while":
            # Grab while scope from tree
            while_scope: ScopeNode = scope_tree.children[0]
            assert while_scope.scope_obj.type == "While", f"Expected while scope, got {while_scope.scope_obj.type}"
            # Remove while scope from tree
            scope_tree.remove_by_id(while_scope.scope_id)
            # Get end of while scope
            while_scope_end: Token = while_scope.scope_obj.classEnd
            # Get while conditional
            conditional_root_token = t.astOperand2

            # Get code for true case
            condition_true_root_tokens: List[Token] = []

            cur_token: Token = while_scope.scope_obj.classStart
            while root_tokens and cur_token.Id != while_scope_end.Id:
                if cur_token.Id == root_tokens[0].Id:
                    condition_true_root_tokens.append(root_tokens.pop(0))

                cur_token = cur_token.next

            # Parse true case
            condition_true: List[Statement] = parse(condition_true_root_tokens, while_scope)

            # Check backwards in scope for break/continue
            break_continue_token = None
            cur_token: Token = while_scope_end
            while cur_token and cur_token.scopeId == while_scope_end.scopeId:
                if cur_token.str in ["break", "continue"]:
                    break_continue_token = cur_token
                    break  # Haha get it?

                cur_token = cur_token.previous

            if break_continue_token:
                # Assumed that break/continue is always at the end of a statement
                condition_true.append(BlockStatement(break_continue_token))

            blocks.append(WhileStatement(conditional_root_token, condition_true))
        # For statement
        elif t.astOperand1 and t.astOperand1.str == "for":
            for_scope: ScopeNode = scope_tree.children[0]
            assert for_scope.scope_obj.type == "For", f"Expected for scope, got {for_scope.scope_obj.type}"
            scope_tree.remove_by_id(for_scope.scope_id)
            for_scope_end: Token = for_scope.scope_obj.classEnd
            conditional_root_token: Token = t.astOperand2

            # Get code for true case
            condition_true_root_tokens: List[Token] = []
            cur_token: Token = for_scope.scope_obj.classStart
            while root_tokens and cur_token.Id != for_scope_end.Id:
                if cur_token.Id == root_tokens[0].Id:
                    condition_true_root_tokens.append(root_tokens.pop(0))

                cur_token = cur_token.next

            condition_true: List[Statement] = parse(condition_true_root_tokens, for_scope)
            for_statement = ForStatement(conditional_root_token, condition_true)

            # Check backwards in scope for break/continue
            break_continue_token = None
            cur_token: Token = for_scope_end
            while cur_token and cur_token.scopeId == for_scope_end.scopeId:
                if cur_token.str in ["break", "continue", "pass"]:
                    break_continue_token = cur_token
                    break  # Haha get it?

                cur_token = cur_token.previous

            if break_continue_token:
                # Assumed that break/continue is always at the end of a statement
                condition_true.append(BlockStatement(break_continue_token))

            # Convert for statement into while format
            desugared_for = for_statement.desugar()
            blocks.extend(desugared_for)
        # Switch statement
        elif t.astOperand1 and t.astOperand1.str == "switch":
            # Grab swtich scope from tree
            switch_scope: ScopeNode = scope_tree.children[0]
            assert switch_scope.scope_obj.type == "Switch", f"Expected switch scope, got {switch_scope.scope_obj.type}"
            # Remove switch scope from tree
            scope_tree.remove_by_id(switch_scope.scope_id)
            # Get end of switch scope
            switch_scope_end: Token = switch_scope.scope_obj.classEnd
            # Get while conditional
            switch_expr_root_token: Token = t.astOperand2

            # Get tokens for switch statment
            switch_root_tokens: List[Statement] = []

            cur_token: Token = switch_scope.scope_obj.classStart
            while root_tokens and cur_token.Id != switch_scope_end.Id:
                if cur_token.Id == root_tokens[0].Id:
                    switch_root_tokens.append(root_tokens.pop(0))

                cur_token = cur_token.next

            # print([tokens_to_str(get_statement_tokens(x)) for x in switch_root_tokens])
            # Get all case/default tokens
            case_default_tokens = []
            cur_token = t
            while cur_token and cur_token.Id != switch_scope_end.Id:
                # print(cur_token.str)
                assert cur_token.str != "switch", "can't handle nested switch!"
                if cur_token.scopeId != switch_scope.scope_id:
                    cur_token = cur_token.next
                    continue
                if cur_token.str in ["case", "default"]:
                    case_default_tokens.append(cur_token)

                cur_token = cur_token.next

            # print([tokens_to_str(get_statement_tokens(x)) for x in case_default_tokens])

            # Get all condition tokens
            for i, cur_token in enumerate(case_default_tokens):
                match_case = None
                if cur_token.str == "case":
                    match_case = cur_token.next if cur_token.next else None

                case_default_tokens[i] = (cur_token, match_case)

            # Get all blocks of code in each case:
            for i, (case_token, match_case) in enumerate(case_default_tokens):
                case_token_blocks = []

                next_case_token = switch_scope_end

                if i < len(case_default_tokens) - 1:
                    next_case_token, _ = case_default_tokens[i + 1]

                while switch_root_tokens:
                    cur_token = switch_root_tokens[0]

                    if cur_token.Id >= next_case_token.Id:
                        break

                    case_token_blocks.append(cur_token)
                    switch_root_tokens.pop(0)

                # print([tokens_to_str(get_statement_tokens(x)) for x in case_token_blocks])

                case_default_tokens[i] = (case_token, match_case, parse(case_token_blocks, switch_scope))

            # Check backwards from each case statement to check for break/continue
            for i in range(1, len(case_default_tokens) + 1):
                end_token = None
                if i == len(case_default_tokens):
                    end_token = switch_scope_end
                else:
                    end_token, _, _ = case_default_tokens[i]

                start_token, match_case, case_blocks = case_default_tokens[i - 1]

                cur_token = end_token
                break_continue_token = None
                while cur_token.Id >= start_token.Id:
                    if cur_token.str in ["break", "continue", "pass"]:
                        break_continue_token = cur_token
                        break  # Haha get it?

                    cur_token = cur_token.previous

                if break_continue_token:
                    # Assumed that break/continue is always at the end of a statement
                    case_blocks.append(BlockStatement(break_continue_token))
                    case_default_tokens[i - 1] = (start_token, match_case, case_blocks)

            # Make switch stmt objects
            switch_blocks = []
            for i, (case_token, match_case, case_blocks) in enumerate(case_default_tokens):
                case_token, match_case, case_blocks = case_default_tokens[i]
                switch_block = SwitchStatment(switch_expr_root_token, match_case, case_blocks)

                if case_token.str == "default":
                    switch_block.is_default = True

                if case_blocks and case_blocks[-1].get_type() == "block":
                    if case_blocks[-1].root_token.str in ["break", "continue", "pass"]:
                        switch_block.has_break = True

                switch_blocks.append(switch_block)

                # Link together switch nodes
                if i == 0:
                    pass
                else:
                    previous = switch_blocks[i - 1]
                    previous.next = switch_block
                    switch_block.previous = previous

            blocks.append(switch_blocks[0].desugar())
        # Regular statement
        else:
            blocks.append(BlockStatement(t))

    return blocks


def print_AST(function_body):
    for b in function_body:
        print("_____")
        if b.get_type() == "block":
            print(tokens_to_str(get_statement_tokens(b.root_token)))
        elif b.get_type() == "if":
            print("IF:")
            print(tokens_to_str(get_statement_tokens(b.condition)))
            print("IF TRUE:")
            print_AST(b.condition_true)
            print("END TRUE")
            print("IF FALSE:")
            print_AST(b.condition_false)
            print("END FALSE")
            print("END IF")
        elif b.get_type() == "while":
            print("WHILE:")
            print(tokens_to_str(get_statement_tokens(b.condition)))
            print("IF TRUE:")
            print_AST(b.condition_true)
            print("END TRUE")
            print("END WHILE")
        elif b.get_type() == "for":
            print("FOR:")
            print(tokens_to_str(get_statement_tokens(b.condition)))
            print("DO:")
            print_AST(b.condition_true)
        elif b.get_type() == "switch":
            if b.is_default:
                print(f"SWITCH: (default = {b.is_default})")
            else:
                print(f"SWITCH: {b.switch_expr.str} == {b.match_expr.str} (default = {b.is_default})")
            print_AST(b.match_true)
            if b.next:
                print_AST([b.next])

if __name__ == "__main__":
    test_path = "/home/rewong/phys/ryan/control_flow/dump_to_ast_test/test_9.cpp.dump"
    parsed = DumpToAST.convert(test_path)
    # print_AST([parsed[0].body[-1]])
    # print([x.scope_obj.type for x in parsed[0].scope_tree.children])

    # cur = [parsed[0].scope_tree]
    # while cur:
    #     x = cur.pop(0)
    #     print(x.scope_id)
    #     print([z.scope_id for z in x.children])
    #     cur.extend(x.children)

    print_AST(parsed[0].body)
    DumpToAST.write(parsed, "test_9.yaml")
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