"""No process-wide correction state: every provider is an object owned by its producer.

A process may build corrections for several eras, so nothing may be kept per class or per
process: no `initialized` flags or class-level era values in the producers, no static provider
singletons and no mutable function-local statics in the headers. Reads the sources only; needs
neither ROOT nor /cvmfs.
"""

import ast
import glob
import os
import re
import unittest

repo = os.path.dirname(os.path.abspath(__file__))


def code_lines(path, comment):
    """(line number, line) of the lines that are not comments."""
    with open(path) as f:
        for number, line in enumerate(f, 1):
            if not line.strip().startswith(comment):
                yield number, line


def find(pattern, paths, comment):
    regex = re.compile(pattern)
    return [
        f"{os.path.basename(path)}:{number}: {line.strip()}"
        for path in paths
        for number, line in code_lines(path, comment)
        if regex.search(line)
    ]


PYTHON = sorted(
    p
    for p in glob.glob(os.path.join(repo, "*.py"))
    if not os.path.basename(p).startswith("test_")
)
HEADERS = sorted(glob.glob(os.path.join(repo, "*.h")))


class NoGlobalState(unittest.TestCase):
    def test_the_sources_exist(self):
        self.assertGreater(len(PYTHON), 20)
        self.assertGreater(len(HEADERS), 20)

    def test_no_initialized_flags(self):
        self.assertEqual(find(r"\binitialized\s*=|\.initialized\b", PYTHON, "#"), [])

    def test_no_global_instances(self):
        self.assertEqual(
            find(
                r"getGlobal|initializeGlobal|_global_instance|::Initialize\(",
                PYTHON,
                "#",
            ),
            [],
        )

    def test_no_era_values_on_classes(self):
        self.assertEqual(
            find(
                r"\b\w+(Producer|Provider|Correction)\.(period|year|ele_year|cross_ele_year)\s*=",
                PYTHON,
                "#",
            ),
            [],
        )
        class_attributes = []
        for path in PYTHON:
            with open(path) as f:
                tree = ast.parse(f.read())
            for cls in (n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)):
                for statement in cls.body:
                    if isinstance(statement, ast.Assign):
                        for target in statement.targets:
                            if isinstance(target, ast.Name) and target.id in (
                                "period",
                                "year",
                            ):
                                class_attributes.append(
                                    f"{os.path.basename(path)}:{statement.lineno}"
                                )
        self.assertEqual(class_attributes, [])

    def test_no_singleton_base(self):
        self.assertEqual(
            find(r"CorrectionsBase|static\s+std::unique_ptr", HEADERS, "//"), []
        )

    def test_no_mutable_function_local_statics(self):
        # a static variable that is not const: one value shared by every object and thread
        self.assertEqual(
            find(
                r"^\s+static\s+(?!const\b|constexpr\b|inline\b)[\w:<>,\s]+?\s\w+\s*(=|;|\{)",
                HEADERS,
                "//",
            ),
            [],
        )


if __name__ == "__main__":
    unittest.main()
