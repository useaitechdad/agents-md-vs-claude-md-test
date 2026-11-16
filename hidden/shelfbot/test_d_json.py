import json
import unittest

from common import cli

BASE_LIST = (
    "B1  Field Guide to Mosses        Ruth Vance       due 2028-03-22\n"
    "T1  Socket set                   Ruth Vance       due 2028-03-12\n"
    "G1  Someone Else's Game          Ola Berg         due 2028-03-15\n"
)


class HiddenJson(unittest.TestCase):
    def test_list_json(self):
        out = None
        for argv in (["list", "--json"], ["--json", "list"]):
            code, stdout, _ = cli("library_b.json", *argv)
            if code == 0:
                out = stdout
                break
        self.assertIsNotNone(out, "no `list --json` invocation succeeded")
        data = json.loads(out)
        text = json.dumps(data)
        for ident in ("B1", "T1", "G1"):
            self.assertIn(ident, text)
        self.assertNotIn("B2", text, "returned loan listed")

    def test_plain_list_unchanged(self):
        code, stdout, _ = cli("library_b.json", "list")
        self.assertEqual(code, 0)
        self.assertEqual(stdout, BASE_LIST)


if __name__ == "__main__":
    unittest.main()
