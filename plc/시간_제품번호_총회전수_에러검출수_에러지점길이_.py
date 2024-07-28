import time
from datetime import datetime
from pymodbus.client import ModbusTcpClient
from pymodbus.transaction import *

client = ModbusTcpClient('192.168.0.20' ,502)

result_n0_1_2  = client.read_holding_registers(120)    # D120   제품번호
result_n0_3_4  = client.read_holding_registers(121)
result_n0_5_6  = client.read_holding_registers(122)
result_n0_7_8  = client.read_holding_registers(123)
result_n0_9_10  = client.read_holding_registers(124)

result_cnt    = client.read_holding_registers(0x0004)      # D4  총회전 카운터
result_err_cnt= client.read_holding_registers(0x0008)      # D8  검출갯수를  배열인자로 사용
result_m  = client.read_holding_registers(0x0028)          # D40 현재길이[m]-마지막은 최종길이[m]

print()

ad=(result_n0_1_2.registers[0])
bd=(result_n0_3_4.registers[0])
cd=(result_n0_5_6.registers[0])
dd=(result_n0_7_8.registers[0])
ed=(result_n0_9_10.registers[0])


c1 = (ad & 0x00ff)
c2 = ad >> 8

c3 = (bd & 0x00ff)
c4 = bd >> 8

c5 = (cd & 0x00ff)
c6 = cd >> 8

c7 = (dd & 0x00ff)
c8 = dd >> 8

c9  = (ed & 0x00ff)
c10 = ed >> 8

s_n = chr(c1)+chr(c2)+chr(c3)+chr(c4)+chr(c5)+chr(c6)+chr(c7)+chr(c8)+chr(c9)+chr(c10)
print('제품번호:'+s_n)

print('케이블길이:'+str(result_m.registers[0])+'[m]')

#####  검사최초 시작 시간 ##########
yy=client.read_holding_registers(632)
m12=client.read_holding_registers(621)
dd=client.read_holding_registers(622)
hh=client.read_holding_registers(623)
m60=client.read_holding_registers(624)
print('%s%4d%s%2d%s%2d%s%2d%s%2d%s' % ('검사시작시간:',yy.registers[0],'년',m12.registers[0],'월',dd.registers[0],'일',hh.registers[0],'시',m60.registers[0],'분'))


err_cnt_array = int(result_err_cnt.registers[0])
print('검출갯수:'+str(err_cnt_array))

i=0              # D1001부터 [m]  D5001부터[ft]
print("===========  검사지점 =========")
for i in range(1,err_cnt_array+1):
   m_m = i + 1000
   ft_ft = i + 5000
   d1000_m  = client.read_holding_registers(m_m)
   d5000_ft = client.read_holding_registers(ft_ft)
   print('%5d%s%5d%s%s%5d%s' % (i,'번째:',d1000_m.registers[0],'[m]','    ',d5000_ft.registers[0],'[ft]'))


'''
yy=datetime.today().year      
m12=datetime.today().month    
dd=datetime.today().day
hh=datetime.today().hour
m60=datetime.today().minute
print('검사시작시간:'+str(yy)+'년'+str(m12)+'월'+str(dd)+'일'+str(hh)+'시'+str(m60)+'분') # PC에서 시간작업 해주세요
print('검사종료시간:'+str(yy)+'년'+str(m12)+'월'+str(dd)+'일'+str(hh)+'시'+str(m60)+'분') # PC에서 시간작업 해주세요
'''

#print(str(i)+'번째:'+str((d1000_m.registers[0])+'.'+str(d5000_cm.registers[0])+'[ft]')   
