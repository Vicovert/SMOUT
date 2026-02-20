from datetime import datetime
from functools import partial
import tkinter.messagebox as tkm
import tkinter as tk
import random
import os


##----- Fonctions -----##

def premiere_lettre(ligne):                                                         # Met la première lettre dans la première case et colore en rouge
    tk.Canvas(fen, bg=Rouge, borderwidth=3,                                         # Colorie la case en rouge
              relief="flat", height=25, width=25).place(x=6, y=6+33*ligne)          #
    if mot[0] == 'I':                                                               # Le 'I' se met trop à gauche donc rectification pour cette lettre seulement
        labelA = tk.Label(fen, text = mot[0], fg="white", bg=Rouge)                 # Colorie le fond de la lettre en rouge (sinon le fond est gris de base)
        labelA.place(x=18, y=13+33*ligne)                                           # Place la lettre au milieu de la case
    else:                                                                           #
        labelA = tk.Label(fen, text = mot[0], fg="white", bg=Rouge)                 # Idem
        labelA.place(x=17, y=13+33*ligne)                                           #
    

def taper_lettre(lettre):                                                           # Ajoute une lettre (clavier et boutons)
    global pos_x                                                                    # Importe les variables à modifier
    global mot_tape                                                                 # 
    if lettre not in alphabet_maj:                                                  # Condition nécessaire si le bouton appuié sur le clavier n'est pas une lettre
        lettre = lettre.keysym                                                      # 
    if (lettre in alphabet_min or lettre in alphabet_maj):                          # Si la lettre est dans l'alphabet (min pour le clavier, max pour les boutons)
        if pos_x < len(mot)*29:                                                     # Ne peut plus taper après la dernière case (ne dépasse pas dans la grille)
            if lettre == 'i':                                                       # Même raison que dans la fonction : premiere_lettre
                pos_x += 33                                                         # Passe à la case suivante (les cases sont espacées de 33 pixels)
                labelA = tk.Label(fen, text = lettre.upper(), fg="white", bg=Bleu)  # Défini la lettre en blanc fond bleu
                labelA.place(x=pos_x+8, y=13+ligne_actuelle*33)                     # Placer la lettre
                mot_tape.append(lettre.upper())                                     # Ajoute le mot à la liste des lettres tapées
            else:                                                                   #
                pos_x += 33                                                         # Idem
                labelA = tk.Label(fen, text = lettre.upper(), fg="white", bg=Bleu)  #
                labelA.place(x=pos_x+6, y=13+ligne_actuelle*33)                     #
                mot_tape.append(lettre.upper())                                     #
    elif lettre == 'BackSpace':                                                     # Supprimer ou valider avec le clavier
        suprimer_lettre()                                                           #
    elif lettre == 'Return':                                                        #
        verifier_mot()                                                              #


def suprimer_lettre():                                                              # Supprime la dernière lettre tapée
    global pos_x                                                                    # 
    global mot_tape                                                                 #
    if pos_x > 42:                                                                  # Empêche la première lettre d'être effacée
        labelA = tk.Label(fen, text = mot_tape[-1], fg=Bleu, bg=Bleu)               # Crée une nouvelle lettre en bleu fond bleu (même lettre que la dernière tapée)
        labelA.place(x=pos_x+6, y=13+ligne_actuelle*33)                             # Place la nouvelle lettre sur l'ancienne pour la cacher
        pos_x -= 33                                                                 # Passe à la case précédente
        mot_tape.pop(-1)                                                            # Supprime le mot de la liste des lettres tapées


def changer_ligne():                                                                # Change de ligne lorsque le mot est validé
    global pos_x                                                                    #
    global ligne_actuelle                                                           #
    global mot_tape                                                                 #
    if ligne_actuelle < nb_essais-1:                                                # Limite le nombre de lignes selon les paramètres
                ligne_actuelle += 1                                                 # 
                pos_x = 10                                                          # Reviens au milieu de la 1ere case
                premiere_lettre(ligne_actuelle)                                     # Place la première lettre
                mot_tape = [mot[0]]                                                 # Réinitialise la liste des lettres tapées

                
