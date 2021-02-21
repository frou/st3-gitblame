import importlib
import unittest

# REF: https://github.com/SublimeText/UnitTesting/blob/master/README.md

# This strange form of import is required because our ST package name has a space in it.
blame = importlib.import_module("Git blame.src.blame")
blame_all = importlib.import_module("Git blame.src.blame_all")
parse = importlib.import_module("Git blame.src.parse")

# NOTE: The sample git-blame CLI outputs were taken from the https://github.com/sublimelsp/LSP
# repo because they exhibit different numbers of components in author names.


class TestParsing(unittest.TestCase):
    def test_blame_parsing(self):
        samples = [
            (
                r"""27399a5b (Tom van Ommeren 2017-10-12 22:53:05 +0200 26)     DiagnosticSeverity.Warning: 'markup.changed.lsp sublimelinter.mark.warning markup.warning.lsp',""",
                (
                    "27399a5b",
                    "Tom van Ommeren",
                    "2017-10-12",
                    "22:53:05",
                ),  # Failing. Issue #29
            ),
            (
                r"""c937eff9 (Duncan Holm 2020-04-11 14:29:47 +0100 3) import re""",
                ("c937eff9", "Duncan Holm", "2020-04-11", "14:29:47"),
            ),
            (
                r"""a30330a6 (jwortmann 2020-06-18 15:29:31 +0200 55)                 for file in window_diagnostics:""",
                ("a30330a6", "jwortmann", "2020-06-18", "15:29:31"),
            ),
        ]
        for cli_output_line, expected_result in samples:
            self.assertEqual(
                blame.Blame.parse_line(cli_output_line),
                expected_result,
            )

    def test_blame_all_parsing(self):
        samples = [
            (
                r"""4a3eb02f plugin/diagnostics.py (Tom van Ommeren  2019-11-27 21:42:13 +0100   1) import html""",
                {
                    "author": "Tom van Ommeren",
                    "date": "2019-11-27",
                    "file": "plugin/diagnostics.py",
                    "line_number": "1",
                    "sha": "4a3eb02f",
                    "time": "21:42:13",
                    "timezone": "+0100",
                },
            ),
            (
                r"""c937eff9 plugin/diagnostics.py (Duncan Holm      2020-04-11 14:29:47 +0100 114)         spaced_message = re.sub(r'(\S)\n(\S)', r'\1 \2', diagnostic.message)""",
                {
                    "author": "Duncan Holm",
                    "date": "2020-04-11",
                    "file": "plugin/diagnostics.py",
                    "line_number": "114",
                    "sha": "c937eff9",
                    "time": "14:29:47",
                    "timezone": "+0100",
                },
            ),
            (
                r"""16a30de1 plugin/diagnostics.py (jwortmann        2020-05-18 08:34:46 +0200 272)                 if settings.diagnostics_gutter_marker == "sign":""",
                {
                    "author": "jwortmann",
                    "date": "2020-05-18",
                    "file": "plugin/diagnostics.py",
                    "line_number": "272",
                    "sha": "16a30de1",
                    "time": "08:34:46",
                    "timezone": "+0200",
                },
            ),
        ]
        for cli_output_line, expected_result in samples:
            self.assertEqual(
                parse.parse_blame_cli_output_line(cli_output_line),
                expected_result,
            )
