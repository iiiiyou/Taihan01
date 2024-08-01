from tkinter import *
ent = Entry(win) # 입력창 생성
ent.pack() # 입력창 배치

win = Tk() # 창 만들기
win.geometry("300x100") # 창 크기 조정 
win.option_add("*Font","궁서 20") # 창 안의 모든 위젯 기본 폰트 옵션 수정
ent = Entry(win) # 입력창 생성
ent.pack() # 입력창 배치
win.mainloop() # 창 실행