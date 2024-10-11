#!/usr/bin/env python3
# Copyright 2024 Canonical Ltd.
# Written by:
#   Hanhsuan Lee <hanhsuan.lee@canonical.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3,
# as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from unittest.mock import patch, MagicMock, mock_open
import unittest
import os

from gnome_randr_cycle import GnomeRandrCycler


class GetMonitorInfosTests(unittest.TestCase):
    output = "tests/test_data/gnome_randr_output.txt"

    @patch("subprocess.check_output")
    def test_success(self, mock_check):
        grc = GnomeRandrCycler()
        with open(self.output, "r") as f:
            mock_check.return_value = f.read()
            (monitors, current_modes) = grc.get_monitor_infos()
            self.assertEqual(
                current_modes,
                [("eDP-1", "2560x1600", "2560x1600@59.994", "59.99*")],
            )


class ParseArgsTests(unittest.TestCase):
    def test_success(self):
        grc = GnomeRandrCycler()
        # no arguments, load default
        args = []
        rv = grc.parse_args(args)
        self.assertEqual(rv.keyword, "")
        self.assertEqual(rv.screenshot_dir, os.environ["HOME"])

        # change keyword
        args = ["--keyword", "test"]
        rv = grc.parse_args(args)
        self.assertEqual(rv.keyword, "test")
        self.assertEqual(rv.screenshot_dir, os.environ["HOME"])

        # change screenshot-dir
        args = ["--screenshot-dir", "test"]
        rv = grc.parse_args(args)
        self.assertEqual(rv.keyword, "")
        self.assertEqual(rv.screenshot_dir, "test")

        # change all
        args = [
            "--keyword",
            "test_keyword",
            "--screenshot-dir",
            "folder",
        ]
        rv = grc.parse_args(args)
        self.assertEqual(rv.keyword, "test_keyword")
        self.assertEqual(rv.screenshot_dir, "folder")


class MainTests(unittest.TestCase):
    @patch("gnome_randr_cycle.GnomeRandrCycler.parse_args")
    @patch("gnome_randr_cycle.GnomeRandrCycler.monitor_resolution_cycling")
    def test_run_main_succ(self, mock_cycling, mock_parse_args):
        args_mock = MagicMock()
        args_mock.keyword = "keyword"
        args_mock.screenshot_dir = "shot"
        mock_parse_args.return_value = args_mock
        self.assertEqual(GnomeRandrCycler().main(), None)
        mock_cycling.assert_called_with(
            "keyword",
            "shot",
        )


if __name__ == "__main__":
    unittest.main()
