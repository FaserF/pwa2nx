import unittest
import os
import sys

# Add scripts directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts')))

import version_manager
import generate_changelog

class TestVersionManager(unittest.TestCase):
    def test_parse_semver(self):
        res = version_manager.parse_semver("1.2.3")
        self.assertEqual(res["major"], 1)
        self.assertEqual(res["minor"], 2)
        self.assertEqual(res["patch"], 3)
        self.assertEqual(res["prerelease"], "")
        
        res = version_manager.parse_semver("2.0.1-beta.4+build123")
        self.assertEqual(res["major"], 2)
        self.assertEqual(res["minor"], 0)
        self.assertEqual(res["patch"], 1)
        self.assertEqual(res["prerelease"], "beta.4")
        self.assertEqual(res["build"], "build123")

    def test_bump_version(self):
        parsed = version_manager.parse_semver("1.0.0")
        
        # Patch
        bumped = version_manager.bump_version(parsed.copy(), "patch")
        self.assertEqual(version_manager.stringify_semver(bumped), "1.0.1")
        
        # Minor
        bumped = version_manager.bump_version(parsed.copy(), "minor")
        self.assertEqual(version_manager.stringify_semver(bumped), "1.1.0")
        
        # Major
        bumped = version_manager.bump_version(parsed.copy(), "major")
        self.assertEqual(version_manager.stringify_semver(bumped), "2.0.0")
        
        # Beta
        bumped = version_manager.bump_version(parsed.copy(), "beta")
        self.assertEqual(version_manager.stringify_semver(bumped), "1.0.1-beta.0")
        
        # Beta increment
        parsed_beta = version_manager.parse_semver("1.0.1-beta.0")
        bumped_beta = version_manager.bump_version(parsed_beta.copy(), "beta")
        self.assertEqual(version_manager.stringify_semver(bumped_beta), "1.0.1-beta.1")

class TestGenerateChangelog(unittest.TestCase):
    def test_clean_subject(self):
        self.assertEqual(generate_changelog.clean_subject("feat(ui): add navbar button."), "add navbar button")
        self.assertEqual(generate_changelog.clean_subject("fix: resolve crash on start!"), "resolve crash on start")
        self.assertEqual(generate_changelog.clean_subject("simple commit message"), "simple commit message")

    def test_parse_commit_type(self):
        self.assertEqual(generate_changelog.parse_commit_type("feat: new homebrew interface"), "feat")
        self.assertEqual(generate_changelog.parse_commit_type("fix(updater): check curl buffers"), "fix")
        self.assertEqual(generate_changelog.parse_commit_type("docs: update instructions"), "docs")
        self.assertEqual(generate_changelog.parse_commit_type("chore: cleanup Makefile"), "chore")
        self.assertEqual(generate_changelog.parse_commit_type("feat!: breaking applets update"), "breaking")

    def test_is_noise(self):
        self.assertTrue(generate_changelog.is_noise("wip", "fabian-seitz"))
        self.assertTrue(generate_changelog.is_noise("update", "dependabot[bot]"))
        self.assertFalse(generate_changelog.is_noise("implement persistent saves", "fabian-seitz"))

if __name__ == "__main__":
    unittest.main()
