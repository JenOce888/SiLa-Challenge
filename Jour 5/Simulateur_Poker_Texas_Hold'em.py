import random
from collections import Counter
from itertools import combinations

#  CLASS: Card
class Card:
    VALUES = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    SUITS  = ['♠', '♥', '♦', '♣']

    def __init__(self, value, suit):
        self.value = value
        self.suit  = suit
        self.rank  = self.VALUES.index(value)  # numeric rank: 2→0, A→12

    def __repr__(self):
        return f"{self.value}{self.suit}"

    def ascii_art(self):
        v = self.value.ljust(2)
        s = self.suit
        return [
            "┌─────┐",
            f"│{v}   │",
            f"│  {s}  │",
            f"│   {v}│",
            "└─────┘"
        ]

    def __eq__(self, other): return self.rank == other.rank
    def __lt__(self, other): return self.rank <  other.rank


#  CLASS: Deck
class Deck:
    def __init__(self):
        self.cards = [
            Card(v, s)
            for s in Card.SUITS
            for v in Card.VALUES
        ]
        self.shuffle()

    def shuffle(self):
        random.shuffle(self.cards)

    def deal(self, n=1):
        if len(self.cards) < n:
            raise ValueError("Not enough cards left in the deck!")
        dealt      = self.cards[:n]
        self.cards = self.cards[n:]
        return dealt

    def __len__(self):
        return len(self.cards)


#  CLASS: Hand  (hand evaluation)
class Hand:
    HAND_RANKS = [
        "High Card", "One Pair", "Two Pair", "Three of a Kind",
        "Straight", "Flush", "Full House", "Four of a Kind",
        "Straight Flush", "Royal Flush"
    ]

    def __init__(self, cards):
        # cards: list of 5 to 7 Card objects
        self.cards = cards
        self.best_hand, self.best_combo = self._evaluate()

    def _evaluate(self):
        """Find the best 5-card hand from all combinations."""
        if len(self.cards) < 5:
            return (0, sorted(self.cards, reverse=True))

        best       = None
        best_combo = None

        for combo in combinations(self.cards, 5):
            score = self._score_5cards(list(combo))
            if best is None or score > best:
                best       = score
                best_combo = list(combo)

        return best, best_combo

    def _score_5cards(self, cards5):
        """Return a comparable score tuple for exactly 5 cards."""
        ranks   = sorted([c.rank for c in cards5], reverse=True)
        suits   = [c.suit for c in cards5]
        counter = Counter(ranks)
        freqs   = sorted(counter.values(), reverse=True)

        is_flush    = len(set(suits)) == 1
        is_straight = (len(set(ranks)) == 5 and ranks[0] - ranks[4] == 4)

        # Special case: wheel straight A-2-3-4-5
        if ranks == [12, 3, 2, 1, 0]:
            is_straight = True
            ranks = [3, 2, 1, 0, -1]  # Ace plays as 1

        # Royal Flush
        if is_flush and is_straight and ranks[0] == 12:
            return (9, ranks)
        # Straight Flush
        if is_flush and is_straight:
            return (8, ranks)
        # Four of a Kind
        if freqs == [4, 1]:
            quad = [r for r, f in counter.items() if f == 4]
            kick = [r for r, f in counter.items() if f == 1]
            return (7, quad + kick)
        # Full House
        if freqs == [3, 2]:
            trio  = [r for r, f in counter.items() if f == 3]
            pair  = [r for r, f in counter.items() if f == 2]
            return (6, trio + pair)
        # Flush
        if is_flush:
            return (5, ranks)
        # Straight
        if is_straight:
            return (4, ranks)
        # Three of a Kind
        if freqs == [3, 1, 1]:
            trio  = [r for r, f in counter.items() if f == 3]
            kicks = sorted([r for r, f in counter.items() if f == 1], reverse=True)
            return (3, trio + kicks)
        # Two Pair
        if freqs == [2, 2, 1]:
            pairs = sorted([r for r, f in counter.items() if f == 2], reverse=True)
            kick  = [r for r, f in counter.items() if f == 1]
            return (2, pairs + kick)
        # One Pair
        if freqs == [2, 1, 1, 1]:
            pair  = [r for r, f in counter.items() if f == 2]
            kicks = sorted([r for r, f in counter.items() if f == 1], reverse=True)
            return (1, pair + kicks)
        # High Card
        return (0, ranks)

    def hand_name(self):
        return self.HAND_RANKS[self.best_hand[0]]

    def __gt__(self, other): return self.best_hand >  other.best_hand
    def __eq__(self, other): return self.best_hand == other.best_hand

