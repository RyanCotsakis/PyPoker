from items import *
from learning import *
import random as rn

STARTING_AMOUNT = 500
SB = 1.0
BB = 2.0

WATCH_AI = False
RANDOMNESS = 0.5
preflop_model, flop_model, turn_model, river_model = load_all_models()

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
            decision = self.decide(call_up_to/BB, opponent_stack/BB)
            if decision > 0:
                chance = 0.9 + rn.random()/5
                total_pot = call_up_to+self.pushed()*2+self.game.pot()
                bet_size = max(call_up_to-self.pushed(), BB, int(total_pot*chance/3.))
                if decision == 2:
                    bet_size *= 3
            else:
                bet_size = decision
        else:
            print('Your chips: ${}'.format(self.chips()))
            print("Computer's chips: ${}".format(opponent_stack))
            print("You are the dealer: {}".format(not self.game.under_the_gun % 2))
            print('Pot: ${}'.format(self.game.pot() + self.pushed() + opponent_pushed))
            if self.game.board is not None:
                print('Board: {}'.format(self.game.board.get_strings()))
            else:
                print('Pre-Flop')
            print('Your hand: {}'.format(self.hand.get_strings()))
            print('${} to call...'.format(call_up_to - self.pushed()))
            bet_size = 0
            try:
                bet_size = int(raw_input("\tEnter a negative number to fold,\n"
                                         "\tor a positive number to indicate\n"
                                         "\thow much you'd like to raise by:\n\t"))
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
        board = self.game.board


        decision = None
        if board is not None:
            combined_hand = hand.plus(board)  # Hand object (not for NN)
            amount_of_one_suit = max([len(combined_hand.get_values(suit)) for suit in Card.suits])
            amount_of_one_suit_board = max([len(board.get_values(suit)) for suit in Card.suits])
            board_values = [c.value for c in board.sort().cards]

            bools = [
                      int(bool(combined_hand.is_oak(2))),
                      int(bool(combined_hand.is_two_pair())),
                      int(bool(combined_hand.is_oak(3))),
                      int(bool(combined_hand.is_straight())),
                      int(bool(combined_hand.is_flush())),
                      int(bool(combined_hand.is_full_house())),
                      int(bool(combined_hand.is_oak(4))),
                      int(bool(combined_hand.is_straight_flush())),
                      int(bool(board.is_oak(2))),
                      int(bool(board.is_two_pair())),
                      int(bool(board.is_oak(3))),
                      int(bool(board.is_straight())),
                      int(bool(board.is_flush())),
                      int(bool(board.is_full_house())),
                      int(bool(board.is_oak(4))),
                      int(bool(board.is_straight_flush()))
                    ]
            # bools = bools.reshape((len(bools),1))
            # bools = np.matmul(bools, bools.T).flatten()
            # bools = list(bools)
            x = np.array([decision,
                          1,  # for the intercept
                          pushed,
                          pot,
                          call_up_to,
                          stack,
                          opponent_stack,
                          dealer,
                          amount_of_one_suit,
                          high_card,
                          low_card,
                          amount_of_one_suit_board,
                          ] + bools + board_values)
        else:  # Preflop
            board_values = []
            amount_of_one_suit = max([len(hand.get_values(suit)) for suit in Card.suits])
            x = np.array([decision,
                          1,
                          pushed,
                          pot,
                          call_up_to,
                          stack,
                          opponent_stack,
                          dealer,
                          amount_of_one_suit,
                          high_card,
                          low_card,
                          int(bool(hand.is_oak(2)))
                          ])
        if WATCH_AI:
            print '~\t{}'.format(x)
            print "~\tHand: {}".format(self.hand.get_strings())

        if len(board_values) == 0:  # PREFLOP
            decision = decision_parameter(x, preflop_model, verbose=WATCH_AI)
        elif len(board_values) == 3:  # FLOP
            decision = decision_parameter(x, flop_model, verbose=WATCH_AI)
        elif len(board_values) == 4:  # TURN
            decision = decision_parameter(x, turn_model, verbose=WATCH_AI)
        else:  # RIVER
            decision = decision_parameter(x, river_model, verbose=WATCH_AI)
        if call_up_to == pushed and decision == -1:
            decision = 0  # Don't fold when you can just call
        if self.recorder is not None:
            if rn.random() < RANDOMNESS:
                decision = rn.randint(-1, 3)
                if WATCH_AI:
                    print('~\tOverriding w/ random decision: {}'.format(decision))
            if call_up_to == pushed and decision == -1:
                decision = 0  # Don't fold when you can just call

            x[0] = decision
            self.recorder.x.append(x)
            self.recorder.y_before.append(self.chips())
        return decision


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

    def betting_round(self, stop_after):
        """
        Allow players to .act() until they have pushed the same amount of chips into the pot.
        :return: None
        Calls self.collect_chips() and possibly modifies self.winner
        """
        if self.board is not None and self.board.size() > stop_after:
            return

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



