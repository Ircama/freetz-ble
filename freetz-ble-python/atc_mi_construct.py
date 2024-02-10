#############################################################################
# atc_mi_construct.py (revision supporting python2.7)
#############################################################################

from atc_mi_construct_adapters import *

# -------------- custom_format -------------------------------------------------
# "PVVX (Custom)" advertising type, encrypted beacon unchecked

# https://github.com/pvvx/ATC_MiThermometer#custom-format-all-data-little-endian
# Min. firmware Version: 0.8

atc_flag = BitStruct(  # GPIO_TRG pin (marking "reset" on circuit board) flags:
    Padding(3),
    "humidity_trigger" / Flag,  # Bit 4 - Humidity trigger event
    "temp_trigger" / Flag,  # Bit 3 - Temperature trigger event
    "out_gpio_trg_flag" / Flag,  # Bit 2 - If this flag is set, the output GPIO_TRG pin is controlled according to the set parameters threshold temperature or humidity
    "out_gpio_trg_value" / Flag,  # Bit 1 - GPIO_TRG pin output value (pull Up/Down)
    "input_gpio_value" / Flag,  # Bit 0 - Reed Switch, input
)

custom_format = Struct(
    "version" / Computed(1),
    "size" / Int8ul,  # 18 (0x12)
    "uid" / Int8ul,  # BLE classifier - Common Data Type; 0x16=22=Service Data, 16-bit UUID follows https://www.bluetooth.com/specifications/assigned-numbers/generic-access-profile/
    "UUID" / ByteSwapped(Const(b"\x18\x1a")),  # GATT Service 0x181A Environmental Sensing
    "MAC" / ReversedMacAddress,  # [0] - lo, .. [6] - hi digits
    "mac_vendor" / MacVendor,
    "temperature" / Int16sl_x100,
    "temperature_unit" / Computed(u'\N{DEGREE SIGN}C'),
    "humidity" / Int16ul_x100,
    "humidity_unit" / Computed("%"),
    "battery_v" / Int16ul_x1000,
    "battery_v_unit" / Computed("V"),
    "battery_level" / Int8ul,  # 0..100 %
    "battery_level_unit" / Computed("%"),
    "counter" / Int8ul,  # measurement count
    "flags" / atc_flag
)

# -------------- custom_enc_format ---------------------------------------------
# "PVVX (Custom)" advertising type, encrypted beacon checked

custom_enc_format = Struct(
    "version" / Computed(1),
    "size" / Int8ul,  # 14 (0x0e)
    "uid" / Int8ul,  # BLE classifier - Common Data Type; 0x16=22=Service Data, 16-bit UUID follows https://www.bluetooth.com/specifications/assigned-numbers/generic-access-profile/
    "UUID" / ByteSwapped(Const(b"\x18\x1a")),  # GATT Service 0x181A Environmental Sensing
    "codec" / AtcMiCodec(
        Struct(
            "temperature" / Int16sl_x100,
            "temperature_unit" / Computed(u'\N{DEGREE SIGN}'),
            "humidity" / Int16ul_x100,
            "humidity_unit" / Computed("%"),
            "battery_level" / Int8ul,  # 0..100 %
            "battery_level_unit" / Computed("%"),
            "flags" / atc_flag
        )
    ),
)

# -------------- atc1441_format ------------------------------------------------
# "ATC1441" advertising type, encrypted beacon unchecked

# https://github.com/pvvx/ATC_MiThermometer#atc1441-format

atc1441_format = Struct(
    "version" / Computed(1),
    "size" / Int8ul,  # 18
    "uid" / Int8ul,  # BLE classifier - Common Data Type; 0x16=22=Service Data, 16-bit UUID follows https://www.bluetooth.com/specifications/assigned-numbers/generic-access-profile/
    "UUID" / ByteSwapped(Const(b"\x18\x1a")),  # GATT Service 0x181A Environmental Sensing
    "MAC" / MacAddress,  # [0] - hi, .. [6] - lo digits
    "mac_vendor" / MacVendor,
    "temperature" / Int16sb_x10,
    "temperature_unit" / Computed(u'\N{DEGREE SIGN}C'),
    "humidity" / Int8ul,  # 0..100 %
    "humidity_unit" / Computed("%"),
    "battery_level" / Int8ul,  # 0..100 %
    "battery_level_unit" / Computed("%"),
    "battery_v" / Int16ub_x1000,
    "battery_v_unit" / Computed("V"),
    "counter" / Int8ub  # frame packet counter
)

# -------------- atc1441_enc_format ------------------------------------------------
# "ATC1441" advertising type, encrypted beacon checked

# encrypted custom beacon
# https://github.com/pvvx/ATC_MiThermometer/issues/94#issuecomment-842846036

atc1441_enc_format = Struct(
    "version" / Computed(1),
    "size" / Int8ul,  # 14 (0x0e)
    "uid" / Int8ul,  # BLE classifier - Common Data Type; 0x16=22=Service Data, 16-bit UUID follows https://www.bluetooth.com/specifications/assigned-numbers/generic-access-profile/
    "UUID" / ByteSwapped(Const(b"\x18\x1a")),  # GATT Service 0x181A Environmental Sensing
    "codec" / AtcMiCodec(
        Struct(
            "temperature" / ExprAdapter(Int8sl,  # -40...87 C degrees with half degree precision
                lambda obj, ctx: int(obj) / 2.0 - 40, lambda obj, ctx: int((float(obj) + 40) * 2)),
            "temperature_unit" / Computed(u'\N{DEGREE SIGN}C'),
            "humidity" / ExprAdapter(Int8ul,  # half unit precision
                lambda obj, ctx: int(obj) / 2.0, lambda obj, ctx: int(float(obj) * 2)),
            "humidity_unit" / Computed("%"),
            "batt_trg" / BitStruct(
                "out_gpio_trg_flag" / Flag,  # If this flag is set, the output GPIO_TRG pin is controlled according to the set parameters threshold temperature or humidity
                "battery_level" / BitsInteger(7),  # 0..100 %
                "battery_level_unit" / Computed("%"),
            )
        )
    ),
)

# -------------- mi_like_format ------------------------------------------------
# "MIJIA (MiHome)" advertising type, encrypted beacon either checked or unchecked

# Can be clear or encrypted
# https://github.com/pvvx/ATC_MiThermometer/tree/master/InfoMijiaBLE

