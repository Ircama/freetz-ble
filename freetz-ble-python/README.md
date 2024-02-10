# freetz-ble-python (test Python code)

Included Python2.7 programs to be run inside freetz (FRITZ!Box):

- `freetz-ble.py`: main program

- `atc_mi_construct.py`: used by *freetz-ble.py* to process BLE advertisements from all supported devices

- `atc_mi_construct_adapters.py`: used by atc_mi_construct.py to provide the needed adapters. It calls *aes_ccm_codec.so*.

## Main process

- Continuously read BLE advertisements from the Ai-Thinker TB-03F-KIT module;
- normalize data;
- decode frames of different types and formats, including decryption;
- extract relevant data and only keep modified values of each measure;
- save data to a local SQLite DB.

## Installation

Use a standard USB SD Card and set freetz to store user data to the USB SD Card.

Python 2.7 shall be installed into a writable storage, like the [freetz external mode](https://freetz.github.io/wiki/help/howtos/common/external.html).

Install PIP for python2.7 (e.g., [get-pip.py](https://bootstrap.pypa.io/pip/2.7/get-pip.py)).

Install all required modules with `--user`.

```
python -m pip install --user --upgrade pip
python -m pip install --user builtins
python -m pip install --user future
python -m pip install --user construct
python -m pip install --user setuptools
python -m pip install --user arrow
python -m pip install --user monotonic
```

Example of installation tree:

- /var/mod/root
  - aes_ccm_codec.so
  - freetz-ble
    - freetz-ble.py
    - atc_mi_construct.py
    - atc_mi_construct_adapters.py

```
cd /var/mod/root
```

Edit `freetz-ble.py` and configure:

- DATA_DIRECTORY
- SQLITE_DATASET
- bindkey
- excluded_mac

The `bindkey` string in `freetz-ble.py` is only tested with Xiaomi Mijia BLE sensors and can be obtained after registering the devices to the Xiaomi portal or via Xiaomi [MiHome mod](https://www.vevs.me/2017/11/mi-home.html). The Bindkey can be downloaded following [3. MiHome mod (Android only)](https://custom-components.github.io/ble_monitor/faq#encryption-keys) and then with the token extractor script ["5. get_beacon_key python script"](https://github.com/PiotrMachowski/Xiaomi-cloud-tokens-extractor). Devices that do not use encrypted protocols, or firmwares like the [pvvx](https://github.com/pvvx/ATC_MiThermometer) one for [LYWSD03MMC](https://esphome.io/components/sensor/xiaomi_ble.html#lywsd03mmc) one, do not need the bindkey.

## Usage

The Ai-Thinker TB-03F-KIT adapter shall have the appropriate firmware installed. Test it with the upload desktop application. Connect the adapter to the FRITZ!Box.

Check that the BLE USB adapter is visible (here in the example it is the one with Driver=ch341; the other is the Mass Storage):

```
# lsusb-freetz -t
/:  Bus 04.Port 1: Dev 1, Class=root_hub, Driver=xhci-hcd/1p, 5000M
/:  Bus 03.Port 1: Dev 1, Class=root_hub, Driver=xhci-hcd/1p, 480M
    |__ Port 1: Dev 6, If 0, Class=Vendor Specific Class, Driver=ch341, 12M
/:  Bus 02.Port 1: Dev 1, Class=root_hub, Driver=xhci-hcd/1p, 5000M
/:  Bus 01.Port 1: Dev 1, Class=root_hub, Driver=xhci-hcd/1p, 480M
    |__ Port 1: Dev 2, If 0, Class=Mass Storage, Driver=usb-storage, 480M
```

To activate the continuous advertising log in the TB-03F-KIT adapter, set `AT+MODE=1` (Master) and `AT+SCAN=3` or `AT+SCAN=2`.

This can be done once via:

```
python freetz-ble.py -a 9  # AT+MODE=1
python freetz-ble.py -a 3  # AT+SCAN=3, or '-a 2' for AT+SCAN=2
```

To create the SQLite DB (once):

```
python freetz-ble.py -cir
```

Each time, to test the connection:

```
python freetz-ble.py -dr
```

Run `python freetz-ble.py --help` for all options.

Run with:

```
nohup python freetz-ble.py &
```

## Command-line arguments

```
freetz-ble.py [-h] [-d] [-i] [-r] [-c] [-a ADV_LEVEL]

optional arguments:
  -h, --help            show this help message and exit
  -d, --debug           Print debug information
  -i, --info            Print limited debug information
  -r, --dry-run         Dry-run DB save
  -c, --create          Drop the DB and recreate it
  -a ADV_LEVEL, --adv-level ADV_LEVEL
                        BLE Driver advertisement level

BLE Advertisement Sensor Processor
```

## Notes

This example code shows how to connect the TB-03F-KIT adapter via USB:

```python
import serial
import time
ser = serial.serial_for_url("/dev/ttyUSB0", 115200)

# Reset module (RTS low)...
time.sleep(0.05)
ser.setDTR(True)
ser.setRTS(True)
time.sleep(0.05)
ser.setDTR(False)
ser.setRTS(False)

while True:
    data = ser.readline().rstrip('\n')
    print(data)
```

`atc_mi_construct.py` is a simplified back-porting of [atc_mi_interface](https://github.com/pvvx/ATC_MiThermometer/tree/master/python-interface) to support Python2.7. It preserves the symmetric data structure and the original support of devices.
