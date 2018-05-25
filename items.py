import random as rn


class Card:
    values = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    bw_values = values[::-1]
    suits = ['D', 'C', 'H', 'S']

    def __init__(self, card_num=None):
        if card_num is None:
            card_num = rn.randrange(52)
        self.card_num = card_num
        self.value, self._suit = divmod(card_num, 4)

    def get_value(self):
        """
        Get the value of the card as a string.
        :return: string representation of the value
        """
        return Card.values[self.value]

    def get_suit(self):
        """
        Get the suit of the card as a string.
        :return: string representation of the suit
        """
        return Card.suits[self._suit]

    def relative_to(self, that):
        """
        Compare the value of two cards, self and that. Aces are high
        :param that: Card object
        :return: 1 if self is higher, -1 if that is higher, 0 if cards have same value
        """
        if self.value > that.value:
            return 1
        elif self.value < that.value:
            return -1
        return 0


class Deck:
    def __init__(self):
        self._cards = range(52)
        rn.shuffle(self._cards)
        self._top_card = 0  # Represents the index of the next card

    def draw(self, num_of_cards=None):
        """
        Returns the next card as a Card or as a list of Cards if num_of_cards is not None
        Ensure first that there are enough cards by calling cards_remaining
        :param num_of_cards: number of cards to remove from the deck
        :return: card objects
        """
        start = self._top_card
        end = self._top_card + num_of_cards
        if num_of_cards is not None:
            self._top_card += num_of_cards
            return [Card(card) for card in self._cards[start:end]]
        else:
            self._top_card += 1
            return Card(self._cards[start])

    def cards_remaining(self):
        """
        Counts the number of cards remaining
        :return: number of cards that have not been drawn
        """
        return 52-self._top_card


class Hand:
    def __init__(self, cards):
        self.cards = cards  # list of Card objects

    def minus(self, that):
        """
        Set subtraction of hands
        :param that: Hand
        :return: Hand
        """
        return Hand([card for card in self.cards if card not in that.cards])

    def plus(self, that):
        """
        Union two hands. Should be cards from the same deck
        :param that: Hand
        :return: Hand
        """
        return Hand(self.cards + that.cards)

    def size(self):
        """
        Get the number of Cards in the hand
        :return: int
        """
        return len(self.cards)

    def sort(self, select=None):
        """
        Sorts the Hand in descending order. If select not None:
        :param select: int. The returned Hand will be of size select,
        and will be the highest cards in the original Hand
        :return: Hand
        """
        card_nums = [card.card_num for card in self.cards]
        card_nums.sort(reverse=True)
        cards = [Card(c_num) for c_num in card_nums]
        if select is not None:
            return Hand(cards[:select])
        return Hand(cards)

    def get_values(self, suit=None):
        """
        Returns list of strings like ['9', '9', '4', 'Q', '3', '2', '8']
        If clubs specified, returns ['4', '3', '2', '8'] (see next method)
        :param suit: String. Will ignore all cards that do not have this suit.
        :return: List of strings
        """
        if suit is None:
            return [card.get_value() for card in self.cards]
        return [card.get_value() for card in self.cards if card.get_suit() == suit]

    def get_strings(self):
        """
        Represent the Hand as a list of strings
        :return: List of strings like ['9S', '9D', '4C', 'QD', '3C', '2C', '8C']
        """
        return [card.get_value()+card.get_suit() for card in self.cards]

    def is_straight(self, suit=None):
        """
        Determine if hand contains a straight
        :param suit: String. Ignore cards that are not of this suit
        :return: Bool
        """
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
        """
        Determine if hand contains a straight flush
        :return: Bool
        """
        for suit in Card.suits:
            if self.is_straight(suit):
                return self.is_straight(suit)
        return False

    # Returns 5 card hand
    def is_flush(self):
        """
        Determine if hand contains a straight flush. If not, returns False.
        If so, returns the 5 cards with the same suit
        :return: False || Hand
        """
        for suit in Card.suits:
            if len(self.get_values(suit)) >= 5:
                mini_hand = Hand([card for card in self.cards if card.get_value() in self.get_values(suit)])
                return mini_hand.sort(5)
        return False

    def is_oak(self, blank):
        """
        Returns a _ card hand (all same value) that was in the original Hand. False if not possible.
        :param blank: int. how many of a kind are we talkin'?
        :return: False || (Hand, Hand). The first hand is the cards that have the same value. The other is the kickers.
        """
        for value in Card.bw_values:
            mini_hand = Hand([card for card in self.cards if card.get_value() == value])
            if mini_hand.size() == blank:
                kickers = self.minus(mini_hand).sort(5-blank)
                return mini_hand, kickers
        return False

    def is_full_house(self):
        """
        Returns the three carded hand and the two carded hand if there's a full house. False if not.
        :return: False || (Hand, Hand)
        """
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
        """
        Returns the two two carded hands, and the highest kicker.
        :return: False || (Hand, Hand, Hand)
        """
        first_pair_hand = False
        for value in Card.bw_values:
            mini_hand = Hand([card for card in self.cards if card.get_value() == value])
            if mini_hand.size() == 2:
                if first_pair_hand:
                    kicker = self.minus(mini_hand).minus(first_pair_hand).sort(1)
                    return first_pair_hand, mini_hand, kicker
                first_pair_hand = mini_hand
        return False

    def compare_kickers(self, that):
        """
        Determines which hand has a higher kicker
        :param that: Hand
        :return: 1 if self is higher, -1 if that is higher, 0 if Hands are equal in terms of values.
        """
        for j in range(self.size()-1):
            a = self.sort().cards[j].relative_to(that.sort().cards[j])
            if a:
                return a
        return self.sort().cards[-1].relative_to(that.sort().cards[-1])

    def showdown(self, that):
        """
        Compare the value of two Hands.
        :param that: Hand
        :return: 1 if self is higher, -1 if that is higher, 0 if Hands are of the same strength
        """
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
