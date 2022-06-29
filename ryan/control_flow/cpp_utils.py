from cpp_parser import *
from typing import *

def get_statement_tokens(t):
    """ #type: Token -> List[Token]
    Returns all tokens involved in a statement in order
    """
    if not t:
        return []
    elif not(t.astOperand1 or t.astOperand2):
        return [t]
    
    return get_statement_tokens(t.astOperand1) + [t] + get_statement_tokens(t.astOperand2)

def get_vars_from_statement(t):
    """ #type: List[Token] -> List[Token]
    Returns a list of variable tokens from a list of tokens
    """
    return list(filter(lambda x: x.varId, t))

def get_LHS_from_statement(t):
    """ #type: List[Token] -> List[Token]
    Returns the tokens of the LHS of an expression
    """
    for i in range(len(t)):
        if "=" in t[i].str:
            return t[:i]

def get_RHS_from_statement(t):
    """ #type: List[Token] -> List[Token]
    Returns the tokens of the RHS of an expression
    """
    for i in range(len(t)):
        if "=" in t[i].str:
            return t[i:]

def tokens_to_str(t):
    """ #type: List[Token] -> List[str]
    Returns a list of strings extracted from a list of tokens
    """
    return list(map(lambda x: x.str, t))

def root_token_to_str(t: Token) -> str:
    if not t:
        return ""
    print(t.str)
    return root_token_to_str(t.previous) + t.str + root_token_to_str(t.next)
