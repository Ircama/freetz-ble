# freetz-ble
__BLE Advertisement controller for freetz (FRITZ!Box)__

This proof of concept shows a mode to continuously collect BLE advertisements sent by Smart Home wireless sensors via a [FRITZ!Box](https://avm.de/) router modem and store data in clear form to a local DB in the FRITZ!Box.

[BLE](https://wikipedia.org/wiki/Bluetooth_Low_Energy) Advertisements are managed through an [Ai-Thinker TB-03F-KIT](https://docs.ai-thinker.com/_media/tb-03f-kit_specification_en.pdf) adapter module connected via USB.

To configure a FRITZ!Box device in order to run this project, [freetz-ng](https://github.com/Freetz-NG/freetz-ng/) must be installed ([freetz](https://freetz.github.io/wiki/) is a [modified extension](https://de.wikipedia.org/wiki/Fritz!Box#Freetz) of the AVM stock firmware).

While [freetz](https://freetz-ng.github.io/) directly supports Bluetooth 2.0 USB adapters, it cannot manage modern BLE 5.x devices (especially with support of passive scanning and CODED PHY) due to the need of updated Linux kernel >= 5.10 (current FRITZ!Box kernel is 4.9) and updated BlueZ >= 5.56 (current Bluez in freetz is 2.25).

Using a BLE SoC chip interfaced via USB serial, like the Ai-Thinker TB-03F-KIT, the Bluetooth stack is completely offloaded, saving kernel and user space resources, other than solving incompatibilities.

The low-cost Ai-Thinker TB-03F-KIT includes a Telink TLSR8253 BLE 5.0 SoC. Main features of the module:

- it completely offloads the BLE stack,
- it offers an easy-to-use USB serial port via CH340 USB-to-serial interface (with driver included in freetz),
- advanced BLE 5 support, including passive scanning, Mesh, CODED PHY,
- 2 LEDs and a 3-color RGB LED,
- configurable PWM, I2C, GPIO and ADC interfaces,
- reset button and user-defined button,
- it allows to distance the BLE antenna from the FRITZ!Box, for reduced interferences.

This project includes a Python module with symmetric parsing and building support of a wide set of BLE modules:

- potentially all [Xiaomi Mijia BLE sensors](https://esphome.io/components/sensor/xiaomi_ble.html),
- all [BT Home DIY sensors](https://bthome.io/) implementing BTHome v1 and v2 protocols,
- Xiaomi Mijia Thermometers with custom firmware (ATC_MiThermometer) developed by [atc1441](https://github.com/atc1441/ATC_MiThermometer) and [pvvx](https://github.com/pvvx/ATC_MiThermometer).

Specifically, the following BLE home sensors have been tested:

- SJWS01LM (Xiaomi Mijia Flood Detector)
- MCCGQ02HL (Xiaomi Mijia Door and Window Sensor 2)
- LYWSD03MMC (Xiaomi Mijia Temperature And Humidity Monitor)

Tested AVM device: FRITZ!Box 7590 AX.

When the TB-03F-KIT connects to the FRITZ!Box device, freetz allows accessing it via /dev/ttyUSB0 (TB-03F-KIT includes a CH340 USB-to-serial interface).

`make menuconfig` configuration:

- Packages -> Python 2.7.18 -> Compress .pyc files; all binary modules (but test)
- Debug helpers -> usbutils 007
- Shared libraries -> USB&FTDI -> libusb-1.0
- Kernel Modules: drivers -> ch341.ko and usbserial.ko
- Busybox lsusb

Move Python and all other possible packages to freetz External Processing.

Included folders in this repository:

- *ble-adv*: Ai-Thinker TB-03F-KIT firmware (including compilation and installation instructions)

- *aes_ccm_codec*: shared library to support AEM CCM encryption, in use by BLE devices

- *freetz-ble-python*: Test Python code. See instructions in the related project folder.
