from functools import partial
import tkinter.messagebox as tkm
import tkinter as tk
import os


##----- Fonctions -----##

#Principe général : ferme la fenêtre et/ou en ouvre une autre

def valider(event):
    if int(numero.get()) <= 26749:
        file = open('fichiers/numero.txt', 'w')                 # Sauvegarde le numéro tapé
        file.write(numero.get())                                #
        file.close()                                            #
        Demande.destroy()
        os.system('python Jouer_PC.py')
        
def accueil():                            # 
    Demande.destroy()                     # 
    os.system('python Accueil.py')        # Ouvre l'accueil

def quitter(page):
    page.destroy()

##--- Création de la fenêtre ---##
    
Demande = tk.Tk()                                                                           # Création de la fenêtre
Demande.title('')                                                                           # Nom
Demande.geometry('200x150')                                                                 # Taille
Demande.tk.call('wm', 'iconphoto', Demande._w, tk.PhotoImage(file='icones/icon_n.ico'))     # Icône
Demande['bg'] = '#0a4160'

##--- Variables ---##

v = tk.StringVar()

##--- Création des boutons ---##

tk.Label(Demande, text="Quel est le code ?", fg='white', bg = '#0a4160').pack()        #Texte

numero = tk.Entry(Demande, width=20, textvariable=v)                                #Zone pour rentrer le code
numero.pack()
Demande.bind('<Return>', valider)
numero.focus_force()                                                                #Permet de rentrer directement un nombre sans cliquer dans la zone

tk.Label(Demande, text="", fg='white', bg = '#0a4160').pack()        # Crée un espace

tk.Button(Demande, text='Valider', command=partial(valider,'rien')).pack()                          # Boutons : Valider,Quitter
tk.Button(Demande, text='Accueil', command=accueil).pack()  
tk.Button(Demande, text='Quitter', command=partial(quitter, Demande)).pack()

##----- Actualise la fenêtre -----##

Demande.mainloop()
