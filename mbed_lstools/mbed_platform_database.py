from mbed_ls_utils import InvalidTargetIDPrefixException

import re
from copy import copy

manufacture_ids = {
    "0001": "LPC2368",
    "0002": "LPC2368",
    "0003": "LPC2368",
    "0004": "LPC2368",
    "0005": "LPC2368",
    "0006": "LPC2368",
    "0007": "LPC2368",
    "0100": "LPC2368",
    "0183": "UBLOX_C027",
    "0200": "KL25Z",
    "0201": "KW41Z",
    "0210": "KL05Z",
    "0214": "HEXIWEAR",
    "0217": "K82F",
    "0218": "KL82Z",
    "0220": "KL46Z",
    "0230": "K20D50M",
    "0231": "K22F",
    "0240": "K64F",
    "0245": "K64F",
    "0250": "KW24D",
    "0261": "KL27Z",
    "0262": "KL43Z",
    "0300": "MTS_GAMBIT",
    "0305": "MTS_MDOT_F405RG",
    "0310": "MTS_DRAGONFLY_F411RE",
    "0311": "K66F",
    "0315": "MTS_MDOT_F411RE",
    "0350": "XDOT_L151CC",
    "0400": "MAXWSNENV",
    "0405": "MAX32600MBED",
    "0406": "MAX32620MBED",
    "0407": "MAX32620HSP",
    "0408": "MAX32625NEXPAQ",
    "0409": "MAX32630FTHR",
    "0415": "MAX32625MBED",
    "0500": "SPANSION_PLACEHOLDER",
    "0505": "SPANSION_PLACEHOLDER",
    "0510": "SPANSION_PLACEHOLDER",
    "0700": "NUCLEO_F103RB",
    "0705": "NUCLEO_F302R8",
    "0710": "NUCLEO_L152RE",
    "0715": "NUCLEO_L053R8",
    "0720": "NUCLEO_F401RE",
    "0725": "NUCLEO_F030R8",
    "0730": "NUCLEO_F072RB",
    "0735": "NUCLEO_F334R8",
    "0740": "NUCLEO_F411RE",
    "0744": "NUCLEO_F410RB",
    "0745": "NUCLEO_F303RE",
    "0747": "NUCLEO_F303ZE",
    "0750": "NUCLEO_F091RC",
    "0755": "NUCLEO_F070RB",
    "0760": "NUCLEO_L073RZ",
    "0765": "NUCLEO_L476RG",
    "0770": "NUCLEO_L432KC",
    "0775": "NUCLEO_F303K8",
    "0777": "NUCLEO_F446RE",
    "0778": "NUCLEO_F446ZE",
    "0780": "NUCLEO_L011K4",
    "0785": "NUCLEO_F042K6",
    "0788": "DISCO_F469NI",
    "0790": "NUCLEO_L031K6",
    "0791": "NUCLEO_F031K6",
    "0795": "DISCO_F429ZI",
    "0796": "NUCLEO_F429ZI",
    "0797": "NUCLEO_F439ZI",
    "0799": "ST_PLACEHOLDER",
    "0805": "DISCO_L053C8",
    "0810": "DISCO_F334C8",
    "0815": "DISCO_F746NG",
    "0816": "NUCLEO_F746ZG",
    "0817": "DISCO_F769NI",
    "0818": "NUCLEO_F767ZI",
    "0819": "NUCLEO_F756ZG",
    "0820": "DISCO_L476VG",
    "0824": "LPC824",
    "0826": "NUCLEO_F412ZG",
    "0827": "NUCLEO_L486RG",
    "0835": "NUCLEO_F207ZG",
    "0840": "B96B_F446VE",
    "0900": "XPRO_SAMR21",
    "0905": "XPRO_SAMW25",
    "0910": "XPRO_SAML21",
    "0915": "XPRO_SAMD21",
    "1000": "LPC2368",
    "1001": "LPC2368",
    "1010": "LPC1768",
    "1017": "HRM1017",
    "1018": "SSCI824",
    "1019": "TY51822R3",
    "1022": "BP359B",
    "1034": "LPC11U34",
    "1040": "LPC11U24",
    "1045": "LPC11U24",
    "1050": "LPC812",
    "1060": "LPC4088",
    "1061": "LPC11U35_401",
    "1062": "LPC4088_DM",
    "1070": "NRF51822",
    "1075": "NRF51822_OTA",
    "1080": "OC_MBUINO",
    "1090": "RBLAB_NRF51822",
    "1095": "RBLAB_BLENANO",
    "1100": "NRF51_DK",
    "1101": "NRF52_DK",
    "1105": "NRF51_DK_OTA",
    "1114": "LPC1114",
    "1120": "NRF51_DONGLE",
    "1130": "NRF51822_SBK",
    "1140": "WALLBOT_BLE",
    "1168": "LPC11U68",
    "1200": "NCS36510",
    "1234": "UBLOX_C027",
    "1235": "UBLOX_C027",
    "1236": "UBLOX_EVK_ODIN_W2",
    "1300": "NUC472-NUTINY",
    "1301": "NUMBED",
    "1302": "NUMAKER_PFM_NUC472",
    "1303": "NUMAKER_PFM_M453",
    "1304": "NUMAKER_PFM_M487",
    "1549": "LPC1549",
    "1600": "LPC4330_M4",
    "1605": "LPC4330_M4",
    "2000": "EFM32_G8XX_STK",
    "2005": "EFM32HG_STK3400",
    "2010": "EFM32WG_STK3800",
    "2015": "EFM32GG_STK3700",
    "2020": "EFM32LG_STK3600",
    "2025": "EFM32TG_STK3300",
    "2030": "EFM32ZG_STK3200",
    "2035": "EFM32PG_STK3401",
    "2100": "XBED_LPC1768",
    "2201": "WIZWIKI_W7500",
    "2202": "WIZWIKI_W7500ECO",
    "2203": "WIZWIKI_W7500P",
    "3001": "LPC11U24",
    "4000": "LPC11U35_Y5_MBUG",
    "4005": "NRF51822_Y5_MBUG",
    "4100": "MOTE_L152RC",
    "4337": "LPC4337",
    "4500": "DELTA_DFCM_NNN40",
    "4501": "DELTA_DFBM_NQ620",
    "4502": "DELTA_DFCM_NNN50",
    "4600": "REALTEK_RTL8195AM",
    "5000": "ARM_MPS2",
    "5001": "ARM_MPS2_M0",
    "5003": "ARM_BEETLE_SOC",
    "5005": "ARM_MPS2_M0DS",
    "5007": "ARM_MPS2_M1",
    "5009": "ARM_MPS2_M3",
    "5011": "ARM_MPS2_M4",
    "5015": "ARM_MPS2_M7",
    "5020": "HOME_GATEWAY_6LOWPAN",
    "5500": "RZ_A1H",
    "6660": "NZ32_SC151",
    "7010": "BLUENINJA_CDP_TZ01B",
    "7778": "TEENSY3_1",
    "8001": "UNO_91H",
    "9001": "LPC1347",
    "9002": "LPC11U24",
    "9003": "LPC1347",
    "9004": "ARCH_PRO",
    "9006": "LPC11U24",
    "9007": "LPC11U35_501",
    "9008": "XADOW_M0",
    "9009": "ARCH_BLE",
    "9010": "ARCH_GPRS",
    "9011": "ARCH_MAX",
    "9012": "SEEED_TINY_BLE",
    "9900": "NRF51_MICROBIT",
    "C002": "VK_RZ_A1H",
    "FFFF": "K20 BOOTLOADER",
    "RIOT": "RIOT",
}


class MbedPlatformDatabase():
    target_id_pattern = re.compile('^[a-fA-F0-9]{4}$')

    def __init__(self):
        self.platforms = copy(manufacture_ids)
    
    def get_platforms(self):
        return self.platforms
    
    def get_platform_name(self, target_id_prefix):
        return self.platforms[target_id_prefix] if target_id_prefix in self.platforms else None
    
    def get_target_id_prefix(self, platform_name):
        # TODO look if there's a builtin function to do a reverse lookup
        for target_id_prefix in self.platforms:
            if self.platforms[target_id_prefix] == platform_name:
                return target_id_prefix
        
        return None
    
    def add(self, target_id_prefix, platform_name):
        if not re.match(self.target_id_pattern, target_id_prefix):
            raise InvalidTargetIDPrefixException(target_id_prefix)
        
        self.platforms[target_id_prefix] = platform_name
    
    def remove(self, target_id_prefix):
        removed_platform = None
        
        if target_id_prefix in self.platforms:
            removed_platform = self.platforms[target_id_prefix]
            del self.platforms[target_id_prefix]
        
        return removed_platform