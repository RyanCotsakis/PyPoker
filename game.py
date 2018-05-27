from items import *
from learning import *
import random as rn

STARTING_AMOUNT = 500
SB = 1.0
BB = 2.0


class Player:
    number_of_players = 0

    def __init__(self, recorder=None, human=False, randomize=False):
        self._chips = STARTING_AMOUNT
        self.randomize = randomize
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
                bet_size = max(call_up_to-self.pushed(), BB, int(total_pot*chance/4))
                if decision == 2:
                    bet_size *= 2
                if decision == 3:
                    bet_size *= 4
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
        if board is not None:
            combined_hand = hand.plus(board)  # Hand object (not for NN)
            amount_of_one_suit = max([len(combined_hand.get_values(suit)) for suit in Card.suits])
            amount_of_one_suit_board = max([len(board.get_values(suit)) for suit in Card.suits])
            board_values = [c.value for c in board.sort().cards]
            x = np.array([0,  # decision parameter
                          # Measured in BBs
                          pushed,
                          pot,
                          call_up_to,
                          stack,
                          opponent_stack,
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
                          int(bool(board.is_oak(2))),
                          int(bool(board.is_two_pair())),
                          int(bool(board.is_oak(3))),
                          int(bool(board.is_straight())),
                          int(bool(board.is_flush())),
                          int(bool(board.is_full_house())),
                          int(bool(board.is_oak(4))),
                          int(bool(board.is_straight_flush())),
                          # Counting Suits
                          amount_of_one_suit_board,
                          amount_of_one_suit,
                          # Card Values
                          high_card,
                          low_card,
                          ] + board_values)
        else:
            board_values = []
            amount_of_one_suit = max([len(hand.get_values(suit)) for suit in Card.suits])
            x = np.array([0,  # decision parameter
                          # Measured in BBs
                          pushed,
                          pot,
                          call_up_to,
                          stack,
                          opponent_stack,
                          # True or False
                          dealer,
                          int(bool(hand.is_oak(2))),
                          # Counting Suits
                          amount_of_one_suit,
                          # Card Values
                          high_card,
                          low_card
                          ])
        x.reshape((1, x.size))

        if WATCH_AI:
            print '~\t{}'.format(x)
            print "~\tHand: {}".format(self.hand.get_strings())

        random_decision = rn.randint(-1, 3)
        if len(board_values) == 0:  # PREFLOP
            x[0] = decision_parameter(x, preflop_model)
            if self.recorder is not None and self.recorder.name == PREFLOP_NAME:
                if self.randomize:
                    x[0] = random_decision
                self.recorder.x.append(x)
                self.recorder.y_before.append(self.chips())
        elif len(board_values) == 3:  # FLOP
            x[0] = decision_parameter(x, flop_model)
            if self.recorder is not None and self.recorder.name == FLOP_NAME:
                if self.randomize:
                    x[0] = random_decision
                self.recorder.x.append(x)
                self.recorder.y_before.append(self.chips())
        elif len(board_values) == 4:  # TURN
            x[0] = decision_parameter(x, turn_model)
            if self.recorder is not None and self.recorder.name == TURN_NAME:
                if self.randomize:
                    x[0] = random_decision
                self.recorder.x.append(x)
                self.recorder.y_before.append(self.chips())
        else:  # RIVER
            x[0] = decision_parameter(x, river_model)
            if self.recorder is not None and self.recorder.name == RIVER_NAME:
                if self.randomize:
                    x[0] = random_decision
                self.recorder.x.append(x)
                self.recorder.y_before.append(self.chips())
        if call_up_to == 0 and x[0] == -1:
            return 0  # Don't fold when you can just call
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


def start_games(n, data_name='test', save_data=False, human=False, randomize=False):
    """
    :param randomize: Bool. Fed to the computer player as an input
    :param n: Number of games to be played
    :param data_name: String. if save_data: the x and y training data is saved under data/data_name.pkl
    :param save_data: Bool. Save and overwrite data/data_name.pkl with data from these games
    :param human: Bool. Play as a human against the computer
    """
    r = Recorder(data_name)
    player_1 = Player(recorder=r, randomize=randomize)
    player_2 = Player(human=human)

    for j in range(n):
        if player_2.human or j % 100 == 99:
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

        r.y_after = player_1.chips()
        r.add_to_list()

    # Done playing all the games
    if save_data:
        r.save()


def train_model(name, epochs=500, new_games=False, number_of_games=5000):
    print 'Training: ' + name
    try:
        model = load_model(model_folder + name + '.h5')
    except IOError:
        print 'Could not find ' + model_folder + name + '.h5'
        start_games(number_of_games, name, save_data=True, randomize=True)
        create_model(name, epochs=epochs)
        return

    if new_games:
        start_games(number_of_games, name, save_data=True, randomize=True)
    create_model(name, epochs=epochs, model=model)


if __name__ == '__main__':
    # start_games(10, human=True)

    # --- TRAIN ---
    river_model = None
    turn_model = None
    flop_model = None
    train_model(PREFLOP_NAME, new_games=True)
    try:
        flop_model = load_model(model_folder + FLOP_NAME + '.h5')
    except IOError:
        flop_model = None
    train_model(FLOP_NAME, new_games=True)
    try:
        turn_model = load_model(model_folder + TURN_NAME + '.h5')
    except IOError:
        turn_model = None
    train_model(TURN_NAME, new_games=True)
    try:
        river_model = load_model(model_folder + RIVER_NAME + '.h5')
    except IOError:
        river_model = None
    train_model(RIVER_NAME, new_games=True)
