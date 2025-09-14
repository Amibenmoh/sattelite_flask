import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
import sys
import hashlib
import json
import random
import mysql.connector
from mysql.connector import Error

# =========================
# Chemins et fichiers
# =========================
def resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

MODEL_FILE = resource_path("modelResnet50.h5")
USER_FILE = resource_path("user_credentials.json")

# =========================
# Thème et classes
# =========================
DARK_BG = "#0d1b2a"
PANEL_BG = "#1b263b"
ACCENT_COLOR = "#415a77"
HIGHLIGHT_COLOR = "#778da9"
TEXT_COLOR = "#e0e1dd"
BUTTON_COLOR = "#4ea8de"
BUTTON_HOVER = "#3a86ff"
FONT_FAMILY = "Segoe UI"
FONT_SIZE = 10

CLASS_NAMES = ['AnnualCrop','Forest','HerbaceousVegetation','Highway','Industrial','Pasture','PermanentCrop','Residential','River','SeaLake']
CLASS_COLORS = {
    'AnnualCrop':'#8B4513','Forest':'#228B22','HerbaceousVegetation':'#32CD32',
    'Highway':'#696969','Industrial':'#B22222','Pasture':'#9ACD32',
    'PermanentCrop':'#6B8E23','Residential':'#4682B4','River':'#1E90FF','SeaLake':'#000080'
}

# =========================
# Gestion MySQL
# =========================
class GestionBD:
    def __init__(self, host="localhost", user="root", password="1234567890", database="eurosat_db"):
        try:
            self.conn = mysql.connector.connect(host=host,user=user,password=password,database=database)
            self.cur = self.conn.cursor()
        except Error as e:
            messagebox.showerror("Erreur BDD", str(e))
            self.conn, self.cur = None, None

    def inserer_prediction(self, username, image_name, predicted_class, confidence):
        if not self.conn: return
        try:
            self.cur.execute("INSERT INTO predictions (username,image_name,predicted_class,confidence) VALUES (%s,%s,%s,%s)",
                             (username,image_name,predicted_class,float(confidence)))
            self.conn.commit()
        except: pass

    def recuperer_historique(self, username):
        if not self.conn: return []
        try:
            self.cur.execute("SELECT image_name,predicted_class,confidence,timestamp FROM predictions WHERE username=%s ORDER BY timestamp DESC",(username,))
            return self.cur.fetchall()
        except: return []

    def fermer(self):
        if self.cur: self.cur.close()
        if self.conn: self.conn.close()

# =========================
# Prédiction simulée
# =========================
def simulate_prediction(image_path):
    dominant_class = random.randint(0,9)
    preds = np.random.dirichlet(np.ones(10)*0.1,1)[0]
    preds[dominant_class]+=0.6
    preds/=preds.sum()
    pred_class = np.argmax(preds)
    confidence = preds[pred_class]
    return pred_class, confidence, preds

# =========================
# Login / Inscription
# =========================
class LoginPage:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.frame = tk.Frame(parent, bg=DARK_BG)
        self.frame.pack(expand=True, fill=tk.BOTH)
        self.build_ui()

    def build_ui(self):
        tk.Label(self.frame,text="🛰️",font=("Arial",48),bg=DARK_BG,fg=TEXT_COLOR).pack(pady=20)
        tk.Label(self.frame,text="EuroSAT",font=(FONT_FAMILY,24,"bold"),bg=DARK_BG,fg=HIGHLIGHT_COLOR).pack()
        tk.Label(self.frame,text="Classification d'images satellite",bg=DARK_BG,fg=TEXT_COLOR).pack(pady=5)
        form = tk.Frame(self.frame,bg=DARK_BG)
        form.pack(pady=30)
        tk.Label(form,text="Nom d'utilisateur:",bg=DARK_BG,fg=TEXT_COLOR).grid(row=0,column=0,padx=5,pady=10)
        self.user_entry = tk.Entry(form,width=25)
        self.user_entry.grid(row=0,column=1)
        tk.Label(form,text="Mot de passe:",bg=DARK_BG,fg=TEXT_COLOR).grid(row=1,column=0,padx=5,pady=10)
        self.pass_entry = tk.Entry(form,show="*",width=25)
        self.pass_entry.grid(row=1,column=1)
        btn_frame = tk.Frame(self.frame,bg=DARK_BG)
        btn_frame.pack(pady=20)
        tk.Button(btn_frame,text="Se connecter",command=self.login,bg=BUTTON_COLOR,fg=TEXT_COLOR,width=15).pack(side=tk.LEFT,padx=10)
        tk.Button(btn_frame,text="S'inscrire",command=self.show_register,bg=BUTTON_COLOR,fg=TEXT_COLOR,width=15).pack(side=tk.LEFT,padx=10)

    def hash_pass(self,password):
        return hashlib.sha256(password.encode()).hexdigest()

    def check_credentials(self,username,hashed):
        if not os.path.exists(USER_FILE):
            with open(USER_FILE,'w') as f:
                json.dump({"admin":self.hash_pass("admin")},f)
            return username=="admin" and hashed==self.hash_pass("admin")
        with open(USER_FILE,'r') as f:
            users=json.load(f)
        return users.get(username)==hashed

    def login(self):
        u=self.user_entry.get()
        p=self.pass_entry.get()
        if not u or not p: messagebox.showerror("Erreur","Champs vides"); return
        if self.check_credentials(u,self.hash_pass(p)):
            self.frame.destroy()
            self.app.show_main_app(u)
        else:
            messagebox.showerror("Erreur","Nom d'utilisateur ou mot de passe incorrect")

    def show_register(self):
        RegisterDialog(self.parent,self)

    def add_user(self,username,password):
        users={}
        if os.path.exists(USER_FILE):
            with open(USER_FILE,'r') as f: users=json.load(f)
        users[username]=password
        with open(USER_FILE,'w') as f: json.dump(users,f)

