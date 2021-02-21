import re

_GIT_BLAME_CLI_OUTPUT_REGEX = re.compile(
    r"""(?x)
    ^   (?P<sha>\^?\w+)
    \s+ (?P<file>[\S ]+)
    \s+
    \(  (?P<author>.+?)
    \s+ (?P<date>\d{4}-\d{2}-\d{2})
    \s+ (?P<time>\d{2}:\d{2}:\d{2})
    \s+ (?P<timezone>[\+-]\d+)
    \s+ (?P<line_number>\d+)
    \)
    \s
    """
)


def parse_blame_cli_output_line(line):
    m = _GIT_BLAME_CLI_OUTPUT_REGEX.match(line)
    return m.groupdict() if m else {}
