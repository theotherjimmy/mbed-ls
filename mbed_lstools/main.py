#!/usr/bin/env python

"""
mbed SDK
Copyright (c) 2011-2015 ARM Limited

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

import sys
import json
import optparse
import logging

from mbed_lstool import MbedLsTool
from mbed_ls_utils import get_os_name

def create(**kwargs):
    """! Factory used to create host OS specific mbed-lstools object

    :param kwargs: To pass arguments transparently to MbedLsToolBase class.
    @return Returns MbedLsTool object or None if host OS is not supported

    @details Function detects host OS. Each host platform should be ported to support new host platform (OS)
    """
    return MbedLsTool(**kwargs)

def cmd_parser_setup():
    """! Configure CLI (Command Line OPtions) options

    @return Returns OptionParser's tuple of (options, arguments)

    @details Add new command line options here to control 'mbedls' command line iterface
    """
    parser = optparse.OptionParser()

    parser.add_option('-s', '--simple',
                      dest='simple',
                      default=False,
                      action="store_true",
                      help='Parser friendly verbose mode')

    parser.add_option('-l', '--list',
                      dest='list_platforms',
                      default=False,
                      action="store_true",
                      help='List all platforms and corresponding TargetID values mapped by mbed-ls')

    parser.add_option('-m', '--mock',
                      dest='mock_platform',
                      help='Add locally manufacturers id and platform name. Example --mock=12B4:NEW_PLATFORM')

    parser.add_option('-j', '--json',
                      dest='json',
                      default=False,
                      action="store_true",
                      help='JSON formatted list of targets detailed information')

    parser.add_option('-J', '--json-by-target-id',
                      dest='json_by_target_id',
                      default=False,
                      action="store_true",
                      help='(DEPRECATED) JSON formatted dictionary ordered by TargetID of targets detailed information')

    parser.add_option('-p', '--json-platforms',
                      dest='json_platforms',
                      default=False,
                      action="store_true",
                      help='(DEPRECATED) JSON formatted list of available platforms')

    parser.add_option('-P', '--json-platforms-ext',
                      dest='json_platforms_ext',
                      default=False,
                      action="store_true",
                      help='(DEPRECATED) JSON formatted dictionary of platforms count')

    parser.add_option('', '--skip-retarget',
                      dest='skip_retarget',
                      default=False,
                      action="store_true",
                      help='Ignores file ./mbedls.json with retarget data')

    parser.add_option('-d', '--debug',
                      dest='debug',
                      default=False,
                      action="store_true",
                      help='Outputs extra debug information')

    parser.add_option('', '--version',
                      dest='version',
                      default=False,
                      action="store_true",
                      help='Prints package version and exits')

    (opts, args) = parser.parse_args()
    return (opts, args)


def mbedls_main():
    """! Function used to drive CLI (command line interface) application
    @return Function exits with success code
    @details Function exits back to command line with ERRORLEVEL
    """

    def get_mbedls_version():
        """! Get mbed-ls Python module version string """
        import pkg_resources  # part of setuptools
        version = pkg_resources.require("mbed-ls")[0].version
        return version

    (opts, args) = cmd_parser_setup()
    
    log_level = logging.WARNING
    
    if opts.debug:
        log_level = logging.DEBUG
    
    logging.basicConfig(level=log_level)
    logging.debug("mbed-ls ver. " + get_mbedls_version())
    logging.debug("host: " + get_os_name())
    
    mbeds = create(skip_retarget=opts.skip_retarget)

    if mbeds is None:
        logging.error('This platform is not supported! Pull requests welcome at github.com/ARMmbed/mbed-ls\n')
        sys.exit(-1)

    if opts.list_platforms:
        print(mbeds.list_manufacture_ids())
        sys.exit(0)

    if opts.mock_platform:
        if opts.mock_platform == '*' and opts.json:
            print(json.dumps(mbeds.get_mocked_platforms(), indent=4))
        else:
            for token in opts.mock_platform.split(','):
                if ':' in token:
                    oper = '+' # Default
                    mid, platform_name = token.split(':')
                    if mid and mid[0] in ['+', '-']:
                        oper = mid[0]   # Operation (character)
                        mid = mid[1:]   # We remove operation character
                    
                    if oper == '+':
                        mbeds.global_mock_manager.add_platform(mid, platform_name)
                    else:
                        mbeds.global_mock_manager.remove_platform(mid)
                elif token and token[0] in ['-', '!']:
                    # Operations where do not specify data after colon: --mock=-1234,-7678
                    oper = token[0]
                    mid = token[1:]
                    if oper == '+':
                        mbeds.global_mock_manager.add_platform(mid, 'dummy')
                    else:
                        mbeds.global_mock_manager.remove_platform(mid)
            if opts.json:
                print(json.dumps(mbeds.get_mocked_platforms(), indent=4))

    elif opts.json:
        print(json.dumps(mbeds.list_mbeds_ext(), indent=4, sort_keys=True))

    elif opts.json_by_target_id:
        print(json.dumps(mbeds.list_mbeds_by_targetid(), indent=4, sort_keys=True))
    
    elif opts.version:
        print(get_mbedls_version())
    
    elif opts.json_platforms:
        print(json.dumps(mbeds.list_platforms(), indent=4, sort_keys=True))

    elif opts.json_platforms_ext:
        print(json.dumps(mbeds.list_platforms_ext(), indent=4, sort_keys=True))
    else:
        print(mbeds.get_string(border=not opts.simple, header=not opts.simple))

    # TODO replace with actual return code
    return_code = 0
    logging.debug("Return code: %d" % return_code)
    sys.exit(return_code)
