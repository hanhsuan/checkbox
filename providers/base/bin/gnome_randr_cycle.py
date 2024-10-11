#!/usr/bin/env python3
#
# This file is part of Checkbox.
#
# Copyright 2022 Canonical Ltd.
# Written by:
#   Sylvain Pineau <sylvain.pineau@canonical.com>
#
# Checkbox is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3,
# as published by the Free Software Foundation.
#
# Checkbox is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Checkbox.  If not, see <http://www.gnu.org/licenses/>.

from collections import OrderedDict
from fractions import Fraction
import subprocess
import argparse
import logging
import tarfile
import time
import sys
import os


class GnomeRandrCycler:
    """
    A class used to changing the screen resoulation.

    :attr logger: console logger
    :type logger: RootLogger
    """

    logger = logging.getLogger()

    def get_monitor_infos(self) -> (dict, list):
        """
        Get monitor information from gnome-randr
        """
        randrinfo = subprocess.check_output(
            "gnome-randr", shell=True, universal_newlines=True
        )
        output = randrinfo.split("\n")

        monitor = ""
        monitors = dict()
        # remember the user's current settings for cleanup later
        current_modes = []
        for line in output:
            # Ignore Interlaced modes that are indicated by presence of a
            # trailing 'i' character.
            if ":" in line or line == "" or "i@" in line:
                continue
            if not (line.startswith(" ") or line.startswith("\t")):
                try:
                    monitor = line.split()[0]
                    monitors[monitor] = OrderedDict()
                    continue
                except IndexError:
                    continue
            if monitor:
                modeline = line.split()
                try:
                    mode, resolution, rate = modeline[:3]
                    # ignore preferred for rate
                    rate = rate.replace("+", "")
                    width, height = [int(x) for x in resolution.split("x")]
                    aspect = Fraction(width, height)
                    if width < 675 or width / aspect < 530:
                        continue
                    if "*" in rate:
                        current_modes.append(
                            (monitor, resolution, mode, rate)
                        )
                    if resolution in monitors[monitor]:
                        rate = rate.replace("*", "")
                        existing_rate = monitors[monitor][resolution][3]
                        if float(rate) < float(existing_rate):
                            continue
                    monitors[monitor][resolution] = (
                        width,
                        aspect,
                        mode,
                        rate,
                    )
                except IndexError:
                    continue
                except ValueError as e:
                    self.logger.info(
                        "Invalid refresh rate format: {}".format(e)
                    )
                    continue
        return (monitors, current_modes)

    def get_highest_resolution_info(self, monitors: dict) -> list:
        """
        Get highest resolution for each monitor

        :param monitors: monitors information
        """
        highest_modes = []  # list of highest-res modes for each aspect ratio
        for monitor in monitors.keys():
            # let's create a dict of aspect_ratio:largest_width for each
            # display (width, because it's easier to compare simple
            # ints when looking for the highest value).
            top_res_per_aspect = OrderedDict()
            for resolution in monitors[monitor]:
                width, aspect, mode, rate = monitors[monitor][resolution]
                cur_max = top_res_per_aspect.get(aspect, 0)
                top_res_per_aspect[aspect] = max(cur_max, width)
            for aspect_ratio, max_width in reversed(
                top_res_per_aspect.items()
            ):
                for resolution in monitors[monitor]:
                    width, aspect, mode, rate = monitors[monitor][resolution]
                    if aspect == aspect_ratio and width == max_width:
                        highest_modes.append(
                            (monitor, resolution, mode, rate)
                        )
        return highest_modes

    def monitor_resolution_cycling(self, keyword: str, screenshot_dir: str):
        """
        Loop changing the resolution

        :param keyword: A keyword to distinguish the screenshots
                        taken in this run of the script

        :param screenshot_dir: Specify a directory to store screenshots in.
        """
        failures = 0  # count the number of failed modesets

        screenshot_path = os.path.join(screenshot_dir, "xrandr_screens")

        if keyword:
            screenshot_path = screenshot_path + "_" + keyword
        os.makedirs(screenshot_path, exist_ok=True)

        (monitors, current_modes) = self.get_monitor_infos()

        highest_modes = self.get_highest_resolution_info(monitors)

        for monitor, resolution, mode, rate in highest_modes + current_modes:
            rate = rate.replace("+", "").replace("*", "")
            self.logger.info(
                "Set mode {}@{} for output {}".format(
                    resolution, rate, monitor
                )
            )
            cmd = "gnome-randr modify " + monitor + " -m " + mode
            try:
                subprocess.run(
                    cmd, check=True, shell=True, stdout=subprocess.PIPE
                )
                mode_string = monitor + "_" + resolution
                filename = os.path.join(screenshot_path, mode_string + ".jpg")
                cmd = "gnome-screenshot -f " + filename
                result = subprocess.run(cmd, shell=True, check=False)
                if result.returncode != 0:
                    self.logger.error(
                        "Could not capture screenshot -\n"
                        "you may need to install the package"
                        "'gnome-screenshot'."
                    )
            except subprocess.CalledProcessError:
                failures = failures + 1
                self.logger.error(
                    "Failed to set mode {} for output {}:".format(
                        mode, monitor
                    )
                )
            time.sleep(8)  # let the hardware recover a bit

        # Tar up the screenshots for uploading
        try:
            with tarfile.open(screenshot_path + ".tgz", "w:gz") as screen_tar:
                for screen in os.listdir(screenshot_path):
                    screen_tar.add(screenshot_path + "/" + screen, screen)
        except (IOError, OSError):
            pass

        if failures != 0:
            raise SystemExit(
                "There are {} fails during test".format(failures)
            )

    def parse_args(self, args=sys.argv[1:]):
        """
        command line arguments parsing

        :param args: arguments from sys
        :type args: sys.argv
        """
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--keyword",
            default="",
            help=(
                "A keyword to distinguish the screenshots "
                "taken in this run of the script"
            ),
        )
        parser.add_argument(
            "--screenshot-dir",
            default=os.environ["HOME"],
            help=(
                "Specify a directory to store screenshots in. "
                "Default is %(default)s"
            ),
        )
        return parser.parse_args(args)

    def main(self):
        args = self.parse_args()

        # create self.logger.formatter
        log_formatter = logging.Formatter(fmt="%(message)s")

        # create logger
        self.logger.setLevel(logging.INFO)

        # create console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_formatter)

        # Add console handler to logger
        self.logger.addHandler(console_handler)

        self.monitor_resolution_cycling(args.keyword, args.screenshot_dir)


if __name__ == "__main__":
    GnomeRandrCycler().main()
