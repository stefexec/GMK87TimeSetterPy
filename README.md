# ZUOYA GMK87 Linux Time Sync

A lightweight, reverse-engineered Python script to synchronize the internal hardware clock (and the OLED screen) of the ZUOYA GMK87 mechanical keyboard on Linux.

By default, the keyboard's Windows software handles the time synchronization. This script allows Linux users to bypass the proprietary software, cleanly detach the specific USB interface from the kernel, and inject the current time using the exact Binary-Coded Decimal (BCD) payload the keyboard expects.

## Prerequisites

This script requires the `libusb1` Python binding to directly communicate with the keyboard's USB endpoints. 

Install the dependency globally via your package manager:
```bash
sudo pacman -S python-libusb1
```
*(Note: Using a Python virtual environment is not recommended, as `sudo` is required to detach the kernel driver and will default back to the system-wide Python environment.)*

## Installation & Setup

1. Clone this repository:
```bash
git clone https://github.com/stefexec/GMK87TimeSetterPy.git
cd GMK87TimeSetterPy
```
2. Make the script executable:
```bash
chmod +x gmk87_time.py
```

## Usage

Plug in your ZUOYA GMK87 keyboard and run the script with root privileges. Root access is strictly required to temporarily unbind the `usbhid` driver from Interface 3 so the payload can be sent without crashing the keyboard.

```bash
sudo ./gmk87_time.py
```

**Expected Output:**
```text
✅ Device found and opened.
✅ Kernel driver detached from Interface 3.
⏳ Sending time update to keyboard: 2026-03-24 01:36:00
🎉 Time updated and acknowledged by keyboard! (ACK: 040b000300000000)
✅ Interface released back to Linux.
```
Your keyboard's screen will instantly update to the correct local time and date.

## How it Works
1. **The Payload:** The script calculates the current system time and formats it into a 64-byte payload. The GMK87 firmware specifically expects the time data to be encoded in **Binary-Coded Decimal (BCD)**, in the following reverse-order sequence starting at byte 44:
   `Second -> Minute -> Hour -> Weekday -> Day -> Month -> Year`
2. **The Handshake:** The keyboard operates on a strict request-acknowledge protocol. After writing the 64-byte payload to Endpoint `0x05`, the script immediately reads an 8-byte acknowledgment receipt from Endpoint `0x83`. This clears the keyboard's internal buffer, ensuring the microcontroller doesn't freeze and safely returns to processing normal keystrokes.
