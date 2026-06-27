"""
Tests for stroop_trainer.py, focusing on the _on_exit method.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add the project directory to sys.path so we can import stroop_trainer
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import stroop_trainer


class TestStroopTrainerOnExit(unittest.TestCase):
    """Tests for StroopTrainer._on_exit method."""

    def setUp(self):
        """Set up a mock StroopTrainer instance with a fake root."""
        self.mock_root = MagicMock()
        self.trainer = stroop_trainer.StroopTrainer(self.mock_root)

    # ---- Normal cases ----

    @patch("os.remove")
    def test_on_exit_removes_both_files(self, mock_remove):
        """Verify _on_exit calls os.remove for both 'stroop' and 'html'."""
        self.trainer._on_exit()

        expected_calls = [patch.call("stroop"), patch.call("html")]
        self.assertEqual(mock_remove.call_args_list, expected_calls)
        self.assertEqual(mock_remove.call_count, 2)

    @patch("os.remove")
    def test_on_exit_removes_stroop_first_then_html(self, mock_remove):
        """Verify the deletion order: 'stroop' first, then 'html'."""
        self.trainer._on_exit()

        calls = [call[0][0] for call in mock_remove.call_args_list]
        self.assertEqual(calls, ["stroop", "html"])

    # ---- Edge cases ----

    @patch("os.remove")
    def test_on_exit_does_not_remove_other_files(self, mock_remove):
        """Verify _on_exit does not attempt to delete files other than 'stroop' and 'html'."""
        self.trainer._on_exit()

        for call_args in mock_remove.call_args_list:
            arg = call_args[0][0]
            self.assertIn(arg, ["stroop", "html"])

    # ---- Error cases ----

    @patch("os.remove")
    def test_on_exit_when_stroop_not_found(self, mock_remove):
        """Verify behavior when 'stroop' file does not exist."""
        mock_remove.side_effect = [FileNotFoundError("stroop not found"), None]

        with self.assertRaises(FileNotFoundError):
            self.trainer._on_exit()

        # First call should have happened (and failed)
        mock_remove.assert_any_call("stroop")
        # Second call should NOT happen because the first one raises
        self.assertEqual(mock_remove.call_count, 1)

    @patch("os.remove")
    def test_on_exit_when_html_not_found(self, mock_remove):
        """Verify behavior when 'html' file does not exist after 'stroop' succeeds."""
        mock_remove.side_effect = [None, FileNotFoundError("html not found")]

        with self.assertRaises(FileNotFoundError):
            self.trainer._on_exit()

        self.assertEqual(mock_remove.call_count, 2)

    @patch("os.remove")
    def test_on_exit_when_both_files_not_found(self, mock_remove):
        """Verify behavior when neither file exists."""
        mock_remove.side_effect = FileNotFoundError("not found")

        with self.assertRaises(FileNotFoundError):
            self.trainer._on_exit()

        self.assertEqual(mock_remove.call_count, 1)

    @patch("os.remove")
    def test_on_exit_when_permission_denied_on_stroop(self, mock_remove):
        """Verify behavior when os.remove raises PermissionError on 'stroop'."""
        mock_remove.side_effect = [PermissionError("permission denied"), None]

        with self.assertRaises(PermissionError):
            self.trainer._on_exit()

        self.assertEqual(mock_remove.call_count, 1)

    @patch("os.remove")
    def test_on_exit_when_permission_denied_on_html(self, mock_remove):
        """Verify behavior when os.remove raises PermissionError on 'html'."""
        mock_remove.side_effect = [None, PermissionError("permission denied")]

        with self.assertRaises(PermissionError):
            self.trainer._on_exit()

        self.assertEqual(mock_remove.call_count, 2)

    @patch("os.remove")
    def test_on_exit_when_os_error_on_stroop(self, mock_remove):
        """Verify behavior when os.remove raises a generic OSError on 'stroop'."""
        mock_remove.side_effect = [OSError("I/O error"), None]

        with self.assertRaises(OSError):
            self.trainer._on_exit()

        self.assertEqual(mock_remove.call_count, 1)

    @patch("os.remove")
    def test_on_exit_when_os_error_on_html(self, mock_remove):
        """Verify behavior when os.remove raises a generic OSError on 'html'."""
        mock_remove.side_effect = [None, OSError("I/O error")]

        with self.assertRaises(OSError):
            self.trainer._on_exit()

        self.assertEqual(mock_remove.call_count, 2)

    # ---- Argument validation ----

    @patch("os.remove")
    def test_on_exit_called_with_string_arguments(self, mock_remove):
        """Verify _on_exit passes string arguments (not Path objects or other types)."""
        self.trainer._on_exit()

        for call_args in mock_remove.call_args_list:
            arg = call_args[0][0]
            self.assertIsInstance(arg, str)

    @patch("os.remove")
    def test_on_exit_called_with_exact_strings(self, mock_remove):
        """Verify the exact string values passed to os.remove."""
        self.trainer._on_exit()

        calls = [call[0][0] for call in mock_remove.call_args_list]
        self.assertEqual(calls[0], "stroop")
        self.assertEqual(calls[1], "html")


class TestStroopTrainerOnExitIntegration(unittest.TestCase):
    """Integration-style tests for _on_exit with real temporary files."""

    def setUp(self):
        """Set up a mock StroopTrainer instance and record current working directory."""
        self.mock_root = MagicMock()
        self.trainer = stroop_trainer.StroopTrainer(self.mock_root)
        self.original_cwd = os.getcwd()

    def test_on_exit_deletes_existing_stroop_file(self):
        """Verify _on_exit can delete a real file named 'stroop' in cwd."""
        # Create a real temporary file named 'stroop'
        test_file = os.path.join(self.original_cwd, "stroop")
        with open(test_file, "w") as f:
            f.write("test content")

        # Since _on_exit doesn't handle FileNotFoundError, we need both files
        # or at least 'stroop' to exist. We'll just test with the real os.remove.
        # But _on_exit will also try to remove 'html' which may not exist.
        # So we need to mock or create both.
        try:
            html_file = os.path.join(self.original_cwd, "html")
            with open(html_file, "w") as f:
                f.write("test html")

            self.assertTrue(os.path.exists(test_file))
            self.assertTrue(os.path.exists(html_file))

            self.trainer._on_exit()

            self.assertFalse(os.path.exists(test_file))
            self.assertFalse(os.path.exists(html_file))
        finally:
            # Cleanup in case the test didn't delete them
            for fname in ["stroop", "html"]:
                fpath = os.path.join(self.original_cwd, fname)
                if os.path.exists(fpath):
                    os.remove(fpath)

    def test_on_exit_raises_when_file_missing(self):
        """Verify _on_exit raises FileNotFoundError when file doesn't exist."""
        # Ensure neither file exists
        for fname in ["stroop", "html"]:
            fpath = os.path.join(self.original_cwd, fname)
            if os.path.exists(fpath):
                os.remove(fpath)

        with self.assertRaises(FileNotFoundError):
            self.trainer._on_exit()


if __name__ == "__main__":
    unittest.main()
