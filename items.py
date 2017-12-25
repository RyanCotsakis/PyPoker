import random as rn


class Card:
    values = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    bw_values = values[::-1]
    suits = ['D', 'C', 'H', 'S']

    def __init__(self, card_num=None):
        if card_num is None:
            card_num = rn.randrange(52)
        self.card_num = card_num
        self.value, self.suit = divmod(card_num, 4)

    # Return string value
    def get_value(self):
        return Card.values[self.value]

    # Return string suit
    def get_suit(self):
        return Card.suits[self.suit]

    # 1: self is higher. -1: that is higher. 0: tie
    def relative_to(self, that):
        if self.value > that.value:
            return 1
        elif self.value < that.value:
            return -1
        return 0


class Deck:
    def __init__(self):
        self.cards = range(52)
        rn.shuffle(self.cards)
        self.top_card = 0  # Represents the index of the next card

    # Returns the next card as a Card or as a list of Cards if num_of_cards is not None
    # Ensure first that there are enough cards by calling cards_remaining
    def draw(self, num_of_cards=None):
        start = self.top_card
        end = self.top_card + num_of_cards
        if num_of_cards is not None:
            self.top_card += num_of_cards
            return [Card(card) for card in self.cards[start:end]]
        else:
            self.top_card += 1
            return Card(self.cards[start])

    def cards_remaining(self):
        return 52-self.top_card


