from typing import List

from cpp_parser import Token, Variable


def get_statement_tokens(token: Token) -> List[Token]:
    """Returns tokens in token tree in inorder"""
    if not token:
        return []
    elif not(token.astOperand1 or token.astOperand2):
        return [token]

    return get_statement_tokens(token.astOperand1) + [token] + get_statement_tokens(token.astOperand2)


def get_vars_from_statement(tokens: List[Token]) -> List[Variable]:
    """Returns all tokens in a list of tokens which represent a variable"""
    variables = []
    for t in tokens:
        if t.variable:
            variables.append(t.variable)

    return variables


def get_lhs_from_statement(tokens: List[Token]) -> List[Token]:
    """Returns the tokens of the LHS of an expression"""
    for idx, t in enumerate(tokens):
        if "=" == t.str:
            return tokens[:idx]


def get_rhs_from_statement(tokens: List[Token]) -> List[Token]:
    """
    Returns the tokens of the RHS of an expression
    """
    for idx, t in enumerate(tokens):
        if "=" == t.str:
            return tokens[idx:]


def tokens_to_str(tokens: List[Token]) -> List[str]:
    """Returns a list of strings extracted from a list of tokens"""
    return list(map(lambda x: x.str, tokens))


def token_to_stmt_str(t: Token) -> List[str]:
    """Traverses token in inorder and returns a list of strings"""
    return tokens_to_str(get_statement_tokens(t))


def get_root_token(t: Token) -> Token:
    """Returns the root of a token tree"""
    while t.astParent:
        t = t.astParent

    return t