# CLASS: Player
class Player:
    def __init__(self, name, chips=1000, is_bot=False):
        self.name         = name
        self.chips        = chips
        self.is_bot       = is_bot
        self.hole_cards   = []   # the 2 private cards
        self.current_bet  = 0
        self.folded       = False
        self.all_in       = False

    def receive_cards(self, cards):
        self.hole_cards = cards

    def show_hand(self, hide=False):
        if hide or not self.hole_cards:
            return display_cards_ascii([None, None], hide=True)
        return display_cards_ascii(self.hole_cards, hide=hide)

    # ── Bot AI ──────────────────────────────────
    def bot_decision(self, amount_to_call, pot, community_cards):
        strength = self._estimate_hand_strength(community_cards)

        if amount_to_call == 0:
            if strength > 0.6:
                raise_amt = min(int(pot * 0.5), self.chips)
                return ('raise', raise_amt)
            return ('check', 0)

        pot_odds = amount_to_call / (pot + amount_to_call) if pot > 0 else 1

        if strength > 0.75:
            raise_amt = min(int(amount_to_call * 2), self.chips)
            return ('raise', raise_amt)
        elif strength > pot_odds:
            return ('call', min(amount_to_call, self.chips))
        elif strength > 0.3 and random.random() < 0.3:   # occasional bluff
            return ('call', min(amount_to_call, self.chips))
        else:
            return ('fold', 0)

    def _estimate_hand_strength(self, community_cards):
        """Return a 0–1 strength estimate for the bot."""
        all_cards = self.hole_cards + community_cards
        if len(all_cards) < 5:
            # Pre-flop: use hole-card ranks
            if len(self.hole_cards) < 2:
                return 0.0
            ranks   = sorted([c.rank for c in self.hole_cards], reverse=True)
            strength = (ranks[0] + ranks[1]) / 24.0
            if self.hole_cards[0].rank == self.hole_cards[1].rank:
                strength += 0.2   # pocket pair bonus
            if self.hole_cards[0].suit == self.hole_cards[1].suit:
                strength += 0.1   # suited bonus
            return min(strength, 1.0)

        h = Hand(all_cards)
        return h.best_hand[0] / 9.0   # normalize 0–9 → 0–1

    def reset_for_new_round(self):
        self.hole_cards  = []
        self.current_bet = 0
        self.folded      = False
        self.all_in      = False

    def __repr__(self):
        return f"{self.name} ({self.chips} chips)"

#  ASCII DISPLAY HELPERS

def display_cards_ascii(cards, hide=False):
    lines = [""] * 5
    for card in cards:
        if hide:
            art = ["┌─────┐", "│░░░░░│", "│░░░░░│", "│░░░░░│", "└─────┘"]
        else:
            art = card.ascii_art()
        for i in range(5):
            lines[i] += art[i] + " "
    return "\n".join(lines)

def separator(char="═", length=60):
    print(char * length)

def title_bar(text, char="═"):
    pad = (60 - len(text) - 2) // 2
    print(f"{'═'*pad} {text} {'═'*(60-pad-len(text)-2)}")


#  MONTE CARLO SIMULATION

