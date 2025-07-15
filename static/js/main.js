document.addEventListener('DOMContentLoaded', () => {
	const socket = io(),
		myName = prompt("Entrez votre nom :") || "Inconnu",
		$ = id => document.getElementById(id),
		setHTML = (id, html) => $(id).innerHTML = html,
		addDebug = msg => {
			const d = document.createElement('div');
			d.style = "font-size:12px;margin-bottom:5px;color:#666;";
			d.innerHTML = `<strong>${new Date().toLocaleTimeString()}:</strong> ${msg}`;
			$('debug-messages').appendChild(d);
			$('debug-messages').scrollTop = 1e9;
		};

	let selected = new Set();

	const createCard = name => Object.assign(document.createElement('img'), {
		src: `/static/Cards-png/${name}.png`,
		id: name,
		className: 'card'
	});

	const showControls = nodes => {
		const c = $('controls');
		c.innerHTML = '';
		(Array.isArray(nodes) ? nodes : [nodes]).forEach(n => c.appendChild(n));
	};

	const mkButton = (text, onClick) => {
		const b = document.createElement('button');
		b.innerText = text;
		b.onclick = onClick;
		return b;
	};

	const mkSelect = (options, id) => {
		const sel = document.createElement('select');
		if (id) sel.id = id;
		options.forEach(o => sel.appendChild(new Option(o.label || o, o.value ?? o)));
		return sel;
	};

	const showSelector = () => {
		const sel = mkSelect([3,4,5].map(n => ({ label: `${n} joueurs`, value: n })), 'player-count');
		showControls([
			Object.assign(document.createElement('label'), { innerText: "Nombre de joueurs: " }),
			sel,
			mkButton("Démarrer", () => {
				socket.emit('start_game', { player: myName, num_players: +sel.value });
				showControls([]);
			})
		]);
	};

	socket.emit('join', { name: myName });

	// Affichage du nom
	document.body.appendChild(Object.assign(document.createElement('div'), {
		id: 'whoami',
		innerText: "Vous êtes : " + myName,
		style: "position:absolute;top:10px;left:10px;font-weight:bold;background:rgba(255,255,255,0.8);padding:5px;border-radius:4px;"
	}));

	// Logging générique de tous les événements
	socket.onAny((ev, data) => addDebug(`[${ev}] ${JSON.stringify(data)}`));

	// Mise à jour liste joueurs
	socket.on('players', list => setHTML('players', `Joueurs connectés: ${list.join(', ')}`));

	// Sélecteur first player
	socket.on('show_player_selector', showSelector);
	socket.on('not_enough_players', ({ msg, needed }) => {
		alert(msg);
		$('status').innerText = `En attente de ${needed} joueur(s)...`;
		showSelector();
	});

	// Mise à jour main
	socket.on('update_hand', ({ cards }) => {
		const h = $('hand');
		h.innerHTML = '';
		cards.forEach(c => h.appendChild(createCard(c)));
	});

	// Affichage du chien
	socket.on('show_chien', ({ chien }) => {
		const div = Object.assign(document.createElement('div'), {
			id: 'chien',
			innerHTML: "<h3>Le chien</h3>"
		});
		showControls(div);
		chien.forEach(c => $('chien').appendChild(createCard(c)));
		$('status').innerText = "Voici le chien";
	});
	socket.on('hide_chien', () => $('chien')?.remove());

	// Phases de jeu
	socket.on('game_started', () => {
		$('status').innerText = "Partie démarrée ! En attente des annonces...";
		showControls([]);
	});
	socket.on('status', msg => $('status').innerText = msg);

	// Reconnexion
	socket.on('reconnected', ({ msg }) => alert(msg));

	// Demandes d'action
	socket.on('ask_announce', () => {
		const sel = mkSelect(['Passe','Prise','Garde','Garde sans','Garde contre']);
		showControls([
			sel,
			mkButton("Valider", () => {
				socket.emit('announce', { player: myName, announce: sel.value });
				showControls([]); // ← on efface direct après l'envoi
			})
		]);
	});

	socket.on('ask_appel', () => {
		showControls(mkButton("Appeler carte", () => {
			const card = prompt("Carte (ex: W14)"); 
			if (card) socket.emit('appel', { player: myName, card });
		}));
	});

	socket.on('ask_discard', ({ num }) => {
		$('status').innerText = `Sélectionnez ${num} carte(s)`;
		selected.clear();
		document.querySelectorAll('#hand img').forEach(img =>
			img.onclick = () => {
				img.classList.toggle('selected');
				img.classList.contains('selected') ? selected.add(img.id) : selected.delete(img.id);
			}
		);
		showControls(mkButton("Valider écart", () => {
			if (selected.size === num) socket.emit('discard', { player: myName, cards: [...selected] });
			else alert(`Sélectionnez exactement ${num} cartes.`);
		}));
	});

	socket.on('start_game_phase', () => $('current-hand').classList.add('visible'));

	socket.on('ask_play', () => {
		$('status').innerText = "Votre tour : jouez une carte";
		document.querySelectorAll('#hand img').forEach(img =>
			img.onclick = () => {
				socket.emit('play_card', { player: myName, card: img.id });
				document.querySelectorAll('#hand img').forEach(i => i.onclick = null);
			}
		);
	});

	// Mises à jour visuelles
    	socket.on('update_current_hand', ({ cards }) => {
		const c = $('current-hand');
		c.innerHTML = "<h3>Pli en cours</h3>";
		cards.forEach(card => c.appendChild(createCard(card)));
	});

	// Erreurs
	socket.on('invalid', ({ msg }) => alert(msg));
	socket.on('invalid_discard', ({ msg, invalid_cards }) => {
		alert(msg);
		(invalid_cards || []).forEach(name => {
			const img = document.getElementById(name);
			if (img?.classList.contains('selected')) {
				img.classList.remove('selected');
				selected.delete(name);
			}
		});
	});

	// Fin de partie
	socket.on('game_end', scores => {
		const text = Object.entries(scores).map(([n,s]) => `${n}: ${s}`).join('\n');
		alert("Partie terminée !\n" + text);
		$('status').innerText = "Partie terminée";
		showControls([]);
	});
});