mi_like_data = Struct(  # https://github.com/pvvx/ATC_MiThermometer/blob/master/src/mi_beacon.h#L77-L102
    "type" / Select(
        Enum(Int16ul,  # https://iot.mi.com/new/doc/accesses/direct-access/embedded-development/ble/object-definition
            XIAOMI_DATA_ID_Sleep                =0x1002,
            XIAOMI_DATA_ID_RSSI                 =0x1003,
            XIAOMI_DATA_ID_Temperature          =0x1004,
            XIAOMI_DATA_ID_WaterBoil            =0x1005,
            XIAOMI_DATA_ID_Humidity             =0x1006,
            XIAOMI_DATA_ID_LightIlluminance     =0x1007,
            XIAOMI_DATA_ID_SoilMoisture         =0x1008,  # Soil moisture
            XIAOMI_DATA_ID_SoilECvalue          =0x1009,  # Soil EC value
            XIAOMI_DATA_ID_Power                =0x100A,  # Battery
            XIAOMI_DATA_ID_TempAndHumidity      =0x100D,
            XIAOMI_DATA_ID_Lock                 =0x100E,
            XIAOMI_DATA_ID_Gate                 =0x100F,
            XIAOMI_DATA_ID_Formaldehyde         =0x1010,
            XIAOMI_DATA_ID_Bind                 =0x1011,
            XIAOMI_DATA_ID_Switch               =0x1012,
            XIAOMI_DATA_ID_RemAmCons            =0x1013,  # Remaining amount of consumables
            XIAOMI_DATA_ID_Flooding             =0x1014,
            XIAOMI_DATA_ID_Smoke                =0x1015,
            XIAOMI_DATA_ID_Gas                  =0x1016,
            XIAOMI_DATA_ID_NoOneMoves           =0x1017,  # No one moves
            XIAOMI_DATA_ID_LightIntensity       =0x1018,
            XIAOMI_DATA_ID_DoorSensor           =0x1019,
            XIAOMI_DATA_ID_WeightAttributes     =0x101A,
            XIAOMI_DATA_ID_NoOneMovesOverTime   =0x101B,  # No one moves over time
            XIAOMI_DATA_ID_SmartPillow          =0x101C,
            XIAOMI_DATA_ID_FormaldehydeNew      =0x101D,
            XIAOMI_DATA_ID_BodyTemperature      =0x2000,  # measured every second
            XIAOMI_DATA_ID_Bracelet             =0x2001,  # Mi Band (Huami)
            XIAOMI_DATA_ID_VacuumCleaner        =0x2002,  # (Rui Mi)
            XIAOMI_DATA_ID_BPBracelet           =0x2003,  # (like one)
            XIAOMI_DATA_ID_Monitor              =0x3000,  # Monitor (flowers and grasses)
            XIAOMI_DATA_ID_SensorLocation       =0x3001,  # Sensor location (Qingping)
            XIAOMI_DATA_ID_PomodoroIncident     =0x3002,  # Pomodoro incident (Qingping)
            XIAOMI_DATA_ID_ToothbrushIncident   =0x3003,  # Xiaobei toothbrush incident (Qinghe Xiaobei) 
            UNBOUND_DEVICE                      =0x0128,
        ),
        Enum(Int8ul,
            XIAOMI_UNBOUND                      =0x08,
        )
    ),
    "data" / Switch(this.type,  # https://github.com/pvvx/ATC_MiThermometer/blob/master/InfoMijiaBLE/Mijia%20BLE%20Object%20Definition.md
        {
            "XIAOMI_DATA_ID_Sleep": Struct(  # 02
                "type_length" / Const(b"\x01"),
                "sleep" / Flag,
            ),
            "XIAOMI_DATA_ID_RSSI": Struct(  # 03
                "type_length" / Const(b"\x01"),
                "RSSI_level" / Int8ul,
                "RSSI_level_unit" / Computed("dBm"),
            ),
            "XIAOMI_DATA_ID_Temperature": Struct(  # 04
                "type_length" / Const(b"\x02"),
                "temperature" / Int16sl_x10,
                "temperature_unit" / Computed(u'\N{DEGREE SIGN}C'),
            ),
            "XIAOMI_DATA_ID_WaterBoil": Struct(  # 05
                "type_length" / Const(b"\x02"),
                "power" / Int8ul,
                "temperature" / Int8ul,
            ),
            "XIAOMI_DATA_ID_Humidity": Struct(  # 06
                "type_length" / Const(b"\x02"),  # ranging from 0-1000
                "humidity" / Int16ul_x10,  # 0..100 %
                "humidity_unit" / Computed("%"),
            ),
            "XIAOMI_DATA_ID_LightIlluminance": Struct(  # 07
                "type_length" / Const(b"\x03"),
                "illuminance" / Int24ul,  # Range: 0-120000
                "illuminance_unit" / Computed("Lux"),
            ),
            "XIAOMI_DATA_ID_SoilMoisture": Struct(  # 08, Humidity percentage
                "type_length" / Const(b"\x01"),
                "moisture_level" / Int8ul,  # 0..100 %
                "moisture_level_unit" / Computed("%"),
            ),
            "XIAOMI_DATA_ID_SoilECvalue": Struct(  # 09, Conductivity
                "type_length" / Const(b"\x02"),
                "conductivity" / Int16ul_x10,  # range: 0-5000
                "conductivity_unit" / Computed("us/cm"),
            ),
            "XIAOMI_DATA_ID_Power": Struct(  # 0A
                "battery_length" / Const(b"\x01"),
                "battery_level" / Int8ul,  # 0..100 %
                "battery_level_unit" / Computed("%"),
            ),
            "XIAOMI_DATA_ID_TempAndHumidity": Struct(  # 0D
                "type_length" / Const(b"\x04"),
                "temperature" / Int16sl_x10,
                "temperature_unit" / Computed(u'\N{DEGREE SIGN}C'),
                "humidity" / Int16ul_x10,
                "humidity_unit" / Computed("%"),
            ),
            "XIAOMI_DATA_ID_Lock": Struct(  # 0E
                "type_length" / Const(b"\x01"),
                "lock" / BitStruct(
                    "child lock status" / Flag,  # (1: open; 0: close)
                    "oblique bolt state" / Flag,  # (1: eject; 0: retract)
                    "dull state" / Flag,  # (1: eject; 0: retract)
                    "square bolt status" / Flag,  # (1: eject; 0: retract)
                ),
                #   0x00: Unlock state (all bolts retracted)
                #   0x04: The lock bolt pops out (the oblique bolt pops out)
                #   0x05: Lock + lock bolt eject (square bolt, oblique bolt eject)
                #   0x06: Reverse lock + bolt ejection (stay bolt, oblique bolt ejection)
                #   0x07: All lock bolts pop out (square bolt, dull bolt, oblique bolt pop out)
            ),
            "XIAOMI_DATA_ID_Gate": Struct(  # 0F
                "type_length" / Const(b"\x01"),
                "gate" / Enum(Int8ul,
                    XIAOMI_door_open      =0x00,
                    XIAOMI_door_closed    =0x01,
                    XIAOMI_door_error     =0xff,
                )
            ),
            "XIAOMI_DATA_ID_Formaldehyde": Struct(  # 10
                "type_length" / Const(b"\x02"),
                "formaldehyde" / Int16ul_x100,
                "formaldehyde_unit" / Computed("mg/m3"),
            ),
            "XIAOMI_DATA_ID_Bind": Struct(  # 11
                "type_length" / Const(b"\x01"),
                "bound" / Flag,
            ),
            "XIAOMI_DATA_ID_Switch": Struct(  # 12
                "type_length" / Const(b"\x01"),
                "switch" / Flag,
            ),
            "XIAOMI_DATA_ID_RemAmCons": Struct(  # 13, Remaining amount of consumables
                "type_length" / Const(b"\x01"),
                "consumables" / Int8ul,
                "consumables_unit" / Computed("%"),
            ),
            "XIAOMI_DATA_ID_Flooding": Struct(  # 14
                "type_length" / Const(b"\x01"),
                "flooding" / Flag,
            ),
            "XIAOMI_DATA_ID_Smoke": Struct(  # 15
                "type_length" / Const(b"\x01"),
                "smoke" / Enum(Int8ul,
                    XIAOMI_Smoke_Normal_Monitoring      =0x00,
                    XIAOMI_Smoke_Fire_Alarm             =0x01,
                    XIAOMI_Smoke_Equipment_Failure      =0x02,
                )
            ),
            "XIAOMI_DATA_ID_Gas": Struct(  # 16
                "type_length" / Const(b"\x01"),
                "gas" / Flag,
            ),
            "XIAOMI_DATA_ID_NoOneMoves": Struct(  # 17, duration of the idle time, in seconds.
                "type_length" / Const(b"\x04"),
                "idle_time" / Int32ul,
            ),
            "XIAOMI_DATA_ID_LightIntensity": Struct(  # 18
                "type_length" / Const(b"\x01"),
                "light_detected" / Flag,
            ),
            "XIAOMI_DATA_ID_DoorSensor": Struct(  # 19
                "type_length" / Const(b"\x01"),
                "door" / Enum(Int8ul,
                    XIAOMI_door_open                =0x00,
                    XIAOMI_door_closed              =0x01,
                    XIAOMI_door_not_closed_in_time  =0x02,
                    XIAOMI_door_reset               =0x03, # knock on the door
                    XIAOMI_door_pry                 =0x04, # Pry the door
                    XIAOMI_door_stuck               =0x05, # The door is stuck
                )
            ),
            "XIAOMI_DATA_ID_WeightAttributes": Struct(  # 1A
                "type_length" / Const(b"\x02"),
                "weight" / Int16ul,
                "weight_unit" / Computed("grams"),
            ),
            "XIAOMI_DATA_ID_NoOneMovesOverTime": Struct(  # 1B
                "type_length" / Const(b"\x01"),
                "timeout_unmoved" / Flag,
                # 0x00: means someone is moving
                # 0x01: means no one is moving for X seconds
                # Note: The user configures no one to move for X seconds on
                #       the plug-in side. The firmware side stores this setting
                #       value and reports this object after the time is reached.
            ),
            "XIAOMI_DATA_ID_SmartPillow": Struct(  # 1C
                "type_length" / Const(b"\x01"),
                "pillow" / Enum(Int8ul,
                    XIAOMI_get_out_of_bed     =0x00,  # (not on the pillow)
                    XIAOMI_on_the_bed         =0x01,  # (lie on the pillow)
                )
            ),
            "XIAOMI_DATA_ID_FormaldehydeNew": Struct(  # 1D
                "type_length" / Const(b"\x02"),
                "formaldehyde" / Int16ul_x1000,
                "formaldehyde_unit" / Computed("mg/m3"),
            ),
            "XIAOMI_DATA_ID_BodyTemperature": Struct(
                "type_length" / Const(b"\x05"),
                "skin temperature" / Int16sl_x100,
                "PCB temperature" / Int16sl_x100,
                "temperature_unit" / Computed(u'\N{DEGREE SIGN}C'),
                "battery_power" / Int8ul,
                "battery_power_unit" / Computed("%"),
            ),
            "XIAOMI_DATA_ID_Bracelet": Struct(  # Huami bracelet attributes
                "type_length" / Const(b"\x04"),
                "steps" / Int16ul,  # Number of steps
                "sleep" / Enum(Int8ul,
                    XIAOMI_bracelet_asleep    =0x01,  # (Falling asleep)
                    XIAOMI_bracelet_waking_up =0x02,  # (waking up)
                ),
                "RSSI_level" / Int8ul,  # Absolute value of signal intensity
                "RSSI_level_unit" / Computed("dBm"),
            ),
            "XIAOMI_DATA_ID_VacuumCleaner": Struct(  # Ruimi vacuum cleaner properties
                "type_length" / Const(b"\x02"),
                "mode" / Enum(Int8ul,
                    XIAOMI_charging    =0x00,
                    XIAOMI_standby     =0x01,
                    XIAOMI_standard    =0x02,
                    XIAOMI_strong      =0x03,
                    XIAOMI_error       =0xff,
                ),
                "gear" / Int8ul,  # Current standard gear
            ),
            "XIAOMI_DATA_ID_BPBracelet": Struct(  # Black plus bracelet attributes
                "type_length" / Const(b"\x04"),
                "steps" / Int16ul,  # Number of steps of the day
                "heart_rate" / Int8ul,  # Last heart rate
                "status" / Int8ul,  # Current activity status
            ),
            "XIAOMI_DATA_ID_Monitor": Struct(  # Flower and grass detector event
                "type_length" / Const(b"\x01"),
                "status" / Flag,  # Normal (0x00), unplug (0x01)
            ),
            "XIAOMI_DATA_ID_SensorLocation": Struct(  # Qingping sensor event
                "type_length" / Const(b"\x01"),
                "position" / Flag,  # Separate from the base (0x00), connect (0x01)
            ),
            "XIAOMI_DATA_ID_PomodoroIncident": Struct(  # Qingping Pomodoro Event
                "type_length" / Const(b"\x01"),
                "event_type" / Flag,  # 0-Start of Pomodoro, 1-End of Pomodoro, 2-Start of rest, 3-End of rest
            ),
            "XIAOMI_DATA_ID_ToothbrushIncident": Struct(  # Beckham toothbrush incident
                "type_length" / Int8ul,
                "state" / Flag,  # 0: Start of brushing, 1: End of brushing
                "date" / Timestamp(Int32ul, 1, 1970),  # UTC time
                "date_is_stored" / IfThenElse(
                    lambda this: this.date.timestamp() > 0,
                    Computed("True"),
                    Computed("False"),
                ),
                "score" / IfThenElse(
                    lambda this: this.type_length == 6,
                    Int8ul,  # This parameter can be added to the end of brushing event: the score of this brushing, 0~100
                    Computed("no_data"),
                )
            ),
            "UNBOUND_DEVICE": Const(b"\x00"),
        }
    )
)