def monte_carlo(hole_cards, community_cards, num_players=2, simulations=1000):
    """
    Estimate win probability by simulating random runouts.
    Returns a float between 0 and 1.
    """
    wins = 0
    known = set((c.value, c.suit) for c in hole_cards + community_cards)

    remaining = [
        Card(v, s)
        for v in Card.VALUES
        for s in Card.SUITS
        if (v, s) not in known
    ]

    for _ in range(simulations):
        deck = remaining.copy()
        random.shuffle(deck)

        # Complete the community cards
        needed   = 5 - len(community_cards)
        board    = community_cards + deck[:needed]
        deck     = deck[needed:]

        # Evaluate our hand
        my_hand  = Hand(hole_cards + board)

        # Evaluate each opponent's hand
        won = True
        for _ in range(num_players - 1):
            opp_hand = Hand(deck[:2] + board)
            deck = deck[2:]
            if opp_hand > my_hand:
                won = False
                break

        if won:
            wins += 1

    return wins / simulations


#  GAME ENGINE

class PokerGame:
    def __init__(self, players):
        self.players       = players
        self.pot           = 0
        self.community     = []   # community cards on the board
        self.deck          = None
        self.small_blind   = 10
        self.big_blind     = 20
        self.dealer_idx    = 0

    # Round setup 
    def new_round(self):
        self.deck      = Deck()
        self.community = []
        self.pot       = 0

        for p in self.players:
            p.reset_for_new_round()
            p.receive_cards(self.deck.deal(2))

    # Display
    def display_state(self, reveal_all=False):
        separator()
        print(f"  POT: {self.pot} chips")
        separator()

        if self.community:
            print("\n  🃏 COMMUNITY CARDS:")
            print(display_cards_ascii(self.community))
        else:
            print("\n  🃏 No community cards yet")
        print()

        for p in self.players:
            status = ""
            if p.folded:  status = " [FOLDED]"
            elif p.all_in: status = " [ALL-IN]"

            print(f"\n  👤 {p.name} | Chips: {p.chips}{status}")
            if not p.folded:
                if not p.is_bot or reveal_all:
                    print(display_cards_ascii(p.hole_cards))
                else:
                    print(display_cards_ascii(p.hole_cards, hide=True))
        print()

    # Betting round 
    def betting_round(self, start_idx=0):
        current_bet = 0
        active      = [p for p in self.players if not p.folded and not p.all_in]
        if len(active) <= 1:
            return

        idx   = start_idx % len(self.players)
        turns = 0

        while turns < len(self.players) * 4:
            p = self.players[idx % len(self.players)]
            idx  += 1

            if p.folded or p.all_in:
                continue

            to_call = current_bet - p.current_bet

            if p.is_bot:
                action, amount = p.bot_decision(to_call, self.pot, self.community)
            else:
                action, amount = self._ask_human(p, to_call, current_bet)

            if action == 'fold':
                p.folded = True
                print(f"  {p.name} folds.")

            elif action == 'call':
                pay = min(to_call, p.chips)
                p.chips       -= pay
                p.current_bet += pay
                self.pot      += pay
                print(f"  {p.name} calls ({pay} chips).")

            elif action == 'check':
                print(f"  {p.name} checks.")

            elif action == 'raise':
                total = to_call + amount
                pay   = min(total, p.chips)
                p.chips       -= pay
                p.current_bet += pay
                self.pot      += pay
                current_bet    = p.current_bet
                print(f"  {p.name} raises by {amount} (total: {pay} chips).")

            elif action == 'allin':
                self.pot      += p.chips
                p.current_bet += p.chips
                if p.current_bet > current_bet:
                    current_bet = p.current_bet
                p.chips  = 0
                p.all_in = True
                print(f"  {p.name} goes ALL-IN ({p.current_bet} chips)!")

            # Check if everyone's bet is equal → end round
            active = [pp for pp in self.players if not pp.folded and not pp.all_in]
            if len(active) <= 1:
                break

            bets_equal = all(
                pp.current_bet == current_bet
                for pp in self.players
                if not pp.folded and not pp.all_in
            )
            if bets_equal and turns >= len(active):
                break

            turns += 1

    # Human input
    def _ask_human(self, player, to_call, current_bet):
        print(f"\n  {'─'*40}")
        print(f"  Your turn, {player.name}!")
        print(f"  Your chips: {player.chips} | To call: {to_call} | Pot: {self.pot}")

        # Show Monte Carlo win probability
        active_count = sum(1 for p in self.players if not p.folded)
        prob = monte_carlo(player.hole_cards, self.community, active_count, 500)
        print(f"  📊 Win probability (Monte Carlo): {prob*100:.1f}%")

        print(f"\n  Your hand:")
        print(display_cards_ascii(player.hole_cards))

        if to_call == 0:
            options = "check (c) | raise (r) | fold (f) | all-in (a)"
        else:
            options = "call (s) | raise (r) | fold (f) | all-in (a)"

        print(f"\n  Options: {options}")

        while True:
            choice = input("  Your choice: ").strip().lower()

            if choice in ['f', 'fold']:
                return ('fold', 0)
            elif choice in ['c', 'check'] and to_call == 0:
                return ('check', 0)
            elif choice in ['s', 'call'] and to_call > 0:
                return ('call', min(to_call, player.chips))
            elif choice in ['a', 'allin']:
                return ('allin', player.chips)
            elif choice in ['r', 'raise']:
                try:
                    amount = int(input("  Raise amount: "))
                    if amount > 0:
                        return ('raise', amount)
                except ValueError:
                    pass
            print("  Invalid choice. Try again.")

    # Determine winner 
    def determine_winner(self):
        active = [p for p in self.players if not p.folded]
        if len(active) == 1:
            return active, {}

        hands = {p: Hand(p.hole_cards + self.community) for p in active}
        ranked = sorted(active, key=lambda p: hands[p].best_hand, reverse=True)
        best   = hands[ranked[0]]
        winners = [p for p in active if hands[p] == best]
        return winners, hands

    # End of round 
    def _end_round(self):
        separator("═")
        title_bar("RESULTS")
        separator("═")

        active = [p for p in self.players if not p.folded]

        if len(active) == 1:
            winner = active[0]
            print(f"\n  🏆 {winner.name} wins the pot of {self.pot} chips!")
            winner.chips += self.pot
        else:
            winners, hands = self.determine_winner()

            print("\n  📋 Showdown:")
            for p in active:
                print(f"\n  {p.name}: {hands[p].hand_name()}")
                print(display_cards_ascii(p.hole_cards))

            print(f"\n  🃏 Community cards:")
            print(display_cards_ascii(self.community))

            share = self.pot // len(winners)
            for w in winners:
                w.chips += share
                print(f"\n  🏆 {w.name} wins {share} chips! ({hands[w].hand_name()})")

        self.dealer_idx = (self.dealer_idx + 1) % len(self.players)
        separator("═")
        print("\n  Current chip counts:")
        for p in self.players:
            print(f"    {p.name}: {p.chips}")
        separator("═")

    # Full round 
    def play_round(self):
        separator("═")
        title_bar("NEW ROUND")
        separator("═")

        self.new_round()

        # Post blinds
        sb_idx = (self.dealer_idx + 1) % len(self.players)
        bb_idx = (self.dealer_idx + 2) % len(self.players)
        sb, bb = self.players[sb_idx], self.players[bb_idx]

        sb_pay = min(self.small_blind, sb.chips)
        bb_pay = min(self.big_blind,   bb.chips)

        sb.chips -= sb_pay;  sb.current_bet = sb_pay;  self.pot += sb_pay
        bb.chips -= bb_pay;  bb.current_bet = bb_pay;  self.pot += bb_pay

        print(f"\n  Dealer : {self.players[self.dealer_idx].name}")
        print(f"  Small Blind: {sb.name} ({sb_pay})")
        print(f"  Big Blind  : {bb.name} ({bb_pay})")

        # PRE-FLOP
        title_bar("PRE-FLOP", "─")
        self.display_state()
        self.betting_round(start_idx=(bb_idx + 1) % len(self.players))

        if len([p for p in self.players if not p.folded]) <= 1:
            return self._end_round()

        # FLOP
        title_bar("FLOP", "─")
        self.community += self.deck.deal(3)
        for p in self.players: p.current_bet = 0
        self.display_state()
        self.betting_round(start_idx=sb_idx)

        if len([p for p in self.players if not p.folded]) <= 1:
            return self._end_round()

        # TURN
        title_bar("TURN", "─")
        self.community += self.deck.deal(1)
        for p in self.players: p.current_bet = 0
        self.display_state()
        self.betting_round(start_idx=sb_idx)

        if len([p for p in self.players if not p.folded]) <= 1:
            return self._end_round()

        # RIVER
        title_bar("RIVER", "─")
        self.community += self.deck.deal(1)
        for p in self.players: p.current_bet = 0
        self.display_state()
        self.betting_round(start_idx=sb_idx)

        return self._end_round()


