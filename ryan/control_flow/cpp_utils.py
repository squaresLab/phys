from cpp_parser import Token, Variable
from typing import List
from collections import deque

def get_statement_tokens(token: Token) -> List[Token]:
    """
    Returns all tokens involved in a statement in order
    """
    if not token:
        return []
    elif not(token.astOperand1 or token.astOperand2):
        return [token]
    
    return get_statement_tokens(token.astOperand1) + [token] + get_statement_tokens(token.astOperand2)

def get_vars_from_statement(tokens: List[Token]) -> List[Variable]:
    """
    Returns a list of variable tokens from a list of tokens
    """
    variables = []
    for t in tokens:
        if t.variable:
            variables.append(t.variable)

    return variables

def get_LHS_from_statement(tokens: List[Token]) -> List[Token]:
    """
    Returns the tokens of the LHS of an expression
    """
    for i in range(len(tokens)):
        if "=" == tokens[i].str:
            return tokens[:i]

def get_RHS_from_statement(tokens: List[Token]) -> List[Token]:
    """
    Returns the tokens of the RHS of an expression
    """
    for i in range(len(tokens)):
        if "=" == tokens[i].str:
            return tokens[i:]

def tokens_to_str(tokens: List[Token]) -> List[str]:
    """
    Returns a list of strings extracted from a list of tokens
    """
    return list(map(lambda x: x.str, tokens))

def root_token_to_str(t: Token) -> str:
    if not t:
        return ""
    return root_token_to_str(t.previous) + t.str + root_token_to_str(t.next)

def token_to_stmt_str(t: Token) -> List[str]:
    return tokens_to_str(get_statement_tokens(t))

def tokens_to_tree(tokens: List[Token]) -> Token:
    """Converts a list of tokens into a tree and returns the root"""
    if not tokens:
        return None
    elif len(tokens) == 1:
        if tokens[0].variableId:
            tokens[0].astOperand1 = None
            tokens[0].astOperand1Id = None
            tokens[0].astOperand2 = None
            tokens[0].astOperandId = None

        return tokens[0]

    root = None
    lhs = []
    rhs = []
    for idx, t in enumerate(tokens):
        if t.str in "+-*/(,":
            root = t
            lhs = tokens[:idx]
            rhs = tokens[idx + 1:]
            break
    
    if not root:
        return None

    left = tokens_to_tree(lhs)
    right = tokens_to_tree(rhs)

    root.astOperand1 = left
    root.astOperand2 = right

    if left:
        root.astOperand1Id = left.Id
        left.astParent = root
        left.astParentId = root.Id

    if right:
        root.astOperand2Id = right.Id
        right.astParent = root
        right.astParentId = root.Id

    return root

def get_root_token(t):
    while t.astParent:
        t = t.astParent
    
    return t
    