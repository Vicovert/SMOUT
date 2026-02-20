from functools import partial
import tkinter.messagebox as tkm
import tkinter as tk
import os


##----- Fonctions -----##

def quitter(page):                                                                       #
    file = open('fichiers/parametres.txt', 'w')                                          # Sauvegarde les paramètres sélectionnés dans un fichier texte
    file.write('%s;%s;%s;%s' % (nb_essais.get(),nb_lettres.get(),c,d))                   #
    file.close()                                                                         #
    page.destroy()                                                                       # Ferme la page
    os.system('python Accueil.py')                                                       # Ouvre l'accueil

##--- Création de la fenêtre ---##

Parametres = tk.Tk()                                                                            # Création de la fênêtre
Parametres.title('Parametres')                                                                  # Nom
Parametres.geometry('500x500')                                                                  # Taille
Parametres.tk.call('wm', 'iconphoto', Parametres._w, tk.PhotoImage(file='icones/icon_s.ico'))   # Icône
Parametres['bg'] = '#0a4160'

##----- Variables -----##

Bleu = '#0a4160'

nb_essais = tk.StringVar()      # Choix du type de paramètre
nb_lettres = tk.StringVar()

f = open('fichiers/parametres.txt','r')   #Récupération et affichage des paramètres actuels
ligne = f.read()
a,b,c,d = ligne.split(';')
nb_essais.set(int(a))
nb_lettres.set(int(b))

##---- Boutons ----##

essais = tk.Frame(Parametres, borderwidth=0, bg = Bleu)            # Une fenêtre par choix
essais.pack(side=tk.LEFT, padx=10, pady=10)


lettres = tk.Frame(Parametres, borderwidth=0, bg = Bleu)
lettres.pack(side=tk.RIGHT, padx=30, pady=30)


tk.Label(essais, text="Nombre d'essais", fg='white', bg = Bleu).pack()         # Textes des choix
tk.Label(lettres, text='Nombre de lettres max', fg='white', bg = Bleu).pack()

for nombre in range(2,11):
     tk.Radiobutton(essais, variable=nb_essais, text=nombre, value=nombre, fg='white', bg = Bleu, activebackground = Bleu, selectcolor=Bleu).pack(side='top')    # Création des boutons à cocher

for nombre in range(6,11):
     tk.Radiobutton(lettres, variable=nb_lettres, text=nombre, value=nombre, fg='white', bg = Bleu, activebackground = Bleu, selectcolor=Bleu).pack(side='top')

b = tk.Button(Parametres, text='Quitter', command=partial(quitter, Parametres))  # Bouton Quitter
b.pack(side='top')

##----- Actualise la fenêtre -----##

Parametres.mainloop()