def verifier_mot():                                                                 # Vérifie le mot existe et si c'est le bon
    global score                                                                    # 
    global essais_restants                                                          # 
    if len(mot_tape) == len(mot):                                                   # Ne peut valider un mot que si toutes les cases sont remplies
        mot_entier = ''.join(str(elem) for elem in mot_tape)                        # Compose le mot à partir de chaque lettre
        if mot_entier in Banque_mots :                                              # Vérifie si le mot existe
            compteur = verifier_lettre()                                            # Compte le nombre de lettres bien placées
            if compteur == len(mot):                                                # Si il y a autant de lettres bien placées que de lettres dans le mot à trouver, le joueur gagne
                gagne()                                                             #
            else:                                                                   # Dans le cas ou le mot tapé n'est pas le bon
                changer_ligne()                                                     # Passage à la ligne suivante
                essais_restants -=1                                                 # Retire 1 au nombre d'essais restants
                if essais_restants ==0:                                             # Si le nombre d'essais max est atteint, le joueur perd
                    perdu()                                                         #
        else :                                                                      # Si le mot n'existe pas
            score -= 30                                                             # Retire des points pour chaque essai
            tkm.showwarning('', "Ce mot n'existe pas")                              # Affiche le message d'erreur


def verifier_lettre():                                                                                                          # Vérifie chaque lettre pour mettre en rouge/jaune/rien
    compteur = 0                                                                                                                # Met le compteur de lettres bien placées à 0
    occurence = []                                                                                                              # Lettres communes au mot tapé et au mot à trouver
    lettres_rouges = []                                                                                                         # Liste des lettres misent en rouge
    lettres_pas_grises = []                                                                                                     # Liste des lettres a ne pas griser
    for i in range(len(mot)):                                                                                                   # Pour chaque lettre du mot tapé
        if mot_tape[i] == mot[i]:                                                                                               # Si la lettre est bien placée
            compteur +=1                                                                                                        # Incrémentation du nombre de lettres bien placées
            occurence.append(mot_tape[i])                                                                                       # On la compte comme apparu
            lettres_rouges.append(i)                                                                                            # La case en rouge ne sera pas prise en compte pour les jaunes
            lettres_pas_grises.append(mot_tape[i])                                                                              # Cette lettre ne sera pas grisée
            tk.Canvas(fen, bg=Rouge, borderwidth=3,                                                                             # Colorie la case en rouge
                      relief="flat", height=25, width=25).place(x=6+i*33, y=6+33*ligne_actuelle)                                #
            globals()['b%s' % mot_tape[i]]["bg"] = Rouge
            if mot[i] == 'I':                                                                                                   # Encore une exception pour 'I'
                labelA = tk.Label(fen, text = mot_tape[i], fg="white", bg=Rouge)                                                # Lettre en blanc fond rouge 
                labelA.place(x=18+33*i, y=13+ligne_actuelle*33)                                                                 # Place la lettre
            else:                                                                                                               #
                labelA = tk.Label(fen, text = mot_tape[i], fg="white", bg=Rouge)                                                # Idem
                labelA.place(x=16+33*i, y=13+ligne_actuelle*33)                                                                 #
    for i in range(len(mot)):                                                                                                   # Si la lettre est dans le mot mais mal placée
        if mot_tape[i] in mot and i not in lettres_rouges and occurence.count(mot_tape[i]) < mot.count(mot_tape[i]):            # Si pas en rouge et apparu - de fois que dans le mot à trouver
            occurence.append(mot_tape[i])                                                                                       # On la compte comme apparu
            lettres_pas_grises.append(mot_tape[i])                                                                              # 
            c = tk.Canvas(fen, bg=Jaune, borderwidth=3,                                                                         # Colorie la case en jaune (rond)
                          relief="flat", height=25, width=25)
            if globals()['b%s' % mot_tape[i]]["bg"] != Rouge :
                globals()['b%s' % mot_tape[i]]["bg"] = Jaune
            c.place(x=6+i*33, y=6+33*ligne_actuelle)                                                                            # 
            c.create_oval(1, 1, 1, 1, fill=Jaune, outline=Jaune)                                                                #
            if mot[i] == 'I':                                                                                                   # Place la lettre comme les fois précédentes
                labelA = tk.Label(fen, text = mot_tape[i], fg="white", bg=Jaune)                                                # 
                labelA.place(x=18+33*i, y=13+ligne_actuelle*33)                                                                 # 
            else:                                                                                                               # 
                labelA = tk.Label(fen, text = mot_tape[i], fg="white", bg=Jaune)                                                # 
                labelA.place(x=17+33*i, y=13+ligne_actuelle*33)                                                                 #
        elif i != 0 and mot_tape[i] not in lettres_pas_grises[1:]:                                                              #
            if globals()['b%s' % mot_tape[i]]["bg"] == "#0a4160":                                                               # Si le bonton n'a pas encore été grisé ou mis en couleur
                globals()['b%s' % mot_tape[i]]["bg"] = "grey"                                                                   # Colore le bouton en gris
    return compteur                                                                                                             # On retroune le nombre de lettres bien placées


