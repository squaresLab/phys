import unittest
from dump_to_ast import DumpToAST
from cpp_utils import token_to_stmt_str

class TestDumpToAST(unittest.TestCase):
    def test_case_1(self):
        test_path = "./dump_to_ast_test/test_1.cpp.dump"
        ast = DumpToAST.convert(test_path)[0].body

        stmts = [['vel_x', '=', '0'], ['ang_z', '=', '0'], ['err_x', '=', '0'],
        ['err_y', '=', 'err_x', '+', 'ang_z'], ['vel_x', '=', 'ang_z', '+', 'err_x']]

        for idx, b in enumerate(ast):
            self.assertEqual(b.get_type(), "block")
            self.assertEqual(token_to_stmt_str(b.root_token),
            stmts[idx])

    def test_case_2(self):
        test_path = "./dump_to_ast_test/test_2.cpp.dump"
        ast = DumpToAST.convert(test_path)[0].body

        stmts = [['vel_x', '=', '0'], ['ang_z', '=', '0'], ['err_x', '=', '0'],
        ['err_y', '=', 'err_x', '+', 'ang_z']]

        for idx in range(len(stmts)):
            self.assertEqual(ast[0].get_type(), "block")
            self.assertEqual(token_to_stmt_str(ast[0].root_token),
            stmts[idx])
            ast.pop(0)


        condition_stmt = ['vel_x', '<', '0']
        condition_true_stmt = ['vel_x', '=', 'ang_z', '+', 'err_x']
        
        self.assertEqual(ast[0].get_type(), "if")
        self.assertEqual(token_to_stmt_str(ast[0].condition), condition_stmt)

        self.assertEqual(len(ast[0].condition_true), 1)
        self.assertEqual(token_to_stmt_str(ast[0].condition_true[0].root_token), 
        condition_true_stmt)

        self.assertEqual(len(ast[0].condition_false), 0)

    def test_case_3(self):
        test_path = "./dump_to_ast_test/test_3.cpp.dump"
        ast = DumpToAST.convert(test_path)[0].body

        # First 4 stmts are same as test case 2
        for idx in range(4):
            ast.pop(0)

        condition_stmt = ['vel_x', '<', '0']
        condition_true_stmt = ['vel_x', '=', 'ang_z', '+', 'err_x']
        condition_false_stmt = ['vel_x', '=', 'vel_x', '+', 'err_y']
        
        self.assertEqual(ast[0].get_type(), "if")
        self.assertEqual(token_to_stmt_str(ast[0].condition), condition_stmt)

        self.assertEqual(len(ast[0].condition_true), 1)
        self.assertEqual(token_to_stmt_str(ast[0].condition_true[0].root_token), 
        condition_true_stmt)

        self.assertEqual(len(ast[0].condition_false), 1)
        self.assertEqual(token_to_stmt_str(ast[0].condition_false[0].root_token), 
        condition_false_stmt)

    def test_case_4(self):
        test_path = "./dump_to_ast_test/test_4.cpp.dump"
        ast = DumpToAST.convert(test_path)[0].body

        # First 4 stmts are same as test case 2
        for idx in range(4):
            ast.pop(0)

        condition_stmt = ['vel_x', '<', '0']
        condition_true_stmt = ['vel_x', '=', 'ang_z', '+', 'err_x']
        
        self.assertEqual(ast[0].get_type(), "if")
        self.assertEqual(token_to_stmt_str(ast[0].condition), condition_stmt)

        self.assertEqual(len(ast[0].condition_true), 1)
        self.assertEqual(token_to_stmt_str(ast[0].condition_true[0].root_token), 
        condition_true_stmt)

        self.assertEqual(len(ast[0].condition_false), 1)
        second_if = ast[0].condition_false[0]
        second_if_cond_stmt = ['vel_x', '>', '0']
        second_if_true_stmt = ['vel_x', '=', 'vel_x', '+', 'err_y']

        self.assertEqual(second_if.get_type(), "if")
        self.assertEqual(token_to_stmt_str(second_if.condition), 
        second_if_cond_stmt)
        
        self.assertEqual(len(second_if.condition_true), 1)
        self.assertEqual(token_to_stmt_str(second_if.condition_true[0].root_token),
        second_if_true_stmt)

        self.assertEqual(len(second_if.condition_false), 0)

    def test_case_5(self):
        test_path = "./dump_to_ast_test/test_5.cpp.dump"
        ast = DumpToAST.convert(test_path)[0].body

        # First 4 stmts are same as test case 2
        for idx in range(4):
            ast.pop(0)

        condition_stmt = ['vel_x', '<', '0']
        condition_true_stmt = ['vel_x', '=', 'ang_z', '+', 'err_x']
        
        self.assertEqual(ast[0].get_type(), "if")
        self.assertEqual(token_to_stmt_str(ast[0].condition), condition_stmt)

        self.assertEqual(len(ast[0].condition_true), 1)
        self.assertEqual(token_to_stmt_str(ast[0].condition_true[0].root_token), 
        condition_true_stmt)

        # Testing else if branch
        self.assertEqual(len(ast[0].condition_false), 1)
        second_if = ast[0].condition_false[0]
        second_if_cond_stmt = ['vel_x', '>', '0']
        second_if_true_stmt = ['vel_x', '=', 'vel_x', '+', 'err_y']
        second_if_false_stmt = ['ang_z', '=', '10']

        self.assertEqual(second_if.get_type(), "if")
        self.assertEqual(token_to_stmt_str(second_if.condition), 
        second_if_cond_stmt)
        
        self.assertEqual(len(second_if.condition_true), 1)
        self.assertEqual(token_to_stmt_str(second_if.condition_true[0].root_token),
        second_if_true_stmt)

        self.assertEqual(len(second_if.condition_false), 1)
        self.assertEqual(token_to_stmt_str(second_if.condition_false[0].root_token),
        second_if_false_stmt)

    def test_case_6(self):
        test_path = "./dump_to_ast_test/test_6.cpp.dump"
        ast = DumpToAST.convert(test_path)[0].body

        # First 4 stmts are same as test case 2
        for idx in range(4):
            ast.pop(0)

        condition_stmt = ['vel_x', '<', '0']
        condition_true_stmt = ['vel_x', '=', 'ang_z', '+', 'err_x']
        
        self.assertEqual(ast[0].get_type(), "if")
        self.assertEqual(token_to_stmt_str(ast[0].condition), condition_stmt)
        
        # Testing nested if in true branch
        cond_true_branch = ast[0].condition_true
        self.assertEqual(len(cond_true_branch), 2)
        self.assertEqual(token_to_stmt_str(cond_true_branch[0].root_token), 
        condition_true_stmt)

        cond_true_branch.pop(0)
        self.assertEqual(cond_true_branch[0].get_type(), "if")

        true_cond_stmt = ['ang_z', '<', '0']
        true_true_stmt = ['vel_x', '=', '10']
        true_false_stmt = ['vel_x', '=', '-10']

        self.assertEqual(token_to_stmt_str(cond_true_branch[0].condition),
        true_cond_stmt)
        self.assertEqual(len(cond_true_branch[0].condition_true), 1)
        self.assertEqual(token_to_stmt_str(cond_true_branch[0].condition_true[0].root_token),
        true_true_stmt)
        self.assertEqual(len(cond_true_branch[0].condition_false), 1)
        self.assertEqual(token_to_stmt_str(cond_true_branch[0].condition_false[0].root_token),
        true_false_stmt)

        # Testing nested if in false branch
        cond_false_branch = ast[0].condition_false
        self.assertEqual(len(cond_false_branch), 1)
        cond_false_branch = cond_false_branch[0]

        self.assertEqual(cond_false_branch.get_type(), "if")

        false_cond_stmt = ['vel_x', '>', '0']
        false_true_stmt = ['vel_x', '=', 'vel_x', '+', 'err_y']
        false_false_stmt = ['ang_z', '=', '10']

        self.assertEqual(token_to_stmt_str(cond_false_branch.condition), false_cond_stmt)
        self.assertEqual(len(cond_false_branch.condition_true), 1)
        self.assertEqual(token_to_stmt_str(cond_false_branch.condition_true[0].root_token), 
        false_true_stmt)

        self.assertEqual(len(cond_false_branch.condition_false), 2)
        self.assertEqual(token_to_stmt_str(cond_false_branch.condition_false[0].root_token), 
        false_false_stmt)

        # Testing nested if inside else
        cond_false_false_branch = cond_false_branch.condition_false[1]
        self.assertEqual(cond_false_false_branch.get_type(), "if")

        false_false_cond_stmt = ['err_x', '<', '0']
        false_false_true_stmt = ['vel_x', '=', '50']
        false_false_false_stmt = ['vel_x', '=', '-50']

        self.assertEqual(token_to_stmt_str(cond_false_false_branch.condition), 
        false_false_cond_stmt)
        self.assertEqual(len(cond_false_false_branch.condition_true), 1)
        self.assertEqual(token_to_stmt_str(cond_false_false_branch.condition_true[0].root_token), 
        false_false_true_stmt)

        self.assertEqual(len(cond_false_false_branch.condition_false), 1)
        self.assertEqual(token_to_stmt_str(cond_false_false_branch.condition_false[0].root_token), 
        false_false_false_stmt)

    def test_case_7(self):
        test_path = "./dump_to_ast_test/test_7.cpp.dump"
        ast = DumpToAST.convert(test_path)[0].body

        # First 4 stmts are same as test case 2
        for idx in range(4):
            ast.pop(0)

        stmt = ['i', '=', '0']
        self.assertEqual(token_to_stmt_str(ast[0].root_token), stmt)
        ast.pop(0)

        self.assertEqual(ast[0].get_type(), "while")

        while_cond = ['i', '<', '10']
        while_true_stmt = ['i', '=', 'i', '+', '1']

        self.assertEqual(token_to_stmt_str(ast[0].condition), while_cond)
        self.assertEqual(len(ast[0].condition_true), 1)
        self.assertEqual(token_to_stmt_str(ast[0].condition_true[0].root_token), 
        while_true_stmt)

    def test_case_8(self):
        test_path = "./dump_to_ast_test/test_8.cpp.dump"
        ast = DumpToAST.convert(test_path)[0].body

        # First 4 stmts are same as test case 2
        for idx in range(4):
            ast.pop(0)

        # Ignoring other branches since they are same as test case 6
        cond_false_false_branch = ast[0].condition_false[0].condition_false

        self.assertEqual(len(cond_false_false_branch), 2)
        false_false_stmt = ['ang_z', '=', '10']

        self.assertEqual(token_to_stmt_str(cond_false_false_branch[0].root_token),
        false_false_stmt)
        while_stmt = cond_false_false_branch[1]
        while_cond = ['ang_z', '>', '0']
        while_true_stmt = ['ang_z', '-=', '1']

        self.assertEqual(token_to_stmt_str(while_stmt.condition),
        while_cond)
        self.assertEqual(len(while_stmt.condition_true), 1)
        self.assertEqual(token_to_stmt_str(while_stmt.condition_true[0].root_token),
        while_true_stmt)

    def test_case_9(self):
        test_path = "./dump_to_ast_test/test_9.cpp.dump"
        ast = DumpToAST.convert(test_path)[0].body

        # First 4 stmts are same as test case 2
        for idx in range(4):
            ast.pop(0)

        stmt = ['i', '=', '0']
        self.assertEqual(token_to_stmt_str(ast[0].root_token),
        stmt)
        ast.pop(0)

        while_stmt = ast[0]
        while_cond = ['i', '<', '10']
        while_true_stmt = [['err_x', '+=', '1'], ['break'], ['i', '++']]
        self.assertEqual(while_stmt.get_type(), "while")
        self.assertEqual(token_to_stmt_str(while_stmt.condition), while_cond)

        self.assertEqual(len(while_stmt.condition_true), 3)
        for i in range(3):
            self.assertEqual(while_true_stmt[i], 
            token_to_stmt_str(while_stmt.condition_true[i].root_token))

    def test_case_10(self):
        test_path = "./dump_to_ast_test/test_10.cpp.dump"
        ast = DumpToAST.convert(test_path)[0].body

        # First 4 stmts are same as test case 2
        for idx in range(4):
            ast.pop(0)

        # Ignoring other branches since already tested in test case 6/8
        true_false_branch = ast[0].condition_true[1].condition_false
        true_false_stmt = ['i', '=', '0']

        self.assertEqual(token_to_stmt_str(true_false_branch[0].root_token),
        true_false_stmt)

        while_stmt = true_false_branch[1]
        while_cond = ['i', '<', '10']
        while_true_stmt = [['vel_x', '-=', '1'], ['i', '++']]
        
        self.assertEqual(token_to_stmt_str(while_stmt.condition),
        while_cond)
        self.assertEqual(len(while_stmt.condition_true), 2)

        for i in range(2):
            self.assertEqual(token_to_stmt_str(while_stmt.condition_true[i].root_token),
            while_true_stmt[i])
    



        


if __name__ == "__main__":
    unittest.main()