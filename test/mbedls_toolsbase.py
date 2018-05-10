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

import unittest
import os
import json
from mock import patch, mock_open
from copy import deepcopy

from mbed_lstools.lstools_base import MbedLsToolsBase, FSInteraction


class DummyLsTools(MbedLsToolsBase):
    return_value = []

    def find_candidates(self):
        return self.return_value


try:
    basestring
except NameError:
    # Python 3
    basestring = str


class BasicTestCase(unittest.TestCase):
    """ Basic test cases checking trivial asserts
    """

    def setUp(self):
        self.base = DummyLsTools()

    def tearDown(self):
        pass

    def test_list_mbeds_valid_platform(self):
        self.base.return_value = [
            {
                "mount_point": "dummy_mount_point",
                "target_id_usb_id": u"0240DEADBEEF",
                "serial_port": "dummy_serial_port",
            },
            {
                "mount_point": None,
                "target_id_usb_id": "00000000000",
                "serial_port": "not_valid",
            },
        ]
        with patch(
            "mbed_lstools.lstools_base.MbedLsToolsBase._read_htm_ids"
        ) as _read_htm, patch(
            "mbed_lstools.lstools_base.MbedLsToolsBase.mount_point_ready"
        ) as _mpr, patch(
            "mbed_lstools.lstools_base.PlatformDatabase.get"
        ) as _get, patch(
            "os.listdir"
        ) as _listdir:
            _mpr.return_value = True
            _read_htm.return_value = (u"0241BEEFDEAD", {})
            _get.return_value = {"platform_name": "foo_target"}
            _listdir.return_value = []
            to_check = self.base.list_mbeds()
            _read_htm.assert_called_once_with("dummy_mount_point")
            _get.assert_any_call("0241", device_type="daplink", verbose_data=True)
        self.assertEqual(len(to_check), 1)
        self.assertEqual(to_check[0]["target_id"], "0241BEEFDEAD")
        self.assertEqual(to_check[0]["platform_name"], "foo_target")

    def test_list_mbeds_invalid_tid(self):
        self.base.return_value = [
            {
                "mount_point": "dummy_mount_point",
                "target_id_usb_id": u"0240DEADBEEF",
                "serial_port": "dummy_serial_port",
            },
            {
                "mount_point": "dummy_mount_point",
                "target_id_usb_id": "",
                "serial_port": "not_valid",
            },
        ]
        with patch(
            "mbed_lstools.lstools_base.MbedLsToolsBase._read_htm_ids"
        ) as _read_htm, patch(
            "mbed_lstools.lstools_base.MbedLsToolsBase.mount_point_ready"
        ) as _mpr, patch(
            "mbed_lstools.lstools_base.PlatformDatabase.get"
        ) as _get, patch(
            "os.listdir"
        ) as _listdir:
            _mpr.return_value = True
            _read_htm.side_effect = [(u"0241BEEFDEAD", {}), (None, {})]
            _get.return_value = {"platform_name": "foo_target"}
            _listdir.return_value = []
            to_check = self.base.list_mbeds()
            _get.assert_any_call("0241", device_type="daplink", verbose_data=True)
        self.assertEqual(len(to_check), 2)
        self.assertEqual(to_check[0]["target_id"], "0241BEEFDEAD")
        self.assertEqual(to_check[0]["platform_name"], "foo_target")
        self.assertEqual(to_check[1]["target_id"], "")
        self.assertEqual(to_check[1]["platform_name"], None)

    def test_list_mbeds_invalid_platform(self):
        self.base.return_value = [
            {
                "mount_point": "dummy_mount_point",
                "target_id_usb_id": u"not_in_target_db",
                "serial_port": "dummy_serial_port",
            }
        ]
        for qos in [FSInteraction.BeforeFilter, FSInteraction.AfterFilter]:
            with patch(
                "mbed_lstools.lstools_base.MbedLsToolsBase._read_htm_ids"
            ) as _read_htm, patch(
                "mbed_lstools.lstools_base.MbedLsToolsBase.mount_point_ready"
            ) as _mpr, patch(
                "mbed_lstools.lstools_base.PlatformDatabase.get"
            ) as _get, patch(
                "os.listdir"
            ) as _listdir:
                _mpr.return_value = True
                _read_htm.return_value = (u"not_in_target_db", {})
                _get.return_value = None
                _listdir.return_value = []
                to_check = self.base.list_mbeds()
                _read_htm.assert_called_once_with("dummy_mount_point")
                _get.assert_any_call("not_", device_type="daplink", verbose_data=True)
            self.assertEqual(len(to_check), 1)
            self.assertEqual(to_check[0]["target_id"], "not_in_target_db")
            self.assertEqual(to_check[0]["platform_name"], None)

    def test_list_mbeds_unmount_mid_read(self):
        self.base.return_value = [
            {
                "mount_point": "dummy_mount_point",
                "target_id_usb_id": u"0240DEADBEEF",
                "serial_port": "dummy_serial_port",
            }
        ]
        with patch(
            "mbed_lstools.lstools_base.MbedLsToolsBase.mount_point_ready"
        ) as _mpr, patch(
            "os.listdir"
        ) as _listdir:
            _mpr.return_value = True
            _listdir.side_effect = OSError
            to_check = self.base.list_mbeds()
        self.assertEqual(len(to_check), 0)

    def test_list_mbeds_read_mbed_htm_failure(self):
        self.base.return_value = [
            {
                "mount_point": "dummy_mount_point",
                "target_id_usb_id": u"0240DEADBEEF",
                "serial_port": "dummy_serial_port",
            }
        ]

        def _test(mock):
            with patch(
                "mbed_lstools.lstools_base.MbedLsToolsBase.mount_point_ready"
            ) as _mpr, patch(
                "os.listdir"
            ) as _listdir, patch(
                "__main__.open", mock
            ):
                _mpr.return_value = True
                _listdir.return_value = ["MBED.HTM", "DETAILS.TXT"]
                to_check = self.base.list_mbeds()
                self.assertEqual(len(to_check), 0)

        m = mock_open()
        m.side_effect = OSError
        _test(m)

        m.reset_mock()
        m.side_effect = IOError
        _test(m)

    def test_list_mbeds_read_details_txt_failure(self):
        self.base.return_value = [
            {
                "mount_point": "dummy_mount_point",
                "target_id_usb_id": u"0240DEADBEEF",
                "serial_port": "dummy_serial_port",
            }
        ]

        def _test(mock):
            with patch(
                "mbed_lstools.lstools_base.MbedLsToolsBase.mount_point_ready"
            ) as _mpr, patch(
                "os.listdir"
            ) as _listdir, patch(
                "mbed_lstools.lstools_base.MbedLsToolsBase._update_device_from_htm"
            ) as _htm, patch(
                "__main__.open", mock
            ):
                _mpr.return_value = True
                _htm.side_effect = None
                _listdir.return_value = ["MBED.HTM", "DETAILS.TXT"]
                to_check = self.base.list_mbeds(read_details_txt=True)
                self.assertEqual(len(to_check), 0)

        m = mock_open()
        m.side_effect = OSError
        _test(m)

        m.reset_mock()
        m.side_effect = IOError
        _test(m)

    def test_list_mbeds_unmount_mid_read_list_unmounted(self):
        self.base.list_unmounted = True
        self.base.return_value = [
            {
                "mount_point": "dummy_mount_point",
                "target_id_usb_id": u"0240DEADBEEF",
                "serial_port": "dummy_serial_port",
            }
        ]
        with patch(
            "mbed_lstools.lstools_base.MbedLsToolsBase.mount_point_ready"
        ) as _mpr, patch(
            "os.listdir"
        ) as _listdir:
            _mpr.return_value = True
            _listdir.side_effect = OSError
            to_check = self.base.list_mbeds()
        self.assertEqual(len(to_check), 1)
        self.assertEqual(to_check[0]["mount_point"], None)
        self.assertEqual(to_check[0]["device_type"], "unknown")
        self.assertEqual(to_check[0]["platform_name"], "K64F")

    def test_list_manufacture_ids(self):
        table_str = self.base.list_manufacture_ids()
        self.assertTrue(isinstance(table_str, basestring))

    def test_mock_manufacture_ids_default_multiple(self):
        # oper='+'
        for mid, platform_name in [
            ("0341", "TEST_PLATFORM_NAME_1"),
            ("0342", "TEST_PLATFORM_NAME_2"),
            ("0343", "TEST_PLATFORM_NAME_3"),
        ]:
            self.base.mock_manufacture_id(mid, platform_name)
            self.assertEqual(platform_name, self.base.plat_db.get(mid))

    def test_mock_manufacture_ids_minus(self):
        # oper='+'
        for mid, platform_name in [
            ("0341", "TEST_PLATFORM_NAME_1"),
            ("0342", "TEST_PLATFORM_NAME_2"),
            ("0343", "TEST_PLATFORM_NAME_3"),
        ]:
            self.base.mock_manufacture_id(mid, platform_name)
            self.assertEqual(platform_name, self.base.plat_db.get(mid))

        # oper='-'
        self.base.mock_manufacture_id("0342", "", oper="-")
        self.assertEqual("TEST_PLATFORM_NAME_1", self.base.plat_db.get("0341"))
        self.assertEqual(None, self.base.plat_db.get("0342"))
        self.assertEqual("TEST_PLATFORM_NAME_3", self.base.plat_db.get("0343"))

    def test_mock_manufacture_ids_star(self):
        # oper='+'
        for mid, platform_name in [
            ("0341", "TEST_PLATFORM_NAME_1"),
            ("0342", "TEST_PLATFORM_NAME_2"),
            ("0343", "TEST_PLATFORM_NAME_3"),
        ]:
            self.base.mock_manufacture_id(mid, platform_name)

            self.assertEqual(platform_name, self.base.plat_db.get(mid))

        # oper='-'
        self.base.mock_manufacture_id("*", "", oper="-")
        self.assertEqual(None, self.base.plat_db.get("0341"))
        self.assertEqual(None, self.base.plat_db.get("0342"))
        self.assertEqual(None, self.base.plat_db.get("0343"))

    def test_update_device_from_fs_mid_unmount(self):
        dummy_mount = "dummy_mount"
        device = {"mount_point": dummy_mount}

        with patch("os.listdir") as _listdir:
            _listdir.side_effect = OSError
            self.base._update_device_from_fs(device, False)
            self.assertEqual(device["device_type"], "unknown")
            self.assertEqual(device["mount_point"], None)

    def test_update_device_from_fs_unknown(self):
        device = {}
        self.base._update_device_from_fs(device, False)
        self.assertEqual(device["device_type"], "unknown")

    def test_detect_device_test(self):
        device_type = self.base._detect_device_type(["Segger.html"])
        self.assertEqual(device_type, "jlink")

        device_type = self.base._detect_device_type(["MBED.HTM", "DETAILS.TXT"])
        self.assertEqual(device_type, "daplink")

    def test_update_device_details_jlink(self):
        jlink_html_contents = (
            '<html><head><meta http-equiv="refresh" '
            'content="0; url=http://www.nxp.com/FRDM-KL27Z"/>'
            "<title>NXP Product Page</title></head><body></body></html>"
        )
        _open = mock_open(read_data=jlink_html_contents)
        dummy_mount_point = "dummy"
        base_device = {"mount_point": dummy_mount_point}

        with patch("mbed_lstools.lstools_base.open", _open):
            device = deepcopy(base_device)
            self.base._update_device_details_jlink(
                device, False, ["Board.html", "User Guide.html"]
            )
            self.assertEqual(device["url"], "http://www.nxp.com/FRDM-KL27Z")
            self.assertEqual(device["platform_name"], "KL27Z")
            _open.assert_called_once_with(
                os.path.join(dummy_mount_point, "Board.html"), "r"
            )

            _open.reset_mock()

            device = deepcopy(base_device)
            self.base._update_device_details_jlink(device, False, ["User Guide.html"])
            self.assertEqual(device["url"], "http://www.nxp.com/FRDM-KL27Z")
            self.assertEqual(device["platform_name"], "KL27Z")
            _open.assert_called_once_with(
                os.path.join(dummy_mount_point, "User Guide.html"), "r"
            )

            _open.reset_mock()

            device = deepcopy(base_device)
            self.base._update_device_details_jlink(
                device, False, ["unhelpful_file.html"]
            )
            self.assertEqual(device, base_device)
            _open.assert_not_called()

    def test_fs_never(self):
        device = {
            "target_id_usb_id": "024075309420ABCE",
            "mount_point": "invalid_mount_point",
            "serial_port": "invalid_serial_port",
        }
        self.base.return_value = [device]
        with patch(
            "mbed_lstools.lstools_base.MbedLsToolsBase._update_device_from_fs"
        ) as _up_fs, patch(
            "mbed_lstools.lstools_base.MbedLsToolsBase.mount_point_ready"
        ) as mount_point_ready:
            mount_point_ready.return_value = True

            filter = None
            ret = self.base.list_mbeds(
                FSInteraction.Never, filter, read_details_txt=False
            )
            ret_with_details = self.base.list_mbeds(
                FSInteraction.Never, filter, read_details_txt=True
            )
            self.assertIsNotNone(ret[0])
            self.assertIsNotNone(ret_with_details[0])
            self.assertEqual(ret[0]["target_id"], ret[0]["target_id_usb_id"])
            self.assertEqual(ret[0]["platform_name"], "K64F")
            self.assertEqual(ret[0], ret_with_details[0])
            _up_fs.assert_not_called()

            def filter_in(m):
                return m["platform_name"] == "K64F"

            ret = self.base.list_mbeds(
                FSInteraction.Never, filter_in, read_details_txt=False
            )
            ret_with_details = self.base.list_mbeds(
                FSInteraction.Never, filter_in, read_details_txt=True
            )
            self.assertIsNotNone(ret[0])
            self.assertIsNotNone(ret_with_details[0])
            self.assertEqual(ret[0]["target_id"], ret[0]["target_id_usb_id"])
            self.assertEqual(ret[0]["platform_name"], "K64F")
            self.assertEqual(ret[0], ret_with_details[0])
            _up_fs.assert_not_called()

            def filter_out(m):
                return m["platform_name"] != "K64F"

            ret = self.base.list_mbeds(
                FSInteraction.Never, filter_out, read_details_txt=False
            )
            ret_with_details = self.base.list_mbeds(
                FSInteraction.Never, filter_out, read_details_txt=True
            )
            _up_fs.assert_not_called()
            self.assertEqual(ret, [])
            self.assertEqual(ret, ret_with_details)
            _up_fs.assert_not_called()

    def test_fs_after(self):
        device = {
            "target_id_usb_id": "024075309420ABCE",
            "mount_point": "invalid_mount_point",
            "serial_port": "invalid_serial_port",
        }
        with patch(
            "mbed_lstools.lstools_base.MbedLsToolsBase._read_htm_ids"
        ) as _read_htm, patch(
            "mbed_lstools.lstools_base.MbedLsToolsBase._details_txt"
        ) as _up_details, patch(
            "mbed_lstools.lstools_base.MbedLsToolsBase.mount_point_ready"
        ) as mount_point_ready, patch(
            "os.listdir"
        ) as _listdir:
            new_device_id = "00017531642046"
            _read_htm.return_value = (new_device_id, {})
            _listdir.return_value = []
            _up_details.return_value = {"automation_allowed": "0"}
            mount_point_ready.return_value = True

            filter = None
            self.base.return_value = [deepcopy(device)]
            ret = self.base.list_mbeds(FSInteraction.AfterFilter, filter, False, False)
            _up_details.assert_not_called()
            self.base.return_value = [deepcopy(device)]
            ret_with_details = self.base.list_mbeds(
                FSInteraction.AfterFilter, filter, False, True
            )

            self.assertIsNotNone(ret[0])
            self.assertIsNotNone(ret_with_details[0])
            self.assertEqual(ret[0]["target_id"], new_device_id)
            self.assertEqual(ret_with_details[0]["daplink_automation_allowed"], "0")
            self.assertDictContainsSubset(ret[0], ret_with_details[0])
            _read_htm.assert_called_with(device["mount_point"])
            _up_details.assert_called_with(device["mount_point"])

            _read_htm.reset_mock()
            _up_details.reset_mock()

            def filter_in(m):
                return m["target_id"] == device["target_id_usb_id"]

            def filter_details(m):
                return m.get("daplink_automation_allowed", None) == "0"

            self.base.return_value = [deepcopy(device)]
            ret = self.base.list_mbeds(
                FSInteraction.AfterFilter, filter_in, False, False
            )
            self.base.return_value = [deepcopy(device)]
            ret_with_details = self.base.list_mbeds(
                FSInteraction.AfterFilter, filter_details, False, True
            )

            self.assertIsNotNone(ret[0])
            self.assertEqual(ret_with_details, [])
            self.assertEqual(ret[0]["target_id"], new_device_id)
            _read_htm.assert_called_with(device["mount_point"])
            _up_details.assert_not_called()

            _read_htm.reset_mock()
            _up_details.reset_mock()

            def filter_out(m):
                return m["target_id"] == new_device_id

            self.base.return_value = [deepcopy(device)]
            ret = self.base.list_mbeds(
                FSInteraction.AfterFilter, filter_out, False, False
            )
            self.base.return_value = [deepcopy(device)]
            ret_with_details = self.base.list_mbeds(
                FSInteraction.AfterFilter, filter_out, False, True
            )

            self.assertEqual(ret, [])
            self.assertEqual(ret_with_details, [])
            _read_htm.assert_not_called()
            _up_details.assert_not_called()

    def test_fs_before(self):
        device = {
            "target_id_usb_id": "024075309420ABCE",
            "mount_point": "invalid_mount_point",
            "serial_port": "invalid_serial_port",
        }
        with patch(
            "mbed_lstools.lstools_base.MbedLsToolsBase._read_htm_ids"
        ) as _read_htm, patch(
            "mbed_lstools.lstools_base.MbedLsToolsBase._details_txt"
        ) as _up_details, patch(
            "mbed_lstools.lstools_base.MbedLsToolsBase.mount_point_ready"
        ) as mount_point_ready, patch(
            "os.listdir"
        ) as _listdir:
            new_device_id = u"00017575430420"
            _read_htm.return_value = (new_device_id, {})
            _listdir.return_value = []
            _up_details.return_value = {"automation_allowed": "0"}
            mount_point_ready.return_value = True

            filter = None
            self.base.return_value = [deepcopy(device)]
            ret = self.base.list_mbeds(FSInteraction.BeforeFilter, filter, False, False)
            _up_details.assert_not_called()

            self.base.return_value = [deepcopy(device)]
            ret_with_details = self.base.list_mbeds(
                FSInteraction.BeforeFilter, filter, False, True
            )
            self.assertIsNotNone(ret[0])
            self.assertIsNotNone(ret_with_details[0])
            self.assertEqual(ret[0]["target_id"], new_device_id)
            self.assertEqual(ret_with_details[0]["daplink_automation_allowed"], "0")
            self.assertDictContainsSubset(ret[0], ret_with_details[0])
            _read_htm.assert_called_with(device["mount_point"])
            _up_details.assert_called_with(device["mount_point"])

            _read_htm.reset_mock()
            _up_details.reset_mock()

            def filter_in(m):
                return m["target_id"] == "00017575430420"

            def filter_in_details(m):
                return m["daplink_automation_allowed"] == "0"

            self.base.return_value = [deepcopy(device)]
            ret = self.base.list_mbeds(
                FSInteraction.BeforeFilter, filter_in, False, False
            )
            _up_details.assert_not_called()

            self.base.return_value = [deepcopy(device)]
            ret_with_details = self.base.list_mbeds(
                FSInteraction.BeforeFilter, filter_in_details, False, True
            )

            self.assertIsNotNone(ret[0])
            self.assertIsNotNone(ret_with_details[0])
            self.assertEqual(ret[0]["target_id"], new_device_id)
            self.assertEqual(ret_with_details[0]["daplink_automation_allowed"], "0")
            self.assertDictContainsSubset(ret[0], ret_with_details[0])
            _read_htm.assert_called_with(device["mount_point"])
            _up_details.assert_called_with(device["mount_point"])

            _read_htm.reset_mock()
            _up_details.reset_mock()

            def filter_out(m):
                return m["target_id"] == "024075309420ABCE"

            def filter_out_details(m):
                return m["daplink_automation_allowed"] == "1"

            ret = self.base.list_mbeds(
                FSInteraction.BeforeFilter, filter_out, False, False
            )
            _up_details.assert_not_called()

            self.base.return_value = [deepcopy(device)]
            ret_with_details = self.base.list_mbeds(
                FSInteraction.BeforeFilter, filter_out_details, False, True
            )

            self.assertEqual(ret, [])
            self.assertEqual(ret_with_details, [])
            _read_htm.assert_called_with(device["mount_point"])


