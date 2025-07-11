from tools import ANNONCES, POINTS_CONTRAT
from os import listdir
import numpy as np

class Player:
    def __init__(self, name):
        self.name = name
        self.score = 0
        self.team = 0
        self.cards = []

    def sort_cards(self):
        order = {'Cups': 0, 'Swords': 1, 'Tarot': 2, 'Wands': 3, 'Pentacles': 4}
        self.cards.sort(key= lambda card: (order.get(card.color), card.valeur))

    def get_cards(self):
        couleurs = {'Cups': [], 'Swords': [], 'Tarot': [], 'Wands': [], 'Pentacles': []}
        for cards in self.cards:
            couleurs[cards.color].append(cards)
        for color in couleurs:
            print(f"\n{couleurs[color]}")

    def __repr__(self):
        return f"Player(name={self.name}, score={self.score}, team={self.team}, cards={len(self.cards)})"
    
class Card:
    def __init__(self, nom):
        self.nom = nom
        if len(nom) > 2 and nom[2] == '-':
            self.color = 'Tarot'
            self.valeur = nom[:2]
        
        if nom[-2].isdigit():
            v = nom[-2:]
        else:
            v = nom[-1:]
        if nom[0] == 'C':
            self.color = 'Cups'
            self.valeur = v
        elif nom[0] == 'W':
            self.color = 'Wands'
            self.valeur = v
        elif nom[0] == 'S':
            self.color = 'Swords'
            self.valeur = v
        elif nom[0] == 'P':
            self.color = 'Pentacles'
            self.valeur = v
        elif nom[0] == 'T':
            self.color = 'Tarot'
            self.valeur = v


        # print(f"Card created: {self.nom}, Color: {self.color}, Value: {self.valeur}")
        self.valeur = int(self.valeur)
        self.selectionner = False
        self.nb_points = self.compute_nb_points()

    def compute_nb_points(self):
        if self.color == "Tarot":
            if self.valeur in (1, 21, 0):
                return 4.5
            return .5
        if self.valeur <= 10:
            return .5
        return self.valeur - 10 + .5

    def __repr__(self):
        return f"{self.valeur} de {self.color}"

class Hand:
    def __init__(self):
        self.cards = []
    
    def add_card(self, joueur, Carte):
        if self.valid(joueur, Carte):
            self.cards.append(Carte)

    def valid(self, joueur: Player, Carte: Card, printing=True):

        if Carte.color == 'Tarot': # Règle de montée à l'atout
            atouts_player = [c for c in joueur.cards if c.color == 'Tarot' and c.valeur != 0]
            atouts_hand = [c for c in self.cards if c.color == 'Tarot' and c.valeur != 0]
            if atouts_hand and atouts_player:
                highest_atout_player = max(atouts_player, key=lambda c: c.valeur)
                highest_atout_hand = max(atouts_hand, key=lambda c: c.valeur)
                if highest_atout_player.valeur > highest_atout_hand.valeur and Carte.valeur < highest_atout_hand.valeur:
                    if printing:
                        print(f"You must play a higher Tarot card than {highest_atout_player} if you have one.")
                    return False
                
        if not self.cards:
            return True # 1st Card
        if len(self.cards) == 1 and self.cards[-1].valeur == 0:
            return True  # Fool
        hand_color = self.cards[0].color
        if Carte.color == hand_color:
            return True  # same color
        for c in joueur.cards:
            if c.color == hand_color:
                if printing:
                    print(f"You must play a card of the same color ({hand_color}) if you have one.")
                return False # different color and he has the color asked
        if Carte.color == 'Tarot':
            return True # cutting with a Tarot card is allowed
        for c in joueur.cards:
            if c.color == 'Tarot':
                if printing:
                    print(f"You must play a Tarot card if you have one.")
                return False # he has Tarot cards
        return True # he doesn't have the color asked and he doesn't have Tarot cards
    
    def __repr__(self):
        return f"Hand({self.cards})"

class Deck :
    def __init__(self, cards):
        self.deck = []
        self.new_deck = cards

    def add_hand(self, hand : Hand):
        self.new_deck += hand.cards
        return None

    def draw_deck(self):
        cut = np.random.randint(78)
        self.deck = self.new_deck[cut:] + self.new_deck[:cut] 
        self.new_deck = []
        return self.deck

