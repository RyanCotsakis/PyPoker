from items import *
from learning import *

STARTING_AMOUNT = 100
SB = 1
BB = 2


class Player:
    number_of_players = 0

    def __init__(self, recorder=None, human=False):
        self._chips = STARTING_AMOUNT
        self.human = human
        self.game = None
        self.hand = None
        self._pushed = 0
        self.folded = False
        self.id = Player.number_of_players
        self.recorder = recorder
        Player.number_of_players += 1

    def chips(self):
        return self._chips

    def pushed(self):
        return self._pushed

    def new_hand(self, game):
        """
        sits the player down at the table, and deals them two cards.
        :param game: Game
        """
        self.game = game
        self.hand = Hand(game.deck.draw(2))
        self._pushed = 0
        self.folded = False
        game.players.append(self)

    def reset_chips(self):
        self._chips = STARTING_AMOUNT

    def get_hand(self):
        """
        Get the combined hand
        :return: Hand
        """
        if self.game.board is not None:
            return self.hand.plus(self.game.board)
        return self.hand

    def bet(self, amount):
        """
        Bet up to amount. Move chips from stack to pushed
        :param amount: float
        """
        bet_size = min(self._chips, amount)
        self._chips -= bet_size
        self._pushed += bet_size

    def collect(self, amount):
        """
        Simply adds money to the chips, and resets pushed. DOES NOT TAKE MONEY FROM ANYWHERE!
        :param amount: float
        """
        self._chips += amount
        self._pushed = 0

    def act(self, call_up_to):
        """
        Call, bet, or fold, based on the result of the NN
        :param call_up_to: float. The total amount that needs to be pushed for a call.
        :return:
        """
        # Things we're allowed to know:
        # everything in the Game, and the opponent's chip stack
        opponent_stack = 0  # Gets overwritten
        opponent_pushed = 0
        for p in self.game.players:
            if p.id != self.id:
                opponent_stack = p.chips()
                opponent_pushed = p.pushed()

        if not self.human:
            # This is the input to the net that produced the highest output.
            bet_size = self.decide(call_up_to/BB, opponent_stack/BB) * max(call_up_to - self.pushed(), BB)
        else:
            print('\nYour stack: ${}'.format(self.chips()))
            print('Opponent Stack: ${}'.format(opponent_stack))
            print('Pot: ${}'.format(self.game.pot() + self.pushed() + opponent_pushed))
            if self.game.board is not None:
                print('Board: {}'.format(self.game.board.get_strings()))
            else:
                print('Pre-Flop')
            print('Your Hand: {}'.format(self.hand.get_strings()))
            print('${} to call...'.format(call_up_to - self.pushed()))
            bet_size = 0
            try:
                bet_size = int(raw_input("\nEnter a negative number to fold,\n"
                                         "or a positive number to indicate\n"
                                         "how much you'd like to raise by:\n"))
            except ValueError:
                pass
        if bet_size < 0:  # Fold
            self.folded = True
        elif bet_size > 0:  # Raise
            self.bet(call_up_to - self.pushed() + bet_size)
        else:  # Call
            self.bet(call_up_to - self.pushed())

    def decide(self, call_up_to, opponent_stack):
        """
        Uses Keras to make a decision based on many parameters.
        Feed into the network the parameters, as well as one of the X decision parameters. Do this X times, and see
        which yields the highest output.

        :param:
        call_up_to: number of big blinds that need to be pushed to call
        pushed: number of BBs that have already been pushed
        stack: BBs in stack
        opponent_stack: BBs in opponent's stack
        high_card: value of highest card in hand
        low_card: value of the other card in hand.

        :return: The decision parameter. -1: fold, 0: call/check, n>1: bet n*min_bet
        """
        hand = self.hand.sort()  # Hand object (not for NN)
        high_card = hand.cards[0].value
        low_card = hand.cards[1].value
        pushed = self.pushed() / BB
        stack = self.chips() / BB
        pot = self.game.pot()/BB
        dealer = (self.id - self.game.under_the_gun) % 2
        if self.game.board is not None:
            combined_hand = hand.plus(self.game.board)  # Hand object (not for NN)
            amount_of_one_suit_board = max([len(self.game.board.get_values(suit)) for suit in Card.suits])
            board_values = [c.value for c in self.game.board.sort().cards]
        else:
            combined_hand = hand
            amount_of_one_suit_board = 0
            board_values = []
        amount_of_one_suit = max([len(combined_hand.get_values(suit)) for suit in Card.suits])

        x = np.array([0,  # decision parameter
                      # Measured in BBs
                      pushed,
                      call_up_to,
                      stack,
                      opponent_stack,
                      pot,
                      # True or False
                      dealer,
                      int(bool(combined_hand.is_oak(2))),
                      int(bool(combined_hand.is_two_pair())),
                      int(bool(combined_hand.is_oak(3))),
                      int(bool(combined_hand.is_straight())),
                      int(bool(combined_hand.is_flush())),
                      int(bool(combined_hand.is_full_house())),
                      int(bool(combined_hand.is_oak(4))),
                      int(bool(combined_hand.is_straight_flush())),
                      # Counting Suits
                      amount_of_one_suit_board,
                      amount_of_one_suit,
                      # Card Values
                      high_card,
                      low_card,
                      ] + board_values)
        x.reshape((1, x.size))

        if len(board_values) == 0:  # PREFLOP
            x[0] = decision_parameter(x, preflop_model)
            if self.recorder is not None and self.recorder.name == PREFLOP_NAME:
                self.recorder.x.append(x)
            return x[0]
        elif len(board_values) == 3:  # FLOP
            x[0] = decision_parameter(x, flop_model)
            if self.recorder is not None and self.recorder.name == FLOP_NAME:
                self.recorder.x.append(x)
            return x[0]
        elif len(board_values) == 4:  # TURN
            x[0] = decision_parameter(x, turn_model)
            if self.recorder is not None and self.recorder.name == TURN_NAME:
                self.recorder.x.append(x)
            return x[0]
        else:  # RIVER
            x[0] = decision_parameter(x, river_model)
            if self.recorder is not None and self.recorder.name == RIVER_NAME:
                self.recorder.x.append(x)
            return x[0]


