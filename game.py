from classes import *
import random

def game(players = [], announces = [], appel = None, ecart_auto = False, game_auto = False):
    party = Party()
    if players == []:
        player = "None"
        while player != "":
            player = input("Entrez le nom du joueur (ou appuyez sur Entrée pour commencer la partie) : ")
            if player != "":
                party.add_player(Player(player))
    else:
        for player in players:
            party.add_player(Player(player))

    party.create_Round(len(party.players))
    print("Joueurs de la partie :")
    print(party.round.players)

    if announces == []:
        while party.round.state == 0 : # announce
            while True:
                # party.round.players[party.round.player_turn].get_cards()
                annonce = input(f"Joueur {party.round.players[party.round.player_turn].name}, Entrez votre annonce (ou 'Passe' pour passer) : ")
                if annonce in ANNONCES:
                    party.round.announce(annonce, party.round.players[party.round.player_turn])
                    break
                else:
                    print("Annonce invalide. Veuillez réessayer.")
        print(f"Annonce finale : {party.round.annonce} par {party.round.taker.name}")

    else :
        for announce in announces:
            party.round.announce(announce, party.round.players[party.round.player_turn])
            
    ### print ###
    for player in party.round.players:
        print(f"{player.name} :")
        player.sort_cards()
        for card in player.cards:
            print(f"    - {card.nom} ({card.color}, {card.valeur})")
    print("Chien :")
    for card in party.round.chien:
        print(f"    - {card.nom} ({card.color}, {card.valeur})")
    ### print ###

    while party.round.state == 1:  # appel
        if appel is None:
            while True:
                appel_input = input(f"Joueur {party.round.players[party.round.player_turn].name}, Entrez votre carte à appeler par exemple Wands14 : ")
                try:
                    appel_card = Card(appel_input)
                    if party.round.appel(party.round.players[party.round.player_turn], appel_card):
                        print(f"Carte appelée : {appel_input}")
                        break
                    else:
                        print("Carte invalide. Veuillez réessayer.")
                except ValueError as e:
                    print(f"Format de carte invalide '{appel_input}'. Erreur: {e}")
                    print("Utilisez le format correct (ex: Wands02, Cups14, 01-TheMagician).")
                except (IndexError, AttributeError) as e:
                    print(f"Erreur lors de la création de la carte '{appel_input}': {e}")
                    print("Veuillez utiliser le format correct (ex: Wands02, Cups14, 01-TheMagician).")
        else:
            party.round.appel(party.round.players[party.round.player_turn], Card(appel))


    while party.round.state == 2:  # ecart
        if not ecart_auto:
            ecart = []
            while len(ecart) < len(party.round.chien):
                party.round.players[party.round.player_turn].get_cards()
                ecart_input = input(f"Joueur {party.round.players[party.round.player_turn].name}, Entrez les cartes à écarter (séparées par des espaces, par exemple Wands14 Swords05) : ")
                try:
                    ecart = [Card(card) for card in ecart_input.split()]
                    print(f"Cartes sélectionnées pour l'écart : {[card.nom for card in ecart]}")
                    if party.round.do_ecart(party.round.players[party.round.player_turn], ecart):
                        print(f"Cartes écartées : {[card.nom for card in ecart]}")
                        break
                    else:
                        print("Écart invalide. Veuillez réessayer.")
                except ValueError as e:
                    print(f"Format de carte invalide. Erreur: {e}")
                    print("Utilisez le format correct (ex: Wands02, Cups14, 01-TheMagician).")
                except (IndexError, AttributeError) as e:
                    print(f"Erreur lors de la création des cartes: {e}")
                    print("Veuillez utiliser le format correct (ex: Wands02, Cups14, 01-TheMagician).")
        else:
            ecart = party.round.players[party.round.player_turn].cards[:len(party.round.chien)]
            while not party.round.do_ecart(party.round.players[party.round.player_turn], ecart, printing=False):
                ecart = np.random.choice(party.round.players[party.round.player_turn].cards, size=len(party.round.chien), replace=False)
            print(f"Cartes écartées automatiquement : {[card.nom for card in ecart]}")
    if not game_auto:
        while party.round.state == 3:  # jeu
            print("\n" * 8)  # Clear screen effect
            party.round.players[party.round.player_turn].get_cards()
            print("\n" * 8)  # Clear screen effect
            hand = party.round.hand
            if hand and len(hand.cards) != party.round.nb_players:
                hand = hand.cards
            else:
                hand = []
            print(f"\nHand actuelle : {hand}")
            
            while True:
                play_card = input(f"Joueur {party.round.players[party.round.player_turn].name}, Entrez la carte à jouer (par exemple Wands14) : ")
                try:
                    card = Card(play_card)
                except ValueError as e:
                    print(f"Format de carte invalide '{play_card}'. Utilisez le format correct (ex: Wands02, Cups14, 01-TheMagician). Erreur: {e}")
                except (IndexError, AttributeError) as e:
                    print(f"Erreur lors de la création de la carte '{play_card}': {e}")
                    print("Veuillez utiliser le format correct (ex: Wands02, Cups14, 01-TheMagician).")
                if party.round.play_hand(party.round.players[party.round.player_turn], card):
                    break
    else:
        while party.round.state == 3:  # jeu
            player = party.round.players[party.round.player_turn]
            card = random.choice(player.cards)
            while not party.round.play_hand(player, card, printing=False):
                card = random.choice(player.cards)
            if len(party.round.hand.cards) == party.round.nb_players:
                pass
                # input("Appuyez sur Entrée pour continuer...")
    
    party.round.end_round()


if __name__ == "__main__":
    # Exemple d'utilisation
    players = ["Alice", "Bob", "Charlie", "David", "Eve"]
    announces = ["Passe", "Garde", "Passe", "Passe", 'Passe']
    appel = "Wands14"
    ecart_auto = True
    game_auto = True
    game(players, announces, appel, ecart_auto, game_auto)