mi_like_format = Struct(
    "version" / Computed(2),
    "size" / Int8ul,  # e.g., 21
    "uid" / Int8ul,  # BLE classifier - Common Data Type; 0x16=22=Service Data, 16-bit UUID follows https://www.bluetooth.com/specifications/assigned-numbers/generic-access-profile/
    "UUID" / ByteSwapped(Const(b"\xfe\x95")),  # 16-bit UUID for Members 0xFE95 Xiaomi Inc.
    "ctrl" / BitStruct(  # Frame Control (https://github.com/pvvx/ATC_MiThermometer/blob/master/src/mi_beacon.h#L104-L124)
        "Mesh" / Flag,  # 0: does not include Mesh; 1: includes Mesh. For standard BLE access products and high security level access, this item is mandatory to 0. This item is mandatory for Mesh access to 1. For more information about Mesh access, please refer to Mesh related documents
        "Object_Include" / Flag,  # 0: does not contain Object; 1: contains Object
        "Capability_Include" / Flag,  # 0: does not include Capability; 1: includes Capability. Before the device is bound, this bit is forced to 1
        "MAC_Include" / Flag,  # 0: Does not include the MAC address; 1: includes a fixed MAC address (the MAC address is included for iOS to recognize this device and connect)
        "isEncrypted" / Flag,  # 0: The package is not encrypted; 1: The package is encrypted
        "Reserved" / BitsInteger(3),
        "version" / BitsInteger(4),  # Version number (currently v5)
        "Auth_Mode" / BitsInteger(2),  # 0: old version certification; 1: safety certification; 2: standard certification; 3: reserved
        "solicited" / Flag,  # 0: No operation; 1: Request APP to register and bind. It is only valid when the user confirms the pairing by selecting the device on the developer platform, otherwise set to 0. The original name of this item was bindingCfm, and it was renamed to solicited "actively request, solicit" APP for registration and binding
        "registered" / Flag,  # 0: The device is not bound; 1: The device is registered and bound. This item is used to indicate whether the device is reset
    ),
    "device_id" / Enum(Int16ul,  # Device type (https://github.com/pvvx/ATC_MiThermometer/blob/master/src/mi_beacon.h#L14-L35)
        XIAOMI_DEV_ID_LYWSDCGQ       = 0x01AA,  # Xiaomi Mijia Bluetooth Thermometer
        XIAOMI_DEV_ID_CGG1           = 0x0347,  # Xiaomi ClearGrass Bluetooth Hygrothermograph
        XIAOMI_DEV_ID_CGG1_ENCRYPTED = 0x0B48,  # Qingping Temp & RH Monitor
        XIAOMI_DEV_ID_CGDK2          = 0x066F,  # Xiaomi Qingping Temp & RH Monitor Lite
        XIAOMI_DEV_ID_LYWSD02        = 0x045B,  # Xiaomi Mijia Digital Clock
        XIAOMI_DEV_ID_LYWSD03MMC     = 0x055B,  # Xiaomi Mijia Temperature And Humidity Monitor
        XIAOMI_DEV_ID_CGD1           = 0x0576,  # Xiaomi Qingping Bluetooth Alarm Clock
        XIAOMI_DEV_ID_MHO_C303       = 0x06d3,  # MiaoMiaoce Smart Clock Temperature and Humidity Sensor
        XIAOMI_DEV_ID_MHO_C401       = 0x0387,  # Xiaomi E-Ink Smart Thermometer Hygrometer
        XIAOMI_DEV_ID_JQJCY01YM      = 0x02DF,  # Xiaomi Formaldehyde Monitor
        XIAOMI_DEV_ID_HHCCJCY01      = 0x0098,  # Xiaomi Mijia Flower Care (Conductivity, Illuminance, Moisture, Temperature)
        XIAOMI_DEV_ID_GCLS002        = 0x03BC,  # Xiaomi Mijia Flower Care (soil moisture, temperature, light, nutrient detection)
        XIAOMI_DEV_ID_HHCCPOT002     = 0x015D,  # Xiaomi Mijia Smart Flower Pot
        XIAOMI_DEV_ID_WX08ZM         = 0x040A,  # Xiaomi Mijia Mosquito Repellent Device
        XIAOMI_DEV_ID_MCCGQ02HL      = 0x098B,  # Xiaomi Mijia Door and Window Sensor 2
        XIAOMI_DEV_ID_YM_K1501       = 0x0083,  # Xiaomi Viomi Mija Smart Kettle
        XIAOMI_DEV_ID_YM_K1501EU     = 0x0113,  # Xiaomi Viomi Mija Smart Kettle
        XIAOMI_DEV_ID_V_SK152        = 0x045C,  # Xiaomi Viomi Mija Smart Kettle
        XIAOMI_DEV_ID_SJWS01LM       = 0x0863,  # Xiaomi Mijia Flood Detector
        XIAOMI_DEV_ID_MJYD02YL       = 0x07F6,  # Xiaomi Mijia Motion Activated Night Light 2
        XIAOMI_DEV_ID_RTCGQ02LM      = 0x0A8D,  # Xiaomi Mi Smart Home Occupancy Sensor 2
        XIAOMI_DEV_ID_XMMFO1JQD      = 0x04E1,  # Xiaomi Mijia bluetooth Smart Rubik's Cube
        XIAOMI_DEV_ID_YLAI003        = 0x07BF   # Yeelight Remote Control 1S Wireless Switch
    ),
    "counter" / Int8ul,  # 0..0xff..0 frame/measurement count
    "MAC" / ReversedMacAddress,  # [0] - lo, .. [6] - hi digits
    "mac_vendor" / MacVendor,
    "data_point" / Switch(this.ctrl.isEncrypted,
        {
            True: MiLikeCodec(
                Struct(
                    "count_id" / Int24ul,
                    "payload" / GreedyRange(mi_like_data)
                )
            ),
            False: GreedyRange(mi_like_data)
        }
    )
)

