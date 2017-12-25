from items import *

STARTING_AMOUNT = 100
SB = 1
BB = 2


class Player:
    def __init__(self):
        self.chips = STARTING_AMOUNT
        self.game = None
        self.hand = None
        self.pushed = 0
        self.folded = False

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
        decision = call_up_to  # TODO: Determine amount

        if decision < call_up_to:  # Fold
            self.folded = True
        elif decision >= 2 * call_up_to - self.pushed and decision >= BB + call_up_to:  # Raise
            self.bet(decision-self.pushed)
        else:  # Call
            self.bet(call_up_to - self.pushed)


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


if __name__ == '__main__':
    player_1 = Player()
    player_2 = Player()

    for i in range(10):
        this_game = Game(i)
        player_1.new_hand(this_game)
        player_2.new_hand(this_game)
        this_game.winner = None

        # Blinds
        sb_index = i % len(this_game.players)
        bb_index = (i + 1) % len(this_game.players)
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
            player_1.chips += this_game.pot/2
            player_2.chips += this_game.pot/2

        # TODO: is the rest necessary?
        this_game.pot = 0
        print player_1.get_hand().get_strings()
        print player_2.get_hand().get_strings()
        print player_1.chips
        print player_2.chips
