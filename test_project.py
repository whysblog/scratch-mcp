import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from src.project import Project


SVG = "<svg xmlns='http://www.w3.org/2000/svg' width='32' height='32'></svg>"


class ProjectTests(unittest.TestCase):
    def test_export_is_repeatable_and_preserves_assets(self):
        project = Project()
        project.add_target("Stage", True, SVG)

        with tempfile.TemporaryDirectory() as tmp:
            first = project.export_sb3(tmp, "first.sb3")
            second = project.export_sb3(tmp, "second.sb3")

            self.assertTrue(Path(first).exists())
            self.assertTrue(Path(second).exists())

            for path in (first, second):
                with zipfile.ZipFile(path) as archive:
                    names = archive.namelist()
                    data = json.loads(archive.read("project.json"))

                self.assertIn("project.json", names)
                self.assertEqual(1, len(data["targets"]))
                self.assertEqual(1, len(data["targets"][0]["costumes"]))
                self.assertTrue(any(name.endswith(".svg") for name in names))

    def test_numeric_string_inputs_are_literals(self):
        project = Project()
        sprite_id = project.add_target("Sprite", False, SVG)

        block_id = project.add_block(sprite_id, "motion_gotoxy", inputs={"X": "-150", "Y": "80"})
        block = project.targets[0]["blocks"][block_id]

        self.assertEqual([1, [4, "-150"]], block["inputs"]["X"])
        self.assertEqual([1, [4, "80"]], block["inputs"]["Y"])

    def test_explicit_block_prefix_keeps_block_references_unambiguous(self):
        project = Project()
        sprite_id = project.add_target("Sprite", False, SVG)

        provider_id = project.add_block(sprite_id, "motion_xposition", block_id="xpos")
        consumer_id = project.add_block(
            sprite_id,
            "operator_lt",
            inputs={"OPERAND1": "block:xpos", "OPERAND2": "10"},
        )
        block = project.targets[0]["blocks"][consumer_id]

        self.assertEqual([1, provider_id], block["inputs"]["OPERAND1"])
        self.assertEqual([1, [4, "10"]], block["inputs"]["OPERAND2"])

    def test_export_filename_cannot_escape_output_directory(self):
        project = Project()
        project.add_target("Stage", True, SVG)

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(project.export_sb3(tmp, "../escape.sb3"))

        self.assertEqual("escape.sb3", out.name)
        self.assertNotIn("..", out.parts)


if __name__ == "__main__":
    unittest.main()
