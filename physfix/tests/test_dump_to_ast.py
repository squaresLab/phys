import unittest
import yaml
from yaml.loader import SafeLoader
from dump_to_ast import DumpToAST
from cpp_utils import token_to_stmt_str

class TestDumpToAST(unittest.TestCase):
    def test(self):
        for i in range(1, 15):
            test_path = f"./dump_to_ast_test/test_{i}.cpp.dump"
            sol_path = f"./dump_to_ast_test/test_{i}_solution.yaml"
            ast = DumpToAST.convert(test_path)
            ast_dict = [f.to_dict() for f in ast]

            sol_dict = None
            with open(sol_path) as f:
                sol_dict = yaml.load(f, Loader=SafeLoader)

            self.assertEqual(ast_dict, sol_dict)

if __name__ == "__main__":
    unittest.main()