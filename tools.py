ANNONCES = ['Passe', 'Prise', 'Garde', 'Garde sans', 'Garde contre']
MULTIPLIEURS = {
    'Prise': 1,
    'Garde': 2,
    'Garde sans': 4,
    'Garde contre': 6
}
POINTS_CONTRAT = {0: 56, 1: 51, 2: 41, 3: 36}
POIGNEE_BONUS = {'simple': 20, 'double': 30, 'triple': 40}

def calcul_score_tarot(points_attaque, bouts, petit_au_bout, poignees, contrat):
    print(f"\nCalculating score for contrat {contrat} with points_attaque {points_attaque}, bouts {bouts}, petit_au_bout {petit_au_bout}, poignees {poignees}")
    if not 0 <= bouts <= 3:
        raise ValueError("Le nombre de bouts doit être entre 0 et 3.")

    if contrat not in ANNONCES[1:]:
        raise ValueError("Contrat invalide. Utilisez : 'prise', " \
        "'garde', 'garde sans', 'garde contre'.")
    points_a_faire = POINTS_CONTRAT[bouts]
    ecart = int(points_attaque - points_a_faire)
    reussite = ecart >= 0
    multiplicateur = MULTIPLIEURS[contrat]

    base_score = 25 + abs(ecart)
    base_score = int(round(base_score))

    if petit_au_bout == 'attaque':
        base_score += 10
    elif petit_au_bout == 'défense':
        base_score -= 10

    score = base_score * multiplicateur
    if not reussite:
        score *= -1

    for poignee in poignees:
        bonus = POIGNEE_BONUS[poignee]*poignees[poignee]
        if reussite:
            score += bonus
        else:
            score -= bonus

    return score