# -------------- bt_home_format ------------------------------------------------
# BTHome v1 advertising type. https://bthome.io/v1/

bt_home_data = Struct(
    "bt_home_type" / Enum(Int16ub,
        # a: 0=uint (unsigned), 2=sint (signed), 4=float, 6=string, 8=MAC
        # b: number of bytes; ab=SD; cc=DID=device id
        #                           abcc
        BT_HOME_packet_id       = 0x0200,  # uint8
        BT_HOME_battery         = 0x0201,  # uint8, %
        BT_HOME_temperature     = 0x2302,  # sint16, 0.01 C degrees
        BT_HOME_humidity        = 0x0303,  # uint16, 0.01 %
        BT_HOME_humidity_8      = 0x022e,  # uint8, 1 %
        BT_HOME_pressure        = 0x0404,  # uint24, 0.01 hPa
        BT_HOME_illuminance     = 0x0405,  # uint24, 0.01 lux
        BT_HOME_weight          = 0x0306,  # uint16, 0.01 kg
        BT_HOME_weight_lb       = 0x0307,  # uint16, 0.01 lb
        BT_HOME_dewpoint        = 0x2308,  # sint16, 0.01 C degrees
        BT_HOME_count_i         = 0x0209,  # uint8
        BT_HOME_count_s         = 0x0309,  # uint16
        BT_HOME_count_m         = 0x0409,  # uint24
        BT_HOME_count_l         = 0x0509,  # uint32
        BT_HOME_energy          = 0x040a,  # uint24, 0.001 kWh
        BT_HOME_power           = 0x040b,  # uint24, 0.01 W
        BT_HOME_voltage         = 0x030c,  # uint16, 0.001 V
        BT_HOME_pm2x5           = 0x030d,  # uint16, ug/m3
        BT_HOME_pm10            = 0x030e,  # uint16, ug/m3
        BT_HOME_co2             = 0x0312,  # uint16, ppm
        BT_HOME_tvoc            = 0x0313,  # uint16, ug/m3
        BT_HOME_moisture        = 0x0314,  # uint16, 0.01 %
        BT_HOME_moisture_8      = 0x022f,  # uint8, %
        BT_HOME_timestamp       = 0x0550,  # 4 bytes
        BT_HOME_acceleration    = 0x0351,  # uint16, 0.001 m/s square
        BT_HOME_gyroscope       = 0x0352,  # uint16, 0.001 C degrees/s
        # boolean set
        BT_HOME_boolean = 0x020f,          # 0x0F, uint8, generic boolean
        BT_HOME_switch = 0x0210,           # 0x10, uint8, power on/off
        BT_HOME_opened = 0x0211,           # 0x11, uint8, opening =0 Closed, = 1 Open
        BT_HOME_low_battery = 0x0215,      # 0x15, uint8, =1 low
        BT_HOME_chg_battery = 0x0216,      # 0x16, uint8, battery charging
        BT_HOME_carbon_monoxide = 0x0217,  # 0x17, uint8, carbon monoxide
        BT_HOME_cold = 0x0218,             # 0x18, uint8
        BT_HOME_connectivity = 0x0219,     # 0x19, uint8
        BT_HOME_door = 0x021a,             # 0x1a, uint8, =0 Closed, =1 Open
        BT_HOME_garage_door = 0x021b,      # 0x1b, uint8, =0 Closed, =1 Open
        BT_HOME_gas = 0x021c,              # 0x1c, uint8, =1 Detected
        BT_HOME_heat = 0x021d,             # 0x1d, uint8, =1 Hot
        BT_HOME_light = 0x021e,            # 0x1e, uint8, =1 Light detected
        BT_HOME_lock = 0x021f,             # 0x1f, uint8, =1 Unlocked
        BT_HOME_moisture_b = 0x0220,       # 0x20, uint8, =0 Dry, =1 Wet
        BT_HOME_motion = 0x0221,           # 0x21, uint8, =0 Clear, =1 Detected
        BT_HOME_moving = 0x0222,           # 0x22, uint8, =1 Moving
        BT_HOME_occupancy = 0x0223,        # 0x23, uint8, =1 Detected
        BT_HOME_plug = 0x0224,             # 0x24, uint8, =0 Unplugged, =1 Plugged in
        BT_HOME_presence = 0x0225,         # 0x25, uint8, =0 Away, =1 Home
        BT_HOME_problem = 0x0226,          # 0x26, uint8, =0 Ok, =1 Problem
        BT_HOME_running = 0x0227,          # 0x27, uint8, =0 Not Running, =1 Running
        BT_HOME_safety = 0x0228,           # 0x28, uint8, =0 Unsafe, =1 Safe
        BT_HOME_smoke = 0x0229,            # 0x29, uint8, =0 Clear, =1 Detected
        BT_HOME_sound = 0x022a,            # 0x2a, uint8, =0 Clear, =1 Detected
        BT_HOME_tamper = 0x022b,           # 0x2b, uint8, =0 Off, =1 On
        BT_HOME_vibration = 0x022c,        # 0x2c, uint8, =0 Clear, =1 Detected
        BT_HOME_window = 0x022d,           # 0x2d, uint8, =0 Closed, =1 Open
        # Text formats are in the form "BT_HOME_raw_nn" and "BT_HOME_text_nn",
        # where nn is the two-digit decimal length of the text, 00..30 bytes.
        # When building, a smaller string is padded with null bytes.
    ),
    "data" / Switch(this.bt_home_type,
        {
            "BT_HOME_packet_id": Struct(
                "packet_id" / Int8ul,  # integer (0..255)
            ),
            "BT_HOME_battery": Struct(
                "battery_level" / Int8ul,  # 0..100 %
                "battery_level_unit" / Computed("%"),
            ),
            "BT_HOME_temperature": Struct(
                "temperature" / Int16sl_x100,
                "temperature_unit" / Computed(u'\N{DEGREE SIGN}C'),
            ),
            "BT_HOME_humidity": Struct(
                "humidity" / Int16ul_x100,
                "humidity_unit" / Computed("%"),
            ),
            "BT_HOME_humidity_8": Struct(
                "humidity_8" / Int8ul,
                "humidity_8_unit" / Computed("%"),
            ),
            "BT_HOME_pressure": Struct(
                "pressure" / Int24ul_x100,
                "pressure_unit" / Computed("hPa"),
            ),
            "BT_HOME_illuminance": Struct(
                "illuminance" / Int24ul_x100,
                "illuminance_unit" / Computed("lux"),
            ),
            "BT_HOME_weight": Struct(
                "weight" / Int16ul_x100,
                "weight_unit" / Computed("kg"),
            ),
            "BT_HOME_weight_lb": Struct(
                "weight_lb" / Int16ul_x100,
                "weight_lb_unit" / Computed("lb"),
            ),
            "BT_HOME_dewpoint": Struct(
                "dewpoint" / Int16sl_x100,
                "dewpoint_unit" / Computed(u'\N{DEGREE SIGN}C'),
            ),
            "BT_HOME_count_i": Struct(
                "count_i" / Int8ul,  # integer (0..255)
            ),
            "BT_HOME_count_s": Struct(
                "count_s" / Int16ul,
            ),
            "BT_HOME_count_m": Struct(
                "count_m" / Int24ul,
            ),
            "BT_HOME_count_l": Struct(
                "count_l" / Int32ul,  # integer (0..4294967295)
            ),
            "BT_HOME_energy": Struct(
                "energy" / Int24ul_x1000,
                "energy_unit" / Computed("kWh"),
            ),
            "BT_HOME_power": Struct(
                "power" / Int24ul_x100,
                "power_unit" / Computed("W"),
            ),
            "BT_HOME_voltage": Struct(
                "battery_v" / Int16ul_x1000,
                "battery_v_unit" / Computed("V"),
            ),
            "BT_HOME_pm2x5": Struct(
                "pm2x5" / Int16ul,
                "pm2x5_unit" / Computed("ug/m3"),
            ),
            "BT_HOME_pm10": Struct(
                "pm10" / Int16ul,
                "pm10_unit" / Computed("ug/m3"),
            ),
            "BT_HOME_co2": Struct(
                "co2" / Int16ul,
                "co2_unit" / Computed("ppm"),
            ),
            "BT_HOME_tvoc": Struct(
                "tvoc" / Int16ul,
                "tvoc_unit" / Computed("ug/m3"),
            ),
            "BT_HOME_moisture": Struct(
                "moisture" / Int16ul_x100,
                "moisture_unit" / Computed("%"),
            ),
            "BT_HOME_moisture_8": Struct(
                "moisture_8" / Int8ul,
                "moisture_8_unit" / Computed("%"),
            ),
            "BT_HOME_timestamp": Struct(
                "date" / Timestamp(Int32ul, 1, 1970),
                "date_is_stored" / IfThenElse(
                    lambda this: this.date.timestamp() > 0,
                    Computed("True"),
                    Computed("False"),
                )
            ),
            "BT_HOME_acceleration": Struct(
                "acceleration" / Int16ul_x1000,
                "acceleration_unit" / Computed("m/s\u00b2"),
            ),
            "BT_HOME_gyroscope": Struct(
                "gyroscope" / Int16ul_x1000,
                "gyroscope_unit" / Computed(u'\N{DEGREE SIGN}/s'),
            ),
            "BT_HOME_boolean": BitStruct(
                Padding(7),
                "boolean" / Flag,  # boolean
            ),
            "BT_HOME_switch": BitStruct(
                Padding(7),
                "switch" / Flag,  # boolean
            ),
            "BT_HOME_opened": BitStruct(
                Padding(7),
                "opened" / Flag,  # boolean
            ),
            "BT_HOME_low_battery": BitStruct(
                Padding(7),
                "low_battery" / Flag,
            ),
            "BT_HOME_chg_battery": BitStruct(
                Padding(7),
                "charging_battery" / Flag,
            ),
            "BT_HOME_carbon_monoxide": BitStruct(
                Padding(7),
                "carbon_monoxide" / Flag,
            ),
            "BT_HOME_cold": BitStruct(
                Padding(7),
                "cold" / Flag,
            ),
            "BT_HOME_connectivity": BitStruct(
                Padding(7),
                "connectivity" / Flag,
            ),
            "BT_HOME_door": BitStruct(
                Padding(7),
                "door_open" / Flag,
            ),
            "BT_HOME_garage_door": BitStruct(
                Padding(7),
                "garage_door_open" / Flag,
            ),
            "BT_HOME_gas": BitStruct(
                Padding(7),
                "gas_detected" / Flag,
            ),
            "BT_HOME_heat": BitStruct(
                Padding(7),
                "heat_hot" / Flag,
            ),
            "BT_HOME_light": BitStruct(
                Padding(7),
                "light_detected" / Flag,
            ),
            "BT_HOME_lock": BitStruct(
                Padding(7),
                "lock_unlocked" / Flag,
            ),
            "BT_HOME_moisture_b": BitStruct(
                Padding(7),
                "moisture_wet" / Flag,
            ),
            "BT_HOME_motion": BitStruct(
                Padding(7),
                "motion_detected" / Flag,
            ),
            "BT_HOME_moving": BitStruct(
                Padding(7),
                "moving" / Flag,
            ),
            "BT_HOME_occupancy": BitStruct(
                Padding(7),
                "occupancy_detected" / Flag,
            ),
            "BT_HOME_plug": BitStruct(
                Padding(7),
                "plug_plugged" / Flag,
            ),
            "BT_HOME_presence": BitStruct(
                Padding(7),
                "presence" / Flag,
            ),
            "BT_HOME_problem": BitStruct(
                Padding(7),
                "problem" / Flag,
            ),
            "BT_HOME_running": BitStruct(
                Padding(7),
                "running" / Flag,
            ),
            "BT_HOME_safety": BitStruct(
                Padding(7),
                "safe" / Flag,
            ),
            "BT_HOME_smoke": BitStruct(
                Padding(7),
                "smoke_detected" / Flag,
            ),
            "BT_HOME_sound": BitStruct(
                Padding(7),
                "sound_detected" / Flag,
            ),
            "BT_HOME_tamper": BitStruct(
                Padding(7),
                "tamper_on" / Flag,
            ),
            "BT_HOME_vibration": BitStruct(
                Padding(7),
                "vibration_detected" / Flag,
            ),
            "BT_HOME_window": BitStruct(
                Padding(7),
                "window_open" / Flag,
            ),
        }
    )
)

