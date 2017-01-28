import os
import sys

ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, ROOT)

from mbed_provider import MbedProvider
from mbed_ls_utils import run_cli_process

import string
import re
import logging

class MbedProviderLinux(MbedProvider):
    HEX_UUID_PATTERN_STRIGN = "usb-[0-9a-zA-Z_-]*_([0-9a-zA-Z]*)-.*"
    # Since Ubuntu 15 DAplink serial port device can have pci- prefix, not only usb- one
    NAME_LINK_PATTERN_STRING = '((%s)-[0-9a-zA-Z_-]*_[0-9a-zA-Z]*-.*$)'% ('|'.join(["pci", "usb"]))
    DISK_STRINGS = ['mbed', 'segger']

    def __init__(self, **kwargs):
        """! ctor
        """
        self.logger = logging.getLogger(__name__)

        self.name_link_pattern = re.compile(self.NAME_LINK_PATTERN_STRING)
        self.hex_uuid_pattern = re.compile(self.HEX_UUID_PATTERN_STRIGN)

    def list_mbeds(self):
        """! Returns detailed list of connected mbeds
        @return Returns list of structures with detailed info about each mbed
        @details Function returns list of dictionaries with mbed attributes such as mount point, TargetID name etc.
        Function returns mbed list with platform names if possible
        all_devices =
        [
            ['*not detected', 'sdi', '/media/usb3', '/dev/ttyACM7', 'usb-MBED_microcontroller_066EFF534951775087215736-0:0 -> ../../sdi'],
            ['*not detected', 'sdg', '/media/usb5', '/dev/ttyACM5', 'usb-MBED_microcontroller_066EFF525257775087141721-0:0 -> ../../sdg'],
            ['*not detected', 'sdf', '/media/przemek/NUCLEO', '/dev/ttyACM4', 'usb-MBED_microcontroller_0671FF534951775087131543-0:0 -> ../../sdf'],
            ['*not detected', 'sdd', '/media/usb4', '/dev/ttyACM2', 'usb-MBED_microcontroller_0670FF494951785087152739-0:0 -> ../../sdd'],
            ['*not detected', 'sdb', '/media/usb0', '/dev/ttyACM0', 'usb-MBED_microcontroller_0674FF484951775087083114-0:0 -> ../../sdb'],
            ['*not detected', 'sdh', '/media/usb6', '/dev/ttyACM6', 'usb-MBED_microcontroller_066FFF525257775087155144-0:0 -> ../../sdh'],
            ['*not detected', 'sdc', '/media/usb1', '/dev/ttyACM1', 'usb-MBED_microcontroller_066AFF494956805087155327-0:0 -> ../../sdc'],
            ['*not detected', 'sde', '/media/usb2', '/dev/ttyACM3', 'usb-MBED_microcontroller_066CFF534951775087112139-0:0 -> ../../sde']
        ]
        MBED format
        {
            'mount_point' : <>,
            'serial_port' : <>,
            'target_id' : <>,
            'platform_name' : <>,
        }
        TIDS format
        {
            "1168": "LPC11U68",
            "1549": "LPC1549",
            "1070": "NRF51822",
            "0200": "KL25Z",
            "0220": "KL46Z",
            "0230": "K20D50M",
            "0240": "K64F"
        }
        """
        # We harness information about what is mounted and connected to serial ports
        disk_ids = self.get_dev_by_id('disk')
        serial_ids = self.get_dev_by_id('serial')
        mount_ids = self.get_mounts()

        # Listing known and undetected / orphan devices
        all_devices = self.get_detected(disk_ids, serial_ids, mount_ids)
        self.ERRORLEVEL_FLAG = 0

        result = {}
        tidpattern = re.compile(r'_([0-9a-zA-Z]+)-\d+:\d+')
        for device in all_devices:
            tid = None
            m = tidpattern.search(device[3])
            if m and len(m.groups()):
                tid = m.group(1)

            result[tid] = {'mount_point' : device[1],
                    'serial_port' : device[2],
                    'target_id' : tid,
                    'target_id_usb_id' : tid,
            }

        return result

    # Private methods

    def get_dev_by_id_cmd(self, subdir):
        """! Calls command line 'ls' to get devices by their ids
        @details Uses Linux shell command: 'ls -oA /dev/disk/by-id/'
        @return tuple(stdout lines, retcode)
        """
        cmd = 'ls -oA /dev/' + subdir + '/by-id/'
        _stdout, _, retval = run_cli_process(cmd)
        return (_stdout.splitlines(), retval)

    def get_dev_by_id_process(self, lines, retval):
        """! Remove unnecessary lines from command line output
        """
        result = []
        if not retval:
            for line in lines:
                line = line.rstrip()
                if type(line) == type(bytes()):
                    line = line.decode('utf8')
                if not line.lower().startswith('total '):    # total 0
                    result.append(line)
                    self.logger.debug(line)
        return result

    def get_dev_by_id(self, subdir):
        """! Lists disk devices by id
        @return List of strings from 'ls' command executed in shell
        """
        lines, retval = self.get_dev_by_id_cmd(subdir)
        return self.get_dev_by_id_process(lines, retval)

    def get_mounts(self):
        """! Lists mounted devices with vfat file system (potential mbeds)
        @result Returns list of all mounted vfat devices
        @details Uses Linux shell command: 'mount | grep vfat'
        """
        result = []
        cmd = 'mount | grep vfat'

        self.logger.debug(cmd)

        _stdout, _, retval = run_cli_process(cmd)

        if not retval:
            for line in _stdout.splitlines():
                line = line.rstrip()
                result.append(line)
                self.logger.debug(line)
        return result

    def get_disk_hex_ids(self, disk_list):
        """! Get only hexadecimal IDs for mbed disks
        @param disk_list List of disks in a system with USBID decoration
        @return Returns map of disks and corresponding disks' Hex ids
        @details Uses regular expressions to get Hex strings (TargeTIDs) from list of disks
        """
        disk_hex_ids = {}
        for dl in disk_list:
            m = self.name_link_pattern.search(dl)
            if m and len(m.groups()):
                disk_link = m.group(1)
                m = self.hex_uuid_pattern.search(disk_link)
                if m and len(m.groups()):
                    disk_hex_ids[m.group(1)] = disk_link
        return disk_hex_ids

    def get_mbed_serial(self, serial_list, dhi):
        """! Get mbed serial by unique hex id (dhi) in disk name
        @param serial_list List of all serial ports
        @param dhi Unique Hex id of possible mbed device
        @return Returns None if corresponding serial device is not found, else returns serial device path
        @details Devices are located in Linux '/dev/' directory structure
        """
        for sl in serial_list:
            if dhi in sl:
                m = self.name_link_pattern.search(sl)
                if m and len(m.groups()):
                    serial_link = m.group(1)
                    mbed_dev_serial = "/dev/" + self.get_dev_name(serial_link)
                    return mbed_dev_serial
        return None

    def get_detected(self, disk_list, serial_list, mount_list):
        """! Find all known mbed devices and assign name by targetID
        @param disk_list List of disks (mount points in /dev/disk)
        @param serial_list List of serial devices (serial ports in /dev/serial)
        @param mount_list List of lines from 'mount' command
        @return list of lists [mbed_name, mbed_dev_disk, mbed_mount_point, mbed_dev_serial, disk_hex_id]
        @details Find for all disk connected all MBED ones we know about from TID list
        """
        # Find for all disk connected all MBED ones we know about from TID list
        valid_disks = []

        for disk in disk_list:
            valid_disk_found = False
            for disk_string in self.DISK_STRINGS:
                if disk_string in disk.lower():
                    valid_disks.append(disk)
                    valid_disk = True
                    break

            if valid_disk_found:
                break

        disk_hex_ids = self.get_disk_hex_ids(valid_disks)
        self.logger.debug('disk_hex_ids:' + str(disk_hex_ids))
        result = []

        # Search if we have
        for dhi in disk_hex_ids.keys():
            mbed_dev_disk = ""
            mbed_dev_serial = ""

            disk_link = disk_hex_ids[dhi]
            # print "Fount MBED disk: " + disk_link #mbed_name + ": " + mttm + " (" + dhi + ")"
            mbed_dev_disk = self.get_dev_name(disk_link) # m.group(1) if m and len(m.groups()) else "unknown"
            mbed_dev_serial = self.get_mbed_serial(serial_list, dhi)
            # Print detected device
            mbed_mount_point = self.get_mount_point(mbed_dev_disk, mount_list)
            if mbed_mount_point:
                result.append([mbed_dev_disk, mbed_mount_point, mbed_dev_serial, disk_hex_ids[dhi]])
        return result

    def get_dev_name(self, link):
        """! Get device name from symbolic link list
        """
        device_sufix_pattern = ".*/([a-zA-Z0-9]*)$"
        dsp = re.compile(device_sufix_pattern)
        m = dsp.search(link)
        mbed_dev = m.group(1) if m and len(m.groups()) else "unknown"
        return mbed_dev

    def get_mount_point(self, dev_name, mount_list):
        """! Find mount points for MBED devices using mount command output
        @param dev_name Device name (e.g 'sda')
        @param mount_list List of all mounted devices (strings from Linux mount shell command)
        @return Returns None if mount point not found. Else returns device mount path
        @details We want to scan names of mount points like this:
        /media/MBED_xxx
        /media/MBED__xxx
        /media/MBED-xxx
        """
        mount_media_pattern = "^/[a-zA-Z0-9/]*/" + dev_name  + " on (/[a-zA-Z0-9_\-/]*) "
        mmp = re.compile(mount_media_pattern)
        for mount in mount_list:
            m = mmp.search(mount)
            if m and len(m.groups()):
                return m.group(1)
        return None
