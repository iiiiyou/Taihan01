
# M0 1bit 쓰기

from pymodbus.client import ModbusTcpClient
from pymodbus.transaction import *
client = ModbusTcpClient('192.168.0.20' ,502)

result_m1=client.read_coils(1)           


result_m50=client.read_coils(50)           
result_m51=client.read_coils(51)

result_m53=client.read_coils(53)           
result_m54=client.read_coils(54)

print('M1 M50 M51 M53 M54',result_m1.bits[0],result_m50.bits[0],result_m51.bits[0],result_m53.bits[0],result_m54.bits[0])          



# client.close()                      #  해도되고 안해도 됨
 





