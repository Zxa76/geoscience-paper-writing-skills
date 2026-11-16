import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

INSTALLER = Path(__file__).resolve().parents[1] / 'scripts/install.py'

class InstallTest(unittest.TestCase):
    def test_install_and_refuse_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / 'skills'
            command = [sys.executable, str(INSTALLER), '--destination', str(destination)]
            first = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(first.returncode, 0, first.stderr)
            entries = list(destination.glob('*/SKILL.md'))
            self.assertEqual(len(entries), 7)
            before = {p: p.read_bytes() for p in entries}
            again = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
            self.assertNotEqual(again.returncode, 0)
            self.assertEqual(before, {p: p.read_bytes() for p in entries})

if __name__ == '__main__':
    unittest.main()
