def return_car_values(list_of_cars, iterations):
    list = []
    for i in range(len(list_of_cars)):
        inner_list = []
        x = list_of_cars[i]
        inner_list.append(x.name)
        inner_list.append(x.state_of_charge)
        inner_list.append(x.potential_state_of_charge)
        inner_list.append(x.start_of_charging)
        inner_list.append(x.end_of_charging)
        inner_list.append(x.break_even)
        inner_list.append(iterations)
        list.append(inner_list)
    return list


def return_market_values(time, price, iterations, charger):
    list = []
    for i in range(len(time)):
        inner_list = []
        inner_list.append(time[i])
        inner_list.append(charger[i])
        inner_list.append(price[i])
        #inner_list.append(ampel[i])
        inner_list.append(iterations)
        list.append(inner_list)
    return list


def return_bid_values(list_of_bids, iterations):
    list = []
    for i in list_of_bids:
        inner_list = []
        inner_list.append(i.price)
        inner_list.append(i.bidder)
        inner_list.append(i.timestamp)
        #inner_list.append(i.psoc)
        inner_list.append(i.soc)
        inner_list.append(i.accepted)
        inner_list.append(iterations)
        list.append(inner_list)
    return list

