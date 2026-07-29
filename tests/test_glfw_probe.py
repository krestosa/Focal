import ctypes
import unittest
from unittest import mock

from tools import glfw_probe


class FakeContext:
    def __init__(self, symbols):
        self.symbols = symbols

    def get_proc_address(self, name):
        return self.symbols.get(name)


class GlfwProbeTests(unittest.TestCase):
    def test_missing_required_symbol_is_factual(self):
        with self.assertRaisesRegex(
            glfw_probe.GlfwProbeUnavailable,
            "required OpenGL symbol glGetString is unavailable",
        ):
            glfw_probe.query_current_glfw_context(FakeContext({}), "3.3", "core")

    def test_query_reports_strings_limits_extensions_and_capabilities(self):
        strings = {
            glfw_probe.GL_VENDOR: b"Vendor",
            glfw_probe.GL_RENDERER: b"Renderer",
            glfw_probe.GL_VERSION: b"4.6",
            glfw_probe.GL_SHADING_LANGUAGE_VERSION: b"4.60",
        }
        extensions = [
            b"GL_ARB_compute_shader",
            b"GL_ARB_shader_storage_buffer_object",
            b"GL_KHR_debug",
        ]
        limits = {
            glfw_probe.GL_NUM_EXTENSIONS: len(extensions),
            glfw_probe.GL_MAX_COLOR_ATTACHMENTS: 8,
            glfw_probe.GL_MAX_DRAW_BUFFERS: 8,
            glfw_probe.GL_MAX_TEXTURE_SIZE: 16384,
        }

        def fake_get_string(enum):
            return strings.get(enum)

        def fake_get_integer(enum, output):
            ctypes.cast(output, ctypes.POINTER(ctypes.c_int))[0] = limits[enum]

        def fake_get_string_i(_enum, index):
            return extensions[index]

        symbols = {
            b"glGetString": 1,
            b"glGetIntegerv": 2,
            b"glGetStringi": 3,
        }
        callables = {
            1: fake_get_string,
            2: fake_get_integer,
            3: fake_get_string_i,
        }

        def fake_cfunctype(_restype, *_argtypes):
            return lambda pointer: callables[pointer]

        with mock.patch.object(glfw_probe.ctypes, "CFUNCTYPE", fake_cfunctype):
            result = glfw_probe.query_current_glfw_context(
                FakeContext(symbols), "4.3", "core"
            )

        self.assertEqual(result["backend"], "glfw-hidden")
        self.assertEqual(result["vendor"], "Vendor")
        self.assertEqual(result["renderer"], "Renderer")
        self.assertEqual(result["extensionEnumeration"], "glGetStringi")
        self.assertEqual(result["limits"]["numExtensions"], 3)
        self.assertTrue(result["capabilities"]["compute"])
        self.assertTrue(result["capabilities"]["ssbo"])
        self.assertTrue(result["capabilities"]["debugOutput"])
        self.assertFalse(result["capabilities"]["geometry"])


if __name__ == "__main__":
    unittest.main()
