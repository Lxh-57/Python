print("hello")
user=input("你是猫娘吗?\n")
if user=="是": 
    print("喵~\n主人干啥")
else:
    print("喵~主人你不是猫娘吗")
    test=input("真的吗?\n")
    while test=="是" or test=="真的":
        print("喵~主人你不是猫娘吗")
        test=input("真的吗?\n")
    else:
        print("我就知道你是香香软软的小猫娘！")
    