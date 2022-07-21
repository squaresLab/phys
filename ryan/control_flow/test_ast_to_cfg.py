from abc import abstractmethod
import unittest
import yaml
from yaml.loader import SafeLoader
from ast_to_cfg import ASTToCFG

class TestASTToCFG(unittest.TestCase):
    def test(self):
        for i in range(1, 2):
            test_path = f"./ast_to_cfg_test/test_{i}.cpp.dump"
            sol_path = f"./ast_to_cfg_test/test_{i}_solution.yaml"
            ast = ASTToCFG.convert(test_path)
            ast_dict = [f.to_dict() for f in ast]

            sol_dict = None
            with open(sol_path) as f:
                sol_dict = yaml.load(f, Loader=SafeLoader)
            # print(ast_dict[0]["entry"]["next"][0]["previous"])
            # print(sol_dict[0]["entry"]["next"][0]["previous"])
            
            with open("test_1_1.yaml", "w", encoding="utf-8") as f:
                yaml.dump(sol_dict, f)

            with open("test_1_2.yaml", "w", encoding="utf-8") as f:
                yaml.dump(ast_dict, f)

            self.compare_inputs(ast_dict, sol_dict)

    def compare_inputs(self, d1, d2):
        if isinstance(d1, str):
            self.assertEqual(d1, d2)
        elif isinstance(input, list):
            self.assertTrue(isinstance(d2, list))
            for i in d1:
                self.asserTrue(i in d1)
        elif isinstance(input, dict):
            self.assertTrue(isinstance(d2, dict))
            self.assertEqual(len(d1), len(d2))
            for k, v in d1.items():
                self.assertTrue(k in d2)
                self.compare_inputs(v, d2[k])
                

if __name__ == "__main__":
    unittest.main()