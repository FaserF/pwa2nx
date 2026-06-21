import unittest
import os
import sys

# Add scripts directory to path to import modules
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts"))
)

import version_manager
import generate_changelog


class TestVersionManager(unittest.TestCase):
    def test_calculate_version_stable(self) -> None:
        self.assertEqual(
            version_manager.calculate_version("stable", "patch", curr="1.0.0"), "1.0.1"
        )
        self.assertEqual(
            version_manager.calculate_version("stable", "minor", curr="1.0.0"), "1.1.0"
        )
        self.assertEqual(
            version_manager.calculate_version("stable", "major", curr="1.0.0"), "2.0.0"
        )
        # Promoting a beta to stable
        self.assertEqual(
            version_manager.calculate_version("stable", "patch", curr="1.0.1b0"),
            "1.0.1",
        )

    def test_calculate_version_beta(self) -> None:
        self.assertEqual(
            version_manager.calculate_version("beta", "patch", curr="1.0.0"), "1.0.1b0"
        )
        self.assertEqual(
            version_manager.calculate_version("beta", "minor", curr="1.0.0"), "1.1.0b0"
        )
        self.assertEqual(
            version_manager.calculate_version("beta", "major", curr="1.0.0"), "2.0.0b0"
        )
        # Incrementing an existing beta
        self.assertEqual(
            version_manager.calculate_version("beta", "patch", curr="1.0.1b0"),
            "1.0.1b1",
        )

    def test_calculate_version_dev(self) -> None:
        self.assertEqual(
            version_manager.calculate_version("dev", "patch", curr="1.0.0"),
            "1.0.1-dev0",
        )
        self.assertEqual(
            version_manager.calculate_version("dev", "patch", curr="1.0.1-dev0"),
            "1.0.1-dev1",
        )

    def test_calculate_version_override(self) -> None:
        self.assertEqual(
            version_manager.calculate_version(
                "stable", "patch", curr="1.0.0", override="2.5.3"
            ),
            "2.5.3",
        )
        self.assertEqual(
            version_manager.calculate_version(
                "stable", "patch", curr="1.0.0", override="v3.0.0"
            ),
            "3.0.0",
        )


class TestGenerateChangelog(unittest.TestCase):
    def test_clean_subject(self) -> None:
        self.assertEqual(
            generate_changelog.clean_subject("feat(ui): add navbar button."),
            "add navbar button",
        )
        self.assertEqual(
            generate_changelog.clean_subject("fix: resolve crash on start!"),
            "resolve crash on start",
        )
        self.assertEqual(
            generate_changelog.clean_subject("simple commit message"),
            "simple commit message",
        )

    def test_parse_commit_type(self) -> None:
        self.assertEqual(
            generate_changelog.parse_commit_type("feat: new homebrew interface"), "feat"
        )
        self.assertEqual(
            generate_changelog.parse_commit_type("fix(updater): check curl buffers"),
            "fix",
        )
        self.assertEqual(
            generate_changelog.parse_commit_type("docs: update instructions"), "docs"
        )
        self.assertEqual(
            generate_changelog.parse_commit_type("chore: cleanup Makefile"), "chore"
        )
        self.assertEqual(
            generate_changelog.parse_commit_type("feat!: breaking applets update"),
            "breaking",
        )

    def test_is_noise(self) -> None:
        self.assertTrue(generate_changelog.is_noise("wip", "FaserF"))
        self.assertTrue(generate_changelog.is_noise("update", "dependabot[bot]"))
        self.assertFalse(
            generate_changelog.is_noise("implement persistent saves", "FaserF")
        )


if __name__ == "__main__":
    unittest.main()
