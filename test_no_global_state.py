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

ERA_NAMES = {"period", "era", "campaign", "year", "ele_year", "cross_ele_year"}
PROVIDER_NAME = re.compile(r"_shared|provider", re.IGNORECASE)


def parse(path):
    with open(path) as f:
        return ast.parse(f.read())


TREES = {os.path.basename(path): parse(path) for path in PYTHON}
CLASSES = {
    node.name
    for tree in TREES.values()
    for node in ast.walk(tree)
    if isinstance(node, ast.ClassDef)
}


def assignments(nodes):
    """(target, value, line number) of the assignments among the nodes."""
    for node in nodes:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                yield target, node.value, node.lineno
        elif isinstance(node, (ast.AnnAssign, ast.AugAssign)) and node.value is not None:
            yield node.target, node.value, node.lineno


def creates_provider(node):
    return any(
        isinstance(n, ast.Call)
        and "CppProvider" in (getattr(n.func, "id", None), getattr(n.func, "attr", None))
        for n in ast.walk(node)
    )


def is_class(node):
    """A class name, `cls`, `type(...)` or `....__class__`."""
    if isinstance(node, ast.Name):
        return node.id in CLASSES or node.id == "cls"
    if isinstance(node, ast.Call):
        return getattr(node.func, "id", None) == "type"
    return isinstance(node, ast.Attribute) and node.attr == "__class__"


def class_attributes():
    """(file:line, name, value) of every value stored on a class: in the class body, or from
    anywhere through the class (`puWeightProducer.x = ...`, `cls.x[key] = ...`)."""
    for file, tree in TREES.items():
        for cls in (n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)):
            for target, value, line in assignments(cls.body):
                if isinstance(target, ast.Name):
                    yield f"{file}:{line}", target.id, value
        for target, value, line in assignments(ast.walk(tree)):
            while isinstance(target, ast.Subscript):
                target = target.value
            if isinstance(target, ast.Attribute) and is_class(target.value):
                yield f"{file}:{line}", target.attr, value


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
                r"\b\w+(Producer|Provider|Correction)\."
                r"(period|era|campaign|year|ele_year|cross_ele_year)\s*=(?!=)",
                PYTHON,
                "#",
            ),
            [],
        )
        self.assertEqual(
            [
                f"{where}: {name}"
                for where, name, _ in class_attributes()
                if name in ERA_NAMES
            ],
            [],
        )

    def test_no_providers_on_classes_or_modules(self):
        # a provider kept by a class or a module is shared by every era built in the process
        on_classes = [
            f"{where}: {name}"
            for where, name, value in class_attributes()
            if PROVIDER_NAME.search(name) or creates_provider(value)
        ]
        on_modules = [
            f"{file}:{line}"
            for file, tree in TREES.items()
            for _, value, line in assignments(tree.body)
            if creates_provider(value)
        ]
        self.assertEqual(on_classes + on_modules, [])

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
