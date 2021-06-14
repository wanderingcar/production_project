import simpy
import numpy as np
import random

SIM_TIME = 1000*60*3  # 초 단위로 30분
num_people = 800

P_mobility_handicapped=22.4
P_the_elder=round(P_mobility_handicapped/100*50.4)
P_infant_companion=round(P_mobility_handicapped/100*18.4)
P_children=round(P_mobility_handicapped/100*16.7)
P_the_disabled=round(P_mobility_handicapped/100*10.7)
P_the_pregnant=round(P_mobility_handicapped/100*3.8)

def IAT(time):  # 사람 간 간격
    return_time = 0   #출력 시간

    if 0 <= time <= 60000:  # 화재 발생 초기에 사람들이 인지를 하는 시간 1분
        return_time = np.random.poisson(lam = 2000)  # 약 2초에 1명 꼴
    elif 60000 < time < 60000 * 2:  # 화재가 발생한 사실을 사람들이 모두 알아 출구에 사람이 몰리는 시간
        return_time = np.random.poisson(lam = 100)  # 약 0.1초에 1명 꼴
    elif time >= 60000 * 2:  # 사람들이 어느 정도 나간 후 아주 작은 수의 사람만 남은 경우
        return_time = np.random.poisson(lam = 2000)  # 약 2초에 1명 꼴
    else:   #함수 입력 값이 잘못 된 경우 확인 문구 출력(시간이 음수이거나, 타입이 안맞거나...)
        print('Check the time value.')

    if return_time < 0:  #임의의 값이 0인 경우, 0으로 가정
        return_time = 1

    return return_time

def stair_time(congested):  # 1인당 계단 소요시간
    return_time = 0  # 출력 시간

    if congested:
        return_time = np.random.poisson(lam = 30000)  # 혼잡시 평균 30초 소요
    else:
        return_time = np.random.poisson(lam = 20000)  # 비혼잡시 평균 20초 소요

    if return_time < 0:  #임의의 값이 0인 경우, 0으로 가정
        return_time = 0

    return return_time

def isItTrue(probability):  # True 난수를 반환받기 위한 확률(백분율)
    p = random.choices(range(0, 2), weights=[probability,100-probability])
    if(p[0]==0):
        return True
    else:
        return False



class Person:
    def __init__(self, env, name):
        self.env = env
        self.name = name
        self.exit_num = random.randrange(0,4)

        self.mobility_handicapped=[False for i in range(5)]

        if(isItTrue(round(P_mobility_handicapped))): #교통약자인지 파악
            p=random.choices(range(0,5), weights=[P_the_elder,P_infant_companion,P_children,P_the_disabled,P_the_pregnant]) #교통약자인 경우 어떤 종류의 교통약자인지 파악. 두 개 이상의 항목에 동시 해당되는 경우는 없다고 가정.
            for i in range(5):
                if (p[0] == i):
                    self.mobility_handicapped[i]=True



    def person_escape(self,env,exit):
        arrival_time = env.now
        print("Person{0} arrives at the exit{1} at".format(self.name,self.exit_num), arrival_time/1000)

        # request shop capacity
        with exit.servers.request() as req:
            yield req
            entering_time = env.now
            yield env.process(exit.escape(self.name))
            leaving_time = env.now
            print("Person{0} leaves the exit{1} at".format(self.name,self.exit_num), leaving_time/1000)
            exit.isCongested=self.isExitCongested(arrival_time,entering_time)

    def isExitCongested(self,arrival_time,entering_time):
        return_value=False

        waiting_time=entering_time-arrival_time
        if(waiting_time>0):
            return_value=True
        elif(waiting_time<0):
            print("Please re-check your program")

        return return_value



class Exit:  # 출구
    def __init__(self, env, capacity):
        self.env = env
        self.servers = simpy.Resource(env, capacity=capacity)  # 한번에 지나갈 수 있는 사람 수
        self.isCongested = False
        self.repairing_time = stair_time(self.isCongested)

    def escape(self, name):
        print("Person{0} enters the exit at".format(name), self.env.now/1000)
        self.renew_parameter()
        yield self.env.timeout(self.repairing_time)

    def renew_parameter(self):
        self.repairing_time = stair_time(self.isCongested)

    def margin_mobility(self,mobility_handicapped):
        if(mobility_handicapped[0]==True): #노인인 경우
            self.repairing_time *= 2
        if (mobility_handicapped[1] == True):  # 영유아 동반자인 경우
            self.repairing_time *= 1.5
        if (mobility_handicapped[2] == True):  # 어린이인 경우
            self.repairing_time *= 1.5
        if (mobility_handicapped[3] == True):  # 장애인인 경우
            self.repairing_time *= 3
        if (mobility_handicapped[4] == True):  # 임산부인 경우
            self.repairing_time *= 2.5


def setup(env,person):
    exit = [Exit(env, 60) for i in range(4)]

    for i in range(len(person)):
        InterArrivalTime = IAT(env.now)
        yield env.timeout(InterArrivalTime)
        env.process(person[i].person_escape(env, exit[person[i].exit_num]))


env = simpy.Environment()
person = [Person(env,i) for i in range(num_people)]
env.process(setup(env,person))

env.run(until=SIM_TIME)