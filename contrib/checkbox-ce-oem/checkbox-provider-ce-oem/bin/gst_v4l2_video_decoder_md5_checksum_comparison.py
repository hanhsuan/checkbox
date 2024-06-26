#!/usr/bin/env python3
# This file is part of Checkbox.
#
# Copyright 2024 Canonical Ltd.
# Written by:
#   Patrick Chang <patrick.chang@canonical.com>
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
# along with Checkbox. If not, see <http://www.gnu.org/licenses/>.

import argparse
import logging
import os
import re
import shlex
import subprocess
from typing import Any

logging.basicConfig(level=logging.INFO)


def register_arguments():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Script helps verify the MD5 checksum from specific Gstreamer"
            " Decoder with different resolutions and color spaces is exactly"
            " match golden reference"
        ),
    )

    parser.add_argument(
        "-gp",
        "--golden_sample_path",
        required=True,
        type=str,
        help="Path of Golden Sample file",
    )

    parser.add_argument(
        "-gmp",
        "--golden_sample_md5_checksum_path",
        required=True,
        type=str,
        help="Path of Golden Sample's MD5 chekcusm",
    )

    parser.add_argument(
        "-dp",
        "--decoder_plugin",
        required=True,
        type=str,
        help="Decoder plugin be used in gstreamer pipeline e.g. v4l2h264dec",
    )

    parser.add_argument(
        "-cs",
        "--color_space",
        required=True,
        type=str,
        help="Color space be used in gstreamer format e.g. I420 or NV12",
    )

    args = parser.parse_args()
    return args


def build_gst_command(
    gst_bin: str, golden_sample_path: str, decoder: str, color_sapce: str
) -> str:
    """
    Builds a GStreamer command to process the golden sample.

    :param gst_bin:
        The binary name of gstreamer. Default is "gst-launch-1.0"
        You can assign the snap name to GST_LAUNCH_BIN env variable if you
        want to using snap.
    :param golden_sample:
        The path to the golden sample file.
    :param decoder:
        The decoder to use for the video, e.g., "v4l2vp8dec", "v4l2vp9dec".
    :param color_space:
        The desired color space format for the output, e.g., "I420", "NV12".

    :returns:
        The GStreamer command to execute.
    """
    if decoder in ["v4l2vp8dec", "v4l2vp9dec"]:
        x_raw_format_str = ""
    else:
        x_raw_format_str = "video/x-raw,format={} ! ".format(color_sapce)

    cmd = (
        "{} -v filesrc location={} ! parsebin ! {} ! v4l2convert ! {}"
        "checksumsink hash=0 sync=false"
    ).format(gst_bin, golden_sample_path, decoder, x_raw_format_str)

    return cmd


def get_md5_checksum_from_command(cmd: str) -> str:
    """
    Executes the GStreamer command and extracts the MD5 checksums.

    :param cmd:
        The GStreamer command to execute.

    :returns:
        The extracted MD5 checksums.
    """
    try:
        logging.info("Starting command: '{}'".format(cmd))
        ret = subprocess.run(
            shlex.split(cmd),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            timeout=30,
        )
        md5_data = extract_the_md5_checksum(ret.stdout)
        return md5_data
    except Exception as e:
        logging.error(e.stderr)
        raise SystemExit(e.returncode)


def extract_the_md5_checksum(intput: str) -> str:
    """
    Extracts the MD5 checksums from the given input string.

    :param intput:
        The input string containing the MD5 checksums.

    :returns:
        The extracted MD5 checksums.
    """
    pattern = r"^(\d+:\d+:\d+\.\d+) ([0-9a-f]+)$"
    checksums = re.findall(pattern, intput, re.MULTILINE)
    output = ""
    for checksum in checksums:
        output += checksum[1] + os.linesep
    return output


def validate_video_decoder_md5_checksum(args: Any) -> None:
    """
    Validates the MD5 checksum of the output generated by a video decoder with
    specific resolution and color space.

    This function performs the following steps:

    1. Checks if the golden sample file and the golden MD5 checksum file exist.
    2. Builds a GStreamer command to process the golden sample using the
        specified decoder and color space.
    3. Executes the GStreamer command and extracts the MD5 checksums from the
        output.
    4. Reads the golden MD5 checksum from the file.
    5. Compares the extracted MD5 checksum with the golden MD5 checksum.
    6. If the checksums match, logs a "Pass" message. If they don't match,
        logs the golden MD5 checksum and raises a `SystemExit` exception.

    :param args:
        An object containing the following attributes:
            - `golden_sample_path` (str): The path to the golden sample file.
            - `golden_sample_md5_checksum_path` (str): The path to the file
                containing the golden MD5 checksum.
            - `decoder_plugin` (str): The video decoder to use, e.g.,
                "v4l2vp8dec", "v4l2vp9dec".
            - `color_space` (str): The desired color space format for the
                output, e.g., "I420", "NV12".

    :raises SystemExit:
        If the golden sample file or the golden MD5 checksum file does not
        exist, or if the extracted MD5 checksum does not match the golden MD5
        checksum.
    """
    # Check the golden sample and golden MD5 checksum exixt
    if not os.path.exists(args.golden_sample_path):
        raise SystemExit(
            "Golden Sample '{}' doesn't exist".format(args.golden_sample_path)
        )
    if not os.path.exists(args.golden_sample_md5_checksum_path):
        raise SystemExit(
            "Golden Sample's MD5 checksum '{}' doesn't exist".format(
                args.golden_sample_md5_checksum_path
            )
        )
    # Run command to get comapred md5 checksum by consuming golden sample
    gst_launch_bin = os.getenv("GST_LAUNCH_BIN", "gst-launch-1.0")
    cmd = build_gst_command(
        gst_bin=gst_launch_bin,
        golden_sample_path=args.golden_sample_path,
        decoder=args.decoder_plugin,
        color_sapce=args.color_space,
    )
    compared_md5_data = get_md5_checksum_from_command(cmd).rstrip(os.linesep)

    logging.info(
        "===== MD5 Checksum: {} ====\n{}\n".format(
            args.golden_sample_path, compared_md5_data
        )
    )
    # Read the Golden Sample's MD5 checksum and compare it
    # with compared_md5_data data
    with open(
        args.golden_sample_md5_checksum_path, mode="r", encoding="UTF-8"
    ) as gf:
        golden_content = gf.read().rstrip(os.linesep)
        if golden_content == compared_md5_data:
            logging.info("Pass. MD5 checksum is same as Golden Sample")
        else:
            logging.info(
                "===== Golden MD5 Checksum: {} ====\n{}\n".format(
                    args.golden_sample_md5_checksum_path, golden_content
                )
            )
            raise SystemExit(
                "Failed. MD5 checksum is not same as Golden Sample"
            )


def main() -> None:
    args = register_arguments()
    validate_video_decoder_md5_checksum(args)


if __name__ == "__main__":
    main()