class Round:
    def __init__(self, players: Player, deck : Deck):
        self.players = players
        self.nb_players = len(players)

        self.annonce = None
        self.taker = None
        self.hand = None
        self.color_called = None
        self.poignee = None
        self.chelem = False

        self.deck = deck
        deck.draw_deck()
        self.chien = []
        self.ecart = []

        self.state = 0 # 0: annonce, 1: appel 2: ecart fait, 3 : jeu
        self.player_turn = 0
        
        self.attack = []
        self.defense = []
        self.team = {}

        self.points = {'attack': 0, 'defense': 0}
        self.bouts = {'attack': 0, 'defense': 0}

        self.distribute()
        for p in self.players:
            p.sort_cards()

    def announce(self, annonce, joueur: Player):
        if self.players.index(joueur) == self.player_turn:
            if annonce != 'Passe' and ANNONCES.index(annonce) > ANNONCES.index(self.annonce if self.annonce else 'Passe'):
                self.annonce = annonce
                self.taker = joueur
            self.player_turn += 1

        if self.annonce == 'Garde contre' or (self.player_turn == self.nb_players and self.annonce is not None):
            print(f"\nAnnouncement complete: {self.annonce} by {self.taker.name}")

            self.next_state()

        elif self.player_turn == self.nb_players:
            self.redistribute()

    def distribute(self):
        nb_chien = 3 if self.nb_players == 5 else 6
        sets = (78 - nb_chien)//3
        pos = np.random.choice(np.arange(1,sets), size = nb_chien, replace=False)
        e = 0
        joueur = 0
        for j in range(sets):
            if j in pos :
                self.chien.append(self.deck.deck[3*j+e])
                e+=1
            self.players[joueur%self.nb_players].cards += [self.deck.deck[3*j+e],self.deck.deck[3*j+e + 1],self.deck.deck[3*j+e + 2]]
            joueur += 1
        self.deck.new_deck = []
        for joueur in self.players:
            self.deck.new_deck += joueur.cards
        self.deck.new_deck += self.chien

    def redistribute(self):
        print("Redistributing cards...")
        for joueur in self.players:
            joueur.cards = []
        self.chien = []
        self.deck.draw_deck()
        self.player_turn = 0
        self.distribute()

    def next_state(self):
        if self.state == 3: # end of the round
            self.state = 4 
        elif self.state == 2: 
            self.state = 3 # jeu
            self.player_turn = 0
            print(f"Starting game with taker {self.taker.name} and announcement {self.annonce}")

        elif self.state == 0 and self.nb_players >= 5 :
            self.state = 1 # appel
            self.player_turn = self.players.index(self.taker)
        elif self.annonce in ('Prise', 'Garde'):
            self.state = 2 # direct chien
            print(f"\nle chien est {self.chien}")
            for Carte in self.chien:
                self.players[self.player_turn].cards.append(Carte)
            self.players[self.player_turn].sort_cards()
            self.player_turn = self.players.index(self.taker)
        elif self.annonce in ('Garde sans', 'Garde contre'):
            self.state = 3
            self.ecart = self.chien
            self.player_turn = 0
        else:
            print("Invalid state transition")
        # print(f"\nTransitioning to state {self.state}")

    def who_has_the_card(self, Carte: Card):
        for joueur in self.players:
            for player_card in joueur.cards:
                if player_card.color == Carte.color and player_card.valeur == Carte.valeur:
                    return joueur
        return None
    
    def remove_card(self, joueur: Player, Carte: Card):
        for player_card in joueur.cards:
            if player_card.color == Carte.color and player_card.valeur == Carte.valeur:
                joueur.cards.remove(player_card)
                return True
        return False
    
    def other_team(self,team):
        if team == 'attack':
            return 'defense'
        elif team == 'defense':
            return 'attack'
        else:
            raise ValueError("Invalid team name")


    def appel(self, joueur: Player, Carte: Card):
        if self.state == 1 and self.players.index(joueur) == self.player_turn: # bon joueur au bon état de la partie
            called_color = Carte.color
            if called_color == 'Tarot':
                print("You can't call a Tarot Card")
                return False
            called_value = Carte.valeur
            for c in range(called_value + 1, 15):
                for couleur in ['Cups', 'Wands', 'Swords', 'Pentacles']:
                    found = any((player_card.color == couleur and player_card.valeur == c) for player_card in joueur.cards)
                    if not found:
                        print(f"you can't call a {Carte.valeur} try higher")
                return False

            self.next_state()

            print(f"{joueur.name} a appelé {Carte.nom}")
            self.color_called = called_color
            for p in self.players:
                if p == self.taker or p == self.who_has_the_card(Carte):
                    self.attack.append(p)
                    self.team[p] = 'attack'
                else:
                    self.defense.append(p)
                    self.team[p] = 'defense'
            print(f"\nAttackers: {[p.name for p in self.attack]}")
            print(f"Defenders: {[p.name for p in self.defense]}")

            return True

    def do_ecart(self, joueur: Player, cartes: list, printing=True):

        if self.state == 2 and self.players.index(joueur) == self.player_turn:  # bon joueur au bon état de la partie
            if len(cartes) != len(self.chien):
                if printing:
                    print(f"You must select exactly {len(self.chien)} cards for the discard.")
                return False

            non_tarot_non_king_cards = [c for c in joueur.cards if c.color != 'Tarot' and c.valeur != 14]
            
            tarot_cards_in_ecart = [c for c in cartes if c.color == 'Tarot']
            king_cards_in_ecart = [c for c in cartes if c.valeur == 14]

            if king_cards_in_ecart:
                if printing:
                    print(f"You cannot discard Kings: {[c.nom for c in king_cards_in_ecart]}")
                return False
            
            # Vérifier qu'on ne met pas d'atouts si on a assez d'autres cartes
            if tarot_cards_in_ecart and (len(tarot_cards_in_ecart) + len(non_tarot_non_king_cards) > len(self.chien)):
                if printing:
                    print("You cannot discard Tarot cards when you have enough other cards available.")
                    print(f"You have {len(non_tarot_non_king_cards)} non-Tarot/non-King cards and need to discard {len(self.chien)} cards.")
                return False

            seen = set()
            for Carte in cartes:
                if Carte.color == 'Tarot' and (Carte.valeur == 0 or Carte.valeur == 1 or Carte.valeur == 21):
                    if printing:
                        print("You cannot discard 'bouts'")
                    return False
                if (Carte.color, Carte.valeur) in seen:
                    if printing:
                        print(f"{Carte.nom} has already been selected.")
                    return False
                seen.add((Carte.color, Carte.valeur))
                Found = False
                for player_card in joueur.cards:
                    if player_card.color == Carte.color and player_card.valeur == Carte.valeur:
                        Found = True
                        break
                if not Found:
                    if printing:
                        print(f"{Carte.nom} is not in your hand.")
                    return False

            self.ecart = cartes
            for Carte in cartes:
                self.remove_card(joueur, Carte)
            
            self.next_state()
            # print(f'le joueur {joueur.name} possède bien 15 cartes : {len(joueur.cards)}')
            return True
        
    def play_hand(self, joueur: Player, Carte: Card, printing=True):
        def aux_play():
            self.hand.add_card(joueur, Carte)
            self.remove_card(joueur, Carte)
            if printing:
                print(f"{joueur.name} played {Carte}")
            self.player_turn = (self.player_turn + 1) % self.nb_players
            
        if self.state == 3 and self.players.index(joueur) == self.player_turn and self.who_has_the_card(Carte) == joueur: # bon joueur au bon état de la partie qui a la cart qu'il veut jouer
            if self.hand is None: # first hand
                if Carte.color == self.color_called and Carte.valeur != 14:
                    if printing:
                        print(f"You cannot play a card of the called color ({self.color_called}) unless it is a King at the first hand")
                    return False
            if self.hand is None or len(self.hand.cards) == self.nb_players: #new hand
                self.hand = Hand()
                print(f"\nNew hand started by {joueur.name}.")
                aux_play()
                return True
            if not self.hand.valid(joueur, Carte, printing=printing):
                return False
            if len(self.hand.cards) == self.nb_players - 1: # last card of the hand
                aux_play()
                self.compute_points_and_more()
                return True
            else:
                aux_play()
                return True

    def compute_points_and_more(self): # after a hand
        def get_joueur_gagnant():
            if self.players[0].cards == [] and self.chelem and self.player_turn == self.players.index(self.taker) and self.hand.cards[0].valeur == 0:
                return self.taker

            color_hand = self.hand.cards[0].color
            atouts = [c for c in self.hand.cards if c.color == 'Tarot' and c.valeur != 0]
            if atouts:
                # biggest Tarot card wins (excluding the Fool)
                max_atout = max(atouts, key=lambda c: c.valeur)
                joueur_gagnant = self.hand.cards.index(max_atout)
            else:
                # if no Tarot cards, find the highest card of the called color
                color_cards = [c for c in self.hand.cards if c.color == color_hand]
                max_color_card = max(color_cards, key=lambda c: c.valeur)
                joueur_gagnant = self.hand.cards.index(max_color_card)
            return self.players[(joueur_gagnant + self.player_turn) % self.nb_players]

        if not len(self.hand.cards)== self.nb_players :
            print("Not enough cards played in this hand.")
            return False
        if self.players[0].cards == [] : # end of the game
            self.next_state()
        joueur_gagnant = get_joueur_gagnant()
        print(f"Hand cards: {self.hand.cards}")
        print(f"Player {joueur_gagnant.name} wins the hand.\n")

        if any(c.color == 'Tarot' and c.valeur == 0 for c in self.hand.cards) and (self.players[0].cards != [] or self.chelem) :
            excuse_player_index = next(i for i, c in enumerate(self.hand.cards) if c.color == 'Tarot' and c.valeur == 0)
            excuse_player = self.players[(excuse_player_index + self.player_turn) % self.nb_players]
            if self.team[joueur_gagnant] != self.team[excuse_player]:
                self.points[self.team[excuse_player]] += 4
                self.bouts[self.team[excuse_player]] += 1
                self.bouts[self.other_team(self.team[excuse_player])] -= 1
                p = sum(c.nb_points for c in self.hand.cards if c.color != 'Tarot' or c.valeur != 0) + 0.5
            else:
                p = sum(c.nb_points for c in self.hand.cards)
        else:
            p = sum(c.nb_points for c in self.hand.cards)
        
        bouts = [c for c in self.hand.cards if c.color == 'Tarot' and c.valeur in (1, 21, 0)]
        self.bouts[self.team[joueur_gagnant]] += len(bouts)
        self.points[self.team[joueur_gagnant]] += p

        self.player_turn = self.players.index(joueur_gagnant) # Update the player turn

        self.deck.add_hand(self.hand) # Add the hand to the deck of the next round

    def end_round(self):
        p = sum(c.nb_points for c in self.ecart)
        if self.annonce == 'Garde contre':
            self.points['defense'] += p
        else:
            self.points['attack'] += p
        assert self.points['attack'] + self.points['defense'] == 91, f"Total points should equal 91 here we have {self.points['attack']} + {self.points['defense']}"
        assert self.bouts['attack'] + self.bouts['defense'] == 3, f"Total bouts should equal 3 here we have {self.bouts['attack']} + {self.bouts['defense']}"
        print(f"\nRound ended. Attack points: {self.points['attack']}")
        print(f"Attack Bouts: {self.bouts['attack']}")
        if self.points['attack'] >= POINTS_CONTRAT[self.bouts['attack']]:
            print(f"Attack wins")
        else:
            print(f"Defense wins")




class Party:
    def __init__(self):
        self.players = []
        self.cards = []
        self.get_cards()
        np.random.shuffle(self.cards)
        print(f"Number of cards: {len(self.cards)}")
        self.deck = Deck(self.cards)
        self.round = None
        self.pos_first_player = -1
        self.pos_dead_players = []

    def add_player(self, joueur: Player):
        self.players.append(joueur)

    def create_Round(self, nb_player):
        if len(self.players) - len(self.pos_dead_players) != nb_player:
            self.pos_dead_players = np.random.choice(self.players, size = len(self.players) - nb_player, replace=False)

        self.pos_first_player = (self.pos_first_player + 1)% nb_player
        for i in range(len(self.pos_dead_players)):
            self.pos_dead_players[i]+=1

        round_players = [self.players[i] for i in range(len(self.players)) if i not in self.pos_dead_players]
        round_players = round_players[self.pos_first_player:] + round_players[:self.pos_first_player]

        self.round = Round(round_players, self.deck)

    def get_cards(self):
        for nompng in listdir('Image/Cards-png'):
            nom = nompng[:-4]
            if nom != 'CardBacks':
                self.cards.append(Card(nom))


