import time
from pymodbus.client import ModbusTcpClient
from pymodbus.transaction import *

client = ModbusTcpClient('192.168.102.20' ,502)

result_n0_1_2  = client.read_holding_registers(0x0000)    # D0  0x0000 제품번호
result_n0_3_4  = client.read_holding_registers(0x0001)
result_n0_5    = client.read_holding_registers(0x0002)

result_cnt    = client.read_holding_registers(0x0004)      # D4  총회전 카운터

result_err_cnt= client.read_holding_registers(0x0008)      # D8 ERROR카운터 배열로 사용

result_m      = client.read_holding_registers(0x0028)     # D40 0x0028 현길이[m]
result_d40 = client.read_holding_registers(40)    # D40 현재 미터수
result_m04 = client.read_coils(0x04)


result_d632 = client.read_holding_registers(632)    # D632 시작 년도 4자리
result_d621 = client.read_holding_registers(621)    # D621 시작 월 2자리
result_d622 = client.read_holding_registers(622)    # D622 시작 일 2자리
result_d623 = client.read_holding_registers(623)    # D623 시작 시 2자리
result_d624 = client.read_holding_registers(624)    # D624 시작 분 2자리
result_d625 = client.read_holding_registers(625)    # D625 시작 초 2자리

yyyy = result_d632.registers[0]
mm = result_d621.registers[0]
dd = result_d622.registers[0]
hh = result_d623.registers[0]
nn = result_d624.registers[0]
ss = result_d625.registers[0]

result_d20 = client.read_holding_registers(20)    # D20
d20 = result_d20.registers[0]


print("제품번호0: ", result_n0_1_2.registers[0])
print("제품번호1: ", result_n0_3_4.registers[0])
print("제품번호2: ", result_n0_5.registers[0])

print("DB Error 카운터 배열로 사용: ", result_err_cnt.registers[0])
print("D4 총회전 카운터: ", result_cnt.registers[0])
print("현길이[m]: ", result_m.registers[0])
print("현길이2[m]: ", result_d40.registers[0])
print("물리적 start버튼 상태: ", result_m04.bits[0])

mm = str(mm).zfill(2)
dd = str(dd).zfill(2)
hh = str(hh).zfill(2)
nn = str(nn).zfill(2)
ss = str(ss).zfill(2)
mmddhhnnss = f"{yyyy}{mm}{dd}{hh}{nn}{ss}"

print("생산 시작 시간: ", mmddhhnnss)

print("D20: ", d20)


err_cnt_array = int(result_err_cnt.registers[0])
print("err_cnt_array: ", err_cnt_array)
i=0
print("=======  검사지점 =========")
for i in range(1,err_cnt_array+1):
   m_m = i + 200
   cm_cm = i + 300
   d200_m = client.read_holding_registers(m_m)
   d300_cm = client.read_holding_registers(cm_cm)
   # print(d200_m.registers[0])
   # print(d300_cm.registers[0])
   # print(i,'번째:',d200_m.registers[0],'.',d300_cm.registers[0],'[m]')



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
