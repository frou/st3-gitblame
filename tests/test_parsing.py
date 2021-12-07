import importlib
import unittest

# REF: https://github.com/SublimeText/UnitTesting/blob/master/README.md

# This strange form of import is required because our ST package name has a space in it.
base = importlib.import_module("Git blame.src.base")


class TestParsing(unittest.TestCase):
    def test_git_blame_cli_output_parsing(self):
        samples = [
            # NOTE: This section of sample git-blame CLI outputs were taken from the
            # https://github.com/sublimelsp/LSP repo because they exhibit different
            # numbers of components in author names:
            (
                r"""4a3eb02f plugin/diagnostics.py (Tom van Ommeren  2019-11-27 21:42:13 +0100   1) import html""",
                {
                    "author": "Tom van Ommeren",
                    "date": "2019-11-27",
                    "file": "plugin/diagnostics.py",
                    "line_number": "1",
                    "sha": "4a3eb02f",
                    "sha_normalised": "4a3eb02f",
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
                    "sha_normalised": "c937eff9",
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
                    "sha_normalised": "16a30de1",
                    "time": "08:34:46",
                    "timezone": "+0200",
                },
            ),
            #
            # A "boundary commit" SHA:
            #
            (
                r"""^ad61094 main.go (Duncan Holm 2016-01-18 21:22:16 +0000 1) package main""",
                {
                    "author": "Duncan Holm",
                    "date": "2016-01-18",
                    "file": "main.go",
                    "line_number": "1",
                    "sha": "^ad61094",
                    "sha_normalised": "ad61094",
                    "time": "21:22:16",
                    "timezone": "+0000",
                },
            ),
        ]
        for cli_output_line, expected_result in samples:
            self.assertEqual(
                base.BaseBlame.parse_line(cli_output_line),  # type: ignore [attr-defined]
                expected_result,
            )
