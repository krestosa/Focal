from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.focal_gl_sources import SourceResolutionError, parse_defines, prepare_program


class SourceAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.shaders = self.root / "shaders"
        self.shaders.mkdir()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write(self, relative: str, content: str) -> Path:
        path = self.shaders / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def test_source_mode_preserves_original_stage_and_hashes_it(self) -> None:
        original = "#version 330 core\nvoid main() {}\n"
        self.write("gbuffers_basic.vsh", original)
        prepared = prepare_program(
            pack=self.root,
            program="gbuffers_basic",
            source_mode="source",
        )
        self.assertEqual(prepared.sourceMode, "source")
        self.assertFalse(prepared.includesResolved)
        self.assertEqual(prepared.stages[0].source, original)
        self.assertEqual(prepared.stages[0].byteLength, len(original.encode("utf-8")))
        self.assertEqual(len(prepared.stages[0].sha256), 64)
        self.assertNotIn("source", prepared.metadata()["stages"][0])

    def test_preprocessed_mode_resolves_relative_and_root_includes_and_defines(self) -> None:
        self.write("lib/common.glsl", "vec3 commonValue() { return vec3(1.0); }\n")
        self.write("program/local.glsl", '#include <lib/common.glsl>\n')
        self.write(
            "program/example.vsh",
            '#version 330 core\n#include "local.glsl"\nvoid main() { gl_Position = vec4(commonValue(), 1.0); }\n',
        )
        prepared = prepare_program(
            pack=self.root,
            source_root=self.shaders / "program",
            program="example",
            source_mode="preprocessed",
            define_values=("FOCAL_PROFILE=2", "FEATURE_ON"),
        )
        source = prepared.stages[0].source
        self.assertIn("#version 330 core\n#define FEATURE_ON 1\n#define FOCAL_PROFILE 2\n", source)
        self.assertIn("commonValue", source)
        self.assertNotIn("#include", source)
        self.assertTrue(prepared.includesResolved)
        self.assertEqual(prepared.defines, {"FEATURE_ON": "1", "FOCAL_PROFILE": "2"})

    def test_preprocessed_root_include_is_anchored_to_explicit_root(self) -> None:
        root = self.root / "export"
        root.mkdir()
        (root / "shared.glsl").write_text("const float VALUE = 1.0;\n", encoding="utf-8")
        (root / "example.fsh").write_text('#version 330 core\n#include <shared.glsl>\n', encoding="utf-8")
        prepared = prepare_program(
            pack=self.root,
            source_root=root,
            program="example",
            source_mode="preprocessed",
        )
        self.assertIn("VALUE", prepared.stages[0].source)

    def test_include_cycle_is_rejected_with_chain(self) -> None:
        self.write("example.vsh", '#include "a.glsl"\n')
        self.write("a.glsl", '#include "b.glsl"\n')
        self.write("b.glsl", '#include "a.glsl"\n')
        with self.assertRaisesRegex(SourceResolutionError, "include cycle"):
            prepare_program(pack=self.root, program="example", source_mode="preprocessed")

    def test_include_escape_is_rejected(self) -> None:
        (self.root / "outside.glsl").write_text("outside\n", encoding="utf-8")
        self.write("example.vsh", '#include "../outside.glsl"\n')
        with self.assertRaisesRegex(SourceResolutionError, "escapes source root"):
            prepare_program(pack=self.root, program="example", source_mode="preprocessed")

    def test_patched_mode_requires_explicit_export_and_rejects_unresolved_include(self) -> None:
        with self.assertRaisesRegex(SourceResolutionError, "requires --source-root"):
            prepare_program(pack=self.root, program="example", source_mode="iris-patched")
        patched = self.root / "patched"
        patched.mkdir()
        (patched / "example.fsh").write_text('#include "still-present.glsl"\n', encoding="utf-8")
        with self.assertRaisesRegex(SourceResolutionError, "retains an unresolved include"):
            prepare_program(
                pack=self.root,
                source_root=patched,
                program="example",
                source_mode="iris-patched",
            )

    def test_patched_mode_consumes_explicit_export_without_claiming_preprocessing(self) -> None:
        patched = self.root / "patched"
        patched.mkdir()
        source = "#version 330 core\nvoid main() {}\n"
        (patched / "example.fsh").write_text(source, encoding="utf-8")
        prepared = prepare_program(
            pack=self.root,
            source_root=patched,
            program="example",
            source_mode="iris-patched",
        )
        self.assertEqual(prepared.sourceMode, "iris-patched")
        self.assertTrue(prepared.includesResolved)
        self.assertEqual(prepared.stages[0].source, source)

    def test_invalid_program_and_conflicting_defines_are_rejected(self) -> None:
        with self.assertRaisesRegex(SourceResolutionError, "single shader program name"):
            prepare_program(pack=self.root, program="../example", source_mode="source")
        with self.assertRaisesRegex(SourceResolutionError, "conflicting"):
            parse_defines(("VALUE=1", "VALUE=2"))
        with self.assertRaisesRegex(SourceResolutionError, "invalid define"):
            parse_defines(("1VALUE=2",))


if __name__ == "__main__":
    unittest.main()