def start_games(n, stop_after=5, save_data_name=False, human=False):

    if not human and save_data_name:
        player_1 = Player(recorder=Recorder(save_data_name))
    else:
        stop_after = 5
        player_1 = Player()
    player_2 = Player(human=human)

    for j in range(n):
        if human or j % 1000 == 999:
            print "Game {}/{}".format(j+1, n)

        if player_1.chips() == 0 or player_2.chips() == 0:
            player_1.reset_chips()
            player_2.reset_chips()

        this_game = Game(j)
        player_1.new_hand(this_game)
        player_2.new_hand(this_game)

        # Blinds
        sb_index = j % len(this_game.players)
        bb_index = (j + 1) % len(this_game.players)
        this_game.players[sb_index].bet(SB)
        this_game.players[bb_index].bet(BB)

        this_game.betting_round(stop_after)

        if this_game.winner is None:
            flop = Hand(this_game.deck.draw(3))
            this_game.board = flop

            this_game.betting_round(stop_after)

            if this_game.winner is None:
                turn = Hand(this_game.deck.draw(1))
                this_game.board = this_game.board.plus(turn)

                this_game.betting_round(stop_after)

                if this_game.winner is None:
                    river = Hand(this_game.deck.draw(1))
                    this_game.board = this_game.board.plus(river)

                    this_game.betting_round(stop_after)

                    if this_game.winner is None:
                        result = player_1.get_hand().showdown(player_2.get_hand())
                        if player_2.human:
                            print 'Showdown: {}'.format(this_game.board.get_strings())
                        if result == 1:
                            this_game.winner = player_1
                        elif result == -1:
                            this_game.winner = player_2

        if this_game.winner is not None:
            this_game.winner.collect(this_game.pot())
        else:
            player_1.collect(this_game.pot() / 2)
            player_2.collect(this_game.pot() / 2)

        if player_2.human:
            print "End of game {}. Computer's hand was: {}".format(j + 1, player_1.hand.get_strings())
            print "Your chips: ${}".format(player_2.chips())
            print "Computer's chips: ${}\n".format(player_1.chips())

        if player_1.recorder is not None:
            player_1.recorder.y_after = player_1.chips()
            player_1.recorder.add_to_list()

    # Done playing all the games
    if save_data_name and player_1.recorder is not None:
        player_1.recorder.save()


# def create_data(name, n=8000):
#     if name == PREFLOP_NAME:
#         model = preflop_model
#         stop_after = 0
#     elif name == FLOP_NAME:
#         model = flop_model
#         stop_after = 3
#     elif name == TURN_NAME:
#         model = turn_model
#         stop_after = 4
#     elif name == RIVER_NAME:
#         model = river_model
#         stop_after = 5
#     else:
#         model = None
#         stop_after = 5
#     start_games(n, stop_after, save_data_name=name)


if __name__ == '__main__':
    WATCH_AI = False
    RANDOMNESS = 0.2

    for i in range(1):
        start_games(1000000, save_data_name="all_games")

        train_model(PREFLOP_NAME, data_name="all_games")
        train_model(FLOP_NAME, data_name="all_games")
        train_model(TURN_NAME, data_name="all_games")
        train_model(RIVER_NAME, data_name="all_games")

        preflop_model, flop_model, turn_model, river_model = load_all_models()

    # WATCH_AI = True
    # start_games(5, human=True)
