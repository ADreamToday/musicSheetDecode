import time
import soundfreq
import decimal


# get inputs from terminal
def inputFromCmd():
    res = []
    while True:     # 接收输入的同时滤掉注释 和空行
        a = input()
        if a == "stop":
            break
        if ( not a.startswith('@') ) and ( not  a.isspace() ) and (a):
            res.append(a)
    return res


# decode eivironments
def decodeEnviro(code):
    print("===Decode EnvironmentSettings===")
    res = {}
    sign = 0
    for i in code:
        if i == ":setEnvironment":
            print("*find settings*")
            sign = 1
            continue
        elif i == "finish" and sign == 1:
            print("*end of environmentsetting*")
            sign = 0
            break

        if sign == 1:
            envir_pair = i.split('=')
            envir_name = envir_pair[0]
            envir_value = envir_pair[1]
            print("-set %s=%s" % (envir_name , envir_value))
            res[envir_name] = envir_value

    print("===Environment Decode Finish===\n")
    return res


def decodeSections(code):
    print("===Decode Section===")

    res = {}
    parts_name = ''
    sign = 0
    for i in code:
        # 控制sign来决定是否添加
        if i.startswith(':') and i.split('=')[0] == ":section":
            sign = 1
            parts_name = i.split('=')[1]	# get the name of a section
            print("*find a section named %s*" % parts_name)
            res[parts_name] = []
            continue
        elif i == "finish" and sign == 1:
            sign = 0

        if sign == 1:                   # 添加
            for j in i.split():
                res[parts_name].append(j)

    print("===Section Decode Finish===\n")
    return res

def decodeMainSheet(code):
    print("===Decode MainSheet===")

    res = []
    sign = 0
    for i in code:
        if i == ":main":
            print("*find mainsheet*")
            sign = 1
            continue
        elif i == "finish" and sign == 1:
            break

        if sign == 1:
            for j in i.split():
                res.append(j)

    print("===MainSheet Decode Finish===\n")
    return res


def basicDecode():
    print("=====Start Basci Decode=====")
    inputsWithRealCode = inputFromCmd()

    # envirs = {}
    envirs		= decodeEnviro(inputsWithRealCode)
    # sections = {'':[]}
    sections	= decodeSections(inputsWithRealCode)
    # main = []
    main		= decodeMainSheet(inputsWithRealCode)

    print("=====Basci Decode Finish=====\n")

    # print(envirs)
    # print(sections)
    # print(main)
    # print(inputsWithRealCode)
    return envirs , sections , main

def envirsgen(envirs):
    # generate stdfreq
    # tunes = []
    if "mainTune" in envirs.keys():
        tune = envirs["mainTune"]
        print("Set tune %s" % tune)
        tunes = soundfreq.stdfreq(tune)
    else:
        tunes = soundfreq.stdfreq('C')

    # get speed
    if "speed" in envirs.keys():
        speed = envirs["speed"]
    else:
        speed = 1

    if "IRC" in envirs.keys():
        IRC = envirs["IRC"]
    else:
        IRC = 0

    return tunes , speed , IRC

# 把所有段乐谱符号解析 ， 包括主乐谱
def decodeSectionSign(sections , main):
    # 先解析段
    # 采用覆写section的方法
    # sections = {'':[]}
    new_sections = {}
    for i in sections.keys():
        new_sections[i] = []

        for j in sections[i]:

            if j.startswith('='):
                # 将一个section塞进另一个
                # 按照逻辑，将要塞的section必须已经载入new_sections
                section_name = j.split('=')[1]
                new_sections[i].extend(new_sections[section_name])
            else:
                # 将原有的值直接复制到新的sections
                new_sections[i].append(j)


    # 覆写完成 解析并覆写main
    # main = []
    new_main = []
    for i in main:
        if i.startswith('='):
            section_name = i.split('=')[1]
            new_main.extend(new_sections[section_name])
        else:
            new_main.append(i)

    return new_main

# 解析一个乐谱音符
def singleSignDecode(astr):
    std = 35    # 12 + 12 + 12 + 1 - 1 - 1
    # 一个 - 号 减12
    # 一个+号 加12

    res = [0 , 0.0]

    # 先解析 - + 号
    plus = astr.count('+')
    minus = astr.count('-')

    change = plus*12 + minus*(-12)

    # 解析 * 号
    if plus != 0:
        remain = astr.split('+')[plus]
    elif minus != 0:
        remain = astr.split('-')[minus]
    else:
        remain = astr

    # 处理时间
    if '*' in remain:
        res[1] = float(remain.split('*')[1])
    else:
        res[1] = float(1.0)

    # 处理序号
    nums = {'1':1,
            '2':3,
            '3':5,
            '4':6,
            '5':8,
            '6':10,
            '7':12,
            '0':-1}
    num = 0
    remain = remain.split('*')[0]
    if 'b' in remain:
        num = -1 + nums[remain.split('b')[0]]
    elif '#' in remain:
        num = 1 + nums[remain.split('#')[0]]
    else:
        num = nums[remain]

    if num != -1:
        num = num + change + std
    else:
        num = -1
    res[0] = num

    # 删除了判断&号

    # res = [freq(num) , time(double)]
    return res


# 解析底层
def decodeSheet(main , tunes):
    main_freq = []
    for i in main:

        singleSign = singleSignDecode(i)
        if singleSign[0] != -1:
            main_freq.append([tunes[singleSign[0]] , singleSign[1]])
        else:
            main_freq.append([0 , singleSign[1]])

    # 时间线时间点累加
    last_time = float(0)
    for i in main_freq:
        i[1] = i[1] + last_time
        last_time = i[1]
    return main_freq


# 解析成寄存器变量
def fun(freq , IRC):
    IRC = decimal.Decimal(IRC)
    freq24 = decimal.Decimal(freq * 24)
    Timer = int((65535 - IRC / freq24).quantize(decimal.Decimal('0')))
    return hex(Timer)

def Timerdecode(main_freq , IRC):
    main_TimerHL  = []
    # [ [hex(str) , time(float)] ]
    for i in main_freq:
        if i[0] != 0:
            main_TimerHL.append([fun(i[0] , IRC) , i[1]])
        else:
            main_TimerHL.append([0 , i[1]])
    return main_TimerHL

def output(main_Time):
    # [ [hex(str) , time(float)] ]
    timelist = []
    Timerlist = []
    for i in main_Time:
        timelist.append(i[1])
        Timerlist.append(i[0])
    with open('output' , 'w') as f:
        f.write("生成时间:\t%s\n" % time.asctime())
        f.write("长度\t%d\n" % len(main_Time))
        # 输出一个二维数组样式,播放码，即高八位，低八位
        # { {0x00 , 0x00}, }
        f.write("u8 code soundTrack[][] = { ")
        for i in Timerlist:
            if type(i) == int and i == 0:
                txt = '{' + '0xff' + ',' + '0xff' + '} , '
            else:
                H8 = '0x' + i[2] + i[3]
                L8 = '0x' + i[4] + i[5]
                txt = '{' + H8 + ',' + L8 + '} , '
            f.write(txt)
        f.write("};\n")

        # 播放时间表 float{}
        f.write("float code time[] = { ")
        for i in timelist:
            f.write("%f , " % i)
        f.write("};\n")


if __name__ == "__main__":
    envirs , sections , main = basicDecode()
    print(envirs)
    tunes , speed , IRC= envirsgen(envirs)
    main = decodeSectionSign(sections , main)
    print(main)
    main_freq = decodeSheet(main , tunes)
    print(main_freq)
    main_time = Timerdecode(main_freq , IRC)
    print(main_time)
    output(main_time)
