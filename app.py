from tools import ANNONCES
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from classes import Player, Card, Party

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

party = Party()
players = []
sockets_by_name = {}
game_started = False

def get_player(name):
    return next((p for p in players if p.name == name), None)

def emit_to_player(player, event, data=None):
    socketio.emit(event, data or {}, room=sockets_by_name[player.name])

def broadcast(event, data=None):
    socketio.emit(event, data or {})

def send_update_hand(player):
    emit_to_player(player, 'update_hand', {'cards': [c.nom for c in player.cards]})

def broadcast_players_list():
    broadcast('players', [p.name for p in players])

def start_round_with_players(num_players):
    global game_started
    if not game_started and len(players) >= num_players:
        game_started = True
        party.create_Round(num_players)
        for p in party.round.players:
            send_update_hand(p)
        broadcast('status', f"Partie démarrée avec {num_players} joueurs ! En attente des annonces…")
        broadcast('game_started')
        ask_announce_current()
    elif len(players) < num_players:
        emit_to_player(players[0], 'not_enough_players', {
            'msg': f"Pas assez de joueurs connectés ({len(players)}/{num_players})",
            'needed': num_players - len(players)
        })

def restore_player_state(player):
    if game_started and party.round:
        send_update_hand(player)
        broadcast('status', f"{player.name} s'est reconnecté")
        if party.round.state == 3:
            emit_to_player(player, 'start_game_phase')
        if party.round.hand and party.round.hand.cards:
            emit_to_player(player, 'update_current_hand', {
                'cards': [c.nom for c in party.round.hand.cards]
            })
        if party.round.players and player in party.round.players:
            current = party.round.players[party.round.player_turn]
            if current == player:
                if party.round.state == 0:
                    current_announce = party.round.annonce or 'Passe'
                    current_index = ANNONCES.index(current_announce)
                    valid_announces = ANNONCES[current_index + 1:] + ['Passe']
                    emit_to_player(player, 'ask_announce', {
                        'valid_announces': valid_announces,
                        'current_announce': current_announce
                    })
                elif party.round.state == 1:
                    emit_to_player(player, 'ask_appel')
                elif party.round.state == 2:
                    chien = [c.nom for c in party.round.chien]
                    emit_to_player(player, 'show_chien', {'chien': chien})
                    emit_to_player(player, 'ask_discard', {'num': len(chien)})
                elif party.round.state == 3:
                    emit_to_player(player, 'ask_play')

def ask_announce_current():
    current = party.round.players[party.round.player_turn]
    current_announce = party.round.annonce or 'Passe'
    current_index = ANNONCES.index(current_announce)
    valid_announces = ANNONCES[current_index + 1:] + ['Passe']
    emit_to_player(current, 'ask_announce', {
        'valid_announces': valid_announces,
        'current_announce': current_announce
    })

def handle_redistribution():
    party.round.redistributed = False
    broadcast('cards_redistributed', {
        'message': "Tout le monde a passé ! Redistribution des cartes…"
    })
    for p in party.round.players:
        send_update_hand(p)
    broadcast('status', "Nouvelles cartes distribuées ! Nouvelles annonces…")

def proceed_after_announce(player, announce):
    party.round.announce(announce, player)
    message = f"{player.name} annonce {announce}"
    if hasattr(party.round, 'chelem') and party.round.chelem and announce != 'Passe':
        message += " (avec chelem)"
    
    broadcast('status', message)
    
    if getattr(party.round, 'redistributed', False):
        handle_redistribution()
    if party.round.state == 0:
        ask_announce_current()
    elif party.round.state == 1:
        emit_to_player(party.round.players[party.round.player_turn], 'ask_appel')
    elif party.round.state == 2:
        chien = [c.nom for c in party.round.chien]
        broadcast('show_chien', {'chien': chien})
        taker = party.round.players[party.round.player_turn]
        send_update_hand(taker)
        emit_to_player(taker, 'ask_discard', {'num': len(chien)})
    else:
        ask_play_current()

