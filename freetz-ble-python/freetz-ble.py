import serial
import time
import codecs
import binascii
import sqlite3
import logging
import os.path
import argparse
from datetime import datetime, date, timedelta
from atc_mi_construct import general_format
import monotonic

# Use UTF-8 with Python2
import sys
reload(sys)
sys.setdefaultencoding('UTF8')

########## START CONFIGURATION #####################
DATA_DIRECTORY = "/var/mod/root/freetz-ble/"
SQLITE_DATASET = DATA_DIRECTORY + 'sensorsData.db'

bindkey = {
    "A4C138AABBCC": codecs.decode("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "hex"),
    "A4C138AABBDD": codecs.decode("bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", "hex"),
    # ...
}

excluded_mac = [
]
########## END CONFIGURATION #######################


def create_db(drop=True):
    if not db:
        logging.error("Internal error: db not valued")
        return

    with db:
        try:
            cur = db.cursor()
            if drop:
                cur.executescript("""
                    DROP TABLE IF EXISTS sensor_data;
                    DROP TABLE IF EXISTS flooding_list;
                    DROP TABLE IF EXISTS door_list;
                    DROP TABLE IF EXISTS light_list;
                    """
                                  )
            cur.executescript("""
                    CREATE TABLE IF NOT EXISTS sensor_data (
                        timestamp DATETIME,
                        humidity NUMERIC,
                        temperature NUMERIC,
                        battery_level NUMERIC);
                    CREATE INDEX i_sd_ts ON sensor_data(timestamp);
                    CREATE TABLE IF NOT EXISTS flooding_list (
                        timestamp DATETIME,
                        state INTEGER);
                    CREATE TABLE IF NOT EXISTS door_list (
                        timestamp DATETIME,
                        state INTEGER);
                    CREATE TABLE IF NOT EXISTS light_list (
                        timestamp DATETIME,
                        state INTEGER);
            """)
            db.commit()
        except Exception as e:
            logging.error("Failed to create DB: %s", e)


############################ MAIN ################################

parser = argparse.ArgumentParser(
    epilog='BLE Advertisement Sensor Processor'
)
parser.add_argument(
    '-d',
    '--debug',
    dest='debug',
    action='store_true',
    help='Print debug information'
)
parser.add_argument(
    '-i',
    '--info',
    dest='info',
    action='store_true',
    help='Print limited debug information'
)
parser.add_argument(
    '-r',
    '--dry-run',
    dest='dry_run',
    action='store_true',
    help='Dry-run DB save'
)
parser.add_argument(
    '-c',
    '--create',
    dest='create',
    action='store_true',
    help='Drop the DB and recreate it'
)
parser.add_argument(
    '-a',
    '--adv-level',
    dest='adv_level',
    type=int,
    default=None,
    action="store",
    help='BLE Driver advertisement level'
)

args = parser.parse_args()

logging_fmt = "%(asctime)s %(message)s"
if args.info or args.debug:
    logging_fmt = "%(message)s"
logging_level = logging.WARNING
logging.basicConfig(level=logging_level, format=logging_fmt)

if args.info:
    logging.getLogger().setLevel(logging.INFO)
if args.debug:
    logging.getLogger().setLevel(logging.DEBUG)

mtime = monotonic.time.time  # now mtime() can be used in place of time.time()
t0 = mtime()
last_numerical_save = 0

if args.create:
    logging.warning("Dropping the DB and recreating it")
    create_db(drop=True)

if not os.path.isfile(SQLITE_DATASET):
    create_db(drop=False)
db = sqlite3.connect(SQLITE_DATASET)

ser = serial.serial_for_url("/dev/ttyUSB0", 115200)

# Reset module (RTS low)
time.sleep(0.05)
ser.setDTR(True)
ser.setRTS(True)
time.sleep(0.05)
ser.setDTR(False)
ser.setRTS(False)

ser.flushInput()  #flush input buffer, discarding all its contents
ser.flushOutput()  #flush output buffer, aborting current output and discard all that is in buffer

if args.adv_level != None:
    logging.warning("Adapter configuration")
    time.sleep(1)

    data = ""
    ser.write("AT+NAME?" + "\r\n")
    while "OK" not in data:
        data = ser.readline().rstrip('\n')
        print(data)

    data = ""
    ser.write("AT+MAC?" + "\r\n")
    while "OK" not in data:
        data = ser.readline().rstrip('\n')
        print(data)

    data = ""
    ser.write("AT+MODE?" + "\r\n")
    while "OK" not in data:
        data = ser.readline().rstrip('\n')
        print(data)

    if args.adv_level == 9:  # Set AT+MODE=1
        data = ""
        ser.write("AT+MODE=1" + "\r\n")
        while "OK" not in data:
            data = ser.readline().rstrip('\n')
            print(data)
        data = ""
        ser.write("AT+MODE?" + "\r\n")
        while "OK" not in data:
            data = ser.readline().rstrip('\n')
            print(data)
        quit()

    if args.adv_level >= 0 and args.adv_level <= 3:  # Set AT+SCAN=0..3
        command = "AT+SCAN=" + str(args.adv_level) + "\r\n"
        logging.warning("Sending command '%s'", command.strip())
        time.sleep(1)
        ser.write(command)

    data = ""
    while "OK" not in data:
        data = ser.readline().rstrip('\n')
        print(data)
    quit()

is_ready = False

latest_frames = {}
latest_values = {}

logging.warning("Starting BLE Advertisement Sensor Processor")

while True:
    data = ser.readline().rstrip()
    if data == '+READY':
        is_ready = True
    if not is_ready:
        continue
    if not data.startswith('+ADV:'):
        continue
    record = data[5:].split(',')
    mac = record[1]
    if record[2].startswith('020106'):
        frame = record[2][6:]
    else:
        frame = record

    logging.debug("rssi: %s", record[0])
    logging.debug("MAC: %s", mac)
    logging.debug("data: %s", record[2])
    logging.debug("frame: %s", frame)

    if mac in excluded_mac:
        continue

    # Remove duplicated frames
    if frame == latest_frames.get(mac):
        continue
    latest_frames[mac] = frame

    atc_mi_data = general_format.parse(
        codecs.decode(frame, "hex"),
        mac_address=codecs.decode(mac, "hex"),
        bindkey=bindkey[mac] if mac in bindkey else None
    )

    logging.debug("atc_mi_data: %s", atc_mi_data)

    logging.info("temperature: %s", atc_mi_data.search_all("^temperature"))
    logging.info("humidity: %s", atc_mi_data.search_all("^humidity"))
    logging.info("battery_level: %s", atc_mi_data.search_all("^battery_level"))
    logging.info("battery_v: %s", atc_mi_data.search_all("^battery_v"))
    logging.info("flooding: %s", atc_mi_data.search_all("^flooding$"))
    logging.info("door: %s", atc_mi_data.search_all("^door$"))
    logging.info("light: %s", atc_mi_data.search_all("^light"))

    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    # Save state events to DB
    light_v = None
    light = atc_mi_data.search_all("^light")
    if light:
        light_v = light[0]

    door_v = None
    door = atc_mi_data.search_all("^door$")
    if door and str(door[0]) == 'XIAOMI_door_open':
        door_v = True
    if door and str(door[0]) == 'XIAOMI_door_closed':
        door_v = False

    flooding_v = None
    flooding = atc_mi_data.search_all("^flooding$")
    if flooding:
        flooding_v = flooding[0]

    history_list = None
    if light_v == True or light_v == False:
        state = light_v
        history_list = "light_list"
    if door_v == True or door_v == False:
        state = door_v
        history_list = "door_list"
    if flooding_v == True or flooding_v == False:
        state = flooding_v
        history_list = "flooding_list"
    if history_list:
        if args.dry_run:
            logging.warning(
                "Dry-run insert state '%s' to table %s", state, history_list
            )
        else:
            cur = db.cursor()
            cur.execute(
                "INSERT INTO " + history_list +
                " (timestamp, state) VALUES(?,?)",
                (timestamp, state)
            )
            logging.debug("Insert state '%s' to table %s", state, history_list)
        db.commit()

    # Process numerical values only after 60 seconds from the last DB save
    if (
        not args.debug and not args.info and mtime() - last_numerical_save < 60
    ):
        continue

    # Extract numerical vlues
    temperature_v = None
    temperature = atc_mi_data.search_all("^temperature")
    if temperature:
        temperature_v = temperature[0]

    humidity_v = None
    humidity = atc_mi_data.search_all("^humidity")
    if humidity:
        humidity_v = humidity[0]

    battery_level_v = None
    battery_level = atc_mi_data.search_all("^battery_level")
    if battery_level:
        battery_level_v = battery_level[0]

    # Remove duplicates on numerical values
    if (
        temperature_v is None or
        temperature_v == latest_values.get("temperature")
    ):
        temperature_v = None
    else:
        latest_values["temperature"] = temperature_v
    if (
        humidity_v is None or
        humidity_v == latest_values.get("humidity")
    ):
        humidity_v = None
    else:
        latest_values["humidity"] = humidity_v
    if (
        battery_level_v is None or
        battery_level_v == latest_values.get("battery_level")
    ):
        battery_level_v = None
    else:
        latest_values["battery_level"] = battery_level_v

    # Save numerical vlues to DB
    if humidity_v or temperature_v or battery_level_v:
        if args.dry_run:
            logging.warning("Dry-run Insert values to table sensor_data")
        else:
            cur = db.cursor()
            cur.execute(
                "INSERT INTO sensor_data ("
                "timestamp, humidity, temperature, battery_level)"
                " VALUES(?,?,?,?)",
                (
                    timestamp,
                    humidity_v,
                    temperature_v,
                    battery_level_v
                )
            )
            db.commit()
            logging.debug("Insert values to table sensor_data")
        last_numerical_save = mtime()
