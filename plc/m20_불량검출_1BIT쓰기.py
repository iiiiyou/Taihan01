
# M20 불량검출 PC에서  1bit False 쓰기

import time
from pymodbus.client import ModbusTcpClient
from pymodbus.transaction import *

client = ModbusTcpClient('192.168.0.20' ,502)

client.write_coils(0x0020,1)
result_m20 = client.read_coils(0x0020)
print(result_m20.bits[0]) 


time.sleep(0.1)

client.write_coils(0x0020,0)
result_m20 = client.read_coils(0x0020)
print(result_m20.bits[0])            # bit 프린트 방법  True False
# client.close()                      #  해도되고 안해도 됨
 





