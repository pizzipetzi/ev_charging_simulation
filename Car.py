import simpy
import settings
import random
import Bid

class Car(object):
    def __init__(self, env: simpy.Environment, charger: simpy.Container, name, soc, end, start):
        self.env = env
        self.name = name
        self.market = None
        self.charger = charger
        self.state_of_charge_start = soc
        self.state_of_charge = soc
        self.potential_state_of_charge = self.state_of_charge + 192
        self.charge_required = settings.SOC_FULL - self.state_of_charge
        self.time_to_full = (self.charge_required / settings.WALLBOX_CAP) * 60
        self.latest_bid = None
        self.start_of_charging = start
        self.end_of_charging = end
        self.charging = False
        self.flex_timeout = False
        self.break_even = random.uniform(5, 9)
        self.break_even_2 = random.uniform(5, 9)

    def set_market(self, market):
        self.market = market

    def increase_battery_state_of_charge(self):
        self.state_of_charge = self.state_of_charge + (settings.CHARGING_INTERVALL/60*settings.WALLBOX_CAP)
        self.charge_required = settings.SOC_FULL - self.state_of_charge
        self.time_to_full = (self.charge_required / settings.WALLBOX_CAP) * 60

    def create_bid(self):
        price = self.return_flex_price()
        auction_id = str(self.name) + "_" + str(self.env.now)
        bid = Bid.FlexBid(self.name, price, auction_id, self.env.now, self.potential_state_of_charge, self.state_of_charge)
        self.latest_bid = bid
        settings.ALL_BIDS.append(bid)
        return bid

    def return_flex_price(self):
        # what can be potentially charged in the remaining time [0, 193]
        potential_charge = ((self.end_of_charging - self.env.now) / 60 ) * settings.WALLBOX_CAP
        # what is the potential total charge of the car [0, 293]
        self.potential_state_of_charge = potential_charge + self.state_of_charge
        # price function with random steepness
        price = (self.break_even / self.potential_state_of_charge) + (self.break_even_2 / self.state_of_charge)
        return price

    def car_wants_to_bid(self) -> bool:
        if self.state_of_charge >= settings.SOC_FULL:
            return False
        if self.end_of_charging <= self.env.now:
            return False
        if self.start_of_charging > self.env.now:
            return False
        if self.flex_timeout:
            return False

        return not self.charging

    def operate(self):
            yield self.env.timeout(self.start_of_charging+1)
            assert self.env.now == self.start_of_charging+1, ('while loop was broken at %d' % self.env.now)
            while True:
                while True:
                    if self.car_wants_to_bid():
                        assert self.latest_bid.timestamp > (self.env.now - 30), \
                            'bid too old from %d at %d with bid-time %d' % \
                            (self.name, self.env.now, self.latest_bid.timestamp)
                        if self.latest_bid.accepted == 1:
                            self.flex_timeout = True
                            yield self.env.timeout(settings.FLEX_TIMEOUT-1)
                            self.flex_timeout = False
                            yield self.env.timeout(1)
                            break
                        if self.latest_bid.accepted == 2:
                            yield from self.charge()
                            break
                        assert self.latest_bid.accepted != 1 or 2, 'bid_accepted is 0'
                    assert self.soc_test(), ('soc = %d, time = %d, self.end = %d' %(self.state_of_charge, self.env.now, self.end_of_charging))
                    yield self.env.timeout(settings.SIM_TIME - self.env.now)

    def charge(self):
        self.charging = True
        yield self.charger.get(settings.WALLBOX_CAP)
        yield self.env.timeout(settings.CHARGING_INTERVALL)
        self.increase_battery_state_of_charge()
        self.charging = False
        yield self.charger.put(settings.WALLBOX_CAP)


    def soc_test(self):
        if self.state_of_charge >= 100 or self.env.now >= self.end_of_charging:
            return True
        else:
            return False

    def bid_test(self):
        if self.latest_bid is None:
            return True
        if self.latest_bid is not None:
            if self.latest_bid.timestamp != self.env.now - 1:
                return True
            else:
                return False
