#제품번호      D0      D1      D2
#5섯자리     0xAABB  0xCCDD  0xEEFF   BB AA DD CC FF 순으로 저장

import time
from pymodbus.client import ModbusTcpClient
from pymodbus.transaction import *

client = ModbusTcpClient('192.168.0.20' ,502)


result_s_no = client.read_holding_registers(0x0000,5)

print(result_s_no.registers[0:3])


aa=result_s_no.registers[0]
bb=result_s_no.registers[1]
cc=result_s_no.registers[2]

aah=hex(aa)
bbh=hex(bb)
cch=hex(cc)

print()
print(aa,bb,cc)
print(aah,bbh,cch)
print(0xaa,0xbb,0xcc)
print()



aah1=(0xaa>>4) & 0x00ff
bbh1=(0xbb>>4) & 0x0f
print(aah1,bbh1)

 


########################################
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
