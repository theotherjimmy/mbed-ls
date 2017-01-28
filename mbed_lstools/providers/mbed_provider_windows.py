import os
import sys

ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, ROOT)

from mbed_provider import MbedProvider
from mbed_ls_utils import run_cli_process

import string
import re
import logging
if sys.version_info[0] < 3:
    import _winreg as winreg
else:
    import winreg

class MbedProviderWindows(MbedProvider):
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def _iter_keys(self, key):
        """! Iterate over subkeys of a key returning subkey as string
        """
        for i in range(winreg.QueryInfoKey(key)[0]):
            yield winreg.EnumKey(key, i)

    def _iter_vals(self, key):
        """! Iterate over values of a key
        """
        for i in range(winreg.QueryInfoKey(key)[1]):
            yield winreg.EnumValue(key, i)
    
    def _get_com_port(self, target_id, is_prefix=False):
        # Query the registry for all USB enumerations
        enums_usb = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SYSTEM\CurrentControlSet\Enum\USB')
        for vid_entry_key in self._iter_keys(enums_usb):
            vid_entry = winreg.OpenKey(enums_usb, vid_entry_key)
            device_entries = []
            try:
                device_entries.append(winreg.OpenKey(vid_entry, target_id))
            except WindowsError:
                pass
            
            if is_prefix:
                for child_entry in self._iter_keys(vid_entry):
                    if target_id in child_entry:
                        device_entries.append(winreg.OpenKey(vid_entry, child_entry))

            for device_entry in device_entries:
                try:
                    param = winreg.OpenKey(device_entry, "Device Parameters")
                    port = winreg.QueryValueEx(param, 'PortName')[0]
                    # Found a valid serial port, return now
                    return port
                except WindowsError:
                    pass
                
                # Try following a symbolic device link
                try:
                    parent_id = winreg.QueryValueEx(device_entry, 'ParentIdPrefix')[0]
                    # Retry with the parent id prefix (being sure to indicate that is a prefix)
                    port = self._get_com_port(parent_id, is_prefix=True)
                    if port:
                        return port
                except WindowsError:
                    pass
        
        return None
    
    def list_mbeds(self):
        mbeds = {}
        
        # Query registry for all mounted volumes
        mount_point_entries = []
        mounted_entries = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 'SYSTEM\MountedDevices')
        for mounted_entry in self._iter_vals(mounted_entries):
            mount_point_entries.append({
                'key_name': mounted_entry[0],
                'key_data': mounted_entry[1]
            })
        
        # Find all valid mount points and target IDs
        for mount_point_entry in mount_point_entries:
            if 'DosDevices' in mount_point_entry['key_name']:
                printable_key_data = filter(lambda char: char in string.printable, mount_point_entry['key_data'])
                for usb_vendor in self.USB_VENDOR_LIST:
                    if usb_vendor.upper() in printable_key_data.upper():
                        # TargetID is a hex string with 10-48 chars
                        m = re.search('[&#]([0-9A-Za-z]{10,48})[&#]', printable_key_data)
                        if m:
                            tid = m.group(1)
                            mountpoint = re.match('.*\\\\(.:)$', mount_point_entry['key_name']).group(1)
                            mbeds[tid] = {
                                'mount_point': mountpoint,
                                'target_id_usb_id': tid,
                                'target_id': tid
                            }
                        
                        break
        
        for target_id in mbeds:
            serial_port = self._get_com_port(target_id)
            mbeds[target_id]['serial_port'] = serial_port
                        
        return mbeds
    
    def mount_point_ready(self, path):
        """! Check if a mount point is ready for file operations
        @return Returns True if the given path exists, False otherwise
        @details Calling the Windows command `dir` instead of using the python
        `os.path.exists`. The latter causes a Python error box to appear claiming
        there is "No Disk" for some devices that are in the ejected state. Calling
        `dir` prevents this since it uses the Windows API to determine if the
        device is ready before accessing the file system.
        """
        stdout, stderr, retcode = run_cli_process('dir %s' % path)
        result = True if retcode == 0 else False

        if result:
            self.logger.debug("Mount point %s is ready" % path)
        else:
            self.logger.debug("Mount point %s reported not ready with error '%s'" % (path, stderr.strip()))

        return result
        
    