def ask_play_current():
    current = party.round.players[party.round.player_turn]
    emit_to_player(current, 'ask_play')

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join')
def on_join(data):
    global game_started
    player_name = data['name']
    player = get_player(player_name)

    if player:
        sockets_by_name[player_name] = request.sid
        emit_to_player(player, 'reconnected', {'msg': 'Reconnexion réussie !'})
        broadcast('status', f"{player_name} s'est reconnecté")
        if players.index(player) == 0 and not game_started:
            emit_to_player(player, 'show_player_selector')
        restore_player_state(player)
    else:
        player = Player(player_name)
        players.append(player)
        sockets_by_name[player.name] = request.sid
        party.add_player(player)
        broadcast('status', f"{player_name} a rejoint la partie")
        if len(players) == 1 and not game_started:
            emit_to_player(player, 'show_player_selector')

    broadcast_players_list()

@socketio.on('start_game')
def on_start_game(data):
    player = get_player(data['player'])
    if player and players.index(player) == 0 and not game_started:
        start_round_with_players(data['num_players'])

@socketio.on('announce')
def on_announce(data):
    player = get_player(data['player'])
    if player:
        announce = data['announce']
        chelem = data.get('chelem', False)
        
        # Mettre à jour le chelem si nécessaire
        if chelem:
            party.round.chelem = True
            
        proceed_after_announce(player, announce)

@socketio.on('appel')
def on_appel(data):
    player = get_player(data['player'])
    if player:
        card = Card(data['card'])
        party.round.appel(player, card)
        broadcast('status', f"{player.name} appelle la carte {card.nom}")
        if party.round.state == 2:
            chien = [c.nom for c in party.round.chien]
            broadcast('show_chien', {'chien': chien})
            send_update_hand(player)
            emit_to_player(player, 'ask_discard', {'num': len(chien)})

@socketio.on('discard')
def on_discard(data):
    player = get_player(data['player'])
    if player:
        cards = [Card(n) for n in data['cards']]
        success, invalid_cards, errors = party.round.do_ecart(player, cards)
        if not success:
            emit_to_player(player, 'invalid_discard', {
                'msg': "\n".join(errors) if errors else "Écart invalide.",
                'invalid_cards': [c.nom for c in invalid_cards]
            })
            return
        broadcast('status', f"{player.name} a écarté ses cartes")
        broadcast('hide_chien')
        broadcast('start_game_phase')
        emit_to_player(player, 'discard_done')
        send_update_hand(player)
        ask_play_current()

@socketio.on('play_card')
def on_play_card(data):
    player = get_player(data['player'])
    if player:
        if not party.round.play_hand(player, Card(data['card'])):
            emit_to_player(player, 'invalid', {'msg': "Coup invalide."})
            return emit_to_player(player, 'ask_play')
        broadcast('update_current_hand', {'cards': [c.nom for c in party.round.hand.cards]})
        send_update_hand(player)
        broadcast('status', f"{player.name} joue {data['card']}")
        
        # Vérifier si le pli est terminé (tous les joueurs ont joué)
        if len(party.round.hand.cards) == len(party.round.players):
            # Envoyer l'information sur la carte gagnante
            if hasattr(party.round.hand, 'winning_card') and party.round.hand.winning_card:
                broadcast('highlight_winning_card', {
                    'winning_card': party.round.hand.winning_card.nom
                })
            
            # Envoyer le gagnant du pli
            if getattr(party.round.hand, 'winner', None):
                broadcast('hand_winner', {'player': party.round.hand.winner.name})
            
            # Vérifier si la partie est terminée
            if party.round.state == 4:
                party.round.end_round()
                scores = {p.name: p.score for p in players}
                broadcast('game_end', scores)
            else:
                ask_play_current()
        else:
            ask_play_current()

@socketio.on('disconnect')
def on_disconnect():
    disconnected = next((name for name, sid in sockets_by_name.items() if sid == request.sid), None)
    if disconnected:
        broadcast('status', f"{disconnected} s'est déconnecté")
        sockets_by_name.pop(disconnected, None)

if __name__ == '__main__':
    socketio.run(app, debug=True)
