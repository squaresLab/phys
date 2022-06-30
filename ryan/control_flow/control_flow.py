from cpp_parser import *
from cpp_utils import *
from typing import *

def get_root_tokens(token_start: Token, token_end: Token) -> List[Token]:
    """ Takes the start and end tokens for a function and finds the root tokens
    of all statments in the function.
    """
    root_tokens_set = set()
    current_token = token_start
    
    while(current_token != token_end):  #todo: reverse token set exploration to top-down instead of bottom-up
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
    root_tokens = sorted(root_tokens, key=lambda x : int(x.linenr))
    return root_tokens


# This is needed since not all tokens in a statment are children of the root token for some reason
def get_function_statements(start_token: Token, end_token: Token, root_tokens: List[Token]) -> List[List[Token]]:
    """Takes the start and end tokens of a function and a list of the root tokens
    of the statments in a funciton and returns all of the tokens of each statment.
    """
    function_statements = [get_statement_tokens(t) for t in root_tokens]
    # print(end_token.str)

    for i in range(len(function_statements)):
        statement = function_statements[i]
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
    """Retrieves function information from Cppcheck Config obj.
    
    """
    function_dicts = {}

    # FIND FUNCTIONS IN "SCOPES" REGION OF DUMP FILE, START AND END TOKENs
    for s in cppcheck_config.scopes:
        if s.type == "Function": 
            # SCAN ALL FUNCTIONS UNLESS LIST OF FUNCTIONS SPECIFIED
            function_dicts[s.Id] = {"name": s.className,
                                    "linern": s.classStart.linenr,
                                    "token_start": s.classStart, 
                                    "token_end": s.classEnd, 
                                    "scopeObject":s,
                                    "scopes": [],
                                    "symbol_table": {},
                                    "function_graph_edges":[],
                                    "function":s.function}
            # CONSTRUCT LIST OF ROOT TOKENS
            function_dicts[s.Id]["root_tokens"] = get_root_tokens(s.classStart, s.classEnd)
                
    #print "Found %d functions..." % len(function_dicts)
    
    return function_dicts

def get_function_scopes(cppcheck_config: Configuration, function_scope_id: str) -> List[Scope]:
    """Takes a function and returns a list of scopes nested within that function.
    """
    nested_scopes = []
    for s in cppcheck_config.scopes:
        if s.nestedIn == function_scope_id:
            nested_scopes.append(s)

    return nested_scopes

class EntryBlock:
    def __init__(self, func_name, func_id, scope_id, line_num, start_token, end_token):
        self.func_name = func_name
        self.func_id = func_id
        self.scope_id = scope_id
        self.line_num = line_num
        self.start_token = start_token
        self.end_token = end_token
        self.next = None

class ExitBlock:
    def __init__(self, previous):
        self.previous

class BasicBlock:
    def __init__(self, tokens, previous):
        self.tokens = tokens
        self.previous = previous
        self.next = None

class ConditionalBlock:
    def __init__(self, conditional_tokens, previous):
        self.conditional_tokens = tokens
        self.previous = previous
        self.condition_true = None
        self.condition_false = None

# def construct_function_cfg_recursive(cur, function_statements: List[Token], function_dict):
#     """Helper for recursively creating CFG"""
#     func_scope_id = function_dict["scopeObject"].Id

#     while function_statements:
#         # print(tokens_to_str(s))
#         s = function_statements.pop(0)
#         if not s:
#             # function_statements.pop(0)
#             continue

#         statement_scope = s[0].scope

#         # If block
#         if statement[0].str == "if":
#             opening_paren = statement[0].next
#             assert opening_paren.str == "(", "Invalid if statement"
#             closing_paren = opening_paren.link
#             cur_token = opening_paren.next

#             conditional_tokens = []
#             while cur_token.next and cur_token != closing_paren:
#                 conditional_tokens.append(cur_token)
#                 cur_token = cur_token.next

#             opening_bracket = cur_token.next
#             assert opening_bracket.str == "{", "Invalid if statement"
#             closing_bracket = cloing_bracket.link

#             if_block_statements = []
#             while True:
#                 function_statements.pop(0)
#                 cur_statement = function_statements[0]
#                 bracket_found = False
#                 for i in range(len(cur_statement)):
#                     if cur_statement[i] == closing_bracket:
#                         if_block_statements.append(cur_statement[:i])
#                         function_statements[0] = cur_statement[i + 1:]
#                         bracket_found = True
#                         break

#                 if bracket_found:
#                     break
#                 else:
#                     if_block_statements.append(cur_statement)

#             conditional_block = ConditionalBlock(conditional_tokens, cur)
#             if cur:
#                 cur.next = conditional_block
#                 cur = cur.next
#             else:
#                 cur = conditional_block

#             conditional_block.condition_true = construct_function_cfg_recursive(cur, 
#             if_block_statements, function_dict) 
            


#         # Basic block
#         elif statement_scope.Id == func_scope_id:
#             basic_block = BasicBlock(s, cur)

#             if cur:
#                 cur.next = basic_block
#                 cur = cur.next
#             else:
#                 cur = basic_block
#         else : 
#             pass

#         function_statements.pop(0)

def construct_function_cfg_recursive(cur, function_statements, function_dict):
    pass

def construct_function_cfg(function_dict: Dict) -> EntryBlock:
    """Constructs the CFG object for a single function"""
    func_name = function_dict["name"]
    func_id = function_dict["function"]
    func_scope_id = function_dict["scopeObject"].Id
    line_num = function_dict["linern"]
    start_token = function_dict["token_start"]
    end_token = function_dict["token_end"]
    cfg = EntryBlock(func_name, func_id, func_scope_id, line_num, start_token, end_token)
    cur = cfg

    function_statements = get_function_statements(start_token, end_token, function_dict["root_tokens"])
    construct_function_cfg_recursive(cur, function_statements, function_dict)

    return cfg

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