# BTHome v1, unencrypted advertising type. https://bthome.io/v1/
# https://github.com/custom-components/ble_monitor/issues/548

bt_home_format = Struct(  # V1 simplified formatting
    "version" / Computed(1),
    "size" / Int8ul,
    "uid" / Int8ul,  # BLE classifier - Common Data Type; 0x16=22=Service Data, 16-bit UUID follows https://www.bluetooth.com/specifications/assigned-numbers/generic-access-profile/
    "UUID" / ByteSwapped(Const(b"\x18\x1c")),  # BT_HOME_GATT, SERVICE_UUID_USER_DATA, HA_BLE, no security
    "bt_home_data" / GreedyRange(bt_home_data)
)

# -------------- bt_home_enc_format --------------------------------------------
# BTHome v1, encrypted advertising type. https://bthome.io/v1/

bt_home_enc_format = Struct(  # Simplified formatting
    "version" / Computed(1),
    "size" / Int8ul,
    "uid" / Int8ul,  # BLE classifier - Common Data Type; 0x16=22=Service Data, 16-bit UUID follows https://www.bluetooth.com/specifications/assigned-numbers/generic-access-profile/
    "UUID" / ByteSwapped(Const(b"\x18\x1e")),  # Bond Management Service
    "codec" / BtHomeCodec(
        Struct(
            "count_id" / Int32ul,  # https://github.com/custom-components/ble_monitor/issues/548#issuecomment-1059874327
            "payload" / GreedyRange(bt_home_data)
        )
    ),
)