class Hand:
    def __init__(self, cards):
        self.cards = cards  # list of Card objects

    # Subtracting the deck would result in an empty hand
    def minus(self, that):
        return Hand([card for card in self.cards if card not in that.cards])

    # Should be cards from the same deck
    def plus(self, that):
        return Hand(self.cards + that.cards)

    def size(self):
        return len(self.cards)

    # sorts hand in descending order. If select not None, returns select highest carded hand
    def sort(self, select=None):
        card_nums = [card.card_num for card in self.cards]
        card_nums.sort(reverse=True)
        cards = [Card(c_num) for c_num in card_nums]
        if select is not None:
            return Hand(cards[:select])
        return Hand(cards)

    # Returns list of strings like ['9', '9', '4', 'Q', '3', '2', '8']
    # If clubs specified, returns ['4', '3', '2', '8'] (see next method)
    def get_values(self, suit=None):
        if suit is None:
            return [card.get_value() for card in self.cards]
        return [card.get_value() for card in self.cards if card.get_suit() == suit]

    # Returns list of strings like ['9S', '9D', '4C', 'QD', '3C', '2C', '8C']
    def get_strings(self):
        return [card.get_value()+card.get_suit() for card in self.cards]

    # The following is_x methods return False, or groups of cards corresponding to what it found
    def is_straight(self, suit=None):
        consecutive = 0
        for value in ['A'] + Card.values:
            if value in self.get_values(suit):
                consecutive += 1
                if consecutive == 5:
                    # Will now return True
                    for card in self.cards:
                        if value == card.get_value():
                            return Hand([card])
            else:
                consecutive = 0
        return False

    # Returns single card hand
    def is_straight_flush(self):
        for suit in Card.suits:
            if self.is_straight(suit):
                return self.is_straight(suit)
        return False

    # Returns 5 card hand
    def is_flush(self):
        for suit in Card.suits:
            if len(self.get_values(suit)) >= 5:
                mini_hand = Hand([card for card in self.cards if card.get_value() in self.get_values(suit)])
                return mini_hand.sort(5)
        return False

    # Returns blank card hand (all same value) and a 5-blank sorted hand
    def is_oak(self, blank):
        for value in Card.bw_values:
            mini_hand = Hand([card for card in self.cards if card.get_value() == value])
            if mini_hand.size() == blank:
                kickers = self.minus(mini_hand).sort(5-blank)
                return mini_hand, kickers
        return False

    # Returns 3 card hand and a 2 card hand
    def is_full_house(self):
        two_hand = False
        three_hand = False
        for value in Card.bw_values:
            mini_hand = Hand([card for card in self.cards if card.get_value() == value])
            if mini_hand.size() == 3:
                three_hand = mini_hand
            elif mini_hand.size() == 2:
                two_hand = mini_hand
            if two_hand and three_hand:
                return three_hand, two_hand
        return False

    # Returns two 2 card hands and a 1 carded hand
    def is_two_pair(self):
        first_pair_hand = False
        for value in Card.bw_values:
            mini_hand = Hand([card for card in self.cards if card.get_value() == value])
            if mini_hand.size() == 2:
                if first_pair_hand:
                    kicker = self.minus(mini_hand).minus(first_pair_hand).sort(1)
                    return first_pair_hand, mini_hand, kicker
                first_pair_hand = mini_hand
        return False

    # Self and that should be sorted hands. Compares based on highest value
    def compare_kickers(self, that):
        for j in range(self.size()-1):
            a = self.cards[j].relative_to(that.cards[j])
            if a:
                return a
        return self.cards[-1].relative_to(that.cards[-1])

    # Returns 1 if better than that, -1 if worse, 0 if same
    def showdown(self, that):
        # Check straight flush
        for suit in Card.suits:
            mine = self.is_straight(suit)
            yours = that.is_straight(suit)
            if mine or yours:
                if mine and not yours:
                    return 1
                elif not mine and yours:
                    return -1
                return mine.compare_kickers(yours)

        # 4oak
        mine = self.is_oak(4)
        yours = that.is_oak(4)
        if mine or yours:
            if mine and not yours:
                return 1
            elif not mine and yours:
                return -1
            a = mine[0].compare_kickers(yours[0])
            if a:
                return a
            return mine[1].compare_kickers(yours[1])

        # Full House
        mine = self.is_full_house()
        yours = that.is_full_house()
        if mine or yours:
            if mine and not yours:
                return 1
            elif not mine and yours:
                return -1
            a = mine[0].compare_kickers(yours[0])
            if a:
                return a
            return mine[1].compare_kickers(yours[1])

        # Flush
        mine = self.is_flush()
        yours = that.is_flush()
        if mine or yours:
            if mine and not yours:
                return 1
            elif not mine and yours:
                return -1
            return mine.compare_kickers(yours)

        # Straight
        mine = self.is_straight()
        yours = that.is_straight()
        if mine or yours:
            if mine and not yours:
                return 1
            elif not mine and yours:
                return -1
            return mine.compare_kickers(yours)

        # 3oak
        mine = self.is_oak(3)
        yours = that.is_oak(3)
        if mine or yours:
            if mine and not yours:
                return 1
            elif not mine and yours:
                return -1
            a = mine[0].compare_kickers(yours[0])
            if a:
                return a
            return mine[1].compare_kickers(yours[1])

        # 2pair
        mine = self.is_two_pair()
        yours = that.is_two_pair()
        if mine or yours:
            if mine and not yours:
                return 1
            elif not mine and yours:
                return -1
            a = mine[0].compare_kickers(yours[0])
            if a:
                return a
            b = mine[1].compare_kickers(yours[1])
            if b:
                return b
            return mine[2].compare_kickers(yours[2])

        # pair
        mine = self.is_oak(2)
        yours = that.is_oak(2)
        if mine or yours:
            if mine and not yours:
                return 1
            elif not mine and yours:
                return -1
            a = mine[0].compare_kickers(yours[0])
            if a:
                return a
            return mine[1].compare_kickers(yours[1])

        # High Card
        mine = self.sort(5)
        yours = that.sort(5)
        return mine.compare_kickers(yours)


if __name__ == '__main__':
    for i in range(100):
        deck = Deck()
        board = Hand(deck.draw(5))
        hand1 = Hand(deck.draw(2)).plus(board)
        hand2 = Hand(deck.draw(2)).plus(board)
        print hand1.get_strings()
        print hand2.get_strings()
        print hand1.showdown(hand2)