def perdu():                                                                                                                    # Si le joueur perd
    global arret_timer                                                                                                          # 
    arret_timer = True                                                                                                          # On arrête le chrono
    answer = tkm.askyesno(title='Fin de partie', message='Vous avez perdu, le mot était : %s.\n\n\t         Rejouer ?' % mot)   # Message de game over
    if answer:                                                                                                                  # Si le joueur veux rejouer
        fen.destroy()                                                                                                           # Ferme la fenêtre
        os.system('python Jouer_PC.py')                                                                                         # Relance le fichier 'Jouer'
    else:                                                                                                                       # 
        fen.destroy()                                                                                                           #
        os.system('python Accueil.py')                                                                                          #
    

def gagne():                                                                                                                    # Idem que perdu mais message de victoire
    global arret_timer                                                                                                          # 
    arret_timer = True                                                                                                          # 
    answer = tkm.askyesno(title='Fin de partie', message='Vous avez gagné, le mot était bien : %s.\n\n\t\tRejouer ?' % mot)     #
    if answer:                                                                                                                  # 
        fen.destroy()                                                                                                           # 
        os.system('python Jouer_PC.py')                                                                                         # 
    else:                                                                                                                       # 
        fen.destroy()                                                                                                           #
        os.system('python Accueil.py')                                                                                          #


def accueil():                            # 
    fen.destroy()                         # 
    os.system('python Accueil.py')        # Ouvre l'accueil


def quitter():                            #
    fen.destroy()                         #


def timer():                                                                                            #
    global M                                                                                            #
    global S                                                                                            #
    if arret_timer == False:                                                                            # Tant que la partie n'est pas finie
        if int(datetime.now().strftime("%S")) > S0 :                                                    # Datetime est le temps actuel donc pour créer un chrono, on ajoute juste les
            S = int(datetime.now().strftime("%S")) - S0                                                 # secondes qui passent sur datetime, il faut donc initialiser à zéro et ne pas
        else:                                                                                           # prendre en compte le passage à zéro réel de datetime (sinon fait passer à zéro
            S = int(datetime.now().strftime("%S")) - S0 + 60                                            # les secondes du chrono lorsque l'horloge du pc passe à la minute suivante)
        if S == 60:                                                                                     #
            M += 1                                                                                      # Ajout d'une minute toutes les 60 secondes
            S = 0                                                                                       # Mise à zéro des secondes
    if S < 10 :                                                                                         # Cas des chiffres qui ne prennent qu'un caractère (rajout d'un 0 devant)
        Timer.configure(text = 'Temps écoulé: %s:0%s' % (M,S))                                          # Affiche en temps réel le chrono
    else :                                                                                              #
        Timer.configure(text = 'Temps écoulé: %s:%s' % (M,S))                                           #
    if int(score)- M*60 - S +50*(essais_restants-nb_essais) > 0 :                                       # Vérifie que le score est positif
        Score.configure(text = 'Score: %s' % (int(score)- M*60 - S +50*(essais_restants-nb_essais)))    # Retire 1 point par secondes et par essai utilisé
    else :                                                                                              #
        Score.configure(text = 'Score: 0')                                                              # Défini le score à 0
    fen.after(1000, timer)                                                                              # Appelle la fonction timer toutes les secondes
        
