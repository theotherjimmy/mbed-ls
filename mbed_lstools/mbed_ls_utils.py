import os
import sys
import platform
from subprocess import Popen, PIPE

class InvalidTargetIDPrefixException(Exception):
    """Should be raised when a target ID prefix is invalid"""
    def __init__(self, target_id_prefix):
        message = ("The target ID '%s' is invalid. Target IDs must be 4 "
            "characters long and can only contain the following characters: "
            "a-f, A-F, or 0-9") % (target_id_prefix)
        super(InvalidTargetIDPrefixException, self).__init__(self.message)
        self.target_id_prefix = target_id_prefix


def get_os_name():
    """! Function used to determine if host OS is supported by mbed-lstools

    @return Returns None if host OS is not supported else return OS short name

    @details This function should be ported for new OS support
    """
    system_name = platform.system()
    result = None
    
    if os.name == 'nt' and system_name == 'Windows':
        result = 'Windows'
    elif os.name == 'posix':
        if system_name in ['Linux', 'Darwin']:
            result = system_name
    return result

def run_cli_process(cmd, shell=True):
    """! Runs command as a process and return stdout, stderr and ret code
    @param cmd Command to execute
    @return Tuple of (stdout, stderr, returncode)
    """
    p = Popen(cmd, shell=shell, stdout=PIPE, stderr=PIPE)
    _stdout, _stderr = p.communicate()
    return _stdout, _stderr, p.returncode