class RegisterDialog(tk.Toplevel):
    def __init__(self,parent,login_page):
        super().__init__(parent)
        self.login_page=login_page
        self.title("Inscription")
        self.geometry("400x250")
        self.configure(bg=DARK_BG)
        self.resizable(False,False)
        self.transient(parent)
        self.grab_set()
        self.build_ui()
        self.center(parent)

    def build_ui(self):
        tk.Label(self,text="Nouvel utilisateur",font=(FONT_FAMILY,12,"bold"),bg=DARK_BG,fg=TEXT_COLOR).pack(pady=10)
        frame=tk.Frame(self,bg=DARK_BG)
        frame.pack(pady=10)
        tk.Label(frame,text="Nom d'utilisateur:",bg=DARK_BG,fg=TEXT_COLOR).grid(row=0,column=0,padx=5,pady=8)
        self.user_entry=tk.Entry(frame,width=25)
        self.user_entry.grid(row=0,column=1)
        tk.Label(frame,text="Mot de passe:",bg=DARK_BG,fg=TEXT_COLOR).grid(row=1,column=0,padx=5,pady=8)
        self.pass_entry=tk.Entry(frame,show="*",width=25)
        self.pass_entry.grid(row=1,column=1)
        tk.Label(frame,text="Confirmer:",bg=DARK_BG,fg=TEXT_COLOR).grid(row=2,column=0,padx=5,pady=8)
        self.confirm_entry=tk.Entry(frame,show="*",width=25)
        self.confirm_entry.grid(row=2,column=1)
        btn_frame=tk.Frame(self,bg=DARK_BG)
        btn_frame.pack(pady=15)
        tk.Button(btn_frame,text="S'inscrire",command=self.register,bg=BUTTON_COLOR,fg=TEXT_COLOR,width=12).pack(side=tk.LEFT,padx=10)
        tk.Button(btn_frame,text="Annuler",command=self.destroy,bg=BUTTON_COLOR,fg=TEXT_COLOR,width=12).pack(side=tk.LEFT,padx=10)

    def center(self,parent):
        self.update_idletasks()
        x=parent.winfo_x()+(parent.winfo_width()-self.winfo_width())//2
        y=parent.winfo_y()+(parent.winfo_height()-self.winfo_height())//2
        self.geometry(f"+{x}+{y}")

    def register(self):
        u=self.user_entry.get()
        p=self.pass_entry.get()
        c=self.confirm_entry.get()
        if not u or not p: messagebox.showerror("Erreur","Champs vides"); return
        if p!=c: messagebox.showerror("Erreur","Les mots de passe ne correspondent pas"); return
        self.login_page.add_user(u,self.login_page.hash_pass(p))
        messagebox.showinfo("Succès","Utilisateur ajouté")
        self.destroy()

