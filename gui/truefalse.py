
# 컴퓨터 키고, 광통신 start 버튼 안눌렀을때(PLC Stop) -> m4 = 0
# 광통신 start 버튼 처음 누름  -> m4 = 1
# PLC 화면 stop 버튼 누르면 -> m4 = 0

# 컴퓨터 키고, 광통신 start 버튼 안눌렀을때 -> m53, M54 = False, False
# 광통신 start 버튼 처음 누름              -> m53, M54 = True, False
# 광통신 start 버튼 두번째 누름            -> m53, M54 = False, True

m53, m54 = False, False
m53m, m54m = m53, m54
# print("m53 =",m53, "m54 =",m54)
# print("m53m=",m53m, "m54m=",m54m)


# ## case 1 - 시작 전
# m53, m54 = False, False
# print("m53 =",m53, "m54 =",m54)
# print("m53m=",m53m, "m54m=",m54m)

# ## case 2 - 처음 실행
# m53, m54 = True, False
# print("m53 =",m53, "m54 =",m54)
# print("m53m=",m53m, "m54m=",m54m)

# ## case 3 - 두번째 실행
# m53, m54 = False, True
# print("m53 =",m53, "m54 =",m54)
# print("m53m=",m53m, "m54m=",m54m)



i = 0
while i < 8: 
    #############################
    i = i + 1
    if i <= 2:
        m53, m54 = False, False
        print(i, ": 컴퓨터 키고 변화 Start 버튼 실행 안함")
    if i > 2 and i <= 4:
        m53, m54 = True, False
        print(i, ": 컴퓨터 키고 변화 Start 버튼 처음 실행 함")
    if i > 4 and i <= 6:
        m53, m54 = False, True
        print(i, ": 컴퓨터 키고 변화 Start 버튼 두번째 실행 함")
    if i > 6 and i <= 8:
        m53, m54 = True, False
        print(i, ": 컴퓨터 키고 변화 Start 버튼 세번째 실행 함")

    # 컴퓨터 부팅 후 물리적 Start 버튼이 아직 안눌린 상태이면
    if m53 == False and m54 == False:
        print("   ", i," :화면 전송만 실행")
        print()

    # 방금 Start 버튼이 눌렸나?
    elif not((m53m == m53) & (m54m == m54)):
        print("   ", i," :10프레임 실행: 밝기 측정, Exposure Time 변경")
        print("   ", i," :10프레임 실행: Segmentation area 측정, 기준 넓이로 지정")
        print("   ", i," :Detact 실행")
        print()
        m53m, m54m = m53, m54
    # Start 버튼 눌른 후 다음 Start 버튼 누르기 전인가?
    else:
        print("   ", i," :Detact 실행")
        print()


print("loop 종료")