class RetargetTestCase(unittest.TestCase):
    """ Test cases that makes use of retargetting
    """

    def setUp(self):
        retarget_data = {"0240DEADBEEF": {"serial_port": "valid"}}

        _open = mock_open(read_data=json.dumps(retarget_data))

        with patch("os.path.isfile"), patch("mbed_lstools.lstools_base.open", _open):
            self.base = DummyLsTools()
            _open.assert_called()

    def tearDown(self):
        pass

    def test_list_mbeds_valid_platform(self):
        self.base.return_value = [
            {
                "mount_point": "dummy_mount_point",
                "target_id_usb_id": u"0240DEADBEEF",
                "serial_port": None,
            }
        ]
        with patch(
            "mbed_lstools.lstools_base.MbedLsToolsBase._read_htm_ids"
        ) as _read_htm, patch(
            "mbed_lstools.lstools_base.MbedLsToolsBase.mount_point_ready"
        ) as _mpr, patch(
            "mbed_lstools.lstools_base.PlatformDatabase.get"
        ) as _get, patch(
            "os.listdir"
        ) as _listdir:
            _mpr.return_value = True
            _read_htm.return_value = (u"0240DEADBEEF", {})
            _get.return_value = {"platform_name": "foo_target"}
            _listdir.return_value = []
            to_check = self.base.list_mbeds()
        self.assertEqual(len(to_check), 1)
        self.assertEqual(to_check[0]["serial_port"], "valid")


if __name__ == "__main__":
    unittest.main()
