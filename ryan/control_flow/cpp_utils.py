from cpp_parser import Token, Variable
from typing import List

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
    print(t.str)
    return root_token_to_str(t.previous) + t.str + root_token_to_str(t.next)
