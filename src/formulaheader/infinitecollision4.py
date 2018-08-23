#!/usr/bin/env python
# coding=utf-8


import numpy as np
import time
import json
import copy
import os
import sys
import multiprocessing
from itertools import *


class Operating(object):
    # 计算阶长度(最长7阶，大约是465亿次运算)
    order = 7
    # 取数方式：      头 | 尾 | 原 | 合 | 积   
    getnumbertype = ['h', 't', 'o', 'j', 'a']
    # 输出最大值，当组合计算超过这个值，便打印输出
    outprintmaxvalue = 60.25
    # 实际最大值，当所有组合计算中超过这个值，便停止子线程计算，依次顺序为 波色 | 头数 | 尾数 | 单双 
    stopmaxvalue = [90.25, 92.25, 98.47, 82.15]
    # 原始49个数字序列
    origindataseq = np.arange(1, 50).tolist()
    # 随机偏移量(0,1,2,3,4,5,6,7,8,9)
    originoffsets = np.arange(0, 10).tolist()
    # 原始数据内容
    originnumbers = np.arange(0, 7).tolist()
    # 排序方式
    originsorttype = ['size', 'nosize']
    # 延迟间隔
    sleep = 0
    # 公式使用类型(波色16+1个一组 | 头数10+1个一组 | 尾数4+1个一组 | 单双24+1个一组)
    formulatype = ['killcolor', 'killhead', 'killtail', 'killsingleordouble']

    def __init__(self):
        pass

    def do(self, formulakilltype, step):

        cpunum = multiprocessing.cpu_count()
        handlernum = cpunum - 1  # 一个守护进程，一个接收进程
        # 罗列计算阶的长度
        # for length in range(step[0], step[1]):
        #     length += 1

        pernumbercollection = [p for p in permutations(self.originnumbers, 7)]
        itercollection = [''.join(x) for x in product(*[self.getnumbertype] * 7)]

        # 得到按照CPU数量-1等分的数组
        pervaluecollection = self.div_list(pernumbercollection, int(len(pernumbercollection) / handlernum))
        itevaluecollection = self.div_list(itercollection, int(len(itercollection) / handlernum))
        if len(itevaluecollection) > len(pervaluecollection):
            last = itevaluecollection[len(itevaluecollection) - 1]
            itevaluecollection.remove(last)
            itevaluecollection[len(itevaluecollection) - 1].extend(last)

        # 创建共享队列
        q = multiprocessing.JoinableQueue()
        for cpuindex in range(handlernum):
            multiprocessing.Process(target=self.create_kill_formula,
                                    args=(pervaluecollection[cpuindex],
                                          itevaluecollection[cpuindex],
                                          q, )).start()

        multiprocessing.Process(target=self.receive_kill_formula, args=(q,)).start()

        q.join()

    def receive_kill_formula(self, in_queue):
        count = 0
        while True:
            item = in_queue.get()
            count += 1
            print(count)
            if item is None or str(item) is '':
                break
            in_queue.task_done()  # 发出信号通知任务完成，
        print('Receive completed')
        
    def create_kill_formula(self, pernumbercollection, itercollection, out_queue):

        for pernumber in pernumbercollection:
            # 迭代所有取数方式
            for it in itercollection:
                expresstion = []
                i = 0
                for p in list(pernumber):
                    expresstion.append(str(p) + it[i])
                    i += 1

                # list 转字符串
                fe = ''
                for f in expresstion:
                    fe += f + ' '
                # 迭代最终公式
                fe = fe[0:len(fe) - 1]
                # 遍历偏移量
                for offset in self.originoffsets:
                    # 遍历排序方式
                    for sort in self.originsorttype:
                        expression = {}
                        expression['expression'] = fe
                        expression['offect'] = offset
                        expression['sort'] = sort
                        out_queue.put(expression)
                        time.sleep(self.sleep)
                        pass
                    pass
                pass
            pass

    def div_list(self, seq, n):
        return [seq[i:i + n] for i in range(0, len(seq), n)]

    def kill_anyaone_formula(self, jos, formulaexpression, sort, formulakilltype, offset):
        r = 0
        joslen = -1
        for jo in jos:
            nextIndex = 0
            for index in range(len(jo)):
                joslen += 1
                killnextseq = []
                nextIndex += 1
                if nextIndex >= len(jo):
                    break
                    pass

                total = self.formula_expression_hander(formulaexpression,
                                                       SortNumber().sort_number(jo[index], sort),
                                                       offset)[0]

                nextnumber = int(jo[nextIndex][1]['unusual_number']['number'])  # 下期特码

                if formulakilltype == self.formulatype[0]:
                    # kill color
                    killnext = str(Common.color(total))  # 下期要杀的颜色
                    killnextseq = Common.getnumber(killnext, 'c')  # 获取杀颜色的序列
                    pass
                if formulakilltype == self.formulatype[1]:
                    # kill head
                    killnext = str(Common.head(total))  # 下期要杀的头数
                    killnextseq = Common.getnumber(killnext, 'z')  # 获取杀头数的序列
                    pass
                if formulakilltype == self.formulatype[2]:
                    # kill killtail
                    killnext = str(Common.tail(total))  # 下期要杀的尾数
                    killnextseq = Common.getnumber(killnext, 't')  # 获取杀尾数的序列
                    pass
                if formulakilltype == self.formulatype[3]:
                    # kill single or double
                    killnext = str(Common.singleordouble(total))  # 下期要杀的单双
                    killnextseq = Common.getnumber(killnext, 't')  # 获取杀单双的序列
                    pass

                # noinspection PyBroadException
                try:
                    if list(set(self.origindataseq) - (set(killnextseq))).index(nextnumber) >= 0:
                        r += 1
                except:
                    pass

        return [round((r / (joslen - 1)) * 100.0, 2), formulaexpression, offset, sort, r, joslen]

    def formula_expression_hander(self, formulaexpression, matharray, offset=0):
        """
        对表达式进行反解析得到实际的数字
        :param formulaexpression: 表达式，比如"1t 0t 3j 5h 1o"
        :param matharray: 需要求和的数组，比如[15, 1, 17, 29, 35, 41, 11]
        :param offset: 求和偏移量，默认0
        :return: 返回[和, 反解析后的数组]，例如[56, [1, 5, 11, 4, 35]]
        """
        fexpressionarray = formulaexpression.split(' ')
        newmatharray = []
        index = 0

        for f in fexpressionarray:
            numIndex = int(f[0])
            operator = f[1]
            if operator == self.getnumbertype[0]:  # 头
                newmatharray.append(int(str(matharray[numIndex]).zfill(2)[0]))
            if operator == self.getnumbertype[1]:  # 尾
                newmatharray.append(int(str(matharray[numIndex]).zfill(2)[1]))
            if operator == self.getnumbertype[2]:  # 原
                newmatharray.append(int(matharray[numIndex]))
            if operator == self.getnumbertype[3]:  # 合 
                newmatharray.append(
                    int(str(matharray[numIndex]).zfill(2)[0]) + int(
                        str(matharray[numIndex]).zfill(2)[1]))
            if operator == self.getnumbertype[4]:  # 积 
                newmatharray.append(
                    int(str(matharray[numIndex]).zfill(2)[0]) * int(
                        str(matharray[numIndex]).zfill(2)[1]))
            index += 1
            pass
        total = 0
        for n in newmatharray:
            total += n
            pass
        total += int(offset)
        return [total, newmatharray]


