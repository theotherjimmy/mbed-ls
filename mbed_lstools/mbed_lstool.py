from mbed_platform_database import MbedPlatformDatabase, InvalidTargetIDPrefixException
from mbed_lister import MbedLister
from mock_manager import MockManager
from providers.mbed_provider import MbedProvider
from mbed_ls_utils import get_os_name
from prettytable import PrettyTable

import os
from copy import copy

class MbedLsTool():
    def __init__(self, skip_retarget=False):
        # Create a platform database
        self.database = MbedPlatformDatabase()
        self.skip_retarget = skip_retarget
        
        # Get globally mocked platforms
        global_mock_file_path = os.path.join(os.path.expanduser("~"), '.mbed-ls', '.mbedls-mock')
        
        self.global_mock_manager = MockManager(global_mock_file_path)
        self.local_mock_manager = MockManager('.mbedls-mock')
        mocked_platforms = self.get_mocked_platforms()
        
        # Add all mocked platforms to the platform database
        for target_id_prefix in mocked_platforms:
            try:
                self.database.add(target_id_prefix, mocked_platforms[target_id_prefix])
            except InvalidTargetIDPrefixException as e:
                # TODO log warning and print full error to debug/verbose
                print 'Warning: invalid target id in mocked target, ignoring'
        
        # Create an mbed provider depending on the current OS
        self.os_name = get_os_name()
        
        if not self.os_name:
            raise Exception('Unsupported OS')
        
        self.provider = None
        
        if self.os_name == 'Windows':
            from providers.mbed_provider_windows import MbedProviderWindows
            self.provider = MbedProviderWindows()
        elif self.os_name == 'Linux':
            from providers.mbed_provider_linux import MbedProviderLinux
            self.provider = MbedProviderLinux()
        
        if not self.provider:
            raise Exception('No valid provider found for OS name "%s"' % self.os_name)
        
        # Create an mbed lister
        self.lister = MbedLister(self.database, self.provider, skip_retarget=self.skip_retarget)
    
    def get_mocked_platforms(self):
        globally_mocked_platforms = self.global_mock_manager.get_platforms()
        locally_mocked_platforms = self.local_mock_manager.get_platforms()
        mocked_platforms = copy(globally_mocked_platforms)
        mocked_platforms.update(locally_mocked_platforms)
        return mocked_platforms
    
    def list_mbeds_by_targetid(self, file_system_behavior=MbedProvider.FS_PRE_TARGET_ID_CHECK, target_id_filters=[]):
        # TODO add deperecation notice
        return self.lister.list_mbeds_ext(file_system_behavior=file_system_behavior, target_id_filters=target_id_filters)    
    
    def list_mbeds(self, file_system_behavior=MbedProvider.FS_PRE_TARGET_ID_CHECK, target_id_filters=[]):
        # TODO add deperecation notice that API will change to listing by target id
        return self.lister.list_mbeds_ext(file_system_behavior=file_system_behavior, target_id_filters=target_id_filters).values()
    
    def list_mbeds_ext(self, file_system_behavior=MbedProvider.FS_PRE_TARGET_ID_CHECK, target_id_filters=[]):
        # TODO add deperecation notice
        return self.list_mbeds(file_system_behavior=file_system_behavior, target_id_filters=target_id_filters)
    
    def list_manufacture_ids(self):
        #TODO add notice that this API will change to just data, no formatting
        """! Creates list of all available mappings for target_id -> Platform
        @return String with table formatted output
        """
        columns = ['target_id_prefix', 'platform_name']
        pt = PrettyTable(columns)
        for col in columns:
            pt.align[col] = 'l'

        platforms = self.database.get_platforms()
        for target_id_prefix in sorted(platforms.keys()):
            platform_name = platforms[target_id_prefix]
            pt.add_row([target_id_prefix, platform_name])

        return pt.get_string()
    
    def list_platforms(self):
        # TODO add deperecation notice
        """! Useful if you just want to know which platforms are currently available on the system
        @return List of (unique values) available platforms
        """
        result = []
        mbeds = self.list_mbeds()
        for i, val in enumerate(mbeds):
            platform_name = str(val['platform_name'])
            if platform_name not in result:
                result.append(platform_name)
        return result
    
    def list_platforms_ext(self):
        # TODO add deperecation notice
        """! Useful if you just want to know how many platforms of each type are currently available on the system
        @return Dict of platform: platform_count
        """
        result = {}
        mbeds = self.list_mbeds()
        for i, val in enumerate(mbeds):
            platform_name = str(val['platform_name'])
            if platform_name not in result:
                result[platform_name] = 1
            else:
                result[platform_name] += 1
        return result

    def get_string(self, border=False, header=True, padding_width=1, sortby='platform_name'):
        # TODO add deperecation notice
        """! Printing with some sql table like decorators
        @param border Table border visibility
        @param header Table header visibility
        @param padding_width Table padding
        @param sortby Column used to sort results
        @return Returns string which can be printed on console
        """
        result = ''
        mbeds = self.list_mbeds_ext()
        if mbeds:
            """ ['platform_name', 'mount_point', 'serial_port', 'target_id'] - columns generated from USB auto-detection
                ['platform_name_unique', ...] - columns generated outside detection subsystem (OS dependent detection)
            """
            columns = ['platform_name', 'platform_name_unique', 'mount_point', 'serial_port', 'target_id', 'daplink_version']
            pt = PrettyTable(columns)
            for col in columns:
                pt.align[col] = 'l'

            for mbed in mbeds:
                row = []
                for col in columns:
                    row.append(mbed[col] if col in mbed and mbed[col] else 'unknown')
                pt.add_row(row)
            result = pt.get_string(border=border, header=header, padding_width=padding_width, sortby=sortby)
        return result        
    
    def __str__(self):
        """! Object to string casting
        @return Stringified class object should be prettytable formated string
        """
        return self.get_string()
