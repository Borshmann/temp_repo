# tcp_server.py
import socket
import serial_handler

HOST = '192.168.12.175'
PORT = 8080

def convert_to_254(value):
    if not (0 <= value <= 100):
        raise ValueError(" 0  100.")
    return round((value * 254) / 100)

def parse_and_convert_command(cmd: str) -> str:
    parts = cmd.split(',')
    if not parts:
        return cmd

    cmd_type = parts[0].strip()

    #0-100
    if cmd_type == 'P':
        if len(parts) >= 3:
            try:
                speed_percent = float(parts[2])
                speed_254 = convert_to_254(speed_percent)
                parts[2] = str(speed_254)
            except (ValueError, IndexError):
                pass  

    elif cmd_type == 'M':
        #M,id,direction,start_type,speed_percent
        if len(parts) >= 5:
            try:
                speed_percent = float(parts[4])
                speed_254 = convert_to_254(speed_percent)
                parts[4] = str(speed_254)
            except (ValueError, IndexError):
                pass

    return ','.join(parts)

def start_tcp_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        s.bind((HOST, PORT))
        s.listen(1)
        print(f"TCP-start{HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            with conn:
                print(f"conn {addr}")
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break
                    raw_cmd = data.decode('utf-8').strip()
                    if not raw_cmd:
                        continue

                    processed_cmd = parse_and_convert_command(raw_cmd)

                    success = False
                    if processed_cmd.startswith('H'):
                        success = serial_handler.send_hand(processed_cmd)
                    elif processed_cmd.startswith('P'):
                        success = serial_handler.send_polish(processed_cmd)
                    else:
                        success = serial_handler.send_i2c(processed_cmd)


                    response = "true" if success else "false"
                    try:
                        conn.sendall(response.encode('utf-8'))
                    except Exception as e:
                        print(f"[err: {e}")
