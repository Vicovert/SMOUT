from functools import partial
import tkinter.messagebox as tkm
import tkinter as tk
import ctypes
import os



##----- Fonctions -----##

#Principe général : ferme la fenêtre et/ou en ouvre une autre

def jouer():
    Accueil.destroy()
    os.system('python Jouer_PC.py')

def rejoindre():
    file = open('fichiers/parametres.txt', 'w')                 # Sauvegarde les paramètres sélectionnés dans un fichier texte
    file.write('%s;%s;True;%s' % (a,b,d))                       #
    file.close()                                                #
    Accueil.destroy()                                           # Ferme la page
    os.system('python Code_partie.py')  
    
    
def mot_du_jour():
    file = open('fichiers/parametres.txt', 'w')                 #
    file.write('%s;%s;%s;True' % (a,b,c))                       #
    file.close()                                                #
    Accueil.destroy()                                           #
    os.system('python Jouer_PC.py')                             #


def parametres():
    Accueil.destroy()                                           #
    os.system('python Parametres.py')
    
    
def quitter(page):
    page.destroy()


##--- Variables ---##

f = open('fichiers/parametres.txt','r')   #Récupération et affichage des paramètres actuels
ligne = f.read()
a,b,c,d = ligne.split(';')
f.close

file = open('fichiers/parametres.txt', 'w')                 # Sauvegarde les paramètres sélectionnés dans un fichier texte
file.write('%s;%s;False;False' % (a,b))                     #
file.close()                                                #

couleur_b = 'wheat'                     #Couleur des boutons définis avant pour changement rapide
couleur_t = 'black'

usr32 = ctypes.windll.user32

##--- Création de la fenêtre ---##

Accueil = tk.Tk()                                                                           # Création de la fenêtre
Accueil.title('Accueil')                                                                    # Nom
Accueil.geometry('%sx%s' % (usr32.GetSystemMetrics (0),usr32.GetSystemMetrics (1)))                     # Taille
Accueil.tk.call('wm', 'iconphoto', Accueil._w, tk.PhotoImage(file='icones/icon_a.ico'))     # Icône
Accueil['bg'] = '#0a4160'

tk.Label(height = 10, bg = '#0a4160').pack()  #Permet de définir l'espace entre le haut de l'écran et le premier boutton
tk.Button(Accueil, text='Jouer', command=jouer, bg = couleur_b, fg = couleur_t, height = 5, width = 30).pack()                          # Boutons
tk.Button(Accueil, text='Rejoindre une Partie', command=rejoindre, bg = couleur_b, fg = couleur_t, height = 5, width = 30).pack()
tk.Button(Accueil, text='Mot du Jour', command=mot_du_jour, bg = couleur_b, fg = couleur_t, height = 5, width = 30).pack()
tk.Button(Accueil, text='Paramètres', command=parametres, bg = couleur_b, fg = couleur_t, height = 5, width = 30).pack()
tk.Button(Accueil, text='Quitter', command=partial(quitter, Accueil), bg = couleur_b, fg = couleur_t, height = 5, width = 30).pack()

##----- Actualise la fenêtre -----##

Accueil.mainloop()
