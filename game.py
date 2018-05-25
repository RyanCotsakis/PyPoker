from items import *

STARTING_AMOUNT = 100
SB = 1
BB = 2


class Player:
    number_of_players = 0

    def __init__(self):
        self.chips = STARTING_AMOUNT
        self.game = None
        self.hand = None
        self.pushed = 0
        self.folded = False
        self.id = Player.number_of_players
        Player.number_of_players += 1

    def new_hand(self, game):
        self.game = game
        self.hand = Hand(game.deck.draw(2))
        self.pushed = 0
        self.folded = False
        game.players.append(self)

    def get_hand(self):
        if self.game.board is not None:
            return self.hand.plus(self.game.board)
        return self.hand

    def bet(self, amount):
        bet_size = min(self.chips, amount)
        self.chips -= bet_size
        self.pushed += bet_size

    def act(self, call_up_to):
        # Things we're allowed to know:
        # everything in the Game, and the opponent's chip stack
        opponent_stack = 0  # Gets overwritten
        for p in self.game.players:
            if p.id != self.id:
                opponent_stack = p.chips
        decision = BB * self.decide(call_up_to/BB, opponent_stack/BB)
        if decision < call_up_to:  # Fold
            self.folded = True
        elif decision >= 2 * call_up_to - self.pushed and decision >= BB + call_up_to:  # Raise
            self.bet(decision-self.pushed)
        else:  # Call
            self.bet(call_up_to - self.pushed)

    def decide(self, call_up_to, opponent_stack):
        _hand = self.hand.sort()
        high_card = _hand.cards[0].value
        low_card = _hand.cards[1].value
        pushed = self.pushed/BB
        chips = self.chips/BB
        pot = self.game.pot/BB
        if self.game.board is not None:
            combined_hand = _hand.plus(self.game.board)
            _board_size = self.game.board.size()
            amount_of_one_suit_board = max([len(self.game.board.get_values(suit)) for suit in Card.suits])
            board_values = [c.value for c in self.game.board.cards]
        else:
            combined_hand = _hand
            _board_size = 0
            board_values = []
        amount_of_one_suit = max([len(combined_hand.get_values(suit)) for suit in Card.suits])

        # TODO:
        # Feed the variables without _preceding into the net (one net per stage of the game)
        # Bet what you think you're going to win, so the next training data is the result from this game played with
        # the result from the last net
        return 1


class Game:
    def __init__(self, utg):
        self.deck = Deck()
        self.pot = 0
        self.board = None
        self.players = []
        self.under_the_gun = utg
        self.winner = None

    def collect_chips(self):
        min_pushed = min([p.pushed for p in self.players])
        self.pot += min_pushed*len(self.players)
        for p in self.players:
            p.chips += p.pushed - min_pushed
            p.pushed = 0

    def betting_round(self):
        j = 0
        while True:
            if self.players[0].pushed == self.players[1].pushed and j >= len(self.players):
                break
            active_player_index = (self.under_the_gun + j) % len(self.players)
            max_bet = max([p.pushed for p in self.players])
            active_player = self.players[active_player_index]
            if active_player.chips == 0:
                break
            else:
                active_player.act(max_bet)

            # TODO: This only works for 2 players
            if self.players[0].folded:
                self.winner = self.players[1]
                break
            elif self.players[1].folded:
                self.winner = self.players[0]
                break
            j += 1
        self.collect_chips()


def start():
    player_1 = Player()
    player_2 = Player()

    for j in range(100):
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
            this_game.winner.chips += this_game.pot
        else:
            player_1.chips += this_game.pot / 2
            player_2.chips += this_game.pot / 2

        # TODO: is the rest necessary?
        this_game.pot = 0
        print player_1.get_hand().get_strings()
        print player_2.get_hand().get_strings()
        print player_1.chips
        print player_2.chips


if __name__ == '__main__':
    start()
