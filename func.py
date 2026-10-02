# func.py
import re
from flask import request, jsonify
import time
import serial_handler

def get_id(motor_id):
    return re.sub(r"[^\d]", "", motor_id)

def get_type(motor_id):
    return re.sub(r"[\d_]", "", motor_id)

def convert_to_254(value):
    if not (0 <= value <= 100):
        raise ValueError("???????? ?????? ???? ? ????????? ?? 0 ?? 100.")
    return round((value * 254) / 100)

def submit_connection():
    data = request.get_json()
    motor_id = data.get('motorId')
    speed_percent = data.get('speed')
    direction = data.get('direction')
    start_type = data.get('startType')
    value = data.get('value')
    status = data.get('status')

    try:
        dev_type = get_type(motor_id)
        dev_id = get_id(motor_id)
    except Exception as e:
        print("error data ID:", e)
        return jsonify({"status": "error", "message": "Invalid motor ID"}), 400

    if dev_type == "motor":
        speed_254 = convert_to_254(speed_percent) if speed_percent is not None else 0
        cmd = f"M,{dev_id},{direction},{start_type},{speed_254}"
        serial_handler.send_i2c(cmd)
        return jsonify({"status": "success", "message": cmd})

    elif dev_type == "servo":
        cmd = f"W,{dev_id},{status},{value}"
        serial_handler.send_i2c(cmd)
        return jsonify({"status": "success", "message": cmd})

    elif dev_type == "polish":
        speed_254 = convert_to_254(speed_percent) if speed_percent is not None else 0
        cmd = f"P,{dev_id},{speed_254}"
        serial_handler.send_polish(cmd)
        return jsonify({"status": "success", "message": cmd})

    elif dev_type == "hand":
        try:
            angle = int(value)
            status = int(status)
        except (ValueError, TypeError):
            return jsonify({"status": "error", "message": "Invalid angle or status"}), 400
        if not (0 <= angle <= 270) or status not in (0, 1):
            return jsonify({"status": "error", "message": "Angle must be 0-270, status 0/1"}), 400
        cmd = f"H,{angle},{status}"
        if not serial_handler.send_hand(cmd):
            return jsonify({"status": "error", "message": "Hand device not available"}), 500
        return jsonify({"status": "success", "message": cmd})

    elif dev_type == "killall":
        if status == 1:
            for i in range(6):
                serial_handler.send_i2c(f"M,{i+1},0,0,0")
                serial_handler.send_i2c(f"W,{i+1},0,0")
            return jsonify({"status": "success", "message": "kill completed"})
        else:
            return jsonify({"status": "success", "message": "kill back"})

    return jsonify({"status": "error", "message": "Unknown device type"}), 400

def submit_connection_service():
    data = request.get_json()
    state = data.get('state')
    if state is None:
        return jsonify({"status": "error", "message": "????????? ?? ????????"}), 400
    cmd = f"S,{state}"
    serial_handler.send_i2c(cmd)
    return jsonify({"status": "success", "message": cmd})