class Common(object):
    @staticmethod
    def color(t):
        if t % 3 + 1 == 1:
            return '红'
        elif t % 3 + 1 == 2:
            return '蓝'
        elif t % 3 + 1 == 3:
            return '绿'

    @staticmethod
    def tail(t):
        return t % 10

    @staticmethod
    def singleordouble(o):
        if int(o) % 2 == 0:
            return '双'
        else:
            return '单'

    @staticmethod
    def head(t):
        return t % 5

    @staticmethod
    def _print(s):
        sys.stdout.write("\r" + s)
        sys.stdout.flush()

    # noinspection PyBroadException
    @staticmethod
    def getnumber(o, t="h"):
        """
        获取制定类型的序列
        :param o: 头 | 尾 | 肖 | 色 | 单 五种类型的数据  
        :param t: h | t | z | c | s
        :return: 
        """
        data = MarksixData()
        if t == "z":
            _Common__zodiac = data.zodiacsequence()
            for z in _Common__zodiac:
                for zz in _Common__zodiac[z]:
                    if o == zz:
                        return _Common__zodiac[z][zz]['Sequence']
        elif t == "h":
            _Common_head = data.head_number_data
            for h in _Common_head:
                try:
                    if o == '0':
                        if h.index(int(1)) > -1:
                            return h
                    if h.index(int(o + '0')) > -1:
                        return h
                except:
                    pass
            pass
        elif t == "t":
            _Common_tail = data.tail_number_data
            for tt in _Common_tail:
                try:
                    if o == '0':
                        o = '1' + o
                    if tt.index(int(o)) > -1:
                        return tt
                except:
                    pass
        elif t == "c":
            if o == "红":
                return data.color_data[0]
            elif o == "蓝":
                return data.color_data[1]
            elif o == "绿":
                return data.color_data[2]
            pass
        elif t == "s":
            if o == '双':
                return data.single_or_double_data[1]
            else:
                return data.single_or_double_data[0]

    @staticmethod
    def writefile(y, s):
        fo = open(os.getcwd() + "/" + str(y) + ".txt", 'w', encoding='utf8')
        fo.write(s)
        fo.close()


