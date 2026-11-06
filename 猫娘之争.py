print("hello")
user=input("你是猫娘吗?\n(Y or N)")
if user=="Y": 
    print("喵~")
else:
    print("喵~主人你不是猫娘吗")
    test=input("真的吗?\n")
    while test=="Y":
        print("喵~主人你不是猫娘吗")
        test=input("真的吗?\n")
    else:
        print("我就知道你是香香软软的小猫娘！")
    