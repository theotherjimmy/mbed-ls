"""
mbed SDK
Copyright (c) 2011-2016 ARM Limited

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

import re
from threading import Timer
from subprocess import Popen, PIPE


def mbedls_run_cli_process(cmd, timeout=5):
    """! Runs command as a process and return stdout, stderr and ret code
    @param cmd Command to execute
    @return Tuple of (stdout, stderr, returncode)
    """
    p = Popen(cmd, stdout=PIPE, stderr=PIPE)
    _stdout, _stderr = p.communicate()
    return _stdout, _stderr, p.returncode

def mbedls_parse_yotta_search_cli(line):
    m = re.search(r'([\w\d-]+) (\d+\.\d+\.\d+)[$:]?', line)
    if m and len(m.groups()):
        yotta_target_name, yotta_target_version = m.groups()
        return yotta_target_name, yotta_target_version
    return None, None

def mbedls_yotta_search(mbed_classic_name):
    """! Function is using 'yotta search' command to fetch matching mbed device target's name
    @return Function returns list of possible targets or empty list if value not found
    @details Example:
             $ yt search -k mbed-target:k64f target
             frdm-k64f-gcc 0.0.16: Official mbed build target for the mbed frdm-k64f development board.
             frdm-k64f-armcc 0.0.10: Official mbed build target for the mbed frdm-k64f development board, using the armcc toolchain.

             Note: Function prints on console
    """
    result = {}
    cmd = ['yotta', '--plain', 'search', '-k', 'mbed-target:%s'% mbed_classic_name.lower().strip(), 'target']
    _stdout, _stderr, _ret = mbedls_run_cli_process(cmd)
    if _ret == 0:
        for line in _stdout.splitlines():
            yotta_target_name, yotta_target_version = mbedls_parse_yotta_search_cli(line)
            if yotta_target_name and yotta_target_name not in result:
                result[yotta_target_name] = yotta_target_version
                # log...
    return result
