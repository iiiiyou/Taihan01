# pip install pymodbus

# M0 1bit False 쓰기

from pymodbus.client import ModbusTcpClient
from pymodbus.transaction import *
client = ModbusTcpClient('192.168.0.20' ,502)
client.write_coils(0x0000,0)            # plc 시작및 hmi 입력가능
result_m0 = client.read_coils(0)
print(result_m0.bits[0])            # bit 프린트 방법  True False
# client.close()                      #  해도되고 안해도 됨
 





