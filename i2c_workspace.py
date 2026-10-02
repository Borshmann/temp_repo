import smbus2

I2C_ADDRESS = 0x08
I2C_BUS = 1
bus = smbus2.SMBus(I2C_BUS)

def send_command(command):
    try:
         command += "\n"
         data = [ord(char) for char in command]
         bus.write_i2c_block_data(I2C_ADDRESS, 0, data)
         print(f"Команда '{command.strip()}' отправлена по I2C на адрес {hex(I2C_ADDRESS)}")
     except Exception as e:
         print(f"Ошибка при отправке команды: {e}")
     finally:
         bus.close()
