from tkinter import *

win = Tk()
win.title("daum Log-in")
win.geometry("400x300")
win.option_add("*Font", "궁서 20")

# 다음 로고
lab_d = Label(win)
img = PhotoImage(file = "C:/source/tkinter/Daum_communication_logo.svg.png", master = win)
img = img.subsample(3)
lab_d.config(image = img)
lab_d.pack()

# id 라벨
lab1 = Label(win)
lab1.config(text = "ID")
lab1.pack()

# id 입력창
ent1 = Entry(win)
ent1.insert(0, "temp@temp.com")
def clear(event):
    if ent1.get() == "temp@temp.com":
        ent1.delete(0, len(ent1.get()))
    
ent1.bind("<Button-1>", clear)
ent1.pack()

# pw 라벨
lab2 = Label(win)
lab2.config(text = "Password")
lab2.pack()

# pw 입력창
ent2 = Entry(win)
ent2.config(show = "*")
ent2.pack()

# 로그인 버튼
btn = Button(win)
btn.config(text = "로그인")
btn.pack()

win.mainloop()
