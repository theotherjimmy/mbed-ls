"""
mbed SDK
Copyright (c) 2017 ARM Limited

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from enum import Enum
import logging
logger = logging.getLogger("mbedls.warnings")
del logging

class Warnings(Enum):
    """Warnings that may occur during the processing of a single device being
    listed, that mbedls is able to work around
    """
    NoHtmId = "Could not find a target id in MBED.HTM"
    NoHtmFile = "Could not open MBED.HTM"
    NoMountPoint = "Mount point not found"
    NoDeviceTxt = "Could not open DEVICE.TXT"
    BadDeviceTxtParse = "Could not parse Device.txt"
    PlatformNotFound = "Device not found in platform database"


_WARNING_SUBSETS = {
    Warnings.NoMountPoint: set([Warnings.NoHtmId, Warnings.NoHtmFile,
                                Warnings.BadDeviceTxtParse, Warnings.NoDeviceTxt]),
    Warnings.NoHtmFile: set([Warnings.NoHtmId]),
    Warnings.NoDeviceTxt: set([Warnings.BadDeviceTxtParse]),
}

_WARNING_SUPERSETS = {sub: set(sup for sup, over in _WARNING_SUBSETS.items()
                             if sub in over)
                    for sub in Warnings}

def warn(device_dict, warning):
    """ Add a warning to a device
    """
    assert warning in Warnings
    device_dict.setdefault("warnings", [])
    if not any(sup in device_dict["warnings"] for sup in _WARNING_SUPERSETS[warning]):
        logger.debug("adding warning %s to device %s", warning, device_dict)
        device_dict["warnings"].append(warning)
