"""Parser tests that run without Home Assistant (python3 -m unittest discover tests)."""

import importlib.util
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "kurir"
pkg = types.ModuleType("kurir_pkg")
pkg.__path__ = [str(ROOT)]
sys.modules["kurir_pkg"] = pkg
for mod in ("const", "carriers"):
    spec = importlib.util.spec_from_file_location(f"kurir_pkg.{mod}", ROOT / f"{mod}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[f"kurir_pkg.{mod}"] = module
    spec.loader.exec_module(module)
carriers = sys.modules["kurir_pkg.carriers"]

KRABI_HUB = {
    "location_name": "AKRBI-B - เมืองกระบี่",
    "full_address": "TH จังหวัดกระบี่ 81000 อำเภอเมืองกระบี่  665 หมู่ที่ 1 ตำบลอ่าวนาง อำเภอเมืองกระบี่ จังหวัดกระบี่ 81000",
}
SURAT = {
    "location_name": "SORC-A",
    "full_address": "TH จังหวัดสุราษฎร์ธานี 84000 อำเภอเมืองสุราษฎร์ธานี",
}
EMPTY = {"location_name": "", "full_address": ""}

SPX_OUT_FOR_DELIVERY = {
    "retcode": 0,
    "data": {
        "sls_tracking_info": {
            "records": [
                {"tracking_code": "F600", "tracking_name": "Out For Delivery", "buyer_description": "Parcel is out for delivery", "display_flag": 1, "actual_time": 1795403725, "current_location": EMPTY, "next_location": EMPTY, "milestone_code": 6, "milestone_name": "Out for delivery"},
                {"tracking_code": "F599", "tracking_name": "Enter Last Mile Hub", "buyer_description": "Parcel has arrived at station", "display_flag": 1, "actual_time": 1795395267, "current_location": KRABI_HUB, "next_location": EMPTY, "milestone_code": 5, "milestone_name": "In transit"},
                {"tracking_code": "F580", "tracking_name": "Domestic Line Haul End", "buyer_description": "System reminder", "display_flag": 0, "actual_time": 1795389857, "current_location": EMPTY, "next_location": EMPTY, "milestone_code": 5, "milestone_name": "In transit"},
                {"tracking_code": "F540", "tracking_name": "Left Domestic Sorting Center", "buyer_description": "Parcel has departed from station ", "display_flag": 1, "actual_time": 1795360782, "current_location": EMPTY, "next_location": KRABI_HUB, "milestone_code": 5, "milestone_name": "In transit"},
                {"tracking_code": "F510", "tracking_name": "Enter Domestic Sorting Center", "buyer_description": "Parcel has arrived at station :SORC-A", "display_flag": 1, "actual_time": 1795330250, "current_location": SURAT, "next_location": KRABI_HUB, "milestone_code": 5, "milestone_name": "In transit"},
                {"tracking_code": "F399", "tracking_name": "Import Customs Cleared", "buyer_description": "Parcel has cleared import customs", "display_flag": 1, "actual_time": 1795183200, "current_location": {"location_name": "BANGKOK", "full_address": "TH  BANGKOK"}, "next_location": EMPTY, "milestone_code": 4, "milestone_name": "Arrived"},
                {"tracking_code": "F341", "tracking_name": "Departure From Origin Port", "buyer_description": "departed", "display_flag": 1, "actual_time": 1795079400, "current_location": {"location_name": "SHENZHEN", "full_address": "CN  Shenzhen"}, "next_location": EMPTY, "milestone_code": 3, "milestone_name": "In transit to"},
            ]
        }
    },
}

SPX_PACKED = {
    "retcode": 0,
    "data": {"sls_tracking_info": {"records": [
        {"tracking_code": "F000", "tracking_name": "Manifested", "buyer_description": "We have received your order", "display_flag": 1, "actual_time": 1795150920, "current_location": EMPTY, "next_location": EMPTY, "milestone_code": 1, "milestone_name": "Preparing to ship"},
        {"tracking_code": "A000", "tracking_name": "SLSTN Created", "buyer_description": "x", "display_flag": 0, "actual_time": 1795150919, "milestone_code": 1},
    ]}},
}

SPX_DELIVERED = {
    "retcode": 0,
    "data": {"sls_tracking_info": {"records": [
        {"tracking_code": "F980", "tracking_name": "Delivered", "buyer_description": "Parcel has been delivered", "display_flag": 1, "actual_time": 1795420000, "current_location": EMPTY, "next_location": EMPTY, "milestone_code": 8, "milestone_name": "Delivered"},
    ]}},
}

SPX_NOT_FOUND = {"retcode": 2, "message": "ref record not unique"}

FLASH = {
    "code": 1,
    "data": {"list": [
        {"pno_display": "TH65019C6BG26H0", "state": 2, "routes": [
            {"route_action": "DELIVERY_MARKER", "routed_at": "2026-11-22 18:38:48", "message": "พัสดุของคุณนำส่งไม่สำเร็จ【อ่าวนาง】"},
            {"route_action": "DELIVERY_TICKET_CREATION_SCAN", "routed_at": "2026-11-22 12:06:00", "message": "กำลังนำส่ง【กระบี่】"},
            {"route_action": "SHIPMENT_WAREHOUSE_SCAN", "routed_at": "2026-11-20 04:57:00", "message": "ออกจาก【พังงา】"},
        ]},
        {"pno_display": "TH65019CKJXM3H0", "state": 5, "routes": [
            {"route_action": "DELIVERY_CONFIRM", "routed_at": "2026-11-21 19:41:09", "message": "นำส่งสำเร็จ【กระบี่】"},
        ]},
        {"pno_display": "TH65019D41ZJ2H0", "state": 1, "routes": []},
    ]},
}

ETR = {
    "meta": {"code": 200},
    "data": {"trackingNo": "TH01234567890A", "status": "ON_DELIVERED", "timelines": [
        {"date": "2026-11-22", "details": [
            {"dateTime": "2026-11-22T18:38:00+07:00", "status": "ON_DELIVERED", "description": "Delivery failed - Problematic parcel, Ao Nang, Krabi - Shipping by Flash"},
            {"dateTime": "2026-11-22T12:06:00+07:00", "status": "ON_SHIPPING", "description": "Out for delivery, Krabi - Shipping by Flash"},
            {"dateTime": "2026-11-20T08:33:00+07:00", "status": "ON_OTHER_STATUS", "description": "08:33, Krabi - Shipping by Flash"},
            {"dateTime": "2026-11-19T21:01:00+07:00", "status": "ON_OTHER_STATUS", "description": "Parcel in transit from Surat Thani, Surat Thani - Shipping by Flash"},
            {"dateTime": "2026-11-18T21:54:00+07:00", "status": "ON_PICKED_UP", "description": "Picked up, Delivery staff phone number 0958721459 - Shipping by Flash"},
        ]}
    ]},
}


class TestDetect(unittest.TestCase):
    def test_detect(self):
        self.assertEqual(carriers.detect_carrier("SPXTH06735947878B"), "spx")
        self.assertEqual(carriers.detect_carrier("spxmy0123456789ab"), "spx")
        self.assertEqual(carriers.detect_carrier("TH65019C6BG26H0"), "flash")
        self.assertEqual(carriers.detect_carrier("EF123456789TH"), "thaipost")
        self.assertIsNone(carriers.detect_carrier("123"))

    def test_find_in_text(self):
        text = "Parcel TH65019CZ7KV8H0 delayed. Shopee: SPXTH06250800314B, again TH65019CZ7KV8H0"
        self.assertEqual(
            carriers.find_tracking_numbers(text),
            [("TH65019CZ7KV8H0", "flash"), ("SPXTH06250800314B", "spx")],
        )

    def test_spx_country(self):
        self.assertEqual(carriers.spx_country("SPXVN0123456789", "th"), "vn")
        self.assertEqual(carriers.spx_country("SPXXX0123456789", "my"), "my")


class TestSpx(unittest.TestCase):
    def test_out_for_delivery(self):
        r = carriers.parse_spx("SPXTH06735947878B", SPX_OUT_FOR_DELIVERY)
        self.assertEqual(r.status, "out_for_delivery")
        self.assertEqual(r.step, 3)
        self.assertEqual(r.event, "Out for delivery")
        self.assertEqual(len(r.events), 6)  # hidden record dropped
        self.assertEqual(r.events[1].location, "Krabi")
        self.assertEqual(r.events[2].location, "→ Krabi")
        self.assertEqual(r.events[3].location, "Surat Thani")
        self.assertEqual(r.events[4].location, "Bangkok")
        self.assertEqual(r.events[5].location, "Shenzhen")
        self.assertTrue(r.time.endswith("+00:00"))

    def test_packed(self):
        r = carriers.parse_spx("SPXTH06250800314B", SPX_PACKED)
        self.assertEqual(r.status, "packed")
        self.assertEqual(r.step, 2)

    def test_delivered(self):
        r = carriers.parse_spx("SPXTH1", SPX_DELIVERED)
        self.assertEqual(r.status, "delivered")
        self.assertEqual(r.delivered_at, r.time)

    def test_not_found(self):
        self.assertIsNone(carriers.parse_spx("SPXTH1", SPX_NOT_FOUND))


class TestFlash(unittest.TestCase):
    def test_parse(self):
        res = carriers.parse_flash(FLASH)
        self.assertEqual(res["TH65019C6BG26H0"].status, "failed_attempt")
        self.assertEqual(res["TH65019C6BG26H0"].events[1].location, "Krabi")
        self.assertEqual(res["TH65019C6BG26H0"].events[2].location, "Phang Nga")
        self.assertEqual(res["TH65019C6BG26H0"].time, "2026-11-22T18:38:48+07:00")
        self.assertEqual(res["TH65019CKJXM3H0"].status, "delivered")
        self.assertEqual(res["TH65019D41ZJ2H0"].status, "packed")


class TestEtrackings(unittest.TestCase):
    def test_failed_attempt(self):
        r = carriers.parse_etrackings("TH01234567890A", "flash", ETR)
        self.assertEqual(r.status, "failed_attempt")
        self.assertEqual(r.events[0].event, "Delivery attempt failed")
        self.assertEqual(r.events[1].event, "Out for delivery")
        self.assertEqual(r.events[1].location, "Krabi")
        self.assertEqual(r.events[2].event, "In transit")
        self.assertEqual(r.events[3].event, "Departed hub")
        self.assertEqual(r.events[4].event, "Picked up by courier")
        self.assertEqual(r.events[4].location, "")

    def test_scrub_stored(self):
        stored = {"tracking_number": "TH1", "event": "18:03", "location": "Delivery staff phone number 0645980037",
                  "events": [{"time": "", "event": "09:20", "location": "Delivery staff phone number 0958721459"}]}
        r = carriers.TrackResult.from_dict(stored)
        self.assertEqual(r.event, "In transit")
        self.assertEqual(r.location, "")
        self.assertEqual(r.events[0].event, "In transit")
        self.assertEqual(r.events[0].location, "")


class TestRoundTrip(unittest.TestCase):
    def test_dict(self):
        r = carriers.parse_spx("SPXTH06735947878B", SPX_OUT_FOR_DELIVERY)
        again = carriers.TrackResult.from_dict(r.as_dict())
        self.assertEqual(again.as_dict(), r.as_dict())


if __name__ == "__main__":
    unittest.main()