class Game:
    def __init__(self, utg):
        self.deck = Deck()
        self._pot = 0
        self.board = None
        self.players = []
        self.under_the_gun = utg
        self.winner = None

    def pot(self):
        return self._pot

    def collect_chips(self):
        """
        The minimum amount that was pushed is what goes into the pot from both players. The rest goes back to the
        player that pushed
        :return: None
        Modifies self.pot, player.pushed, player.chips
        """
        min_pushed = min([p.pushed() for p in self.players])
        self._pot += min_pushed * len(self.players)
        for p in self.players:
            p.collect(p.pushed() - min_pushed)

    def betting_round(self):
        """
        Allow players to .act() until they have pushed the same amount of chips into the pot.
        :return: None
        Calls self.collect_chips() and possibly modifies self.winner
        """
        j = 0
        while True:
            if self.players[0].pushed() == self.players[1].pushed() and j >= len(self.players):
                break
            active_player_index = (self.under_the_gun + j) % len(self.players)
            max_bet = max([p.pushed() for p in self.players])
            active_player = self.players[active_player_index]
            if active_player.chips() == 0:
                break
            else:
                active_player.act(max_bet)

            if self.players[0].folded:
                self.winner = self.players[1]
                break
            elif self.players[1].folded:
                self.winner = self.players[0]
                break
            j += 1
        self.collect_chips()


def start_games(n, data_name='test', save_data=False, human=False):
    r = Recorder(data_name)
    player_1 = Player(recorder=r)
    player_2 = Player(human=human)

    for j in range(n):
        if player_1.chips() == 0 or player_2.chips() == 0:
            player_1.reset_chips()
            player_2.reset_chips()
        r.y_before = player_1.chips()
        this_game = Game(j)
        player_1.new_hand(this_game)
        player_2.new_hand(this_game)

        # Blinds
        sb_index = j % len(this_game.players)
        bb_index = (j + 1) % len(this_game.players)
        this_game.players[sb_index].bet(SB)
        this_game.players[bb_index].bet(BB)

        this_game.betting_round()

        if this_game.winner is None:
            flop = Hand(this_game.deck.draw(3))
            this_game.board = flop

            this_game.betting_round()

            if this_game.winner is None:
                turn = Hand(this_game.deck.draw(1))
                this_game.board = this_game.board.plus(turn)

                this_game.betting_round()

                if this_game.winner is None:
                    river = Hand(this_game.deck.draw(1))
                    this_game.board = this_game.board.plus(river)

                    this_game.betting_round()

                    if this_game.winner is None:
                        result = player_1.get_hand().showdown(player_2.get_hand())
                        if result == 1:
                            this_game.winner = player_1
                        elif result == -1:
                            this_game.winner = player_2

        if this_game.winner is not None:
            this_game.winner.collect(this_game.pot())
        else:
            player_1.collect(this_game.pot() / 2)
            player_2.collect(this_game.pot() / 2)

        r.y_after = player_1.chips()
        r.add_to_list()

        print 'Game #{}'.format(j+1)

    # Done playing all the games
    if save_data:
        r.save()


if __name__ == '__main__':
    start_games(3, human=True)
