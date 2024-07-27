import time
from datetime import datetime
from pymodbus.client import ModbusTcpClient
from pymodbus.transaction import *

client = ModbusTcpClient('192.168.0.20' ,502)

result_n0_1_2  = client.read_holding_registers(0x0000)    # D0  0x0000 제품번호
result_n0_3_4  = client.read_holding_registers(0x0001)
result_n0_5    = client.read_holding_registers(0x0002)

result_cnt    = client.read_holding_registers(0x0004)      # D4  총회전 카운터
result_err_cnt= client.read_holding_registers(0x0008)      # D8  검출갯수를  배열인자로 사용
result_m  = client.read_holding_registers(0x0028)          # D40 현재길이[m]-마지막은 최종길이[m]


print()


ad=(result_n0_1_2.registers[0])
bd=(result_n0_3_4.registers[0])
cd=(result_n0_5.registers[0])
c1 = (ad & 0x00ff)
c2 = ad >> 8
c3 = (bd & 0x00ff)
c4 = bd >> 8
c5 = cd
s_n = chr(c1)+chr(c2)+chr(c3)+chr(c4)+chr(c5)
print('제품번호:'+s_n)

print('케이블길이:'+str(result_m.registers[0])+'[m]')

yy=datetime.today().year        # PC에서 M0-True PLC에 쓰면서 이때 시간을 별도의 변수에저장
m12=datetime.today().month      # M96(chk_start) 읽어서-True면 검사종료 이떄 시간도 별도의 변수에저장
dd=datetime.today().day
hh=datetime.today().hour
m60=datetime.today().minute
print('검사시작시간:'+str(yy)+'년'+str(m12)+'월'+str(dd)+'일'+str(hh)+'시'+str(m60)+'분')
print('검사종료시간:'+str(yy)+'년'+str(m12)+'월'+str(dd)+'일'+str(hh)+'시'+str(m60)+'분')


err_cnt_array = int(result_err_cnt.registers[0])
print('검출갯수:'+str(err_cnt_array))

i=0
print("=======  검사지점 =========")
for i in range(1,err_cnt_array+1):



   
   m_m = i + 200
   cm_cm = i + 300
   d200_m = client.read_holding_registers(m_m)
   d300_cm = client.read_holding_registers(cm_cm)
   print('%5d%s%5d%s%2d%s' % (i,'번째:',d200_m.registers[0],'.',d300_cm.registers[0],'[m]'))
   #print(str(i)+'번째:'+str((d200_m.registers[0])+'.'+str(d300_cm.registers[0])+'[m]')
   
