import ctypes
import unittest

from tools import glfw_context


class FakeFunction:
    def __init__(self, implementation):
        self.implementation = implementation
        self.argtypes = None
        self.restype = None

    def __call__(self, *args):
        return self.implementation(*args)


class FakeGlfw:
    def __init__(self, *, init_result=glfw_context.GLFW_TRUE, window=1234):
        self.hints = []
        self.current = []
        self.destroyed = []
        self.terminated = 0
        self._window = window
        self.glfwInit = FakeFunction(lambda: init_result)
        self.glfwWindowHint = FakeFunction(self._window_hint)
        self.glfwCreateWindow = FakeFunction(self._create_window)
        self.glfwMakeContextCurrent = FakeFunction(self._make_current)
        self.glfwDestroyWindow = FakeFunction(self._destroy_window)
        self.glfwGetProcAddress = FakeFunction(
            lambda name: 99 if name == b"glGetStringi" else None
        )
        self.glfwTerminate = FakeFunction(self._terminate)

    def _window_hint(self, hint, value):
        self.hints.append((hint, value))

    def _create_window(self, width, height, title, monitor, share):
        self.created = (width, height, title, monitor, share)
        return self._window

    def _make_current(self, window):
        self.current.append(window.value)

    def _destroy_window(self, window):
        self.destroyed.append(window.value)

    def _terminate(self):
        self.terminated += 1


class HiddenGlfwContextTests(unittest.TestCase):
    def test_library_resolution_tries_both_common_names(self):
        calls = []

        def find_library(name):
            calls.append(name)
            return "libglfw.so.3" if name == "glfw3" else None

        self.assertEqual(
            glfw_context._resolve_glfw_library(find_library),
            "libglfw.so.3",
        )
        self.assertEqual(calls, ["glfw", "glfw3"])

    def test_missing_library_is_factual_unavailability(self):
        with self.assertRaisesRegex(
            glfw_context.GlfwContextUnavailable,
            "shared library is unavailable",
        ):
            glfw_context._resolve_glfw_library(lambda _name: None)

    def test_hidden_context_sets_bounded_hints_and_cleans_up(self):
        fake = FakeGlfw()
        context = glfw_context.create_hidden_glfw_context(
            "4.3",
            "core",
            "320x180",
            find_library=lambda _name: "fake-glfw",
            loader=lambda _name: fake,
        )

        self.assertEqual(context.window, 1234)
        self.assertEqual(context.get_proc_address(b"glGetStringi"), 99)
        self.assertEqual(fake.created[:3], (320, 180, b"focal-gl"))
        self.assertIn(
            (glfw_context.GLFW_VISIBLE, glfw_context.GLFW_FALSE),
            fake.hints,
        )
        self.assertIn(
            (glfw_context.GLFW_CONTEXT_VERSION_MAJOR, 4),
            fake.hints,
        )
        self.assertIn(
            (glfw_context.GLFW_CONTEXT_VERSION_MINOR, 3),
            fake.hints,
        )
        self.assertIn(
            (
                glfw_context.GLFW_OPENGL_PROFILE,
                glfw_context.GLFW_OPENGL_CORE_PROFILE,
            ),
            fake.hints,
        )
        self.assertEqual(fake.current, [1234])

        context.close()
        self.assertEqual(fake.destroyed, [1234])
        self.assertEqual(fake.terminated, 1)

    def test_compatibility_profile_hint_is_explicit(self):
        fake = FakeGlfw()
        with glfw_context.create_hidden_glfw_context(
            "3.3",
            "compatibility",
            "64x64",
            find_library=lambda _name: "fake-glfw",
            loader=lambda _name: fake,
        ):
            self.assertIn(
                (
                    glfw_context.GLFW_OPENGL_PROFILE,
                    glfw_context.GLFW_OPENGL_COMPAT_PROFILE,
                ),
                fake.hints,
            )
        self.assertEqual(fake.destroyed, [1234])
        self.assertEqual(fake.terminated, 1)

    def test_failed_window_creation_terminates_glfw(self):
        fake = FakeGlfw(window=0)
        with self.assertRaisesRegex(
            glfw_context.GlfwContextUnavailable,
            "glfwCreateWindow 3.3 core failed",
        ):
            glfw_context.create_hidden_glfw_context(
                "3.3",
                "core",
                "64x64",
                find_library=lambda _name: "fake-glfw",
                loader=lambda _name: fake,
            )
        self.assertEqual(fake.destroyed, [])
        self.assertEqual(fake.terminated, 1)

    def test_init_failure_does_not_claim_a_context(self):
        fake = FakeGlfw(init_result=glfw_context.GLFW_FALSE)
        with self.assertRaisesRegex(glfw_context.GlfwContextUnavailable, "glfwInit failed"):
            glfw_context.create_hidden_glfw_context(
                "3.3",
                "core",
                "64x64",
                find_library=lambda _name: "fake-glfw",
                loader=lambda _name: fake,
            )
        self.assertEqual(fake.destroyed, [])


if __name__ == "__main__":
    unittest.main()
