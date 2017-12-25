from items import *


class Network:
    def __init__(self, board_size):
        if board_size == 0:
            self.num_layers = len(sizes)
            self.sizes = sizes
            self.biases = [np.random.randn(y, 1) for y in sizes[1:]]
            self.weights = [np.random.randn(y, x)
                            for x, y in zip(sizes[:-1], sizes[1:])]



def decide(call_up_to, pushed, opponent_stack, stack, pot, hand, board_hand):
    high_card = hand.cards[0].value
    low_card = hand.cards[1].value

    if board_hand is not None:
        combined_hand = hand.plus(board_hand)
        board_size = board_hand.size()
        amount_of_one_suit_board = max([len(board_hand.get_values(suit)) for suit in Card.suits])
        board_values = [c.value for c in board_hand.cards]
    else:
        combined_hand = hand
        board_size = 0

    amount_of_one_suit = max([len(combined_hand.get_values(suit)) for suit in Card.suits])




    return 1
