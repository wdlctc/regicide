from regicide_card import RegicideCard

class RegicideHand(object):
    def __init__(self, game, desk, discard_desk):
        """Creates a RegicideHand object.

        Args:
            game: A game instance, containing information about the game configuration.
            desk: A desk instance representing the draw pile.
            discard_desk: A desk instance representing the discard pile.
        """
        self._desk = desk
        self._discard_desk = discard_desk
        self._game = game
        self._hand_size = game.hand_size()
        self._hand = [desk.dealCard() for _ in range(game.hand_size())]

    def total_value(self):
        """ return the all enemy's health"""
        return sum(list(map(lambda x: x.value(), self._hand)))

    def valid(self, index):
        return 0 <= index < len(self._hand)

    def card(self, index):
        """Returns the card at the given index in the hand.
        """
        return self._hand[index]

    def empty(self):
        """Checks if the hand is empty.
        """
        return len(self._hand) == 0

    def full(self):
        """Checks if the hand is full.
        """
        return len(self._hand) == self._hand_size

    def pop(self, i):
        """Pops a card from the hand at the specified index."""
        if not 0 <= i < len(self._hand):
            raise ValueError("%d is not a valid card index."%i)
        card = self._hand.pop(i)
        return card

    def removefromhand(self, card):
        """remove the specified card from the hand."""
        if not card in self._hand:
            raise ValueError("%s is not a valid card index."%card)
        card = self._hand.remove(card)
        return card

    def addcard(self, card): 
        """Appends the specified card to the hand."""
        self._hand.append(c)

    def drawcard(self):
        """Draws a card from the desk and adds it to the hand if it's not full."""
        if self._desk.empty() or self.full() :
            return
        card = self._desk.dealCard()
        self._hand.append(card)

    def discardcard(self, i):
        """Discards a card from the hand to the discard desk."""
        if not 0 <= i < len(self._hand):
            raise ValueError("%d is not a valid card index."%i)
        card = self._hand.pop(i)
        self._discard_desk.placecard(card)
        return card

    def card_in_hand(self, card_info):
        """Check whether the specified card is hold in hand."""
        for card in self._hand:
            if card.info() == card_info:
                return True
        return False

    def pop_card_in_hand(self, card_info):
        """pop the specified card from hand."""
        for i in range(len(self._hand)):
            if self._hand[i].info() == card_info:
                card = self._hand.pop(i)
                return card
        return False

    def sort(self): self._hand.sort(key=lambda card: card.key())

    def __len__(self): 
        return len(self._hand)

    def __str__(self):
        return "".join([c.__str__() + '|' for c in self._hand])

    def __repr__(self):
        return str(self)