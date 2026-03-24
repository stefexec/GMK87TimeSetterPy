#!/usr/bin/env python3
import datetime
import usb1
import sys

# ZUOYA GMK87 Identifiers
VID = 0x320F
PID = 0x5055
INTERFACE = 3
ENDPOINT = 0x05
EP_IN = 0x83

def to_bcd(val):
    """Converts a standard integer to Binary-Coded Decimal"""
    return ((val // 10) << 4) | (val % 10)

def generate_time_payload():
    """Generates the exact 64-byte payload with the true BCD byte order"""
    now = datetime.datetime.now()
    
    # 43-byte static prefix
    prefix = [
        0x04, 0x9c, 0x04, 0x06, 0x30, 0x00, 0x00, 0x00, 0x00, 0x01, 0x09, 0x04, 0x00, 0x00, 0x00, 0xdc,
        0xff, 0x17, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xff, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x09, 0x02, 0x00, 0x04, 0x00, 0x14
    ]
    
    # 7-byte time block in the exact order the GMK87 expects
    time_bytes = [
        to_bcd(now.second),
        to_bcd(now.minute),
        to_bcd(now.hour),
        to_bcd(now.isoweekday()), # 1 = Monday, 7 = Sunday
        to_bcd(now.day),
        to_bcd(now.month),
        to_bcd(now.year % 100)
    ]
    
    # 14-byte static suffix
    suffix = [
        0x00, 0x3c, 0x00, 0x00, 0x1f, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
    ]
    
    # Combine them all into the final 64-byte packet
    payload = bytearray(prefix + time_bytes + suffix)
    
    # Absolute safety check
    if len(payload) != 64:
        raise ValueError(f"CRITICAL: Payload is {len(payload)} bytes instead of 64!")
        
    return bytes(payload)

def main():
    with usb1.USBContext() as context:
        dev = context.getByVendorIDAndProductID(VID, PID)
        
        if dev is None:
            print("❌ Keyboard not found. Is it plugged in?")
            sys.exit(1)
            
        handle = dev.open()
        print("✅ Device found and opened.")
        
        # 1. Detach kernel driver safely
        if handle.kernelDriverActive(INTERFACE):
            handle.detachKernelDriver(INTERFACE)
            print("✅ Kernel driver detached from Interface 3.")
            
        handle.claimInterface(INTERFACE)
        
        try:
            # 2. Send the time payload
            payload = generate_time_payload()
            current_time_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"⏳ Sending time update to keyboard: {current_time_str}")
            handle.interruptWrite(ENDPOINT, payload, timeout=1000)
            
            # 3. FIX: Read the 8-byte acknowledgment so the keyboard doesn't freeze!
            ack = handle.interruptRead(EP_IN, 8, timeout=1000)
            print(f"🎉 Time updated and acknowledged by keyboard! (ACK: {ack.hex()})")
            
        except Exception as e:
            print(f"❌ Failed to communicate: {e}")
            
        finally:
            # 4. Clean up gracefully
            handle.releaseInterface(INTERFACE)
            
            try:
                # Politely hand it back to Linux
                handle.attachKernelDriver(INTERFACE)
                print("✅ Interface released back to Linux.")
            except Exception:
                pass # If Linux already grabbed it, just silently move on

if __name__ == "__main__":
    main()
