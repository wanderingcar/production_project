import simpy
import numpy as np
import random

SIM_TIME = 1000*60 * 30  # 초 단위로 30분


def IAT(time):  # 사람 간 간격
    if time <= 30:  # 화재 발생 초기에 사람들이 인지를 하는 시간 1분
        return np.random.exponential(scale=10)  # 약 20초에 1명 꼴
    elif 60 < time < 60 * 5:  # 화재가 발생한 사실을 사람들이 모두 알아 출구에 사람이 몰리는 시간
        return np.random.exponential(scale=1)  # 약 1초에 1명 꼴
    elif time >= 60 * 5:  # 사람들이 어느 정도 나간 후 아주 작은 수의 사람만 남은 경우
        return np.random.exponential(scale=60)  # 약 60초에 1명 꼴


def stair_time(congested=0):  # 1인당 계단 소요시간
    if congested == 0:
        return np.random.exponential(scale=20)  # 비혼잡시 평균 20초 소요
    else:
        return np.random.exponential(scale=30)  # 혼잡시 평균 30초 소요


class Person:
    def __init__(self, env, name):
        self.env = env
        self.name = name
        self.exit_num = random.randrange(0,3)

    def person(env,exit):
        a = env.now
        print("{0} arrives at the exit{1} at".format(self.name,self.exit_num), a)

        # request shop capacity
        with exit.servers.request() as req:
            yield req
            yield env.process(exit.escape(name))
            b = env.now
            print("{0} leaves the shop at".format(name), b)


class Exit:  # 출구
    def __init__(self, env, capacity):
        self.env = env
        self.servers = simpy.Resource(env, capacity=capacity)  # 한번에 지나갈 수 있는 사람 수
        self.repairing_time = stair_time()

    def escape(self, name):
        print("{0} enters the stair at".format(name), self.env.now)
        self.renew_parameter()
        yield self.env.timeout()
        print("Repairing done at", self.env.now)

    def renew_parameter(self):
        self.repairing_time = stair_time()


def setup(env):
    exit = [Exit(env, 60) for i in range(4)]

    customer_num = 0
    while True:
        customer_num += 1
        IAT = IAT()
        yield env.timeout(IAT)
        env.process(person(env, "Customer {0}".format(customer_num), exit[person.exit_num]))


env = simpy.Environment()
wayout = simpy.Resource(env, capacity=4)  # 출구 4개
env.process(setup(env))
person = [Person(env,i) for i in range(num_people)]

env.run(until=SIM_TIME)
