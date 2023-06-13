#!/usr/bin/env python3
"""prime offload test module."""

import sys
import threading
import subprocess
import time
import re
import json
import argparse
import logging
from enum import IntEnum


class PrimeOffloaderError(IntEnum):
    """
    A class used to define PrimeOffloader Error code

    Attributes
    ----------
    NO_ERROR : int
        process success
    NO_CARD_ID : int
        couldn't find card id
    NO_CARD_NAME : int
        couldn't find card name
    """

    NO_ERROR = 0
    NO_CARD_ID = -1
    NO_CARD_NAME = -2
    OFFLOAD_FAIL = -3
    NOT_SUPPORT_NV_PRIME = -4


class PrimeOffloader:
    """
    A class used to execute process to specific GPU.
    Have to run this as root.

    Attributes
    ----------
    logger : obj
        console log
    check_result : int
        store the result of checking offloading is ok or not.

    Methods
    -------
    find_card_id(pci_name)
        find card id by pci name

    find_card_name(pci_name)
        find card name by pci name

    check_offload(cmd, card_id, card_name)
        check offload status

    check_nv_offload_env()
        check the environment is ok for prime offload

    run_offload_cmd(cmd, pci_name, driver)
        exectue the command that you would like to offload to specific GPU

    main()
        main function for command line processing
    """

    logger = logging.getLogger()

    check_result = PrimeOffloaderError.OFFLOAD_FAIL

    def find_card_id(self, pci_name):
        """
        use pci name to find card id under /sys/kernel/debug/dri

        Parameters
        ----------
        pci_name: pci device name in NNNN:NN:NN.N format
        """
        cmd = f'sudo grep -lr --include=name "{pci_name}" \
        /sys/kernel/debug/dri 2>/dev/null'
        try:
            card_path = subprocess.run(cmd, shell=True,
                                       stdout=subprocess.PIPE,
                                       universal_newlines=True)
            card_id = card_path.stdout.split('/')[5]
            return card_id
        except (ValueError, IndexError):
            return PrimeOffloaderError.NO_CARD_ID

    def find_card_name(self, pci_name):
        """
        use pci name to find card name by lshw

        Parameters
        ----------
        pci_name: pci device name in NNNN:NN:NN.N format
        """
        cmd = 'sudo lshw -c display -json'
        try:
            card_infos = subprocess.run(cmd, shell=True,
                                        stdout=subprocess.PIPE,
                                        universal_newlines=True)
            infos = json.loads(card_infos.stdout)
            for info in infos:
                if pci_name in info['businfo']:
                    return info['product']
        except (ValueError, IndexError):
            return None

    def check_offload(self, cmd, card_id, card_name):
        """
        checking command is running

        Parameters
        ----------
        cmd: command that running under prime offload

        card_id: card id of dri device
        """
        cmd_without_args = cmd.split(' ')[0]
        for index in range(11):
            time.sleep(2)
            try:
                read_clients_cmd = \
                    f"sudo cat /sys/kernel/debug/dri/{card_id}/clients"
                clients = subprocess.run(read_clients_cmd, shell=True,
                                         stdout=subprocess.PIPE,
                                         universal_newlines=True)
                if cmd_without_args in clients.stdout:
                    self.logger.info(f"Find process [{cmd}] running on "
                                     f"specific GPU\n[{card_id}]"
                                     f"[{card_name}]\n")
                    self.check_result = PrimeOffloaderError.NO_ERROR
                    return
                self.check_result = PrimeOffloaderError.OFFLOAD_FAIL
            except OSError:
                # Missing file or permissions?
                self.logger.info("Couldn't open file for"
                                 "reading clients of dri device")
                self.check_result = PrimeOffloaderError.OFFLOAD_FAIL
                return
        self.logger.info(f"Couldn't find process [{cmd}]"
                         f" running after check {index} times")
        self.check_result = PrimeOffloaderError.OFFLOAD_FAIL

    def check_nv_offload_env(self):
        """
        prime offload of nvidia driver is limited.
        Only on-demand is supported.
        """
        # check prime-select to make sure system with nv driver.
        # If no nv driver, prime offload is fine for other drivers.
        ps = subprocess.run("whereis prime-select | cut -d ':' -f 2",
                            shell=True,
                            stdout=subprocess.PIPE,
                            universal_newlines=True)
        if 'prime-select' not in ps.stdout:
            return PrimeOffloaderError.NO_ERROR

        # prime offload could running on on-demand mode only
        mode = subprocess.run("prime-select query",
                              shell=True,
                              stdout=subprocess.PIPE,
                              universal_newlines=True)
        if "on-demand" not in mode.stdout:
            return PrimeOffloaderError.NOT_SUPPORT_NV_PRIME

        # prime offload couldn't running on nvlink active
        nvlink = subprocess.run("nvidia-smi nvlink -s",
                                shell=True,
                                stdout=subprocess.PIPE,
                                universal_newlines=True)
        if (not re.search('inactive', nvlink.stdout, re.IGNORECASE)
                and len(nvlink.stdout) != 0):
            return PrimeOffloaderError.NOT_SUPPORT_NV_PRIME

        return PrimeOffloaderError.NO_ERROR

    def run_offload_cmd(self, cmd, pci_name, driver, timeout):
        """
        run offload command and check it runs on correct GPU

        Parameters
        ----------
        cmd: command that running under prime offload

        pci_name: pci device name in NNNN:NN:NN.N format

        driver: GPU driver, such as i915, amdgpu, nvidia
        """
        card_id = self.find_card_id(pci_name)
        if card_id == PrimeOffloaderError.NO_CARD_ID:
            self.logger.info("Couldn't find card id,"
                             " please check your pci name")
            return PrimeOffloaderError.NO_CARD_ID

        card_name = self.find_card_name(pci_name)
        if card_name is None:
            self.logger.info("Couldn't find card name,"
                             " please check your pci name")
            return PrimeOffloaderError.NO_CARD_NAME

        # run offload command in other process
        dri_pci_name_format = re.sub("[:.]", "_", pci_name)

        if timeout > 0:
            tmp_cmd = f"timeout {timeout} {cmd}"
        else:
            tmp_cmd = cmd

        if driver in ('nvidia', 'pcieport'):
            offload_cmd = f"__NV_PRIME_RENDER_OFFLOAD=1" \
                          f" __GLX_VENDOR_LIBRARY_NAME=nvidia {tmp_cmd}"
        else:
            offload_cmd = f"DRI_PRIME=pci-{dri_pci_name_format} {tmp_cmd}"

        # if nv driver under nvidia mode, prime/reverse prime couldn't work.
        if self.check_nv_offload_env() \
           == PrimeOffloaderError.NOT_SUPPORT_NV_PRIME:
            self.logger.info("Couldn't use nv prime offload"
                             " on this system environment")
            offload_cmd = f"{tmp_cmd}"
        else:
            # use other thread to check offload is correctly or not
            check_thread = threading.Thread(target=self.check_offload,
                                            args=(cmd, card_id, card_name))
            check_thread.start()

        offload = subprocess.Popen(offload_cmd,
                                   shell=True,
                                   stdout=subprocess.PIPE,
                                   universal_newlines=True)

        self.logger.info(f"offload command:[{offload_cmd}]")

        # redirect offload command output real time
        while offload.poll() is None:
            line = offload.stdout.readline().strip()
            self.logger.info(line)
        return PrimeOffloaderError.NO_ERROR

    def main(self) -> int:
        """
        main function for command line processing
        """
        parser = argparse.ArgumentParser(
            prog="Prime offload tester",
            description="Test prime offload feature",
        )

        parser.add_argument(
            "-c", "--command", type=str, default='glxgears',
            help='command to offload to specific GPU (default: %(default)s)'
        )
        parser.add_argument(
            "-p", "--pci", type=str, default='0000:00:02.0',
            help='pci name in NNNN:NN:NN.N format (default: %(default)s)'
        )
        parser.add_argument(
            "-d", "--driver", type=str, default='i915',
            help='Type of GPU driver (default: %(default)s)'
        )
        parser.add_argument(
            "-t", "--timeout", type=int, default=0,
            help='executing command duration in second (default: %(default)s)'
        )

        args = parser.parse_args()

        # create self.logger.formatter
        log_formatter = logging.Formatter(fmt='%(message)s')

        # create logger
        self.logger.setLevel(logging.INFO)

        # create console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_formatter)

        # Add console handler to logger
        self.logger.addHandler(console_handler)

        # run_offload_cmd("glxgears", "0000:00:02.0", "i915", 0)
        self.run_offload_cmd(args.command, args.pci, args.driver, args.timeout)

        return self.check_result


if __name__ == "__main__":
    sys.exit(PrimeOffloader().main())
