import datetime as datetime
from tkinter import *
win = Tk() # 창 생성
win.geometry("600x100")
win.title("What time?") # 제목 : What time?
win.option_add("*Font","궁서 20")
btn = Button(win, width=20, height=2, text="현재 시각") # 버튼 생성 # Button 함수 안에 옵션으로 넣음
btn.config(width=20, height=2) # 버튼 가로 세로 크기 변경
btn.config(text="현재 시각") # 현재 시각
def alert():
    print("버튼 눌림")
def what_time():
    print(datetime.now())
btn.config(command = alert)
btn.pack() # 버튼 배치
win.mainloop() # 창 실행