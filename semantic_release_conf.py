"""
Scipy Inspired commit message parser for python-semantic-release.

Parses commit messages using `scipy tags <scipy-style>`_ of the form::

    <tag>(<scope>): <subject>

    <body>


The elements <tag>, <scope> and <body> are optional. If no tag is present, the
commit will be added to the changelog section "None" and no version increment
will be performed.

While <scope> is supported here it isn't actually part of the scipy style.
If it is missing, parentheses around it are too. The commit should then be
of the form::

    <tag>: <subject>

    <body>

To communicate a breaking change add "BREAKING CHANGE" into the body at the
beginning of a paragraph. Fill this paragraph with information how to migrate
from the broken behavior to the new behavior. It will be added to the
"Breaking" section of the changelog.

Supported Tags::

    API, DEP, ENH, REV, BUG, MAINT, BENCH, BLD,
    DEV, DOC, STY, TST, REL, FEAT, TEST

Supported Changelog Sections::

    breaking, feature, fix, other, None

.. _`scipy-style`: https://docs.scipy.org/doc/scipy/reference/dev/contributor/development_workflow.html#writing-the-commit-message
"""

import logging
import re

from semantic_release import UnknownCommitMessageStyleError
from semantic_release.helpers import LoggedFunction
from semantic_release.history.parser_helpers import ParsedCommit

logger = logging.getLogger(__name__)


class ChangeType:
    def __init__(self, tag, section) -> None:
        self.tag: str = tag
        self.section: str = section
        self.bump_level: int = 0

    def make_breaking(self):
        self.bump_level = 3


class Breaking(ChangeType):
    def __init__(self, tag, section) -> None:
        super().__init__(tag, section)
        self.bump_level: int = 3


class Compatible(ChangeType):
    def __init__(self, tag, section) -> None:
        super().__init__(tag, section)
        self.bump_level: int = 2


class Patch(ChangeType):
    def __init__(self, tag, section) -> None:
        super().__init__(tag, section)
        self.bump_level: int = 1


class Ignore(ChangeType):
    def __init__(self, tag, section) -> None:
        super().__init__(tag, section)
        self.bump_level: int = 0


COMMIT_TYPES = [
    Breaking("API", "breaking"),
    Ignore("BENCH", "other"),
    Ignore("BLD", "other"),
    Patch("BUG", "fix"),
    Ignore("DEP", "other"),
    Ignore("DEV", "other"),
    Ignore("DOC", "other"),
    Compatible("ENH", "feature"),
    Ignore("MAINT", "other"),
    Patch("REV", "fix"),
    Ignore("STY", "None"),
    Ignore("TST", "None"),
    Ignore("REL", "None"),
    # strictly speaking not part of the standard
    Compatible("FEAT", "feature"),
    Ignore("TEST", "None"),
]

_commit_filter = "|".join(c.tag for c in COMMIT_TYPES)
re_parser = re.compile(
    rf"(?P<tag>{_commit_filter})?"
    r"(?:\((?P<scope>[^\n]+)\))?"
    r":? "
    r"(?P<subject>[^\n]+):?"
    r"(\n\n(?P<text>.*))?",
    re.DOTALL,
)


@LoggedFunction(logger)
def parse_commit_message(message: str) -> ParsedCommit:
    """
    Parse a scipy-style commit message

    :param message: A string of a commit message.
    :return: A tuple of (level to bump, type of change, scope of change, a tuple
    with descriptions)
    :raises UnknownCommitMessageStyleError: if regular expression matching fails
    """

    parsed = re_parser.match(message)
    if not parsed:
        raise UnknownCommitMessageStyleError(
            f"Unable to parse the given commit message: {message}"
        )

    if parsed.group("subject"):
        subject = parsed.group("subject")
    else:
        raise UnknownCommitMessageStyleError(f"The commit has no subject {message}")

    if parsed.group("text"):
        blocks = parsed.group("text").split("\n\n")
        blocks = [x for x in blocks if not x == ""]
        blocks.insert(0, subject)
    else:
        blocks = [subject]

    msg_type: ChangeType
    for msg_type in COMMIT_TYPES:
        if msg_type.tag == parsed.group("tag"):
            break
    else:
        # some commits may not have a tag, e.g. if they belong to a PR that
        # wasn't squashed (for maintainability) ignore them
        msg_type = Ignore("", "None")

    # Look for descriptions of breaking changes
    migration_instructions = [
        block for block in blocks if block.startswith("BREAKING CHANGE")
    ]
    if migration_instructions:
        msg_type.make_breaking()

    return ParsedCommit(
        msg_type.bump_level,
        msg_type.section,
        parsed.group("scope"),
        blocks,
        migration_instructions,
    )
