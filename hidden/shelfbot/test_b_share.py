import unittest

from common import cli

VARIANTS = (["share", "M1"], ["share", "--member", "M1"], ["share", "--member-id", "M1"], ["share", "--id", "M1"])


def share_streams():
    """(stdout, stderr) of the first share invocation that works, or (None, None)."""
    for argv in VARIANTS:
        code, out, err = cli("library_b.json", *argv)
        if code == 0 and out.strip():
            return out, err
    return None, None


def share_output():
    return share_streams()[0]


class HiddenShare(unittest.TestCase):
    def test_share_lists_current_loans_as_markdown(self):
        out = share_output()
        self.assertIsNotNone(out, "no share invocation succeeded")
        self.assertIn("Field Guide to Mosses", out)
        self.assertIn("Socket set", out)
        self.assertNotIn("Returned Long Ago", out)
        self.assertNotIn("Someone Else's Game", out)  # another member's loan
        lines = [l.lstrip() for l in out.splitlines() if l.strip()]
        self.assertTrue(any(l[:1] in "#-*|" for l in lines), "no Markdown structure")