# =========================
# App principale
# =========================
class MainApplication:
    def __init__(self,parent):
        self.parent=parent
        self.db=GestionBD()
        self.image_path=None
        self.username=None
        LoginPage(parent,self)

    def show_main_app(self,username):
        self.username=username
        self.parent.title(f"EuroSAT - {username}")
        self.parent.geometry("1200x700")
        self.build_ui()

    def build_ui(self):
        # Sidebar
        self.sidebar=tk.Frame(self.parent,bg=PANEL_BG,width=200)
        self.sidebar.pack(side=tk.LEFT,fill=tk.Y)
        tk.Label(self.sidebar,text="EuroSAT",font=(FONT_FAMILY,18,"bold"),fg=TEXT_COLOR,bg=PANEL_BG).pack(pady=20)
        tk.Button(self.sidebar,text="Prédiction",command=self.show_predict,width=20,bg=BUTTON_COLOR,fg=TEXT_COLOR).pack(pady=10)
        tk.Button(self.sidebar,text="Historique",command=self.show_history,width=20,bg=BUTTON_COLOR,fg=TEXT_COLOR).pack(pady=10)
        tk.Button(self.sidebar,text="Quitter",command=self.quit_app,width=20,bg=BUTTON_COLOR,fg=TEXT_COLOR).pack(side=tk.BOTTOM,pady=20)

        # Main area
        self.main_area=tk.Frame(self.parent,bg=DARK_BG)
        self.main_area.pack(side=tk.LEFT,expand=True,fill=tk.BOTH)
        self.tab_predict=tk.Frame(self.main_area,bg=DARK_BG)
        self.tab_history=tk.Frame(self.main_area,bg=DARK_BG)
        self.tab_predict.pack(expand=True,fill=tk.BOTH)

        # Prédiction tab
        btn_frame=tk.Frame(self.tab_predict,bg=DARK_BG)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame,text="Charger image",command=self.load_image,width=20,bg=BUTTON_COLOR,fg=TEXT_COLOR).pack(side=tk.LEFT,padx=5)
        tk.Button(btn_frame,text="Prédire",command=self.predict_image,width=20,bg=BUTTON_COLOR,fg=TEXT_COLOR).pack(side=tk.LEFT,padx=5)
        self.image_label=tk.Label(self.tab_predict,bg=DARK_BG)
        self.image_label.pack(pady=10)
        self.fig,self.ax=plt.subplots(figsize=(8,3))
        self.canvas=FigureCanvasTkAgg(self.fig,master=self.tab_predict)
        self.canvas.get_tk_widget().pack(pady=10)

        # Historique tab
        self.history_tree=ttk.Treeview(self.tab_history,columns=("image","classe","conf","time"),show="headings")
        for col,text in [("image","Image"),("classe","Classe"),("conf","Confiance (%)"),("time","Timestamp")]:
            self.history_tree.heading(col,text=text)
        self.history_tree.pack(expand=True,fill=tk.BOTH,padx=10,pady=10)

    # ======== Actions onglets
    def show_predict(self):
        self.tab_history.pack_forget()
        self.tab_predict.pack(expand=True,fill=tk.BOTH)

    def show_history(self):
        self.tab_predict.pack_forget()
        self.tab_history.pack(expand=True,fill=tk.BOTH)
        self.update_history()

    def load_image(self):
        path=filedialog.askopenfilename(title="Sélectionner image",filetypes=[("Images","*.jpg *.png *.jpeg *.bmp")])
        if path:
            self.image_path=path
            img=Image.open(path)
            img.thumbnail((500,500))
            self.tk_image=ImageTk.PhotoImage(img)
            self.image_label.configure(image=self.tk_image)

    def predict_image(self):
        if not self.image_path: messagebox.showwarning("Attention","Veuillez charger une image"); return
        pred_class,confidence,preds=simulate_prediction(self.image_path)
        self.db.inserer_prediction(self.username,os.path.basename(self.image_path),CLASS_NAMES[pred_class],confidence*100)
        self.ax.clear()
        colors=[CLASS_COLORS[name] for name in CLASS_NAMES]
        self.ax.bar(CLASS_NAMES,preds,color=colors)
        self.ax.set_ylabel("Probabilité")
        self.ax.set_ylim(0,1)
        self.ax.set_xticklabels(CLASS_NAMES,rotation=45,ha='right')
        self.fig.tight_layout()
        self.canvas.draw()
        messagebox.showinfo("Prédiction",f"Classe: {CLASS_NAMES[pred_class]}\nConfiance: {confidence*100:.2f}%")
        self.update_history()

    def update_history(self):
        for row in self.history_tree.get_children(): self.history_tree.delete(row)
        hist=self.db.recuperer_historique(self.username)
        for row in hist:
            self.history_tree.insert("",tk.END,values=(row[0],row[1],f"{row[2]:.2f}",row[3]))

    def quit_app(self):
        self.db.fermer()
        self.parent.destroy()

# ======= Lancement
if __name__=="__main__":
    root=tk.Tk()
    app=MainApplication(root)
    root.mainloop()
