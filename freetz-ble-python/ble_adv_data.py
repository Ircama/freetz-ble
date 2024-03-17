#coding=utf-8

from uuid import UUID
from construct import *
from atc_mi_construct import general_format


# 06: Any nearby device can discover it by scanning. Bluetooth Basic Rate/Enhanced Data Rate (BR/EDT) is not supported.
# 1a: The device can be used as BLE as well as full Bluetooth Controller/Host simultaneously.
flags_values = BitStruct(
    Padding(3),
    "FLAG_LE_BR_EDR_HOST" / Flag,  # Bit 4
    "FLAG_LE_BR_EDR_CONTROLLER" / Flag,  # Bit 3
    "FLAG_BR_EDR_NOT_SUPPORTED" / Flag,  # Bit 2
    "FLAG_LE_GENERAL_DISC_MODE" / Flag,  # Bit 1
    "FLAG_LE_LIMITED_DISC_MODE" / Flag,  # Bit 0
)

LeAddress = ExprAdapter(Byte[6],
    decoder = lambda obj, ctx: ":".join("%02x" % b for b in obj[::-1]).upper(),
    encoder = lambda obj, ctx: bytes.fromhex(re.sub(r'[.:\- ]', '', obj))[::-1]
)

Uuid128_format = ExprAdapter(Bytes(16),
    decoder = lambda obj, ctx: str(UUID(bytes=obj[::-1])),
    encoder = lambda obj, ctx: UUID(obj).bytes[::-1]
)

uuid128_values = Struct(
    "uuid" / Uuid128_format,
    "data" / Switch(this.uuid,
        {
            "2141e110-213a-11e6-b67b-9e71128cae77": Computed(
                "DAIKINS_ACUnitManagement"
            ),
            "2141e112-213a-11e6-b67b-9e71128cae77": Computed(
                "DAIKINS_CHAR_WRITE_WITHOUT_RESPONSE_UUID"
            ),
            "2141e111-213a-11e6-b67b-9e71128cae77": Computed(
                "DAIKINS_CHAR_NOTIF_UUID"
            ),
            "2141e100-213a-11e6-b67b-9e71128cae77": Computed(
                "DAIKINS_FIRMWARE_MANAGEMENT"
            ),
            "2141e101-213a-11e6-b67b-9e71128cae77": Computed(
                "DAIKINS_Notify"
            ),
            "2141e102-213a-11e6-b67b-9e71128cae77": Computed(
                "DAIKINS_WriteWithoutResponse"
            ),
            "2141e103-213a-11e6-b67b-9e71128cae77": Computed(
                "DAIKINS_Notify2"
            ),
        }
    )
)

# https://bitbucket.org/bluetooth-SIG/public/src/main/assigned_numbers/uuids/service_uuids.yaml
# https://jonas-schievink.github.io/rubble/src/rubble/uuid.rs.html
uuid_values = Enum(Int16ul,
    Health_Thermometer_service = 0x1809,  # org.bluetooth.service.health_thermometer
    Device_Information = 0x180a,  # org.bluetooth.service.device_information
    LG_Electronics = 0xfeb9,
    Google_LLC = 0xfe9f,
)

# https://bitbucket.org/bluetooth-SIG/public/src/main/assigned_numbers/core/ad_types.yaml
ble_ad_data = GreedyRange(Prefixed(Byte,
    Struct(
        "ble_type" / Enum(Byte,
            FLAGS = 0x01,
            INCOMPLETE_LIST_SERVICE_UUID16 = 0x02,
            COMPLETE_LIST_SERVICE_UUID16 = 0x03,
            INCOMPLETE_LIST_SERVICE_UUID32 = 0x04,
            COMPLETE_LIST_SERVICE_UUID32 = 0x05,
            INCOMPLETE_LIST_SERVICE_UUID128 = 0x06,
            COMPLETE_LIST_SERVICE_UUID128 = 0x07,
            SHORTENED_LOCAL_NAME = 0x08,
            COMPLETE_LOCAL_NAME = 0x09,
            TX_POWER_LEVEL = 0x0A,
            CLASS_OF_DEVICE = 0x0D,

            SERVICE_DATA_UUID16 = 0x16,
            LE_BLUETOOTH_DEVICE_ADDRESS = 0x1B,
            SERVICE_DATA_UUID32 = 0x20,
            SERVICE_DATA_UUID128 = 0x21,

            MANUFACTURER_SPECIFIC_DATA = 0xFF
        ),
        "adv_data" / Switch(this.ble_type,
            {
                "FLAGS": Struct(
                    "flags" / flags_values
                ),
                "INCOMPLETE_LIST_SERVICE_UUID16": uuid_values,
                "COMPLETE_LIST_SERVICE_UUID16": uuid_values,
                "INCOMPLETE_LIST_SERVICE_UUID32": uuid_values,
                "COMPLETE_LIST_SERVICE_UUID32": uuid_values,
                "INCOMPLETE_LIST_SERVICE_UUID128": uuid128_values,
                "COMPLETE_LIST_SERVICE_UUID128": uuid128_values,
                "SERVICE_DATA_UUID16": Struct(
                    "uuid16" / general_format
                ),
                "SHORTENED_LOCAL_NAME": Struct(
                    "shortened_local_name" / GreedyString("utf8"),
                ),
                "COMPLETE_LOCAL_NAME": Struct(
                    "complete_local_name" / GreedyString("utf8"),
                ),
                "MANUFACTURER_SPECIFIC_DATA": Struct(
                    "manuf_spec_data" / GreedyBytes,
                ),
                "TX_POWER_LEVEL": Struct(
                    "power" / Int8sl,
                    "power_unit" / Computed("dBm"),
                ),
                "LE_BLUETOOTH_DEVICE_ADDRESS": LeAddress,
            }
        )
    ))
)
