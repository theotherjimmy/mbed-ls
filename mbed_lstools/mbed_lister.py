import os
import re
import json
import logging
from providers.mbed_provider import MbedProvider
from copy import copy

class MbedLister():
    MBED_HTM_NAME = 'mbed.htm'
    DETAIL_TXT_NAME = 'details.txt'
    RETARGET_FILE_NAME = 'mbedls.json'
    
    def __init__(self, database, provider, skip_retarget=False):
        self.database = database
        self.provider = provider
        self.skip_retarget = skip_retarget
        self.logger = logging.getLogger(__name__)
        
        self.retarget_data = {}
        if (not self.skip_retarget
                and os.path.exists(self.RETARGET_FILE_NAME)
                and os.path.isfile(self.RETARGET_FILE_NAME)):
            self.logger.info('Found retarget file at "%s"' % (self.RETARGET_FILE_NAME))
            with open(self.RETARGET_FILE_NAME, "r") as f:
                self.retarget_data = json.load(f)
        
    def list_mbeds_ext(self,
                       file_system_behavior=MbedProvider.FS_PRE_TARGET_ID_CHECK,
                       target_id_filters=[]):
        self.logger.info('Listing mbeds')
        mbeds = copy(self.provider.list_mbeds())
        
        self.logger.debug('Initial list of target IDs: %s' % (', '.join(mbeds.keys())))
        
        if file_system_behavior == MbedProvider.FS_PRE_TARGET_ID_CHECK:
            self.logger.info('Performing filesystem update before filtering target IDs')
            mbeds = self._target_info_from_filesystem(mbeds)
        
        if target_id_filters:
            self.logger.info('Filtering target IDs to the following regular expressions: %s' % (', '.join(target_id_filters)))
            patterns = [re.compile(x) for x in target_id_filters]
            for target_id in mbeds.keys():
                match_found = False
                
                for pattern in patterns:
                    if re.match(pattern, target_id):
                        self.logger.debug('Match found for target ID "%s" with pattern "%s"' % (target_id, pattern.pattern))
                        match_found = True
                        continue
                
                if not match_found:
                    self.logger.debug('No matches found for target ID "%s", removing from results"' % (target_id))
                    del mbeds[target_id]
        
        if file_system_behavior == MbedProvider.FS_POST_TARGET_ID_CHECK:
            self.logger.info('Performing filesystem update after filtering target IDs')
            mbeds = self._target_info_from_filesystem(mbeds)

        platform_names = {}
        for index, target_id in enumerate(mbeds):
            platform_name = self.database.get_platform_name(target_id[:4])
            
            if platform_name:
                self.logger.debug('Platform name "%s" found for target ID "%s"' % (platform_name, target_id))
            else:
                self.logger.debug('No platform found for target ID "%s"' % (target_id))
            
            if platform_name not in platform_names:
                platform_names[platform_name] = 0
            else:
                platform_names[platform_name] += 1
            
            mbeds[target_id]['platform_name'] = platform_name
            mbeds[target_id]['platform_name_unique'] = "%s[%d]" % (platform_name, platform_names[platform_name])
            
            if not self.skip_retarget:
                if target_id in self.retarget_data:
                    self.logger.info('Retarget data found for target ID "%s"' % (target_id))
                    self.logger.debug('Updating platform data with retarget data for target ID "%s"' % (target_id), self.retarget_data[target_id])
                    mbeds[target_id].update(self.retarget_data[target_id])
                
        
        return mbeds
    
    def _get_case_agnostic_file_name(self, mount_point, file_name):
        '''Not all interface firmwares use the same case for file names
        This function will normalize them and provide the correct file name
        '''
        mount_point_files = os.listdir(mount_point)
        matching = [f for f in mount_point_files if f.lower() == file_name.lower()]
        return matching[0] if len(matching) > 0 else None
    
    def _get_mbed_htm_target_id(self, line):
        result = None
        patterns = [
            '\?code=([a-fA-F0-9]+)', # modern mbed.htm file format
            '\?auth=([a-fA-F0-9]+)'  # legacy mbed.htm file format
        ]
        
        for pattern in patterns:
            # Detecting 
            m = re.search('\?code=([a-fA-F0-9]+)', line)
            if m:
                result = m.groups()[0]
                break

        return result
    
    def _get_mbed_htm_version_build(self, line):
        result = (None, None)
        patterns = [
            # Format: <!-- Version: 0200 Build: Mar 26 2014 13:22:20 -->
            r'^<!-- Version: (\d+) Build: ([\d\w: ]+) -->',
            # Format: <!-- Version: 0219 Build: Feb  2 2016 15:20:54 Git Commit SHA: 0853ba0cdeae2436c52efcba0ba76a6434c200ff Git local mods:No-->
            r'^<!-- Version: (\d+) Build: ([\d\w: ]+) Git Commit SHA',
            # Format: <!-- Version: 0.14.3. build 471 -->
            r'^<!-- Version: ([\d+\.]+)\. build (\d+) -->'
        ]
        
        for pattern in patterns:
            # Detecting 
            m = re.search(pattern, line)
            if m:
                version_str, build_str = m.groups()
                result = (version_str.strip(), build_str.strip())
                break

        return result
    
    def _parse_mbed_htm(self, path):
        result = {}
        with open(path, 'r') as mbed_htm:
            for line in mbed_htm:
                # First check for target ID
                mbed_htm_target_id = self._get_mbed_htm_target_id(line)
                if mbed_htm_target_id:
                    result['target_id_mbed_htm'] = mbed_htm_target_id
                
                # Now check if version and build info are present in a html comment
                mbed_htm_version, mbed_htm_build = self._get_mbed_htm_version_build(line)
                if mbed_htm_version:
                    result['version'] = mbed_htm_version
                
                if mbed_htm_build:
                    result['build'] = mbed_htm_build
        
        return result
    
    def _parse_details_txt(self, path):
        result = {}
        with open(path, 'r') as details_txt:
            for line in details_txt:
                if not line.startswith('#'):
                    # Lines starting with '#' are comments
                    line_split = line.split(':')
                    if len(line_split) > 1:
                        key = line_split[0].strip()
                        key = key.replace(' ', '_')
                        key = 'daplink_' + key.lower()
                        value = (''.join(line_split[1:])).strip()
                        result[key] = value
        
        # Support newer versions of DAPLink version string
        if 'daplink_interface_version' in result:
            result['daplink_version'] = result['daplink_interface_version']
        
        return result
    
    def _target_info_from_filesystem(self, mbeds):
        # Do not modify argument
        result = {}

        for target_id in mbeds:
            mbed_original = mbeds[target_id]
            if (not 'mount_point' in mbed_original
                or not mbed_original['mount_point']):
                self.logger.debug('No mount point detected for target ID "%s", removing from results' % (target_id))
            elif not self.provider.mount_point_ready(mbed_original['mount_point']):
                self.logger.debug('Mount point "%s" for target ID "%s" not ready, removing from results' % (mbed_original['mount_point'], target_id))
            else:
                # Mount point is specified and it is ready
                mbed = copy(mbed_original)
                mbed_htm_file_name = self._get_case_agnostic_file_name(mbed['mount_point'], self.MBED_HTM_NAME)
                if mbed_htm_file_name:
                    mbed_htm_path = os.path.join(mbed['mount_point'], mbed_htm_file_name)
                    mbed_htm_info = self._parse_mbed_htm(mbed_htm_path)
                    mbed.update(mbed_htm_info)
                    
                    if ('target_id_mbed_htm' in mbed_htm_info
                            and mbed_htm_info['target_id_mbed_htm'] != target_id):
                        target_id = mbed_htm_info['target_id_mbed_htm']
                        mbed['target_id'] = mbed_htm_info['target_id_mbed_htm']
                
                details_txt_file_name = self._get_case_agnostic_file_name(mbed['mount_point'], self.DETAIL_TXT_NAME)
                if details_txt_file_name:
                    details_txt_path = os.path.join(mbed['mount_point'], details_txt_file_name)
                    details_txt_info = self._parse_details_txt(details_txt_path)
                    mbed.update(details_txt_info)                
                
                result[target_id] = mbed
        
        return result