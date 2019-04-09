import settings
import simpy


class Flexmarket(object):
    def __init__(self, env: simpy.Environment, charger: simpy.Container, cars):
        self.env = env
        self.charger = charger
        self.list_of_cars = cars
        for car in cars:
            car.set_market(self)
        self.current_bids = []
        self.selected_bids = []
        self.selected_cars =[]
        self.merit_order_price = [0]
        self.market_data = []

    def cars_willing_to_charge(self) -> int:
        return len([car.name for car in self.list_of_cars if car.car_wants_to_bid()])

    def cars_currently_charging(self):
        return [car for car in self.list_of_cars if car.charging]

    def available_charging_slots(self) -> int:
        current_cap = settings.DSO_CAP - settings.DEMAND[self.env.now]
        current_max_cars = (current_cap / settings.WALLBOX_CAP)
        return int(current_max_cars)

    def operate(self):
        while True:
            bids = [car.create_bid() for car in self.list_of_cars if car.car_wants_to_bid()]

            self.selected_bids = []

            sorted_bid_list = sorted(bids, key=lambda x: x.price, reverse=True)
            flex_cars_needed = self.cars_willing_to_charge() + len(self.cars_currently_charging()) - \
                               self.available_charging_slots()

            self.market_data.append([self.env.now, self.available_charging_slots(), len(self.cars_currently_charging()),
                                     flex_cars_needed, self.cars_willing_to_charge(), len(sorted_bid_list)])

            if flex_cars_needed > 0:
                self.create_selected_flex_cars_list(flex_cars_needed, sorted_bid_list)
            else:
                for bid in sorted_bid_list:
                    bid.update_not_acceptance()
                settings.MERIT_ORDER_TIMESERIES.append(0)
                self.selected_bids = []

            #assert len(bids) == len(sorted_bid_list), 'len_sorted is wrong'
            #assert self.bid_test(bids), 'bid is 0'
            yield self.env.timeout(1)

    def create_selected_flex_cars_list(self, flex_cars_needed, sorted_bid_list):
        self.selected_bids = sorted_bid_list[:flex_cars_needed]
        not_selected_bids = sorted_bid_list[flex_cars_needed:]
        for bid in not_selected_bids:
            bid.update_not_acceptance()
        for bid in self.selected_bids:
            bid.update_acceptance()
            settings.SELECTED_BIDS.append(bid)
        if len(self.selected_bids) > 0:
            settings.MERIT_ORDER_TIMESERIES.append(self.selected_bids[-1].price)
        else:
            settings.MERIT_ORDER_TIMESERIES.append(0)

    def bid_test(self, bid_list):
        for bid in bid_list:
            if bid.accepted == 2 or 1:
                return True


