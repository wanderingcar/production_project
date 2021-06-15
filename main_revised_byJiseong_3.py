import simpy
import numpy as np
import random
SIM_TIME = 1000 * 60 * 3  # 초 단위로 30분

num_people = 1000
num_exits = 4
stair_breadth = 300

P_type = [0.703, 0.025, 0.164, 0.005, 0.04, 0.063]  # [일반, 장애인, 고령자, 임산부, 영유아 동반, 어린이], 2020년 교통안전정보관리시스템 기준
# https://tmacs.ts2020.kr/web/TW/weak01.jsp?mid=S3098

def IAT(time,person_index):  # 사람 간 간격
    return_time = 0  # 출력 시간
    if 0 <= time <= 30000:  # 화재 발생 초기에 사람들이 인지를 하는 시간 1분
        return_time = np.random.poisson(lam=2000)  # 약 2초에 1명 꼴
    elif person_index<0.9*num_people:  # 화재가 발생한 사실을 사람들이 모두 알아 출구에 사람이 몰리는 시간
        return_time = np.random.poisson(lam=100)  # 약 0.1초에 1명 꼴
    elif people_remaining>100:  # 사람들이 어느 정도 나간 후 아주 작은 수의 사람만 남은 경우
        return_time = np.random.poisson(lam=500)  # 약 2초에 1명 꼴
    else:  # 함수 입력 값이 잘못 된 경우 확인 문구 출력(시간이 음수이거나, 타입이 안맞거나...)
        print('Check the time value.')
    if return_time <= 0:  # 임의의 값이 0인 경우, 1으로 가정
        return_time = 1
    return return_time

def stair_time(type, congested):  # 1인당 계단 소요시간
    return_time = 0  # 출력 시간
    if congested:
        return_time = np.random.poisson(lam=5000)  # 혼잡시 평균 1초 소요
    else:
        return_time = np.random.poisson(lam=4000)  # 비혼잡시 평균 0.5초 소요
    if return_time <= 0:  # 임의의 값이 0인 경우, 1으로 가정
        return_time = 1
    if type == 0:  # 일반
        return_time = return_time
    elif type == 1:  # 장애인
        return_time *= 3
    elif type == 2:  # 고령자
        return_time *= 2
    elif type == 3:  # 임산부
        return_time *= 2.5
    elif type == 4:  # 영유아 동반
        return_time *= 1.5
    elif type == 5:  # 어린이
        return_time *= 1.5
    return return_time

def isExitCongested(arrival_time, entering_time):
    return_value = False
    waiting_time = entering_time - arrival_time
    if waiting_time > 0:
        return_value = True
    elif waiting_time < 0:
        print("Please re-check your program")
    return return_value

class Person:
    def __init__(self, env, name):
        self.env = env
        self.name = name
        self.exit_num = np.random.randint(0, num_exits)
        self.required_place = np.random.normal(40,3)+10
        self.type = np.random.choice(6, p=P_type)
        # type number - 0: 일반, 1: 장애, 2: 고령, 3: 임산부, 4: 영유아 동반, 5: 어린이

    def person_escape(self, env, exit):
        arrival_time = env.now
        print("Person{0} arrives at the exit{1} at".format(self.name, self.exit_num), arrival_time / 1000)
        # request shop capacity

        if exit.servers.level >= self.required_place: #server의 남은 여유공간이 개체의 요구공간보다 크다면 할당 수행
            entering_time = env.now
            exit.servers.get(self.required_place) #할당한 공간만큼 여유공간이 줄어듦
            escape_time = stair_time(type, exit.isCongested)
            yield env.process(exit.escape(self.name, escape_time))
            leaving_time = env.now
            print("Person{0} leaves the exit{1} at".format(self.name, self.exit_num), leaving_time / 1000)
            exit.servers.put(self.required_place) #개체가 빠져나간 뒤 여유공간이 다시 늘어남
            exit.isCongested = isExitCongested(arrival_time, entering_time)
        else:
            print("There's no enough place to enter the stairs")

class Exit:  # 출구
    def __init__(self, env, capacity):
        self.env = env
        self.servers = simpy.Container(env, capacity=capacity, init=capacity) #300cm의 여유공간. 초기에 300cm의 여유공간 존재
        self.isCongested = False
    def escape(self, name, stair_time):
        print("Person{0} enters the exit at".format(name), self.env.now / 1000)
        yield self.env.timeout(stair_time)

def setup(env, person):
    exit = [Exit(env,stair_breadth) for i in range(num_exits)]
    for i in range(len(person)):
        InterArrivalTime = IAT(env.now,i)
        yield env.timeout(InterArrivalTime)
        env.process(person[i].person_escape(env, exit[person[i].exit_num]))

env = simpy.Environment()
person = [Person(env, i) for i in range(num_people)]
env.process(setup(env, person))
env.run(until=SIM_TIME)