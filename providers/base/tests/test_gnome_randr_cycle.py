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

from unittest.mock import patch, MagicMock, call
from collections import OrderedDict
from fractions import Fraction
import subprocess
import unittest
import os

from gnome_randr_cycle import GnomeRandrCycler


class CreatePathTests(unittest.TestCase):
    @patch("os.makedirs")
    def test_with_keyword(self, mock_dir):
        grc = GnomeRandrCycler()
        screenshot_path = grc._create_path("test", "/tmp/")
        self.assertEqual(screenshot_path, "/tmp/xrandr_screens_test")
        mock_dir.assert_called_with(
            screenshot_path,
            exist_ok=True,
        )

    @patch("os.makedirs")
    def test_without_keyword(self, mock_dir):
        grc = GnomeRandrCycler()
        screenshot_path = grc._create_path("", "/tmp")
        self.assertEqual(screenshot_path, "/tmp/xrandr_screens")
        mock_dir.assert_called_with(
            screenshot_path,
            exist_ok=True,
        )

    @patch("os.makedirs")
    def test_without_screenshot_dir(self, mock_dir):
        grc = GnomeRandrCycler()
        screenshot_path = grc._create_path("test", "")
        self.assertEqual(screenshot_path, "xrandr_screens_test")
        mock_dir.assert_called_with(
            screenshot_path,
            exist_ok=True,
        )


class TarScreenshotTests(unittest.TestCase):
    @patch("os.listdir")
    @patch("tarfile.open")
    def test_success(self, mock_open, mock_list):
        path = "/tmp/xrandr_screens_test"
        grc = GnomeRandrCycler()
        mock_add = MagicMock()
        mock_open.return_value.__enter__.return_value.add = mock_add
        mock_list.return_value = ["1.jpg", "2.jpg"]
        grc._tar_screenshot(path)
        mock_open.assert_called_with(
            path + ".tgz",
            "w:gz",
        )
        mock_add.assert_has_calls(
            [
                call(path + "/" + "1.jpg", "1.jpg"),
                call(path + "/" + "2.jpg", "2.jpg"),
            ]
        )


