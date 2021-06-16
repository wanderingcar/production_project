import simpy
import numpy as np
import random
import matplotlib.pyplot as plt
SIM_TIME = 1000 * 60 * 6  # 초 단위로 30분

num_people = 1000
num_exits = 4
num_platform = 4
stair_breadth = 300

P_type = [0.703, 0.025, 0.164, 0.005, 0.04, 0.063]  # [일반, 장애인, 고령자, 임산부, 영유아 동반, 어린이], 2020년 교통안전정보관리시스템 기준
# https://tmacs.ts2020.kr/web/TW/weak01.jsp?mid=S3098

plt.ion()
fig = plt.figure()
plt.plot([0,4],[4,4])
for i in range(4):
    plt.plot([i,i],[0,4])
plt.xlim(0,4)
plt.ylim(0,5)
plt.xticks([],[])
plt.yticks([],[])
plt.xlabel('Exit number')
plt.title('Queue of Exit')
plt.text(0.4,4.2, 'Exit 1')
plt.text(1.4,4.2, 'Exit 2')
plt.text(2.4,4.2, 'Exit 3')
plt.text(3.4,4.2, 'Exit 4')


def TimetoPlatformtoExit():
    return np.random.normal(60000,10000)

def IAT(time):  # 사람 간 간격
    return_time = 0  # 출력 시간

    if 0 <= time <= 30000:  # 화재 발생 초기에 사람들이 인지를 하는 시간 1분
        return_time = np.random.poisson(lam=2000/num_exits)  # 약 2초에 1명 꼴
    else:
        return_time = np.random.normal(50, 10, 1)

    if return_time <= 0:  # 임의의 값이 0인 경우, 1으로 가정
        return_time = 1

    return return_time


def stair_time(type, congested):  # 1인당 계단 소요시간
    return_time = 0  # 출력 시간

    if congested:
        return_time = np.random.poisson(lam=4000)  # 혼잡시 평균 30초 소요
    else:
        return_time = np.random.poisson(lam=1000)  # 비혼잡시 평균 20초 소요

    if return_time <= 0:  # 임의의 값이 0인 경우, 1으로 가정
        return_time = 1

    if type == 0:  # 일반
        return_time = return_time
    elif type == 1:  # 장애인
        return_time *= 4
    elif type == 2:  # 고령자
        return_time *= 1.5
    elif type == 3:  # 임산부
        return_time *= 2
    elif type == 4:  # 영유아 동반
        return_time *= 1.5
    elif type == 5:  # 어린이
        return_time *= 1.5

    return return_time


def isExitCongested(stairs,capacity):
    return_value = False

    if stairs.servers.count > round(0.5*capacity):
        return_value=True

    return return_value


class Person:
    def __init__(self, env, name):
        self.env = env
        self.name = name
        self.exit_num = np.random.randint(0, num_exits)
        self.platform_num = np.random.randint(0, num_platform)
        self.type = np.random.choice(6, p=P_type)
        self.isHeatPlatform = random.choice([True, False])
        self.Evacuation_time = 0
        # type number - 0: 일반, 1: 장애, 2: 고령, 3: 임산부, 4: 영유아 동반, 5: 어린이

    def person_escape(self, env, exit, platform):
        # request shop capacity
        time_1=env.now
        if self.isHeatPlatform==True:
            platform.isCongested = isExitCongested(platform,5)
            arrival_time = env.now
            print("Person{0} arrives at the platform stairs{1} at".format(self.name, self.platform_num), arrival_time / 1000)
            with platform.servers.request() as req:
                fig.canvas.flush_events()
                yield req
                entering_time = env.now
                escape_time = stair_time(type, platform.isCongested)
                print("Person{0} enters the platform stairs at".format(self.name), self.env.now / 1000)
                yield env.process(platform.escape(escape_time))
            yield self.env.timeout(escape_time*19)
            leaving_time = env.now
            print("Person{0} leaves the platform{1} at".format(self.name, self.platform_num), leaving_time / 1000)
            yield self.env.timeout(TimetoPlatformtoExit())


        with exit.servers.request() as req:
            exit.isCongested = isExitCongested(exit,7)
            if env.now>30000:
                plt.text(1.5,4.5,'Fire Alarm sounded')
            print("Person{0} arrives at the exit{1} at".format(self.name, self.exit_num), env.now / 1000)
            x = np.random.rand(len(exit.servers.queue)) + self.exit_num
            y = 4 * np.random.rand(len(exit.servers.queue))
            if self.type == 0:
                colors = 'Black'
            else:
                colors = 'red'
            ax = plt.scatter(x, y, c=colors)
            yield req
            ax.set_visible(False)
            escape_time = stair_time(type, platform.isCongested)
            print("Person{0} enters the exit at".format(self.name), self.env.now / 1000)
            yield env.process(exit.escape(escape_time))
        yield self.env.timeout(escape_time * 19)
        leaving_time = env.now
        print("Person{0} leaves the exit{1} at".format(self.name, self.exit_num), leaving_time / 1000)
        time_2=env.now
        self.Evacuation_time=time_2-time_1


class Stairs:  # 출구
    def __init__(self, env, capacity):
        self.env = env
        self.servers = simpy.Resource(env, capacity=capacity)  # 한번에 지나갈 수 있는 사람 수
        self.isCongested = False

    def escape(self, stair_time):
        yield self.env.timeout(stair_time)


def setup(env, person):
    Platform = [Stairs(env, 5) for i in range(num_platform)]
    Exit = [Stairs(env, 7) for i in range(num_exits)]

    for i in range(len(person)):
        InterArrivalTime = IAT(env.now)
        yield env.timeout(InterArrivalTime)
        env.process(person[i].person_escape(env, Exit[person[i].exit_num],Platform[person[i].platform_num]))



env = simpy.Environment()
person = [Person(env, i) for i in range(num_people)]
env.process(setup(env, person))

env.run(until=SIM_TIME)