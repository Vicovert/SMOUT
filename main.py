import tkinter as tk
import os
import sys
from page_solo import PageSolo
from page_multi import PageMulti
from page_multi import LogoSmout, BLEU, JAUNE, ROUGE

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class BoutonSquare(tk.Canvas):
    def __init__(self, parent, text, command, size=180, color="#f5deb3", is_wide=False):
        width = size * 2 + 60 if is_wide else size
        height = 60 if is_wide else size
        super().__init__(parent, width=width, height=height, bg=parent["bg"], highlightthickness=0, cursor="hand2")
        self.command = command
        self.color = color
        self.hover_color = self._adjust_color(color, 1.1)
        self.rect = self.draw_round_rect(4, 4, width-4, height-4, 15, fill=color)
        self.create_text(width/2, height/2, text=text, fill=BLEU, font=("Helvetica", 12, "bold"), width=width-20, justify="center")
        self.bind("<ButtonRelease-1>", lambda e: self.command())
        self.bind("<Enter>", lambda e: self.itemconfig(self.rect, fill=self.hover_color))
        self.bind("<Leave>", lambda e: self.itemconfig(self.rect, fill=self.color))

    def _adjust_color(self, hex_color, factor):
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        new_rgb = [min(255, max(0, int(c * factor))) for c in rgb]
        return '#{:02x}{:02x}{:02x}'.format(*new_rgb)

    def draw_round_rect(self, x1, y1, x2, y2, r, **kwargs):
        p = [x1+r,y1, x1+r,y1, x2-r,y1, x2-r,y1, x2,y1, x2,y1+r, x2,y1+r, x2,y2-r, x2,y2-r, x2,y2, x2-r,y2, x2-r,y2, x1+r,y2, x1+r,y2, x1,y2, x1,y2-r, x1,y2-r, x1,y1+r, x1,y1+r, x1,y1]
        return self.create_polygon(p, **kwargs, smooth=True)

class MenuPrincipal(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SMOUT")
        self.geometry("1000x850")
        self.configure(bg=BLEU)
        
        # Application de l'icône depuis le dossier fichiers
        icon_path = resource_path(os.path.join('fichiers', 'logo.ico'))
        if os.path.exists(icon_path):
            try: self.iconbitmap(icon_path)
            except: pass
            
        self.container = tk.Frame(self, bg=BLEU)
        self.container.pack(fill="both", expand=True)
        self.creer_menu_accueil()

    def creer_menu_accueil(self):
        for widget in self.container.winfo_children(): widget.destroy()
        main_frame = tk.Frame(self.container, bg=BLEU)
        main_frame.place(relx=0.5, rely=0.5, anchor="center")
        LogoSmout(main_frame, 130).pack(pady=(0, 60))
        ligne_boutons = tk.Frame(main_frame, bg=BLEU); ligne_boutons.pack()
        BoutonSquare(ligne_boutons, "SOLO", self.ouvrir_solo, size=180, color=JAUNE).pack(side="left", padx=15)
        BoutonSquare(ligne_boutons, "MULTIJOUEUR", self.ouvrir_multi, size=180, color=ROUGE).pack(side="left", padx=15)
        BoutonSquare(main_frame, "QUITTER", self.quitter_jeu, size=180, color="#f87171", is_wide=True).pack(pady=30)

    def ouvrir_solo(self):
        for widget in self.container.winfo_children(): widget.destroy()
        PageSolo(parent=self.container, controller=self).pack(fill="both", expand=True)

    def ouvrir_multi(self):
        for widget in self.container.winfo_children(): widget.destroy()
        PageMulti(parent=self.container, controller=self).pack(fill="both", expand=True)

    def quitter_jeu(self):
        self.quit(); self.destroy()

if __name__ == "__main__":
    app = MenuPrincipal(); app.mainloop()