# -------------- bt_home_v2_format ---------------------------------------------
# BTHome v2 advertising type. Can be clear or encrypted: https://bthome.io/format/

bt_home_v2_data = Struct(
    "bt_home_v2_type" / Enum(Int8ul,
        BtHomeID_PacketId = 0,            # 0x00, uint8
        BtHomeID_battery = 0x01,          # 0x01, uint8, %
        BtHomeID_temperature = 0x02,      # 0x02, sint16, 0.01 C degrees
        BtHomeID_humidity = 0x03,         # 0x03, uint16, 0.01 %
        BtHomeID_pressure = 0x04,         # 0x04, uint24, 0.01 hPa
        BtHomeID_illuminance = 0x05,      # 0x05, uint24, 0.01 lux
        BtHomeID_weight = 0x06,           # 0x06, uint16, 0.01 kg
        BtHomeID_weight_lb = 0x07,        # 0x07, uint16, 0.01 lb
        BtHomeID_dewpoint = 0x08,         # 0x08, sint16, 0.01 C degrees
        BtHomeID_count8 = 0x09,           # 0x09, uint8, factor=1
        BtHomeID_energy24 = 0x0a,         # 0x0A, uint24, 0.001 kWh
        BtHomeID_power24 = 0x0b,          # 0x0B, uint24, 0.01 W
        BtHomeID_voltage = 0x0c,          # 0x0C, uint16, 0.001 V
        BtHomeID_pm2x5 = 0x0d,            # 0x0D, uint16, ug/m3, factor=1
        BtHomeID_pm10 = 0x0e,             # 0x0E, uint16, ug/m3, factor=1
        BtHomeID_co2 = 0x12,              # 0x12, uint16, ppm, factor=1
        BtHomeID_tvoc = 0x13,             # 0x13, uint16, ug/m3, factor=1
        BtHomeID_moisture16 = 0x14,       # 0x14, uint16, 0.01 %
        # boolean set
        BtHomeID_boolean = 0x0f,          # 0x0F, uint8, generic boolean
        BtHomeID_switch = 0x10,           # 0x10, uint8, power on/off
        BtHomeID_opened = 0x11,           # 0x11, uint8, opening =0 Closed, = 1 Open
        BtHomeID_low_battery = 0x15,      # 0x15, uint8, =1 low
        BtHomeID_chg_battery = 0x16,      # 0x16, uint8, battery charging
        BtHomeID_carbon_monoxide = 0x17,  # 0x17, uint8, carbon monoxide
        BtHomeID_cold = 0x18,             # 0x18, uint8
        BtHomeID_connectivity = 0x19,     # 0x19, uint8
        BtHomeID_door = 0x1a,             # 0x1a, uint8, =0 Closed, =1 Open
        BtHomeID_garage_door = 0x1b,      # 0x1b, uint8, =0 Closed, =1 Open
        BtHomeID_gas = 0x1c,              # 0x1c, uint8, =1 Detected
        BtHomeID_heat = 0x1d,             # 0x1d, uint8, =1 Hot
        BtHomeID_light = 0x1e,            # 0x1e, uint8, =1 Light detected
        BtHomeID_lock = 0x1f,             # 0x1f, uint8, =1 Unlocked
        BtHomeID_moisture_b = 0x20,       # 0x20, uint8, =0 Dry, =1 Wet
        BtHomeID_motion = 0x21,           # 0x21, uint8, =0 Clear, =1 Detected
        BtHomeID_moving = 0x22,           # 0x22, uint8, =1 Moving
        BtHomeID_occupancy = 0x23,        # 0x23, uint8, =1 Detected
        BtHomeID_plug = 0x24,             # 0x24, uint8, =0 Unplugged, =1 Plugged in
        BtHomeID_presence = 0x25,         # 0x25, uint8, =0 Away, =1 Home
        BtHomeID_problem = 0x26,          # 0x26, uint8, =0 Ok, =1 Problem
        BtHomeID_running = 0x27,          # 0x27, uint8, =0 Not Running, =1 Running
        BtHomeID_safety = 0x28,           # 0x28, uint8, =0 Unsafe, =1 Safe
        BtHomeID_smoke = 0x29,            # 0x29, uint8, =0 Clear, =1 Detected
        BtHomeID_sound = 0x2a,            # 0x2a, uint8, =0 Clear, =1 Detected
        BtHomeID_tamper = 0x2b,           # 0x2b, uint8, =0 Off, =1 On
        BtHomeID_vibration = 0x2c,        # 0x2c, uint8, =0 Clear, =1 Detected
        BtHomeID_window = 0x2d,           # 0x2d, uint8, =0 Closed, =1 Open
        # others
        BtHomeID_humidity8 = 0x2e,        # 0x2e, uint8, %, factor=1
        BtHomeID_moisture8 = 0x2f,        # 0x2f, uint8, %, factor=1
        BtHomeID_0x30 = 0x30,             # 0x30, uint8
        BtHomeID_0x31 = 0x31,             # 0x31, uint8
        BtHomeID_0x32 = 0x32,             # 0x32, uint8
        BtHomeID_0x33 = 0x33,             # 0x33, uint8
        BtHomeID_0x34 = 0x34,             # 0x34, uint8
        BtHomeID_0x35 = 0x35,             # 0x35, uint8
        BtHomeID_0x36 = 0x36,             # 0x36, uint8
        BtHomeID_0x37 = 0x37,             # 0x37, uint8
        BtHomeID_0x38 = 0x38,             # 0x38, uint8
        BtHomeID_0x39 = 0x39,             # 0x39, uint8
        BtHomeID_button = 0x3a,           # 0x3a, uint8, =1 press, =2 double_press ... https:# bthome.io/format/
        BtHomeID_0x3b = 0x3b,             # 0x3b, uint8
        BtHomeID_dimmer = 0x3c,           # 0x3c, uint16 ?, =1 rotate left 3 steps, ... https:# bthome.io/format/
        BtHomeID_count16 = 0x3d,          # 0x3d, uint16
        BtHomeID_count32 = 0x3e,          # 0x3e, uint32
        BtHomeID_rotation = 0x3f,         # 0x3f, sint16, 0.1
        BtHomeID_distance_mm  = 0x40,     # 0x40, uint16, mm
        BtHomeID_distance_m = 0x41,       # 0x41, uint16, m, 0.1
        BtHomeID_duration = 0x42,         # 0x42, uint24, 0.001, s
        BtHomeID_current = 0x43,          # 0x43, uint16, 0.001, A
        BtHomeID_speed = 0x44,            # 0x44, uint16, 0.01
        BtHomeID_temperature_01 = 0x45,   # 0x45, sint16, 0.1
        BtHomeID_UV_index = 0x46,         # 0x46, uint8, 0.1
        BtHomeID_volume16_01 = 0x47,      # 0x47, uint16, 0.1
        BtHomeID_volume16 = 0x48,         # 0x48, uint16, 1
        BtHomeID_Flow_Rate = 0x49,        # 0x49, uint16, 0.001
        BtHomeID_voltage_01 = 0x4a,       # 0x4a, uint16, 0.1
        BtHomeID_gas24 = 0x4b,            # 0x4b, uint24, 0.001
        BtHomeID_gas32 = 0x4c,            # 0x4c, uint32, 0.001
        BtHomeID_energy32 = 0x4d,         # 0x4d, uint32, 0.001
        BtHomeID_volume32 = 0x4e,         # 0x4e, uint32, 0.001
        BtHomeID_water32 = 0x4f,          # 0x4f, uint32, 0.001
        BtHomeID_timestamp = 0x50,        # 0x50, uint48 (4 bytes)
        BtHomeID_acceleration = 0x51,     # 0x51, uint16, 0.001 m/s square
        BtHomeID_gyroscope = 0x52,        # 0x52, uint16, 0.001 C degrees/s
        BtHomeID_text = 0x53,             # 0x53, size uint8, uint8[]
        BtHomeID_raw = 0x54               # 0x54, size uint8, uint8[]
    ),
    "data" / Switch(this.bt_home_v2_type,
        {
            "BtHomeID_PacketId": Struct(
                "packet_id" / Int8ul,  # integer (0..255)
            ),
            "BtHomeID_count8": Struct(
                "counter8" / Int8ul,  # integer (0..255)
            ),
            "BtHomeID_count16": Struct(
                "counter16" / Int16ul,  # integer (0..65535)
            ),
            "BtHomeID_count32": Struct(
                "counter32" / Int32ul,  # integer (0..4294967295)
            ),
            "BtHomeID_voltage": Struct(
                "battery_v" / Int16ul_x1000,
                "battery_v_unit" / Computed("V"),
            ),
            "BtHomeID_voltage_01": Struct(
                "battery_v" / Int16ul_x10,
                "battery_v_unit" / Computed("V"),
            ),
            "BtHomeID_temperature": Struct(
                "temperature" / Int16sl_x100,
                "temperature_unit" / Computed(u'\N{DEGREE SIGN}C'),
            ),
            "BtHomeID_temperature_01": Struct(
                "temperature" / Int16sl_x10,
                "temperature_unit" / Computed(u'\N{DEGREE SIGN}C'),
            ),
            "BtHomeID_humidity": Struct(
                "humidity" / Int16ul_x100,
                "humidity_unit" / Computed("%"),
            ),
            "BtHomeID_pressure": Struct(
                "pressure" / Int24ul_x100,
                "pressure_unit" / Computed("hPa"),
            ),
            "BtHomeID_illuminance": Struct(
                "illuminance" / Int24ul_x100,
                "illuminance_unit" / Computed("lux"),
            ),
            "BtHomeID_weight": Struct(
                "weight" / Int16ul_x100,
                "weight_unit" / Computed("kg"),
            ),
            "BtHomeID_weight_lb": Struct(
                "weight_lb" / Int16ul_x100,
                "weight_lb_unit" / Computed("lb"),
            ),
            "BtHomeID_dewpoint": Struct(
                "dewpoint" / Int16sl_x100,
                "dewpoint_unit" / Computed(u'\N{DEGREE SIGN}C'),
            ),
            "BtHomeID_humidity8": Struct(
                "humidity" / Int8ul,
                "humidity_unit" / Computed("%"),
            ),
            "BtHomeID_battery": Struct(
                "battery_level" / Int8ul,  # 0..100 %
                "battery_level_unit" / Computed("%"),
            ),
            "BtHomeID_energy24": Struct(
                "energy24" / Int24ul_x1000,  # 0..1000 %
                "energy24_unit" / Computed("kWh"),
            ),
            "BtHomeID_energy32": Struct(
                "energy32" / Int32ul_x1000,  # 0..1000 %
                "energy32_unit" / Computed("kWh"),
            ),
            "BtHomeID_power24": Struct(
                "power24" / Int24ul_x100,  # 0..100 %
                "power24_unit" / Computed("W"),
            ),
            "BtHomeID_pm2x5": Struct(
                "pm2x5" / Int16ul,
                "pm2x5_unit" / Computed("ug/m3"),
            ),
            "BtHomeID_pm10": Struct(
                "pm10" / Int16ul,
                "pm10_unit" / Computed("ug/m3"),
            ),
            "BtHomeID_co2": Struct(
                "co2" / Int16ul,
                "co2_unit" / Computed("ppm"),
            ),
            "BtHomeID_tvoc": Struct(
                "tvoc" / Int16ul,
                "tvoc_unit" / Computed("ug/m3"),
            ),
            "BtHomeID_acceleration": Struct(
                "acceleration" / Int16ul_x1000,
                "acceleration_unit" / Computed("m/s\u00b2"),
            ),
            "BtHomeID_current": Struct(
                "current" / Int16ul_x1000,
                "current_unit" / Computed("A"),
            ),
            "BtHomeID_distance_mm": Struct(
                "distance_mm" / Int16ul,
                "distance_mm_unit" / Computed("mm"),
            ),
            "BtHomeID_distance_m": Struct(
                "distance_m" / Int16ul_x10,
                "distance_m_unit" / Computed("m"),
            ),
            "BtHomeID_duration": Struct(
                "duration" / Int24ul_x1000,
                "duration_unit" / Computed("s"),
            ),
            "BtHomeID_gas24": Struct(
                "gas24" / Int24ul_x1000,
                "gas24_unit" / Computed("m3"),
            ),
            "BtHomeID_gas32": Struct(
                "gas32" / Int32ul_x1000,
                "gas32_unit" / Computed("m3"),
            ),
            "BtHomeID_gyroscope": Struct(
                "gyroscope" / Int16ul_x1000,
                "gyroscope_unit" / Computed(u'\N{DEGREE SIGN}/s'),
            ),
            "BtHomeID_moisture16": Struct(
                "moisture16" / Int16ul_x100,
                "moisture16_unit" / Computed("%"),
            ),
            "BtHomeID_moisture8": Struct(
                "moisture8" / Int8ul,
                "moisture8_unit" / Computed("%"),
            ),
            "BtHomeID_raw": Struct(
                "raw" / PascalString(VarInt, "utf8"),
            ),
            "BtHomeID_text": Struct(
                "text" / PascalString(VarInt, "utf8"),
            ),
            "BtHomeID_rotation": Struct(
                "rotation" / Int16sl_x10,
                "rotation_unit" / Computed(u'\N{DEGREE SIGN}'),
            ),
            "BtHomeID_speed": Struct(
                "speed" / Int16ul_x100,
                "speed_unit" / Computed("m/s"),
            ),
            "BtHomeID_timestamp": Struct(
                "date" / Timestamp(Int32ul, 1, 1970),
                "date_is_stored" / IfThenElse(
                    lambda this: this.date.timestamp() > 0,
                    Computed("True"),
                    Computed("False"),
                )
            ),
            "BtHomeID_volume16_01": Struct(
                "volume16_01" / Int16ul_x10,
                "volume16_01_unit" / Computed("l"),
            ),
            "BtHomeID_volume16": Struct(
                "volume16" / Int16ul,
                "volume16_unit" / Computed("ml"),
            ),
            "BtHomeID_volume32": Struct(
                "volume32" / Int32ul_x1000,
                "volume32_unit" / Computed("l"),
            ),
            "BtHomeID_Flow_Rate": Struct(
                "Flow_Rate" / Int16ul_x1000,
                "Flow_Rate_unit" / Computed("m3/hr"),
            ),
            "BtHomeID_UV_index": Struct(
                "UV_index" / Int8ul_x10,
                "UV_index_unit" / Computed("UV Index"),
            ),
            "BtHomeID_water32": Struct(
                "water32" / Int32ul_x1000,
                "water32_unit" / Computed("l"),
            ),
            "BtHomeID_boolean": BitStruct(
                Padding(7),
                "boolean" / Flag,  # boolean
            ),
            "BtHomeID_switch": BitStruct(
                Padding(7),
                "switch" / Flag,  # boolean
            ),
            "BtHomeID_opened": BitStruct(
                Padding(7),
                "opened" / Flag,  # boolean
            ),
            "BtHomeID_low_battery": BitStruct(
                Padding(7),
                "low_battery" / Flag,
            ),
            "BtHomeID_chg_battery": BitStruct(
                Padding(7),
                "charging_battery" / Flag,
            ),
            "BtHomeID_carbon_monoxide": BitStruct(
                Padding(7),
                "carbon_monoxide" / Flag,
            ),
            "BtHomeID_cold": BitStruct(
                Padding(7),
                "cold" / Flag,
            ),
            "BtHomeID_connectivity": BitStruct(
                Padding(7),
                "connectivity" / Flag,
            ),
            "BtHomeID_door": BitStruct(
                Padding(7),
                "door_open" / Flag,
            ),
            "BtHomeID_garage_door": BitStruct(
                Padding(7),
                "garage_door_open" / Flag,
            ),
            "BtHomeID_gas": BitStruct(
                Padding(7),
                "gas_detected" / Flag,
            ),
            "BtHomeID_heat": BitStruct(
                Padding(7),
                "heat_hot" / Flag,
            ),
            "BtHomeID_light": BitStruct(
                Padding(7),
                "light_detected" / Flag,
            ),
            "BtHomeID_lock": BitStruct(
                Padding(7),
                "lock_unlocked" / Flag,
            ),
            "BtHomeID_moisture_b": BitStruct(
                Padding(7),
                "moisture_wet" / Flag,
            ),
            "BtHomeID_motion": BitStruct(
                Padding(7),
                "motion_detected" / Flag,
            ),
            "BtHomeID_moving": BitStruct(
                Padding(7),
                "moving" / Flag,
            ),
            "BtHomeID_occupancy": BitStruct(
                Padding(7),
                "occupancy_detected" / Flag,
            ),
            "BtHomeID_plug": BitStruct(
                Padding(7),
                "plug_plugged" / Flag,
            ),
            "BtHomeID_presence": BitStruct(
                Padding(7),
                "presence" / Flag,
            ),
            "BtHomeID_problem": BitStruct(
                Padding(7),
                "problem" / Flag,
            ),
            "BtHomeID_running": BitStruct(
                Padding(7),
                "running" / Flag,
            ),
            "BtHomeID_safety": BitStruct(
                Padding(7),
                "safe" / Flag,
            ),
            "BtHomeID_smoke": BitStruct(
                Padding(7),
                "smoke_detected" / Flag,
            ),
            "BtHomeID_sound": BitStruct(
                Padding(7),
                "sound_detected" / Flag,
            ),
            "BtHomeID_tamper": BitStruct(
                Padding(7),
                "tamper_on" / Flag,
            ),
            "BtHomeID_vibration": BitStruct(
                Padding(7),
                "vibration_detected" / Flag,
            ),
            "BtHomeID_window": BitStruct(
                Padding(7),
                "window_open" / Flag,
            ),
            "BtHomeID_button": Enum(Int8ul,
                button_no_event = 0,
                button_press = 1,
                button_double_press = 2,
                button_triple_press = 3,
                button_long_press = 4,
                button_long_double_press = 5,
                button_long_triple_press = 6,
            ),
            "BtHomeID_dimmer": Struct(
                "rotation" / Enum(Int8ul,
                    rotate_none = 0,
                    rotate_left = 1,
                    rotate_right = 2,
                ),
                "steps" / Int8ul
            ),
        }
    )
)

