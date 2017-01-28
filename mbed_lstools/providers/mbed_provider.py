from abc import ABCMeta, abstractmethod
import os

class MbedProvider():
    
    __metaclass__ = ABCMeta
    
    # TODO provide a better way to enumerate this
    FS_PRE_TARGET_ID_CHECK = 0
    FS_POST_TARGET_ID_CHECK = 1
    FS_DISABLED = 2
    
    USB_VENDOR_LIST = ['Ven_MBED', 'Ven_SEGGER']
    
    @abstractmethod
    def list_mbeds(self):
        '''This function must not hit the file system.
        It should just get a list of all potential mbeds.
        '''
        raise NotImplemented
    
    def mount_point_ready(self, path):
        '''This function must not hit the file system.
        It should just get a list of all potential mbeds.
        '''
        return os.path.exists(path) and os.path.isdir(path)