class MonitorResolutionCyclingTests(unittest.TestCase):
    test_monitors = {
        "eDP-1": OrderedDict(
            [
                (
                    "3840x2400",
                    (
                        3840,
                        Fraction(8, 5),
                        "3840x2400@59.994",
                        "59.99",
                    ),
                ),
                (
                    "3840x2160",
                    (
                        3840,
                        Fraction(16, 9),
                        "3840x2160@59.994",
                        "59.99",
                    ),
                ),
                (
                    "3200x1800",
                    (
                        3200,
                        Fraction(16, 9),
                        "3200x1800@59.994",
                        "59.99",
                    ),
                ),
                (
                    "2880x1620",
                    (
                        2880,
                        Fraction(16, 9),
                        "2880x1620@59.994",
                        "59.99",
                    ),
                ),
                (
                    "2560x1600",
                    (
                        2560,
                        Fraction(8, 5),
                        "2560x1600@59.994",
                        "59.99*",
                    ),
                ),
                (
                    "2560x1440",
                    (
                        2560,
                        Fraction(16, 9),
                        "2560x1440@59.994",
                        "59.99",
                    ),
                ),
                (
                    "2048x1536",
                    (
                        2048,
                        Fraction(4, 3),
                        "2048x1536@59.994",
                        "59.99",
                    ),
                ),
                (
                    "1920x1440",
                    (
                        1920,
                        Fraction(4, 3),
                        "1920x1440@59.994",
                        "59.99",
                    ),
                ),
                (
                    "1856x1392",
                    (
                        1856,
                        Fraction(4, 3),
                        "1856x1392@59.994",
                        "59.99",
                    ),
                ),
                (
                    "1792x1344",
                    (
                        1792,
                        Fraction(4, 3),
                        "1792x1344@59.994",
                        "59.99",
                    ),
                ),
                (
                    "2048x1152",
                    (
                        2048,
                        Fraction(16, 9),
                        "2048x1152@59.994",
                        "59.99",
                    ),
                ),
                (
                    "1920x1200",
                    (
                        1920,
                        Fraction(8, 5),
                        "1920x1200@59.994",
                        "59.99",
                    ),
                ),
                (
                    "1920x1080",
                    (
                        1920,
                        Fraction(16, 9),
                        "1920x1080@59.994",
                        "59.99",
                    ),
                ),
                (
                    "1600x1200",
                    (
                        1600,
                        Fraction(4, 3),
                        "1600x1200@59.994",
                        "59.99",
                    ),
                ),
                (
                    "1680x1050",
                    (
                        1680,
                        Fraction(8, 5),
                        "1680x1050@59.993",
                        "59.99",
                    ),
                ),
                (
                    "1400x1050",
                    (
                        1400,
                        Fraction(4, 3),
                        "1400x1050@59.994",
                        "59.99",
                    ),
                ),
                (
                    "1600x900",
                    (
                        1600,
                        Fraction(16, 9),
                        "1600x900@59.993",
                        "59.99",
                    ),
                ),
                (
                    "1280x1024",
                    (
                        1280,
                        Fraction(5, 4),
                        "1280x1024@59.994",
                        "59.99",
                    ),
                ),
                (
                    "1400x900",
                    (
                        1400,
                        Fraction(14, 9),
                        "1400x900@59.993",
                        "59.99",
                    ),
                ),
                (
                    "1280x960",
                    (
                        1280,
                        Fraction(4, 3),
                        "1280x960@59.994",
                        "59.99",
                    ),
                ),
                (
                    "1440x810",
                    (
                        1440,
                        Fraction(16, 9),
                        "1440x810@59.994",
                        "59.99",
                    ),
                ),
                (
                    "1368x768",
                    (
                        1368,
                        Fraction(57, 32),
                        "1368x768@59.993",
                        "59.99",
                    ),
                ),
                (
                    "1280x800",
                    (
                        1280,
                        Fraction(8, 5),
                        "1280x800@59.994",
                        "59.99",
                    ),
                ),
                (
                    "1280x720",
                    (
                        1280,
                        Fraction(16, 9),
                        "1280x720@59.993",
                        "59.99",
                    ),
                ),
                (
                    "1024x768",
                    (
                        1024,
                        Fraction(4, 3),
                        "1024x768@59.994",
                        "59.99",
                    ),
                ),
                (
                    "960x720",
                    (
                        960,
                        Fraction(4, 3),
                        "960x720@59.994",
                        "59.99",
                    ),
                ),
                (
                    "928x696",
                    (
                        928,
                        Fraction(4, 3),
                        "928x696@59.993",
                        "59.99",
                    ),
                ),
                (
                    "896x672",
                    (
                        896,
                        Fraction(4, 3),
                        "896x672@59.993",
                        "59.99",
                    ),
                ),
                (
                    "1024x576",
                    (
                        1024,
                        Fraction(16, 9),
                        "1024x576@59.993",
                        "59.99",
                    ),
                ),
                (
                    "960x600",
                    (
                        960,
                        Fraction(8, 5),
                        "960x600@59.993",
                        "59.99",
                    ),
                ),
                (
                    "960x540",
                    (
                        960,
                        Fraction(16, 9),
                        "960x540@59.993",
                        "59.99",
                    ),
                ),
                (
                    "800x600",
                    (
                        800,
                        Fraction(4, 3),
                        "800x600@59.994",
                        "59.99",
                    ),
                ),
            ]
        )
    }

    test_current_modes = [
        ("eDP-1", "2560x1600", "2560x1600@59.994", "59.99*")
    ]

    test_highest_modes = [
        ("eDP-1", "1368x768", "1368x768@59.993", "59.99"),
        ("eDP-1", "1400x900", "1400x900@59.993", "59.99"),
        ("eDP-1", "1280x1024", "1280x1024@59.994", "59.99"),
        ("eDP-1", "2048x1536", "2048x1536@59.994", "59.99"),
        ("eDP-1", "3840x2160", "3840x2160@59.994", "59.99"),
        ("eDP-1", "3840x2400", "3840x2400@59.994", "59.99"),
    ]

    @patch("gnome_randr_cycle.GnomeRandrCycler._tar_screenshot")
    @patch("time.sleep", return_value=None)
    @patch("subprocess.check_output")
    @patch("subprocess.run")
    @patch("gnome_randr_cycle.GnomeRandrCycler.get_highest_resolution_info")
    @patch("gnome_randr_cycle.GnomeRandrCycler._create_path")
    @patch("gnome_randr_cycle.GnomeRandrCycler.get_monitor_infos")
    def test_success(
        self,
        mock_monitor,
        mock_path,
        mock_highest,
        mock_run,
        mock_check,
        mock_sleep,
        mock_tar,
    ):
        grc = GnomeRandrCycler()
        mock_path.return_value = "/tmp"
        mock_monitor.return_value = (
            self.test_monitors,
            self.test_current_modes,
        )
        mock_highest.return_value = self.test_highest_modes
        result = grc.monitor_resolution_cycling("", "/tmp")
        self.assertEqual(result, None)
        cmd_mode = "gnome-randr modify eDP-1 -m "
        mock_check.assert_has_calls(
            [
                call(cmd_mode + "1368x768@59.993", shell=True),
                call(cmd_mode + "1400x900@59.993", shell=True),
                call(cmd_mode + "1280x1024@59.994", shell=True),
                call(cmd_mode + "2048x1536@59.994", shell=True),
                call(cmd_mode + "3840x2160@59.994", shell=True),
                call(cmd_mode + "3840x2400@59.994", shell=True),
            ]
        )
        cmd_shot = "gnome-screenshot -f "
        mock_run.assert_has_calls(
            [
                call(
                    cmd_shot + "/tmp/" + "eDP-1_1368x768.jpg",
                    shell=True,
                    check=False,
                ),
                call().returncode.__ne__(0),
                call(
                    cmd_shot + "/tmp/" + "eDP-1_1400x900.jpg",
                    shell=True,
                    check=False,
                ),
                call().returncode.__ne__(0),
                call(
                    cmd_shot + "/tmp/" + "eDP-1_1280x1024.jpg",
                    shell=True,
                    check=False,
                ),
                call().returncode.__ne__(0),
                call(
                    cmd_shot + "/tmp/" + "eDP-1_2048x1536.jpg",
                    shell=True,
                    check=False,
                ),
                call().returncode.__ne__(0),
                call(
                    cmd_shot + "/tmp/" + "eDP-1_3840x2160.jpg",
                    shell=True,
                    check=False,
                ),
                call().returncode.__ne__(0),
                call(
                    cmd_shot + "/tmp/" + "eDP-1_3840x2400.jpg",
                    shell=True,
                    check=False,
                ),
                call().returncode.__ne__(0),
            ]
        )

    @patch("gnome_randr_cycle.GnomeRandrCycler._tar_screenshot")
    @patch("time.sleep", return_value=None)
    @patch("subprocess.check_output")
    @patch("subprocess.run")
    @patch("gnome_randr_cycle.GnomeRandrCycler.get_highest_resolution_info")
    @patch("gnome_randr_cycle.GnomeRandrCycler._create_path")
    @patch("gnome_randr_cycle.GnomeRandrCycler.get_monitor_infos")
    def test_fail(
        self,
        mock_monitor,
        mock_path,
        mock_highest,
        mock_run,
        mock_check,
        mock_sleep,
        mock_tar,
    ):
        grc = GnomeRandrCycler()
        mock_path.return_value = "/tmp"
        mock_monitor.return_value = (
            self.test_monitors,
            self.test_current_modes,
        )
        mock_highest.return_value = self.test_highest_modes
        mock_check.side_effect = subprocess.CalledProcessError(-1, "fail")
        with self.assertRaises(SystemExit):
            grc.monitor_resolution_cycling("", "/tmp")