# MAIN MENU
def main_menu():
    separator("═")
    title_bar("♠ TEXAS HOLD'EM POKER ♠")
    separator("═")
    print("""
  1. Play against bots
  2. Monte Carlo probability demo
  3. Quit
    """)
    return input("  Your choice: ").strip()

def play_mode():
    name = input("\n  Enter your name: ").strip() or "Player"

    all_bots = [
        Player("Bot_Alice",   1000, is_bot=True),
        Player("Bot_Bob",     1000, is_bot=True),
        Player("Bot_Charlie", 1000, is_bot=True),
    ]

    try:
        nb = int(input("  Number of bots (1-3, default=2): ").strip())
        nb = max(1, min(3, nb))
    except ValueError:
        nb = 2

    players = [Player(name, 1000, is_bot=False)] + all_bots[:nb]
    game    = PokerGame(players)

    while True:
        game.players = [p for p in game.players if p.chips > 0]

        if len(game.players) <= 1:
            if game.players:
                print(f"\n  🎉 GAME OVER! {game.players[0].name} wins the game!")
            break

        human = next((p for p in game.players if not p.is_bot), None)
        if not human:
            print("\n  You have been eliminated. Game over!")
            break

        game.play_round()

        again = input("\n  Play another round? (y/n): ").strip().lower()
        if again == 'n':
            break

def monte_carlo_demo():
    title_bar("MONTE CARLO SIMULATION DEMO")
    print()

    deck  = Deck()
    hole  = deck.deal(2)
    print("  Your hole cards:")
    print(display_cards_ascii(hole))

    print("\n  Win probabilities at each street:")
    for nb_community, street in [(0, "Pre-Flop"), (3, "Flop"), (4, "Turn"), (5, "River")]:
        community = deck.deal(nb_community) if nb_community > 0 else []
        if community:
            print(f"\n  {street} — Community cards:")
            print(display_cards_ascii(community))
        else:
            print(f"\n  {street}:")

        for nb_opp in [1, 2, 3]:
            prob = monte_carlo(hole, community, nb_opp + 1, 2000)
            print(f"    vs {nb_opp} opponent(s): {prob*100:.1f}%")

        # Reset deck for next street
        deck = Deck()
        hole = deck.deal(2)

def main():
    while True:
        choice = main_menu()
        if choice == '1':
            play_mode()
        elif choice == '2':
            monte_carlo_demo()
        elif choice == '3':
            print("\n  See you next time! 🃏\n")
            break
        else:
            print("  Invalid choice.")

if __name__ == "__main__":
    main()