bt_home_v2_format = Struct(  # https://bthome.io/format/
    "version" / Computed(1),
    "size" / Int8ul,  # examples: 0B or 0E
    "uid" / Int8ul,  # 0x16
    "UUID" / ByteSwapped(Const(b"\xfc\xd2")),  # BTHomeV2
    "DevInfo" / BitStruct(
        "Version" / BitsInteger(3),  # Version number (currently v2)
        "Reserved2" / BitsInteger(2),
        "Trigger" / Flag,  # 0: advertisements at a regular interval (bit 2 = 0), or when triggered (bit 2 = 1)
        "Reserved1" / BitsInteger(1),
        "Encryption" / Flag,  # non-encrypted data (bit 0 = 0), or encrypted data (bit 0 = 1)
    ),
    "data_point" / Switch(this.DevInfo.Encryption,
        {
            True: BtHomeV2Codec(
                Struct(
                    "count_id" / Int32ul,
                    "payload" / GreedyRange(bt_home_v2_data),
                )
            ),
            False: GreedyRange(bt_home_v2_data)
        }
    )
)

# -------------- general_format ------------------------------------------------
# All format types are embraced

general_format = Struct(
    "version" / Computed(1),
    "custom_enc_format" / GreedyRange(custom_enc_format),
    "custom_format" / GreedyRange(custom_format),
    "atc1441_enc_format" / GreedyRange(atc1441_enc_format),
    "atc1441_format" / GreedyRange(atc1441_format),
    "mi_like_format" / GreedyRange(mi_like_format),
    "bt_home_format" / GreedyRange(bt_home_format),
    "bt_home_enc_format" / GreedyRange(bt_home_enc_format),
    "bt_home_v2_format" / GreedyRange(bt_home_v2_format),
)