class SortNumber(object):
    def __init__(self):
        self.n01 = 0
        self.n02 = 0
        self.n03 = 0
        self.n04 = 0
        self.n05 = 0
        self.n06 = 0
        self.n07 = 0

    def sort_number(self, o, sort):
        # 获取每个号码
        sixnumber = o[1]['six_number']
        unusualnum = o[1]['unusual_number']
        # 按照掉球排序
        self.n01 = sixnumber['1']['number']
        self.n02 = sixnumber['2']['number']
        self.n03 = sixnumber['3']['number']
        self.n04 = sixnumber['4']['number']
        self.n05 = sixnumber['5']['number']
        self.n06 = sixnumber['6']['number']
        self.n07 = unusualnum['number']

        if sort == "size":
            lists = [self.n01, self.n02, self.n03, self.n04, self.n05, self.n06, self.n07]
            lists = self.bubble_sort(lists)  # 按照大小进行排序
            self.n01 = lists[0]
            self.n02 = lists[1]
            self.n03 = lists[2]
            self.n04 = lists[3]
            self.n05 = lists[4]
            self.n06 = lists[5]
            self.n07 = lists[6]
        return [self.n01, self.n02, self.n03, self.n04, self.n05, self.n06, self.n07]

    @staticmethod
    def bubble_sort(lists):
        # 大小排序（冒泡排序）
        count = len(lists)
        for i in range(0, count):
            for j in range(i + 1, count):
                if lists[i] < lists[j]:
                    lists[i], lists[j] = lists[j], lists[i]
        return lists


