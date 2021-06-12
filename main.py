import simpy
import numpy as np

num_people = 0


def IAT():
    return np.random.exponential(scale=20)


def service_time():  # 1인당 대피 소요시간
    return np.random.exponential(scale=20)


class Person:  # 사람
    def __init__(self, env):
        self.env = env
        self.time = service_time()
        self.index = num_people

    def escape(self, env):
        yield self.env.timeout(self.time)
        print("")


class Exit:  # 출구
    def __init__(self, env):
        self.env = env


env = simpy.Environment()
wayout = simpy.Resource(env, capacity=4)  # 출구
