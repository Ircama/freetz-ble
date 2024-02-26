<!--
 * @Author: ircama
 * @Date: 2020-03-31 19:46:54
 * @LastEditTime: 2024-02-10 16:53:37
 * @LastEditors: Please set LastEditors
 * @Description: In User Settings Edit
 * @FilePath: ble-adv-telink/README.md
 -->
# Ble-Adv-Telink Project

This code is based on [Telink_825X_SDK](https://github.com/Ai-Thinker-Open/Telink_825X_SDK) and is tested on a [Ai-Thinker TB-03F-KIT](https://docs.ai-thinker.com/_media/tb-03f-kit_specification_en.pdf).

It reuses the [AT example](https://github.com/Ai-Thinker-Open/Telink_825X_SDK/tree/master/example/at) included in the SDK, modifying it in order to appropriately process BLE advertisements for a FRITZ!Box device.

[TLSR8253 chip](http://wiki.telink-semi.cn/doc/ds/DS_TLSR8253-E_Datasheet%20for%20Telink%20BLE+IEEE802.15.4%20Multi-Standard%20Wireless%20SoC%20TLSR8253.pdf) documentation: http://wiki.telink-semi.cn/wiki/chip-series/TLSR825x-Series/

The code offers USB serial UART interface at 115200 bps, N, 8, 1 and uses DTR and RTS. To reset the device and start serial communication:

- open the serial port,
- set DTR on,
- set RTS on,
- wait 50 millisecs,
- set DTR off,
- set RTS off.

Changes vs. the original firmware:

- added `AT+SCAN` setting modes, including continuous advertising in passive mode, which can also be activated at boot
- advertising duplicates are not disabled
- using the colored LED to show the device brand of each received advertising
- added filter advertising on specific three brands
- added GPIO, PWM and other features.

To enable scanning and to set `AT+SCAN=<value>`, the device shall be in host/master mode (`AT+MODE=1`):

Setting|Device mode
---|---
`AT+MODE=0`|Slave
`AT+MODE=1`|Master
`AT+MODE=2`|iBeacon

The following SCAN modes are allowed:

|AT setting code|Return code|Note|
|---|---|---|
|`AT+SCAN`|Output depends on the SCAN mode|Start SCAN without modifying the SCAN mode|On-demand mode
|`AT+SCAN=0`|`+SCAN_TYPE:0`|Start SCAN and automatically disable it after 3 seconds (default)| On-demand mode
|`AT+SCAN=1`|`+SCAN_TYPE:1`, `+SCAN_SET_CONTINUOUS`|Start SCAN with no timeout|On-demand mode. If the device is rebooted, the scan does not automatically start.
|`AT+SCAN=2`|`+SCAN_TYPE:2`, `+SCAN_SET_AUTO`|Autonomous mode. The SCAN is automatically started at boot, with no need to issue an `AT+SCAN` command each time the device is booted. To stop this mode, use `AT+SCAN=0`
|`AT+SCAN=3`|`+SCAN_TYPE:3`, `+SCAN_SET_AUTO_FILTER`|Same as `AT+SCAN=2`, but the scan filters only the OUIs in the following table

Recognized OUIs in `AT+SCAN=3` mode:

MAC OUI|Brand name|GPIO|LED
--------|---|---|---
A4:C1:38|Telink Semiconductor (Taipei) Co. Ltd|PC2 on, PC3 off, PC4 off|RBG Blue on, all others off
54:EF:44|Lumi United Technology Co., Ltd|PC2 off, PC3 on, PC4 off|RBG Red on, all others off
E4:AA:EC|Tianjin Hualai Tech Co, Ltd|PC2 off, PC3 off, PC4 on|RBG Green on, all others off
Any other MAC|filtered out|PC2 off, PC3 off, PC4 off|All RBG LEDs off

`AT+SCAN=3` reduces the amount of data sent to the host by only filtering BLE advertising in scope based on the OUI. The OUI (Organizationally Unique Identifier) takes the first 3 octets of the MAC and consists of a 24-bit number that uniquely identifies a vendor or manufacturer. At the moment, the filtering is in the code and cannot be customized via AT commands. The filtered vendors shall refer to the related BLE sensors in scope. Change the code *app_master.c* to edit the OUIs and control related LED colors.

All settings (e.g., `AT+MODE=<n>` and `AT+SCAN=<n>`) are permanently stored in the non-volatile RAM of the device.

## Compiling and installing

- Copy the folder on a Linux system (Ubuntu). [WSL](https://en.wikipedia.org/wiki/Windows_Subsystem_for_Linux) is supported.
- `cd ble-adv-telink`
- `make`

Switches can be passed with CFLAGS; e.g., `make CFLAGS="-D... -D..."`.

The produced firmware is `src/out/ble-adv-telink.bin`.

To burn the firmware with a PC, connect the device via USB and use either the *Telink_Tools.py* Python program (Python2 and Python3, Windows and Linux), or the [Ai-Thinker_TB_Tools_V1.5.0.exe](https://ai-thinker.oss-cn-shenzhen.aliyuncs.com/TB_Tool/Ai-Thinker_TB_Tools_V1.5.0.exe) Window software. Check also the [related repository](https://github.com/Ai-Thinker-Open/TBXX_Flash_Tool/tree/1.x.x).

The *Telink_Tools.py* Python program requires `pip install pyserial`.

Burning via Python program with Windows (in this example the Ai-Thinker device is connected via USB to the virtual COM8 serial port of a PC):

```
python3 make\Telink_Tools.py --port com8 burn src\out\ble-adv-telink.bin
```

With WSL (Ubuntu), install [USBIPD-WIN](https://learn.microsoft.com/windows/wsl/connect-usb#install-the-usbipd-win-project), then connect the USB device, run a CMD in Administration mode and issue:

```cmd
usbipd list
usbipd bind -b 1-5
usbipd attach --wsl --busid 1-5
```

Notes: use the BUSID returned by `usbipd list`. Ignore the warning. Use *usbipd attach* each time the USB device is reconnected.

Then, with WSL:

```bash
lsusb -tv
python3 ../make/Telink_Tools.py --port /dev/ttyUSB0 burn out/ble-adv-telink.bin
```

The *Telink_Tools.py* program will NOT work on freetz (the freetz device driver does not support sending ascii 0 characters).

To flash the firmware with *Ai-Thinker_TB_Tools_V1.5.0.exe*:

- First tab
- Select the appropriate COM port
- Press the button with "..." and select the firmware
- Press the right side button to the previously mentioned one "..."

*Ai-Thinker_TB_Tools_V1.5.0.exe* can be used to test the AT commands. To enter an AT command, use the second tab. Select the port and bitrate, press the second button to connect the device, verify that the checkbox is selected.

## Test program

```python
import serial
import time
import sys

ser = serial.serial_for_url(sys.argv[1], 115200)

# Reset module
time.sleep(0.05)
ser.setDTR(True)
ser.setRTS(True)
time.sleep(0.05)
ser.setDTR(False)
ser.setRTS(False)

while True:
    data = ser.readline().decode().rstrip('\n')
    print(data)
```

## Return message formats

### Boot return message

```
IRCAMA Ai-Thinker BLE AT V1.0.1
+READY
```

### Confirmation message

Confirmation of command receipt:

```
OK
```

### +NAME

Example of return message of `AT+NAME?`:

```
+NAME:Ai-Thinker
```

### +MAC

Example of return message of `AT+MAC?` (Telink Semiconductor MAC):

```
+MAC:A4C138AABBCC
```

### +MODE

Example of return message of `AT+MODE?`:

```
+MODE:1
```

### Scan modes

Output of `AT+SCAN=1`:

```
+SCAN_SET_CONTINUOUS:1
```

Output of `AT+SCAN=2`:

```
+SCAN_SET_AUTO:2
```

Output of `AT+SCAN=3`:

```
+SCAN_SET_AUTO_FILTER:3
```

Output of the start of the advertising scan (`<n>` is the scan mode):

```
+SCAN_TYPE:<n>
```

Output of the start of the automatic advertising scan at boot (`<n>` is the scan mode):

```
+SCAN_TYPE_INIT:<n>
```

### +ADV

Advertising data

```
+ADV:<RSSI>,<MAC>,<ADV>
```

- `<RSSI>`: [RSSI](https://en.wikipedia.org/wiki/Received_signal_strength_indicator)
- `<MAC>`: BLE MAC Address (12 hex characters without ':')
- `<ADV>`: Advertisement data frame

A BLE data fame is decoded as follows:

- 1st byte = length (n bytes)
- 2nd byte = Types
- n-1 bytes = actual data

And this repeats over the whole raw data. You can find the meaning of raw data in the [2.3 "Common Data Types" paragraph](https://www.bluetooth.com/wp-content/uploads/Files/Specification/Assigned_Numbers.html#bookmark43) of the Assigned Numbers Bluetooth Document.

- Example: `020106110677AE8C12719E7BB6E6113A2110E1412107084461696B696E`:

  1st Set:

  - 02: Length: 2 Bytes
  - 01: Type: Flags
  - 06: Flag - 02 && 04: LE General Discoverable Mode, BR/EDR Not Supported. This means that the module producing the advertisement is configured as broadcaster, without connection/pairing

  2nd Set:

  - 11: Length: 17 bytes
  - 06: Type: Incomplete List of 128-bit Service Class UUIDs
  - 110677AE8C12719E7BB6E6113A2110E14121: characteristic 2141e110-213a-11e6-b67b-9e71128cae77 (AC Unit Management)

  3rd Set:

  - 07: Length: 9 bytes
  - 08: Type: Shortened Local Name
  - 4461696B696E: Daikin (Name of device in ASCII)

- Example: `0201061416D2FC4195B0EFDA789DD953B02600009341626F`:

  1st Set:

  - 02: Length: 2 Bytes
  - 01: Type: Flags
  - 06: Flag - 02 && 04: LE General Discoverable Mode, BR/EDR Not Supported. This means that the module producing the advertisement is configured as broadcaster, without connection/pairing

  2nd Set:

  - 14: Length: 20 bytes
  - 16: Type: Service Data - 16-bit UUID
  - FCB2: UUID
  - 4195b0efda789dd953b02600009341626f: BT Home v2 format data

  ```
    size = 20
    uid = 22
    UUID = b"\xfc\xd2" (total 2)
    DevInfo = Container:
        Version = 2
        Reserved2 = 0
        Trigger = False
        Reserved1 = 0
        Encryption = True
    data_point = Container:
        count_id = 9904
        payload = ListContainer:
            Container:
                bt_home_v2_type = (enum) BtHomeID_battery 1
                data = Container:
                    battery_level = 80
                    battery_level_unit = u"%" (total 1)
            Container:
                bt_home_v2_type = (enum) BtHomeID_temperature 2
                data = Container:
                    temperature = 19.2
                    temperature_unit = u"°C" (total 2)
            Container:
                bt_home_v2_type = (enum) BtHomeID_humidity 3
                data = Container:
                    humidity = 62.22
                    humidity_unit = u"%" (total 1)
  ```

Example of output with `AT+SCAN=2`:

```
IRCAMA Ai-Thinker BLE AT V1.0.1
+READY

+SCAN_TYPE_INIT:2
+ADV:-97,30F94BA4F247,020106110677AE8C12719E7BB6E6113A2110E1412107084461696B696E
+ADV:-90,30F94BA51C5D,020106110677AE8C12719E7BB6E6113A2110E1412107084461696B696E
+ADV:-93,30F94BA4A1A0,020106110677AE8C12719E7BB6E6113A2110E1412107084461696B696E
+ADV:-99,30F94BA521D2,020106110677AE8C12719E7BB6E6113A2110E1412107084461696B696E
+ADV:-94,30F94BA524DE,020106110677AE8C12719E7BB6E6113A2110E1412107084461696B696E
+ADV:-94,A4C138AABBCC,0201061416D2FC4195B0EFDA789DD953B02600009341626F
...
```

--------------

Note: Coded PHY not working at the moment.

The SDK in this repo is borrowed from https://github.com/pvvx/ATC_MiThermometer and https://github.com/atc1441/ATC_MiThermometer that possibly in turn reused the [Telink_825X_SDK](https://github.com/Ai-Thinker-Open/Telink_825X_SDK) (which might be based on Telink SDK 3.1 or 3.2).

SDK documentation: https://shyboy.oss-cn-shenzhen.aliyuncs.com/readonly/tb/Telink%20Kite%20BLE%20SDK%20Developer%20Handbook.pdf

-----------------------------------------

Note: comments come from the original code (AT version 0.7.4), English translation from Chinese.

## AT mode selection and conversion

If the control is not processed (left floating) and the module is not connected to the mobile phone, it will be in AT mode and can respond to AT commands. After the module is connected to the mobile phone, it enters the transparent transmission mode. In the transparent transmission mode, the data sent by the MCU to the module through the serial port will be forwarded intact to the mobile phone via Bluetooth by the module. Similarly, the data sent by the mobile phone to the module through Bluetooth will be transmitted intact to the MCU through the serial port.


|   Module|Serial port TX|Serial port RX|Control pin|Low power consumption status indication pin|Connection status indication pin|
|---------|--------------|--------------|-----------|-------------------------------------------|--------------------------------|
|TB-01    |PB1           |PB0           |PC5        |None                                       |None                            |
|TB-02+   |PB1           |PA0           |PC5        |PC3, RBG Red                               |PC4, RBG Green                  |
|TB-02_Kit|PB1           |PB7           |PC5        |PC3, RBG Red                               |PC4, RBG Green                  |

When the module is not connected to the mobile phone, it will be in AT mode and can respond to AT commands. After connecting with the mobile phone, it will enter the transparent transmission mode and no longer respond to AT commands. If the user needs to send AT commands in transparent transmission mode, the control pin can be pulled low. After pulling low, the module will temporarily enter AT mode, and return to transparent transmission mode after releasing it. The status corresponds to the following table:

||No connection established with mobile phone|Connection established with mobile phone
|---|---|---|
|CONTROL_GPIO is high level|AT mode|Transparent transmission mode
|CONTROL_GPIO is low |AT mode |AT mode
||STATE pin is low|STATE pin is high|

Note: If the user does not need to use transparent transmission mode, just pull down CONTROL_GPIO through a resistor. In AT mode, data can be sent through the AT+SEND command.

## Modify control and indication pins

The above `control pin` `low power status indication pin` `connection status indication pin` is defined in the `app_config.h` file, if necessary Can be modified by yourself.

## Serial port adaptation

The serial port configuration part is in the `app_uart.c` file. The default TX is PB1, and the RX pin adopts an adaptive method. The level status of PA0, PB0, and PB7 is detected after power-on. If one is high level , then set it as serial port Rx.


## AT command format
AT commands can be subdivided into four format types:

|Type|Command format|Description|Remarks
|---|---------|---|---|
|Query command|AT+?|Query the current value in the command.	
|Setting command|AT+
    =<…>|Set user-defined parameter values.	
|Execute command|AT+
     |Perform some function with immutable parameters.	
|Test command|AT+
      =?|Return command help information	


## AT command set

|Serial number|Command|Function|Remarks|
|----|-----|----|----|
|1|AT|Test AT|
|2|ATE|Switch echo|
|3|AT+GMR|Query firmware version|Use AT+GMR to qyery, not AT+GMR?
|4|AT+RST|Restart module
|5|AT+SLEEP|Deep sleep|
|6|AT+RESTORE|Restore factory settings|Will restart after recovery|
|7|AT+BAUD|Query or set the baud rate|It will take effect after restart|
|8|AT+NAME|Query or set the Bluetooth broadcast name|It will take effect after restart|
|9|AT+MAC|Set or query the module MAC address|It will take effect after restart|
|10|AT+MODE|Query or master-slave mode
|11|AT+STATE|Query Bluetooth connection status
|12|AT+SCAN|Initiate scan in host mode
|13|AT+CONNECT|Initiate connection in host mode
|14|AT+DISCON|Disconnect
|15|AT+SEND|Send data in AT mode|
|16|+DATA|Data received in AT mode|
|17|AT+ADVDATA|Set the manufacturer-defined field content in the broadcast data|
|18|AT+LSLEEP|Set or enter light sleep|
|19|AT+RFPWR|Set or read transmit power|
|20|AT+IBCNUUID|Set or read iBeacon UUID|
|21|AT+MAJOR|Set or read iBeacon Major|
|22|AT+MINOR|Set or read iBeacon Minor|
|23|AT+BTEST|Enter board test loop of all 5 LEDs|Terminate the board test loop with a reset
|24|AT+GPIO?|Read all GPIO ports|Do not change any setting. Return a full list of +GPIO=Pxx:n, then OK
|25|AT+GPIO=Pxx?|Set port as GPIO. Set GPIO as INPUT. Read GPIO port Pxx|Return +GPIO=Pxx:n, then OK
|26|AT+GPIO=Pxx:n|Set port as GPIO. Set GPIO as OUTPUT. Write n GPIO port Pxx|n can be 0 or 1. Return +GPIO=Pxx:n, then OK
|27|AT+GPIO=Pxx^n|Set up/down resistor for a GPIO|n can be 0, 1, 2 or 3. Return +GPIO=Pxx^n, then OK
|28|TESTCHR?|Test characters|
|29|TESTCHR=<characters>|Test characters|
|30|AT+PWM?|stop PWM0|+PWM_STOP:PWM0
|31|AT+PWM=PWMy?|stop PWMy|Example: AT+PWM=PWM5?
|32|AT+PWM=PWMy,Pxx,d,c|start 'PWMy' with port 'Pxx', 'd' duty cycle and 'c' CMP|Example: AT+PWM=PWM5,PB5,1000,500

Pxx can be PA1..8, PB0..7, PC0..7, PD0..7, PE0..3
PWMy can be PWM0..5, PWM0_N..PWM5_N

LED|Color
---|-----
PC2|RBG Blue
PC3|RBG Red
PC4|RBG Green
PB4|Lateral small Yellow
PB5|Lateral While

## Host mode
In master mode, the module can communicate with another slave module. The main operations are as follows:

Configure the module into host (master) mode:

	AT+MODE=1

Scan surrounding modules:

	AT+SCAN

Connect the modules specified by the guide:

	AT+CONNECT=AC04187852AD

Please replace the above MAC address with the MAC address of your slave module.

Returning `OK` means the connection is successful. Use the following command to send data to the slave:

	AT+SEND=5,12345

Note: There is only AT command mode in the host state, and there is no transparent transmission mode.

## Low power consumption
The AT firmware supports two sleep modes, namely `deep sleep` and `light sleep`. In deep sleep mode, except for the GPIO wake-up function, all other functions of the module are turned off, and the power consumption is 1uA. one time. In addition to retaining GPIO wake-up, the light sleep mode also maintains the Bluetooth function. The power consumption is determined by the broadcast parameters, with an average of less than 10uA.

Enter deep sleep mode:

	AT+SLEEP

After executing the AT+SLEEP instruction and returning OK, the module will immediately enter sleep mode and set the serial port RX as the wake-up pin. Send any character to the module again to wake it up.

Light sleep settings:
In the disconnected state, send the following command and the module will enter light sleep mode:

	AT+LSLEEP

In light sleep mode, the module will still perform Bluetooth broadcast. Light sleep mode no longer responds to any AT commands, and any data can be sent through the serial port RX pin to wake up the module.

When another Bluetooth device is successfully connected to the module, the module will also be woken up.

Automatically enter light sleep mode after power on:

	AT+LSLEEP=1

It does not automatically enter light sleep mode after powering on;

	AT+LSLEEP=0

Note: Light sleep mode only works in the slave state. If low power consumption is used, it is not recommended to set the baud rate below 115200. If the baud rate is too low, sending data through the serial port will take up a lot of time, thus affecting power consumption.

## iBeacon Mode
iBeacon is a special set of broadcast formats defined by Apple, mainly used for indoor positioning.
This iBeacon broadcast packet is 30 bytes in total, and the data format is as follows:

	02 # The number of bytes of the first AD structure (the number of next bytes, here is 2 bytes)
	01 # Flag of AD type
	1A # Flag value 0x1A = 000011010  
	bit 0 (OFF) LE Limited Discoverable Mode
	bit 1 (ON) LE General Discoverable Mode
	bit 2 (OFF) BR/EDR Not Supported
	bit 3 (ON) Simultaneous LE and BR/EDR to Same Device Capable (controller)
	bit 4 (ON) Simultaneous LE and BR/EDR to Same Device Capable (Host)
	1A # The number of bytes of the second AD structure (the next number of bytes, here is 26)
	FF # AD type flag, here is Manufacturer specific data. More flags can be found on the BLE official website: for example, 0x16 represents servicedata
	4C 00 # Company logo (0x004C == Apple)
	02 # Byte 0 of iBeacon advertisement indicator
	15 # Byte 1 of iBeacon advertisement indicator
	B9 40 7F 30 F5 F8 46 6E AF F9 25 55 6B 57 FE 6D # iBeacon proximity uuid
	00 01# major
	00 01 #minor
	c5 # calibrated Tx Power


TB series modules support sending iBeacon broadcasts. In iBeacon mode, the module can send broadcasts according to iBeacon format. The main operations are as follows:

Configure the module in iBeacon mode:

	AT+MODE=2

Set the UUID of iBeacon (hexadecimal format, 16 bytes in total):

	AT+IBCNUUID=11223344556677889900AABBCCDDEEFF

Set the MAJOR of iBeacon (hexadecimal format, 2 bytes in total):

	AT+MAJOR=1234

Set the MINOR of iBeacon (hexadecimal format, 2 bytes in total):

	AT+MINOR=4567

Note: The above commands will take effect after restarting and will be saved after power off. In conjunction with setting the broadcast gap, automatic light sleep can reduce iBeacon power consumption.

## Note

To modify the default Bluetooth broadcast name, edit `const u8 tbl_scanRsp []` in *app.c*. The default value is "Ai-Thinker":

```c
const u8 tbl_scanRsp [] = {
    0x0B, 0x09, 'A', 'i', '-', 'T', 'h', 'i', 'n', 'k', 'e', 'r',
};
```