class MarksixData(object):
    # 用于基础计算中的全局变量
    currnetmarksix = [0, 0, 0, 0, 0, 0, 0]

    # 五行生肖（固定）
    five_lines = {
        '金': {'Sequence': ['猴', '鸡']},
        '木': {'Sequence': ['虎', '兔']},
        '水': {'Sequence': ['鼠', '猪']},
        '火': {'Sequence': ['蛇', '马']},
        '土': {'Sequence': ['牛', '龙', '羊', '狗']}
    }
    # 五行相克（固定）
    five_lines_mutex = [
        ['金', '木'],
        ['土', '水'],
        ['火', '金'],
        ['木', '土'],
        ['水', '火']
    ]

    # 十二生肖集合（固定）
    zodiacs = ['鼠', '牛', '虎', '兔',
               '龙', '蛇', '马', '羊',
               '猴', '鸡', '狗', '猪']

    # 反十二生肖集合（固定）
    r_zodiac = ['猪', '狗', '鸡', '猴',
                '羊', '马', '蛇', '龙',
                '兔', '虎', '牛', '鼠']

    # 49个数字集合（固定）
    number_data = np.arange(1, 50).tolist()

    # 波色集合（固定）
    color_data = [
        # 红
        [1, 2, 7, 8, 12, 13, 18, 19, 23, 24, 29, 30, 34, 35, 40, 45, 46],
        # 蓝
        [3, 4, 9, 10, 14, 15, 20, 25, 26, 31, 36, 37, 41, 42, 47, 48],
        # 绿
        [5, 6, 11, 16, 17, 21, 22, 27, 28, 32, 33, 38, 39, 43, 44, 49]
    ]

    # 大数集合（固定）
    large_data = np.arange(25, 49).tolist()

    # 小数集合（固定）
    small_data = np.arange(1, 24).tolist()

    # 合数集合（固定）
    join_data_01 = [1, 10]
    join_data_02 = [2, 11, 20]
    join_data_03 = [3, 12, 21, 30]
    join_data_04 = [4, 13, 22, 31, 40]
    join_data_05 = [5, 14, 23, 32, 41]
    join_data_06 = [6, 15, 24, 33, 42]
    join_data_07 = [7, 16, 25, 34, 43]
    join_data_08 = [8, 17, 26, 35, 44]
    join_data_09 = [9, 18, 27, 36, 45]
    join_data_10 = [19, 28, 37, 46]
    join_data_11 = [29, 38, 47]
    join_data_12 = [39, 48]
    join_data_13 = [49]

    # 合大（固定）
    join_large_data = [1, 2, 3, 4, 5, 6, 10, 11, 12, 13, 14, 15, 20, 21, 22, 23, 24, 30, 31, 32, 33,
                       40, 41, 42]

    # 合小（固定）
    join_small_data = [7, 8, 9, 16, 17, 18, 19, 25, 26, 27, 28, 29, 34, 35, 36, 37, 38, 39, 43, 44,
                       45, 46, 47, 48, 49]

    # 头数集合（固定）
    head_number_data = [
        [1, 2, 3, 4, 5, 6, 7, 8, 9],
        [10, 11, 12, 13, 14, 15, 16, 17, 18, 19],
        [20, 21, 22, 23, 24, 25, 26, 27, 28, 29],
        [30, 31, 32, 33, 34, 35, 36, 37, 38, 39],
        [40, 41, 42, 43, 44, 45, 46, 47, 48, 49],
    ]

    # 尾数集合（固定）
    tail_number_data = [
        [10, 20, 30, 40],
        [1, 11, 21, 31, 41],
        [2, 12, 22, 32, 42],
        [3, 13, 23, 33, 43],
        [4, 14, 24, 34, 44],
        [5, 15, 25, 35, 45],
        [6, 16, 26, 36, 46],
        [7, 17, 27, 37, 47],
        [8, 18, 28, 38, 48],
        [9, 19, 29, 39, 49]
    ]

    # 单双集合（固定）
    single_or_double_data = [
        # 单数
        [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31, 33, 35, 37, 39, 41, 43, 45, 47,
         49],
        # 双数
        [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48]
    ]

    # 尾大（固定）
    tail_large_data = [5, 6, 7, 8, 9, 15, 16, 17, 18, 19, 25, 26, 27, 28, 29, 35, 36, 37, 38, 39,
                       45, 46, 47, 48, 49]

    # 尾小（固定）
    tail_small_data = [1, 2, 3, 4, 10, 11, 12, 13, 14, 20, 21, 22, 23, 24, 30, 31, 32, 33, 34, 40,
                       41, 42, 43, 44]

    # 门数集合（集合）
    door_number_data_00 = np.arange(1, 9).tolist()
    door_number_data_01 = np.arange(10, 18).tolist()
    door_number_data_02 = np.arange(19, 27).tolist()
    door_number_data_03 = np.arange(28, 37).tolist()
    door_number_data_04 = np.arange(38, 49).tolist()

    # 半波集合（固定）
    half_red_even = [2, 8, 12, 18, 24, 30, 34, 40, 46]
    half_red_bill = [1, 7, 13, 19, 23, 29, 35, 45]
    half_blue_even = [4, 10, 14, 20, 26, 36, 42, 48]
    half_blue_bill = [3, 9, 15, 25, 31, 37, 41, 47]
    half_green_even = [6, 16, 22, 28, 32, 38, 44]
    half_green_bill = [5, 11, 17, 21, 27, 33, 39, 43, 49]

    # 半单双（固定）
    small_bill = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23]
    small_even = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24]
    large_bill = [25, 27, 29, 31, 33, 35, 37, 39, 41, 43, 45, 47, 49]
    large_even = [26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48]

    # 段位集合（固定）
    dondata01 = np.arange(1, 7).tolist()
    dondata02 = np.arange(8, 14).tolist()
    dondata03 = np.arange(15, 21).tolist()
    dondata04 = np.arange(22, 28).tolist()
    dondata05 = np.arange(29, 35).tolist()
    dondata06 = np.arange(36, 42).tolist()
    dondata07 = np.arange(43, 49).tolist()

    # 尾数杀肖（固定）
    killzodiac = [
        {"0": "猪"},
        {"1": "狗"},
        {"2": "鸡"},
        {"3": "蛇"},
        {"4": "猪"},
        {"5": "猪"},
        {"6": "兔"},
        {"7": "马"},
        {"8": "鸡"},
        {"9": "牛"}
    ]

    def __init__(self, zodiacname='鸡'):
        self.zodiac = zodiacname

    def zodiacsequence(self):
        """
        十二生肖对应的不同号码集合
        :return: 
        """
        i = 0
        reversalZodiac = copy.deepcopy(self.r_zodiac)
        split = 0
        b = {}
        for z in self.zodiacs:
            if z == self.zodiac:
                split = i
            i = i + 1
        befor = (len(self.zodiacs) - split)
        i = 0
        for z in reversalZodiac:
            if i != befor:
                b[i] = z
            if i == befor:
                break
            i = i + 1
        for _ in b:
            del reversalZodiac[0]
        fast = b[len(b) - 1]
        del b[len(b) - 1]
        retZodiac = [fast]
        for z in reversalZodiac:
            retZodiac.append(z)
        for bb in b:
            retZodiac.append(b[bb])
        return {
            1: {retZodiac[0]:
                    {'Sequence': [1, 13, 25, 37, 49],
                     'Color': ['red', 'red', 'blue', 'blue', 'green']}},
            2: {retZodiac[1]:
                    {'Sequence': [2, 14, 26, 38], 'Color': ['red', 'blue', 'blue', 'green']}},
            3: {retZodiac[2]:
                    {'Sequence': [3, 15, 27, 39], 'Color': ['blue', 'blue', 'green', 'green']}},
            4: {retZodiac[3]:
                    {'Sequence': [4, 16, 28, 40], 'Color': ['blue', 'green', 'green', 'red']}},
            5: {retZodiac[4]:
                    {'Sequence': [5, 17, 29, 41], 'Color': ['green', 'green', 'red', 'blue']}},
            6: {retZodiac[5]:
                    {'Sequence': [6, 18, 30, 42], 'Color': ['green', 'red', 'red', 'blue']}},
            7: {retZodiac[6]:
                    {'Sequence': [7, 19, 31, 43], 'Color': ['red', 'red', 'blue', 'green']}},
            8: {retZodiac[7]:
                    {'Sequence': [8, 20, 32, 44], 'Color': ['red', 'blue', 'green', 'green']}},
            9: {retZodiac[8]:
                    {'Sequence': [9, 21, 33, 45], 'Color': ['blue', 'green', 'green', 'red']}},
            10: {retZodiac[9]:
                     {'Sequence': [10, 22, 34, 46], 'Color': ['blue', 'green', 'red', 'red']}},
            11: {retZodiac[10]:
                     {'Sequence': [11, 23, 35, 47], 'Color': ['green', 'red', 'red', 'blue']}},
            12: {retZodiac[11]:
                     {'Sequence': [12, 24, 36, 48], 'Color': ['red', 'red', 'blue', 'blue']}},
        }


class Data2017(object):

    @staticmethod
    def __data__():
        c = '''
        '''
        return json.loads(c)


def main(par):
    Operating().do('killtail', par)


if __name__ == '__main__':
    step = []
    if multiprocessing.cpu_count() == 4:
        step = [
            [0, 3],  # 574035 
            [3, 5],  # 176400000
            [5, 6],  # 1653750000
            [6, 7]   # 8268750000
        ]
    if multiprocessing.cpu_count() == 8:
        step = [[0, 4], [1, 2], [2, 3], [3, 4],
                [4, 5], [5, 6], [6, 7], [7, 7]]
    # 
    # for cpu in range(multiprocessing.cpu_count()):
    #     multiprocessing.Process(target=main, args=(step[cpu],)).start()

    main(step[0])