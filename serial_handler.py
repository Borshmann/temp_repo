# serial_handler.py
import serial
import serial.tools.list_ports
import time
from smbus2 import SMBus

_robohand_ser = None
_polish_ser = None
_robohand_port = None
_polish_port = None
_robohand_initialized = False

BAUD_RATE = 115200
I2C_ADDRESS = 0x0C


def _query_device(port, timeout_total=5.0, retry_interval=0.2):
    try:
        # Open serial port with minimal timeout
        ser = serial.Serial(
            port=port,
            baudrate=BAUD_RATE,
            timeout=0.1,
            exclusive=True
        )
        
        ser.dtr = False
        ser.rts = False
        time.sleep(0.1)
        
        if 'ACM' in port.upper():
            time.sleep(2.5)
        
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        
        ser.write(b"?\n")
        ser.flush()
        
        start_time = time.time()
        response_buffer = ""
        while time.time() - start_time < timeout_total:
            chunk = ser.read(256)
            if chunk:
                response_buffer += chunk.decode('utf-8', errors='ignore')
                if "robohand" in response_buffer.lower():
                    ser.close()
                    return "robohand"
                if "polish" in response_buffer.lower():
                    ser.close()
                    return "polish"
            time.sleep(retry_interval)
        
        ser.close()
        return ""
    
    except Exception as e:
        if 'ACM' in str(port).upper() and 'Permission' not in str(e):
            pass
        return ""

def auto_detect_devices(debug=True):
    global _robohand_port, _polish_port, _robohand_initialized
    
    _robohand_port = None
    _polish_port = None

    ports = [p.device for p in serial.tools.list_ports.comports()]
    
    if debug:
        print("\n?? Scanning serial ports...")
        for p in serial.tools.list_ports.comports():
            print(f"  {p.device:15} | {p.description:30} | {p.hwid}")
        print()

    for port in ports:
        resp = _query_device(port, timeout_total=4.0)
        if debug:
            print(f"   > {port:15} | response: '{resp}'")
        if resp == "robohand" and not _robohand_port:
            _robohand_port = port
        elif resp == "polish" and not _polish_port:
            _polish_port = port

    if not _polish_port and _robohand_port:
        acm_ports = [p for p in ports if 'ACM' in p.upper()]
        if acm_ports and acm_ports[0] != _robohand_port:
            _polish_port = acm_ports[0]
            if debug:
                print(f"   ??  Assigned {_polish_port} as 'polish' (ACM heuristic)")

    if not _robohand_port or not _polish_port:
        usb_ports = [p for p in ports if 'USB' in p.upper()]
        acm_ports = [p for p in ports if 'ACM' in p.upper()]
        
        if usb_ports and not _robohand_port:
            _robohand_port = usb_ports[0]
            if debug:
                print(f"   ??  Assigned {_robohand_port} as 'robohand' (USB heuristic)")
        
        if acm_ports and not _polish_port:
            _polish_port = acm_ports[0]
            if debug:
                print(f"   ??  Assigned {_polish_port} as 'polish' (ACM heuristic)")

    if _robohand_port and not _robohand_initialized:
        if debug:
            print(f"\n??  Initializing robohand on {_robohand_port}...")
        success1 = send_hand("H,1,0")
        if success1:
            time.sleep(3.0)
            success2 = send_hand("H,0,90")
            if success2:
                _robohand_initialized = True
                if debug:
                    print("? Robohand successfully initialized")

    if debug:
        print(f"\n? Final configuration:")
        print(f"   Robohand: {_robohand_port or '? not found'}")
        print(f"   Polish:   {_polish_port or '? not found'}")
    
    return _robohand_port is not None and _polish_port is not None

def _get_hand():
    global _robohand_ser
    if _robohand_ser is None and _robohand_port:
        _robohand_ser = serial.Serial(_robohand_port, BAUD_RATE, timeout=1)
        time.sleep(1)
    return _robohand_ser


def _get_polish():
    global _polish_ser
    if _polish_ser is None and _polish_port:
        _polish_ser = serial.Serial(_polish_port, BAUD_RATE, timeout=1)
        time.sleep(1)
    return _polish_ser


def send_hand(command: str) -> bool:
    ser = _get_hand()
    if ser:
        ser.write((command + "\n").encode('utf-8'))
        return True
    return False


def send_polish(command: str) -> bool:
    ser = _get_polish()
    if ser:
        ser.write((command + "\n").encode('utf-8'))
        return True
    return False


def send_i2c(command: str) -> bool:
    data = [ord(c) for c in command + "\n"]
    bus = None
    max_retries = 5
    delay = 0.5
    for attempt in range(1, max_retries + 1):
        try:
            bus = SMBus(1)
            bus.write_i2c_block_data(I2C_ADDRESS, 0, data)
            return True
        except Exception:
            pass
        finally:
            if bus is not None:
                try:
                    bus.close()
                except Exception:
                    pass
                bus = None
        if attempt < max_retries:
            time.sleep(delay)
    return False
