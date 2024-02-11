# freetz-ble
__BLE Advertisement controller for freetz (FRITZ!Box)__

This proof of concept shows a mode to continuously collect BLE advertisements sent by Smart Home wireless consumer sensors via a [FRITZ!Box](https://avm.de/) router modem and store data in clear form to a local DB in the FRITZ!Box. At the moment the code is just an example.

The [BLE](https://wikipedia.org/wiki/Bluetooth_Low_Energy) stack is managed through an [Ai-Thinker TB-03F-KIT](https://docs.ai-thinker.com/_media/tb-03f-kit_specification_en.pdf) adapter module connected via [USB-to-serial interface](https://en.wikipedia.org/wiki/USB-to-serial_adapter).

To configure a FRITZ!Box device in order to run this project, [freetz-ng](https://github.com/Freetz-NG/freetz-ng/) must be installed. [freetz](https://freetz.github.io/wiki/) is a [modified extension](https://de.wikipedia.org/wiki/Fritz!Box#Freetz) of the [AVM](https://en.wikipedia.org/wiki/AVM_GmbH) stock firmware.

While [freetz](https://freetz-ng.github.io/) directly supports Bluetooth 2.0 USB adapters (installing related packages) with BlueZ protocol stack, it cannot manage modern BLE 5.x devices (especially with support of passive scanning and CODED PHY) due to the need of updated Linux kernel >= 5.10 (current FRITZ!Box kernel is 4.9) and updated [BlueZ](https://www.bluez.org/) >= 5.56 (current BlueZ in freetz is the old 2.25).

Using a BLE SoC chip interfaced via a USB-to-serial adapter, like the Ai-Thinker TB-03F-KIT, the Bluetooth stack is completely offloaded, saving kernel and user space resources, other than solving incompatibilities.

The low-cost Ai-Thinker TB-03F-KIT includes a Telink TLSR8253 BLE 5.0 SoC. Main features of the module:

- it completely offloads the BLE stack,
- it offers an easy-to-use USB serial port via CH340 USB-to-serial interface (with driver included in freetz),
- it includes advanced BLE 5 support, comprehensive of passive scanning, Mesh, CODED PHY,
- there are 2 LEDs, a 3-color RGB LED, a reset button and a user-defined button,
- it also provides configurable PWM, I2C, GPIO and ADC interfaces, so that, other than BLE, it can also connect the FRITZ!Box with local sensors (like, e.g., an I2C air quality sensor chip),
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

When the TB-03F-KIT is connected to the FRITZ!Box device, freetz allows accessing it via the serial device driver /dev/ttyUSB0.

## Project software

Included folders in this repository:

- *ble-adv*: Ai-Thinker TB-03F-KIT firmware (including compilation and installation instructions),

- *freetz-ble-python*: test Python code (running with freetz),

- *aes_ccm_codec*: shared library to support AES CCM encryption, which is typically used by consumer BLE devices; this library can be invoked by Python code.

For each software, see instructions README in the related project folder.

## Configuration notes

Suggested `make menuconfig` configuration:

- Packages > Python 2.7.18 > Compress .pyc files; all binary modules (but test)
- Debug helpers > usbutils 007
- Shared libraries > USB&FTDI > libusb-1.0
- Kernel Modules: drivers > ch341.ko and usbserial.ko
- Busybox lsusb

Move Python and all other possible packages to freetz External Processing.