class GetHighestResolutionInfoTests(unittest.TestCase):
    test_monitors = {
        "eDP-1": OrderedDict(
            [
                (
                    "3840x2400",
                    (
                        3840,
                        Fraction(8, 5),
                        "3840x2400@59.994",
                        "59.99",
                    ),
                ),
                (
                    "3840x2160",
                    (
                        3840,
                        Fraction(16, 9),
                        "3840x2160@59.994",
                        "59.99",
                    ),
                ),
                (
                    "3200x1800",
                    (
                        3200,
                        Fraction(16, 9),
                        "3200x1800@59.994",
                        "59.99",
                    ),
                ),
                (
                    "2880x1620",
                    (
                        2880,
                        Fraction(16, 9),
                        "2880x1620@59.994",
                        "59.99",
                    ),
                ),
                (
                    "2560x1600",
                    (
                        2560,
                        Fraction(8, 5),
                        "2560x1600@59.994",
                        "59.99*",
                    ),
                ),
                (
                    "2560x1440",
                    (
                        2560,
                        Fraction(16, 9),
                        "2560x1440@59.994",
                        "59.99",
                    ),
                ),
                (
                    "2048x1536",
                    (
                        2048,
                        Fraction(4, 3),
                        "2048x1536@59.994",
                        "59.99",
                    ),
                ),
                (
                    "1920x1440",
                    (
                        1920,
                        Fraction(4, 3),
                        "1920x1440@59.994",
                        "59.99",
                    ),
                ),
                (
                    "1856x1392",
                    (
                        1856,
                        Fraction(4, 3),
                        "1856x1392@59.994",
                        "59.99",
                    ),
                ),
                (
                    "1792x1344",
                    (
                        1792,
                        Fraction(4, 3),
                        "1792x1344@59.994",
                        "59.99",
                    ),
                ),
                (
                    "2048x1152",
                    (
                        2048,
                        Fraction(16, 9),
                        "2048x1152@59.994",
                        "59.99",
                    ),
                ),
                (
                    "1920x1200",
                    (
                        1920,
                        Fraction(8, 5),
                        "1920x1200@59.994",
                        "59.99",
                    ),
                ),
                (
                    "1920x1080",
                    (
                        1920,
                        Fraction(16, 9),
                        "1920x1080@59.994",
                        "59.99",
                    ),
                ),
                (
                    "1600x1200",
                    (
                        1600,
                        Fraction(4, 3),
                        "1600x1200@59.994",
                        "59.99",
                    ),
                ),
                (
                    "1680x1050",
                    (
                        1680,
                        Fraction(8, 5),
                        "1680x1050@59.993",
                        "59.99",
                    ),
                ),
                (
                    "1400x1050",
                    (
                        1400,
                        Fraction(4, 3),
                        "1400x1050@59.994",
                        "59.99",
                    ),
                ),
                (
                    "1600x900",
                    (
                        1600,
                        Fraction(16, 9),
                        "1600x900@59.993",
                        "59.99",
                    ),
                ),
                (
                    "1280x1024",
                    (
                        1280,
                        Fraction(5, 4),
                        "1280x1024@59.994",
                        "59.99",
                    ),
                ),
                (
                    "1400x900",
                    (
                        1400,
                        Fraction(14, 9),
                        "1400x900@59.993",
                        "59.99",
                    ),
                ),
                (
                    "1280x960",
                    (
                        1280,
                        Fraction(4, 3),
                        "1280x960@59.994",
                        "59.99",
                    ),
                ),
                (
                    "1440x810",
                    (
                        1440,
                        Fraction(16, 9),
                        "1440x810@59.994",
                        "59.99",
                    ),
                ),
                (
                    "1368x768",
                    (
                        1368,
                        Fraction(57, 32),
                        "1368x768@59.993",
                        "59.99",
                    ),
                ),
                (
                    "1280x800",
                    (
                        1280,
                        Fraction(8, 5),
                        "1280x800@59.994",
                        "59.99",
                    ),
                ),
                (
                    "1280x720",
                    (
                        1280,
                        Fraction(16, 9),
                        "1280x720@59.993",
                        "59.99",
                    ),
                ),
                (
                    "1024x768",
                    (
                        1024,
                        Fraction(4, 3),
                        "1024x768@59.994",
                        "59.99",
                    ),
                ),
                (
                    "960x720",
                    (
                        960,
                        Fraction(4, 3),
                        "960x720@59.994",
                        "59.99",
                    ),
                ),
                (
                    "928x696",
                    (
                        928,
                        Fraction(4, 3),
                        "928x696@59.993",
                        "59.99",
                    ),
                ),
                (
                    "896x672",
                    (
                        896,
                        Fraction(4, 3),
                        "896x672@59.993",
                        "59.99",
                    ),
                ),
                (
                    "1024x576",
                    (
                        1024,
                        Fraction(16, 9),
                        "1024x576@59.993",
                        "59.99",
                    ),
                ),
                (
                    "960x600",
                    (
                        960,
                        Fraction(8, 5),
                        "960x600@59.993",
                        "59.99",
                    ),
                ),
                (
                    "960x540",
                    (
                        960,
                        Fraction(16, 9),
                        "960x540@59.993",
                        "59.99",
                    ),
                ),
                (
                    "800x600",
                    (
                        800,
                        Fraction(4, 3),
                        "800x600@59.994",
                        "59.99",
                    ),
                ),
            ]
        )
    }

    @patch("gnome_randr_cycle.GnomeRandrCycler.get_monitor_infos")
    def test_success(self, mock_monitor):
        grc = GnomeRandrCycler()
        self.assertEqual(
            grc.get_highest_resolution_info(self.test_monitors),
            [
                ("eDP-1", "1368x768", "1368x768@59.993", "59.99"),
                ("eDP-1", "1400x900", "1400x900@59.993", "59.99"),
                ("eDP-1", "1280x1024", "1280x1024@59.994", "59.99"),
                ("eDP-1", "2048x1536", "2048x1536@59.994", "59.99"),
                ("eDP-1", "3840x2160", "3840x2160@59.994", "59.99"),
                ("eDP-1", "3840x2400", "3840x2400@59.994", "59.99"),
            ],
        )


