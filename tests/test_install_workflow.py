"""Installer integration checks. Test artifacts are retained, never auto-deleted."""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("install_workflow", ROOT / "scripts" / "install_workflow.py")
assert SPEC is not None and SPEC.loader is not None
INSTALLER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INSTALLER)


class InstallWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        configured_root = os.environ.get("KAGGLE_SKILLS_TEST_ROOT")
        base = Path(configured_root) if configured_root else Path(tempfile.gettempdir())
        base.mkdir(parents=True, exist_ok=True)
        cls.artifacts = Path(tempfile.mkdtemp(prefix="workflow-tests-", dir=str(base)))

    @classmethod
    def tearDownClass(cls):
        print(f"Retained test artifacts: {cls.artifacts}")

    def target(self, name):
        return self.artifacts / name

    def test_new_install_preserves_exact_payload(self):
        target, created = INSTALLER.install_skill(INSTALLER.SKILL_SOURCE, self.target("new"))
        self.assertTrue(created)
        self.assertEqual(INSTALLER.read_payload(target), INSTALLER.read_payload(INSTALLER.SKILL_SOURCE))

    def test_identical_install_is_a_noop(self):
        base = self.target("repeat")
        target, _ = INSTALLER.install_skill(INSTALLER.SKILL_SOURCE, base)
        before = {p.relative_to(target): p.stat().st_mtime_ns for p in target.rglob("*") if p.is_file()}
        _, created = INSTALLER.install_skill(INSTALLER.SKILL_SOURCE, base)
        after = {p.relative_to(target): p.stat().st_mtime_ns for p in target.rglob("*") if p.is_file()}
        self.assertFalse(created)
        self.assertEqual(before, after)

    def test_conflicting_install_is_preserved(self):
        base = self.target("conflict")
        target = base / INSTALLER.SKILL_NAME
        target.mkdir(parents=True)
        sentinel = target / "SKILL.md"
        sentinel.write_bytes(b"an existing user skill")
        with self.assertRaises(FileExistsError):
            INSTALLER.install_skill(INSTALLER.SKILL_SOURCE, base)
        self.assertEqual(sentinel.read_bytes(), b"an existing user skill")
        self.assertEqual(list(target.iterdir()), [sentinel])

    def test_missing_source_stops_before_creating_destination(self):
        target = self.target("missing-source-target")
        with self.assertRaises(ValueError):
            INSTALLER.install_skill(self.target("source-does-not-exist"), target)
        self.assertFalse(target.exists())

    def test_extra_existing_file_prevents_silent_replacement(self):
        base = self.target("extra")
        target, _ = INSTALLER.install_skill(INSTALLER.SKILL_SOURCE, base)
        extra = target / "user-note.txt"
        extra.write_text("keep", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            INSTALLER.install_skill(INSTALLER.SKILL_SOURCE, base)
        self.assertEqual(extra.read_text(encoding="utf-8"), "keep")

    def test_invalid_source_file_is_not_installed(self):
        source = self.target("invalid-source")
        source.mkdir()
        (source / "SKILL.md").write_text("valid entry", encoding="utf-8")
        (source / "credentials.json").write_text("not a payload", encoding="utf-8")
        target = self.target("invalid-target")
        with self.assertRaises(ValueError):
            INSTALLER.install_skill(source, target)
        self.assertFalse(target.exists())

    def test_cli_accepts_spaces_and_unicode(self):
        target = self.target("space and 中文")
        environment = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
        run = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "install_workflow.py"), "--target-root", str(target)],
            capture_output=True, text=True, encoding="utf-8", env=environment, check=False,
        )
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertTrue((target / INSTALLER.SKILL_NAME / "SKILL.md").is_file())

    def test_codex_home_is_used_without_mutation(self):
        custom = str(self.target("codex home"))
        with patch.dict(os.environ, {"CODEX_HOME": custom}):
            self.assertEqual(INSTALLER.default_target_root(), Path(custom) / "skills")
            self.assertEqual(os.environ["CODEX_HOME"], custom)


if __name__ == "__main__":
    unittest.main()
