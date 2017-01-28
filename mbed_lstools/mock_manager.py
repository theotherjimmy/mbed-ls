import os
import json
import logging
from fasteners import InterProcessLock

class MockManager:
    def __init__(self, mock_file):
        self.logger = logging.getLogger(__name__)
        self.mock_file = mock_file
        
        if not os.path.exists(self.mock_file):
            self.logger.info('No mock file at "%s"' % self.mock_file)
            mock_file_dir = os.path.dirname(self.mock_file)
            if mock_file_dir and not os.path.exists(mock_file_dir):
                os.makedirs(mock_file_dir)
        else:
            self.logger.info('Found mock file at "%s"' % self.mock_file)
        
        self.mock_file_lock_file = '%s.lockfile' % self.mock_file
        self.lock = InterProcessLock(self.mock_file_lock_file)
        self.platforms = {}
        self.lock_acquired = False
    
    def __del__(self):
        if self.lock_acquired:
            self._release_lock()
    
    def add_platform(self, target_id_prefix, platform_name, timeout=60):
        exception = None
        self.logger.info('Adding mocked target "%s:%s" to mock file at "%s"' % (target_id_prefix, platform_name, self.mock_file))
        self._acquire_lock(timeout)
        try:
            self._mock_file_read()
            self.platforms[target_id_prefix] = platform_name
            self._mock_file_write(self.platforms)
        except (IOError, ValueError):
            self._release_lock()
            raise
        else:
            self._release_lock()
    
    def remove_platform(self, target_id_prefix, timeout=60):
        self.logger.info('Removing mocked target "%s" from mock file at "%s"' % (target_id_prefix, self.mock_file))
        self._acquire_lock(timeout)
        try:
            self._mock_file_read()
        except (IOError, ValueError):
            self._release_lock()
            raise
            
        if target_id_prefix in self.platforms:
            del self.platforms[target_id_prefix]
        else:
            raise Exception('Target ID prefix "%s" was not present in mock file located at "%s"' % (target_id_prefix, self.mock_file))
        
        try:
            self._mock_file_write(self.platforms)
        except (IOError, ValueError):
            self._release_lock()
            raise
        else:
            self._release_lock()
    
    def get_platforms(self, use_cache=False, timeout=60):
        if not use_cache:
            self._acquire_lock(timeout)
            try:
                self._mock_file_read()
            except (IOError, ValueError):
                self._release_lock()
                raise
            else:
                self._release_lock()
        
        return self.platforms
    
    def _acquire_lock(self, timeout):
        self.logger.debug('Acquiring lock for mock file "%s" (timeout in %d seconds)' % (self.mock_file, timeout))
        acquired = self.lock.acquire(blocking=True, timeout=timeout)
        
        # TODO may need to remove this in the future
        if not acquired:
            raise Exception('Failed to acquire mock file lock')
        
        self.lock_acquired = True
    
    def _release_lock(self):
        self.logger.debug('Releasing lock for mock file "%s"' % (self.mock_file))
        self.lock.release()
        self.lock_acquired = False
    
    def _mock_file_read(self):
        self.logger.debug('Reading mock file "%s"' % (self.mock_file))
        if os.path.exists(self.mock_file) and os.path.isfile(self.mock_file):
            with open(self.mock_file, 'r') as f:
                self.platforms = json.load(f)
        else:
            self.platforms = {}

    def _mock_file_write(self, mock_ids):
        self.logger.debug('Writing to mock file "%s"' % (self.mock_file))
        with open(self.mock_file, 'w') as f:
            f.write(json.dumps(mock_ids, indent=4))