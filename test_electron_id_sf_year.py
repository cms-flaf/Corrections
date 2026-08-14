import ast
import os
import unittest


def _load_electron_id_sf_year():
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "electron.py")
    with open(path, encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=path)
    fn = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "electron_id_sf_year"
    )
    ns = {}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), path, "exec"), ns)
    return ns["electron_id_sf_year"]


class TestElectronIdSfYear(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.year_fn = staticmethod(_load_electron_id_sf_year())

    def test_existing_run3_years_unchanged(self):
        year = self.year_fn
        self.assertEqual(year("2022_Summer22"), "2022Re-recoBCD")
        self.assertEqual(year("2022_Summer22EE"), "2022Re-recoE+PromptFG")
        self.assertEqual(year("2023_Summer23"), "2023PromptC")
        self.assertEqual(year("2023_Summer23BPix"), "2023PromptD")
        self.assertEqual(year("2024_Summer24"), "2024Prompt")
        self.assertEqual(year("2025_Summer24"), "2025Prompt")

    def test_2026_uses_2025_json_year(self):
        self.assertEqual(self.year_fn("2026_Summer24"), "2025Prompt")

    def test_2026_does_not_invent_2026Prompt(self):
        self.assertNotEqual(self.year_fn("2026_Summer24"), "2026Prompt")


if __name__ == "__main__":
    unittest.main()
