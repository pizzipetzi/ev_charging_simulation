class FlexBid:
    def __init__(self, bidder, price, auction_id, timestamp, psoc, soc):
            self.bidder = bidder
            self.auction_id = auction_id
            self.price = price
            self.timestamp = timestamp
            self.psoc = psoc
            self.soc = soc
            self.accepted = 0

    def update_acceptance(self):
        self.accepted = 1

    def update_not_acceptance(self):
        self.accepted = 2
