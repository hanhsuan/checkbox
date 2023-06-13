#!/usr/bin/env python3
"""prime offload test module."""

import sys
import threading
import subprocess
import time
import re
import json
import argparse
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


class PrimeOffloader:
    """
    A class used to execute process to specific GPU.
    Have to run this as root.

    Attributes
    ----------
    version : str
        store the distribution of test environment
    report_dict : dict
        dict to store test information in different result status

    Methods
    -------
    process(args)
        process target file to generate test report in desired format
    main()
        main function for command line processing
    """

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
                read_clients_cmd = f"sudo cat /sys/kernel/debug/dri/{card_id}/clients"
                clients = subprocess.run(read_clients_cmd, shell=True,
                                         stdout=subprocess.PIPE,
                                         universal_newlines=True)
                if cmd_without_args in clients.stdout:
                    print(f"Find process [{cmd}] running on "
                          f"specific GPU\n[{card_id}][{card_name}]\n")
                    return
            except OSError:
                # Missing file or permissions?
                print("Couldn't open file for reading clients of dri device")
                return
        print(f"Couldn't find process [cmd] running after check {index} times")

    def run_offload_cmd(self, cmd, pci_name, driver):
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
            print("Couldn't find card id, please check your pci name")
            return PrimeOffloaderError.NO_CARD_ID

        card_name = self.find_card_name(pci_name)
        if card_name is None:
            print("Couldn't find card name, please check your pci name")
            return PrimeOffloaderError.NO_CARD_NAME

        # run offload command in other process
        dri_pci_name_format = re.sub("[:.]", "_", pci_name)
        if driver in ('nvidia', 'pcieport'):
            offload_cmd = f"__NV_PRIME_RENDER_OFFLOAD=1" \
                          f" __GLX_VENDOR_LIBRARY_NAME=nvidia {cmd}"
        else:
            offload_cmd = f"DRI_PRIME=pci-{dri_pci_name_format} {cmd}"

        offload = subprocess.Popen(offload_cmd,
                                   shell=True,
                                   stdout=subprocess.PIPE,
                                   universal_newlines=True)

        print(f"offload command:[{offload_cmd}]")

        # use other thread to check offload is correctly or not
        check_thread = threading.Thread(target=self.check_offload,
                                        args=(cmd, card_id, card_name))
        check_thread.start()

        # redirect offload command output real time
        while offload.poll() is None:
            line = offload.stdout.readline().strip()
            print(line)
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

        args = parser.parse_args()

        # run_offload_cmd("glxgears", "0000:00:02.0", "i915")
        self.run_offload_cmd(args.command, args.pci, args.driver)


if __name__ == "__main__":
    sys.exit(PrimeOffloader().main())
