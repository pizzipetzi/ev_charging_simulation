from scipy.ndimage.filters import gaussian_filter1d
import random
import simpy
import numpy as np
from Car import Car
import settings
import Data
import pandas as pd
from Flex_Market import Flexmarket
from openpyxl import load_workbook
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt


time = []
charger_level = []
price = []
ample = []


def import_non_ev_loads():
    loads = []
    wb = load_workbook(filename='Powers_Transformer_Secondary_24hr.xlsx')
    sheet_ranges = wb['Powers']
    for i in range(2, settings.SIM_TIME+2):
        loads.append(int(sheet_ranges['L%d' % i].value))
    settings.DEMAND = loads


def price_over_time(env, price):
    while True:
        if len(settings.MERIT_ORDER_TIMESERIES) == 0:
            price.append(0)
        else:
            price.append(settings.MERIT_ORDER_TIMESERIES[-1])
        yield env.timeout(1)


def charger_checker(env, time, cap, charger):
    while True:
        clock = 0
        clock += env.now
        time.append(clock)
        cap.append(charger.level)
        yield env.timeout(1)


def ampel_setter (env, charger):
    while True:
        if charger.level < settings.AMPEL_TRESHOLD:
            settings.AMPEL = settings.DSO_CAP
        else:
            settings.AMPEL = 0
        ample.append(settings.AMPEL)
        yield env.timeout(settings.AMPEL_TIMEOUT)


def car_monitor (env, car, list):
    while True:
        inner_list = []
        inner_list.append(car.name)
        inner_list.append(env.now)
        inner_list.append(car.start_of_charging)
        inner_list.append(car.state_of_charge)
        inner_list.append(car.charging)
        inner_list.append(car.latest_bid)
        inner_list.append(car.potential_state_of_charge)
        list.append(inner_list)
        yield env.timeout(1)


def plotter():
    gelbe_line = []
    rote_linie = []
    zeroline = []
    load_with_EV = []
    for clock in time:
        gelbe_line.append(3000)
        rote_linie.append(3800)
        zeroline.append(0)
        load_with_EV.append(settings.DEMAND[clock] + (settings.DSO_CAP - charger_level[clock]))

    plt.subplot(2, 2, 1)
    plt.title("GRID CAPACITY OVER SIMULATION TIME")
    plt.xlabel('time (min)')
    plt.ylabel('capacity (kW)')
    xsmoothed = gaussian_filter1d(load_with_EV, sigma=2)
    plt.plot(time, xsmoothed)
    ysmoothed = gaussian_filter1d(settings.DEMAND, sigma=2)
    plt.plot(time, ysmoothed)
    plt.plot(time, zeroline, color='white')
    plt.plot(time, rote_linie, color='red')
    # plt.plot(time, ampel)
    plt.plot(time, gelbe_line, color='green')

    # plot market price
    plt.subplot(2, 2, 2)
    plt.title("PRICE OVER SIMULATION TIME")
    plt.xlabel('time (min)')
    plt.ylabel('price (€)')
    plt.plot(time, gaussian_filter1d(price, sigma=2))


def soc_distribution():
    mean = settings.SOC_MEAN
    standart_deviation = settings.SOC_SD
    sample_size = 2000
    distribution = np.random.normal(mean, standart_deviation, sample_size)
    discrete_distribution = [int(i) for i in distribution if i >= 10 and i <= 100]
    return discrete_distribution


def start_of_charging_distribution():
    mean = settings.START_MEAN
    standart_deviation = settings.END_MEAN
    sample_size = 2000
    distribution = np.random.normal(mean, standart_deviation, sample_size)
    discrete_distribution = [int(i) for i in distribution if i >= 0 and i < 540]
    return discrete_distribution


def end_of_charging_distribution():
    mean = settings.END_MEAN
    standart_deviation = settings.END_SD
    sample_size = 2000
    distribution = np.random.normal(mean, standart_deviation, sample_size)
    discrete_distribution = [int(i) for i in distribution if i < 1440 and i > 540]
    return discrete_distribution


def data_export(cars, market, amount_cars, iterations, charger):
    df = pd.DataFrame(Data.return_car_values(cars, iterations))
    df2 = pd.DataFrame(Data.return_bid_values(settings.ALL_BIDS, iterations))
    df3 = pd.DataFrame(Data.return_market_values(time, price, iterations, charger))
    df4 = pd.DataFrame(car_values_over_time)
    df5 = pd.DataFrame(market.market_data)


    df.to_csv('cars.csv', mode='a',  encoding='utf-8', index=False)
    df2.to_csv('bids.csv', mode='a',  encoding='utf-8', index=False)
    df3.to_csv('market.csv', mode='a',  encoding='utf-8', index=False)
    df4.to_csv('car.csv', encoding='utf-8', index=False)
    df5.to_csv('flexmarket.csv', mode='a', encoding='utf-8', index=False)


def programm_execution(amount_cars, iterations):
    # Create environment and DSO contaier
    env = simpy.Environment()
    charger = simpy.Container(env, settings.DSO_CAP, init=settings.DSO_CAP)
    import_non_ev_loads()

    # start ampel monitor
    env.process(ampel_setter(env, charger))
    env.process(charger_checker(env, time, charger_level, charger))
    env.process(price_over_time(env, price))

    # create distributions
    soc = soc_distribution()
    start = start_of_charging_distribution()
    end = end_of_charging_distribution()

    # run cars and market
    cars = [Car(env=env, charger=charger, start=random.choice(start), soc=random.choice(soc), end=random.choice(end), name=i) for i in range(amount_cars)]
    market = Flexmarket(env, charger, cars)
    env.process(market.operate())
    for car in cars:
        env.process(car.operate())
        #env.process(car_monitor(env, car, car_values_over_time))

    # Execute!
    env.run(until=settings.SIM_TIME)

    #uncomment this for data export
    #data_export(cars, market, amount_cars, iterations, charger_level)

    plotter()
    plt.show()

def clear_lists():
    global time
    global charger_level
    global price
    global ample
    time = []
    charger_level = []
    price = []
    ample = []
    settings.ALL_BIDS = []
    settings.SELECTED_BIDS = []
    settings.MERIT_ORDER_TIMESERIES = []


if __name__ == '__main__':
    random.seed(0)
    np.random.seed(0)
    for i in range(1):
        programm_execution(1000, i)