##----- Création des variables -----##

arret_timer = False

Rouge = '#ef4444'     #Couleurs utiles
Jaune = '#eab308'
Bleu =  '#0a4160'
Bleu_c = '#0ea5e9'
alphabet_min = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z']    #Alphabets utiles
alphabet_maj = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']
ligne_actuelle = 0   #Initialisation de la ligne
pos_x = 10           #Centre de la première case

f = open('fichiers/parametres.txt','r')          #Récupération des paramètres choisis
ligne = f.read()
a,b,c,d = ligne.split(';')
f.close()
nb_essais = (int(a))
nb_lettres = (int(b))
multijoueur = c
mdj = d
score = 1500-nb_essais*100 + 50*nb_lettres       #Initialisation du score

essais_restants = nb_essais

                    
##----- Récupération du mot -----##
f = open('fichiers/date_triche.txt', 'r')
L = f.readlines()
f.close()
jour = str(datetime.now().strftime("%d"))
if L[0] != jour.lstrip('0'):                     #La liste des mots joués est réinitialisée chaque jour
    f = open('fichiers/numeros_joues.txt', 'w')
    f.close()
    f = open('fichiers/date_triche.txt', 'w')    #Date mise a jour    
    f.write(jour.lstrip('0'))                    #Retire le 0 devant les 10 premiers chiffres
    f.close()
     
f = open('fichiers/mots_trouver.txt','r', errors='ignore')                  #Récupère la liste de mots
L = f.readlines()
f.close()
Lmots = []
for i in range(len(L)):
    L[i] = L[i].rstrip('\n')              #Suprimme les \n et \t
    L[i] = L[i].rstrip('\t')
    if len(L[i]) <= nb_lettres:
        Lmots.append(L[i])


if mdj == 'True':
    #Le mot change chaque jour (tentative d'approche d'aléatoire)
    nb = 124378524855769*int(datetime.now().strftime("%d")) % len(Lmots)
elif multijoueur == 'True':
    f = open('fichiers/numero.txt','r')          #Récupération de la position du mot à jouer
    nb = f.read()
    f.close()
else:   #Tire un mot au hasard
    nb = random.randint(0, len(Lmots)-1)
    
mot = Lmots[int(nb)]       #Défini le mot à touver
mot_tape = [mot[0]]        #Défini la première lettre du mot à taper

f = open('fichiers/numeros_joues.txt', 'r')          # Récupère la liste des mots déjà joués
L_mots_joues = f.readlines()
f.close()
for i in range(len(L_mots_joues)):
    L_mots_joues[i].strip()
    L_mots_joues[i] = L_mots_joues[i].rstrip('\n')              #Suprimme les \n et les espaces

f = open('fichiers/numeros_joues.txt', 'a')          # Sauvegarde le mot joué
f.write('%s\n' % nb)
f.close()

f = open('fichiers/banque_mots.txt','r', errors='ignore')           #Récupère la liste de mots
L = f.readlines()
f.close()

Banque_mots = []
for i in range(len(L)):
    L[i] = L[i].rstrip('\n')              #Suprimme les \n et \t
    L[i] = L[i].rstrip('\t')
    if len(L[i]) <= nb_lettres and len(L[i]) > 5:  #Ne prends en compte que les mots de la même taille pour réduire le temps de récupération
        Banque_mots.append(L[i])

#La banque de mots permets de compter bien plus de mots comme existants
#Il y a 25750 mots qui à trouver et 411430 mots existants