class GetMonitorInfosTests(unittest.TestCase):
    output = "tests/test_data/gnome_randr_output.txt"

    @patch("subprocess.check_output")
    def test_success(self, mock_check):
        grc = GnomeRandrCycler()
        with open(self.output, "r") as f:
            mock_check.return_value = f.read()
            (monitors, current_modes) = grc.get_monitor_infos()
            self.assertEqual(
                monitors,
                {
                    "eDP-1": OrderedDict(
                        [
                            (
                                "3840x2400",
                                (
                                    3840,
                                    Fraction(8, 5),
                                    "3840x2400@59.994",
                                    "59.99",
                                ),
                            ),
                            (
                                "3840x2160",
                                (
                                    3840,
                                    Fraction(16, 9),
                                    "3840x2160@59.994",
                                    "59.99",
                                ),
                            ),
                            (
                                "3200x1800",
                                (
                                    3200,
                                    Fraction(16, 9),
                                    "3200x1800@59.994",
                                    "59.99",
                                ),
                            ),
                            (
                                "2880x1620",
                                (
                                    2880,
                                    Fraction(16, 9),
                                    "2880x1620@59.994",
                                    "59.99",
                                ),
                            ),
                            (
                                "2560x1600",
                                (
                                    2560,
                                    Fraction(8, 5),
                                    "2560x1600@59.994",
                                    "59.99*",
                                ),
                            ),
                            (
                                "2560x1440",
                                (
                                    2560,
                                    Fraction(16, 9),
                                    "2560x1440@59.994",
                                    "59.99",
                                ),
                            ),
                            (
                                "2048x1536",
                                (
                                    2048,
                                    Fraction(4, 3),
                                    "2048x1536@59.994",
                                    "59.99",
                                ),
                            ),
                            (
                                "1920x1440",
                                (
                                    1920,
                                    Fraction(4, 3),
                                    "1920x1440@59.994",
                                    "59.99",
                                ),
                            ),
                            (
                                "1856x1392",
                                (
                                    1856,
                                    Fraction(4, 3),
                                    "1856x1392@59.994",
                                    "59.99",
                                ),
                            ),
                            (
                                "1792x1344",
                                (
                                    1792,
                                    Fraction(4, 3),
                                    "1792x1344@59.994",
                                    "59.99",
                                ),
                            ),
                            (
                                "2048x1152",
                                (
                                    2048,
                                    Fraction(16, 9),
                                    "2048x1152@59.994",
                                    "59.99",
                                ),
                            ),
                            (
                                "1920x1200",
                                (
                                    1920,
                                    Fraction(8, 5),
                                    "1920x1200@59.994",
                                    "59.99",
                                ),
                            ),
                            (
                                "1920x1080",
                                (
                                    1920,
                                    Fraction(16, 9),
                                    "1920x1080@59.994",
                                    "59.99",
                                ),
                            ),
                            (
                                "1600x1200",
                                (
                                    1600,
                                    Fraction(4, 3),
                                    "1600x1200@59.994",
                                    "59.99",
                                ),
                            ),
                            (
                                "1680x1050",
                                (
                                    1680,
                                    Fraction(8, 5),
                                    "1680x1050@59.993",
                                    "59.99",
                                ),
                            ),
                            (
                                "1400x1050",
                                (
                                    1400,
                                    Fraction(4, 3),
                                    "1400x1050@59.994",
                                    "59.99",
                                ),
                            ),
                            (
                                "1600x900",
                                (
                                    1600,
                                    Fraction(16, 9),
                                    "1600x900@59.993",
                                    "59.99",
                                ),
                            ),
                            (
                                "1280x1024",
                                (
                                    1280,
                                    Fraction(5, 4),
                                    "1280x1024@59.994",
                                    "59.99",
                                ),
                            ),
                            (
                                "1400x900",
                                (
                                    1400,
                                    Fraction(14, 9),
                                    "1400x900@59.993",
                                    "59.99",
                                ),
                            ),
                            (
                                "1280x960",
                                (
                                    1280,
                                    Fraction(4, 3),
                                    "1280x960@59.994",
                                    "59.99",
                                ),
                            ),
                            (
                                "1440x810",
                                (
                                    1440,
                                    Fraction(16, 9),
                                    "1440x810@59.994",
                                    "59.99",
                                ),
                            ),
                            (
                                "1368x768",
                                (
                                    1368,
                                    Fraction(57, 32),
                                    "1368x768@59.993",
                                    "59.99",
                                ),
                            ),
                            (
                                "1280x800",
                                (
                                    1280,
                                    Fraction(8, 5),
                                    "1280x800@59.994",
                                    "59.99",
                                ),
                            ),
                            (
                                "1280x720",
                                (
                                    1280,
                                    Fraction(16, 9),
                                    "1280x720@59.993",
                                    "59.99",
                                ),
                            ),
                            (
                                "1024x768",
                                (
                                    1024,
                                    Fraction(4, 3),
                                    "1024x768@59.994",
                                    "59.99",
                                ),
                            ),
                            (
                                "960x720",
                                (
                                    960,
                                    Fraction(4, 3),
                                    "960x720@59.994",
                                    "59.99",
                                ),
                            ),
                            (
                                "928x696",
                                (
                                    928,
                                    Fraction(4, 3),
                                    "928x696@59.993",
                                    "59.99",
                                ),
                            ),
                            (
                                "896x672",
                                (
                                    896,
                                    Fraction(4, 3),
                                    "896x672@59.993",
                                    "59.99",
                                ),
                            ),
                            (
                                "1024x576",
                                (
                                    1024,
                                    Fraction(16, 9),
                                    "1024x576@59.993",
                                    "59.99",
                                ),
                            ),
                            (
                                "960x600",
                                (
                                    960,
                                    Fraction(8, 5),
                                    "960x600@59.993",
                                    "59.99",
                                ),
                            ),
                            (
                                "960x540",
                                (
                                    960,
                                    Fraction(16, 9),
                                    "960x540@59.993",
                                    "59.99",
                                ),
                            ),
                            (
                                "800x600",
                                (
                                    800,
                                    Fraction(4, 3),
                                    "800x600@59.994",
                                    "59.99",
                                ),
                            ),
                        ]
                    )
                },
            )
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
