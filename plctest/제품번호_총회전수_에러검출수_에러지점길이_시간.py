import time
from pymodbus.client import ModbusTcpClient
from pymodbus.transaction import *

client = ModbusTcpClient('192.168.0.20' ,502)

result_n0_1_2  = client.read_holding_registers(0x0000)    # D0  0x0000 제품번호
result_n0_3_4  = client.read_holding_registers(0x0001)
result_n0_5    = client.read_holding_registers(0x0002)

result_cnt    = client.read_holding_registers(0x0004)      # D4  총회전 카운터

result_err_cnt= client.read_holding_registers(0x0008)      # D8 ERROR카운터 배열로 사용

result_m      = client.read_holding_registers(0x0028)     # D40 0x0028 현길이[m] 

print(result_n0_1_2.registers[0])
print(result_n0_3_4.registers[0])
print(result_n0_5.registers[0])

print(result_err_cnt.registers[0])
print(result_cnt.registers[0])
print(result_m.registers[0])


err_cnt_array = int(result_err_cnt.registers[0])
print(err_cnt_array)
i=0
print("=======  검사지점 =========")
for i in range(1,err_cnt_array+1):
   m_m = i + 200
   cm_cm = i + 300
   d200_m = client.read_holding_registers(m_m)
   d300_cm = client.read_holding_registers(cm_cm)
   print(d200_m.registers[0])
   print(d300_cm.registers[0])
   print(i,'번째:',d200_m.registers[0],'.',d300_cm.registers[0],'[m]')



# print(result_m.registers)
# c_m_no1 = result_m.registers


'''
예 제품번호를  1234A 로 입력

 DEC       HEX     ASCII
12849 -> 0x3231     2 1
13363 -> Ox3433     4 3
65    -> 0x0041     A

0x30(48)---0
0x39(57)---9
0x41(65)---A
0x5A(90)---Z

'''
