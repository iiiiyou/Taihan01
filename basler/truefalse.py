m53, m54 = False, False
m53m, m54m = m53, m54
print("m53 =",m53, "m54 =",m54)
print("m53m=",m53m, "m54m=",m54m)


## case 1 - 시작 전
m53, m54 = False, False
print("m53 =",m53, "m54 =",m54)
print("m53m=",m53m, "m54m=",m54m)

## case 2 - 처음 실행
m53, m54 = True, False
print("m53 =",m53, "m54 =",m54)
print("m53m=",m53m, "m54m=",m54m)

## case 3 - 두번째 실행
m53, m54 = False, True
print("m53 =",m53, "m54 =",m54)
print("m53m=",m53m, "m54m=",m54m)

#############################
if (not((m53m == m53) & (m54m == m54))):
    print("m53 =",m53, "m54 =",m54)
    print("m53m=",m53m, "m54m=",m54m)
    m53m, m54m = m53, m54
    print("10프레임 실행")
    print("m53 =",m53, "m54 =",m54)
    print("m53m=",m53m, "m54m=",m54m)
else:
    print("Detact 실행")

