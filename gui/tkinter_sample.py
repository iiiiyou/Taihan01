import tkinter as tk

def calculate():
    try:
        # 입력값 가져오기
        num1 = float(entry1.get())
        num2 = float(entry2.get())


        # 입력값 검증: 0.1 ~ 0.9 사이의 0.1 단위인지 확인
        if num1 not in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9] or \
           num2 not in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]:
            result_label.config(text="잘못된 입력입니다. 0.1 ~ 0.9 사이의 0.1 단위 값을 입력해주세요.")
            return

        # 계산 결과
        result = num1 + num2

        # 결과 출력 (소수점 둘째 자리까지 반올림)
        result_label.config(text="결과: {:.2f}".format(result))

        # 입력 필드 내용 삭제
        entry1.delete(0, tk.END)
        entry2.delete(0, tk.END)
        
    except ValueError:
        result_label.config(text="숫자만 입력해주세요.")

# 메인 창 생성
window = tk.Tk()
window.title("간단한 계산기")

# 창 크기 조절 (가로 300, 세로 150)
window.geometry("300x150")

# 입력 필드 생성 및 배치
label1 = tk.Label(window, text="첫 번째 숫자:")
label1.place(x=20, y=20)
entry1 = tk.Entry(window)
entry1.place(x=100, y=20)

label2 = tk.Label(window, text="두 번째 숫자:")
label2.place(x=20, y=50)
entry2 = tk.Entry(window)
entry2.place(x=100, y=50)

# 계산 버튼 생성 및 배치
calculate_button = tk.Button(window, text="계산", command=calculate)
calculate_button.place(x=100, y=80)

# 결과 출력 라벨 생성 및 배치
result_label = tk.Label(window, text="")
result_label.place(x=20, y=110)

# 창 실행
window.mainloop()