##----- Création fenêtre -----##

fen = tk.Tk()                                                                           # Utililise tkinter pour créer une fenêtre
fen.title('SMOUT')                                                                      # Nom
fen.geometry('1000x400')                                                                # Taille
fen.tk.call('wm', 'iconphoto', fen._w, tk.PhotoImage(file='icones/icon_j.ico'))         # Icône
fen['bg'] = Bleu                                                                        # Fond

##----- Création des cases -----##

for colonne in range(len(mot)):                                                         #
    for ligne in range(nb_essais):                                                      # Crée les cases pour chaques lignes
        ca = tk.Canvas(fen, bg=Bleu, borderwidth=3, relief="flat", height=25, width=25) # Case de 25x25
        ca.place(x=colonne*33+6, y=ligne*33+6)                                          #


##----- Création des boutons PC -----##

#Boutons de l'aphabet
lettre = 0
for ligne in range(2):
    for colonne in range(13):
        globals()['b%s' % alphabet_maj[lettre]] = tk.Button(fen, text=alphabet_maj[lettre], activebackground=Bleu_c, fg="white", bg=Bleu,
                   command=partial(taper_lettre,alphabet_maj[lettre]), height = 1, width = 3, borderwidth=1)
        globals()['b%s' % alphabet_maj[lettre]].place(x=40*len(mot)+29*colonne, y=100+24*ligne)
        globals()['b%s' % alphabet_maj[lettre]].bind("<Button-3>")
        lettre +=1

tk.Button(fen, text='suprimer',command=partial(suprimer_lettre), fg="white", bg=Bleu, height = 1, width = 7, borderwidth=1).place(x=40*len(mot)+377, y=100)  #Bouton supprimer

tk.Button(fen, text='valider',command=partial(verifier_mot), fg="white", bg=Bleu, height = 1, width = 7, borderwidth=1).place(x=40*len(mot)+377, y=124) #Bouton valider

        
##----- Autres boutons -----##

tk.Button(fen, text='Abandon', command=perdu).place(x=50+33*len(mot), y=0)       # Création du bouton Abandon

tk.Button(fen, text='Accueil', command=accueil).place(x=110+33*len(mot), y=0)    # Bouton Accueil

tk.Button(fen, text='Quitter', command=quitter).place(x=160+33*len(mot), y=0)    # Bouton Quitter

Timer = tk.Label(fen, text='Horloge', fg='white', bg=Bleu)                       # Mise en place du chrono
Timer.place(x=10, y=20+33*nb_essais)

Score = tk.Label(fen, text=score, fg='white', bg=Bleu)                           # Mise en place du score
Score.place(x=10, y=40+33*nb_essais)

                                                                                
Num = tk.Label(fen, text=nb, fg='white', bg=Bleu)                                #Affiche la position du mot pour pouvoir la rentrer sur d'autres appareils et jouer ensemble
Num.place(x=210+33*len(mot), y=3)


if str(nb) in L_mots_joues:
    Triche = tk.Label(fen, text='T', fg='white', bg=Bleu)                             #Affiche la position du mot pour pouvoir la rentrer sur d'autres appareils et jouer ensemble
    Triche.place(x=128+33*len(mot), y=30)

b = tk.Label(relief=tk.FLAT, bg=Bleu)                                            # Permet de prendre en compte le clavier pour taper les lettre, valider ou supprimer
b.place(x=1000, y=1000)                                                          # Hors du cadre pour ne pas le voir
b.bind ("<Key>", taper_lettre)                                                   # Prend en compte une frappe sur le clavier
b.focus_set()                                                                    # Nécessaire pour le fonctionnement mais non compris


##----- Première lettre du mot -----##

premiere_lettre(0)  # Initialisation de la première ligne

    
##----- Actualise la fenêtre -----##

M = -1   #Bug de minutes si 0
S0 = int(datetime.now().strftime("%S")) #Initialise les secondes
         
timer()             #Lance le chrono
fen.mainloop()
