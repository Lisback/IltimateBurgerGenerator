import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import random
import sqlite3
import webbrowser
from datetime import datetime
from PIL import Image, ImageTk
import os
from fpdf import FPDF

class UltimateBurgerApp:
    def __init__(self, root):
        self.root = root
        self.language = "FR"
        self.current_burger = None
        self.load_translations()
        self.setup_database()
        self.setup_styles()
        self.setup_ui()
        self.load_history()

    def load_translations(self):
        """Charge les traductions depuis le fichier JSON"""
        try:
            lang_file = f'translations_{self.language.lower()}.json'
            with open(lang_file, 'r', encoding='utf-8') as f:
                self.trans = json.load(f)
        except FileNotFoundError:
            messagebox.showerror("Erreur", f"Fichier de traduction manquant: {lang_file}")
            self.trans = {}
        except json.JSONDecodeError:
            messagebox.showerror("Erreur", "Fichier de traduction corrompu")
            self.trans = {}

    def setup_database(self):
        """Initialise la base de données SQLite"""
        self.conn = sqlite3.connect('burgers.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS burgers
                            (id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT,
                            ingredients TEXT,
                            sauce TEXT,
                            diet TEXT,
                            calories INTEGER,
                            created_at TEXT,
                            burger_type TEXT)''')
        self.conn.commit()

    def setup_styles(self):
        """Configure les styles visuels"""
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure(".", background="#f5f5f5", foreground="#333", font=('Helvetica', 11))
        self.style.configure("TButton", padding=8, background="#4a7a96", foreground="white")
        self.style.configure("Zodiac.TFrame", background="#e6f9ff")

    def setup_ui(self):
        """Construit l'interface utilisateur"""
        self.root.title(self.t("app_title"))
        self.root.geometry("1200x800")
        
        # Barre de contrôle
        control_frame = ttk.Frame(self.root)
        control_frame.pack(pady=10)
        
        ttk.Button(control_frame, text="🇫🇷 FR", command=lambda: self.set_language("FR")).pack(side="left", padx=5)
        ttk.Button(control_frame, text="🇬🇧 EN", command=lambda: self.set_language("EN")).pack(side="left", padx=5)
        
        # Onglets
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.setup_classic_tab()
        self.setup_extreme_tab()
        self.setup_zodiac_tab()
        
        # Résultats
        self.setup_result_display()
        self.setup_history_section()

    def setup_classic_tab(self):
        """Onglet des burgers classiques"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=self.t("classic_tab"))
        
        # Type de burger
        burger_types = [
            "Hamburger", "Cheeseburger", "Bacon Burger",
            "Chicken Burger", "Fish Burger", "Veggie Burger"
        ]
        
        ttk.Label(tab, text=self.t("type_label")).grid(row=0, column=0, padx=5, pady=5)
        self.classic_type = ttk.Combobox(tab, values=burger_types, state="readonly")
        self.classic_type.grid(row=1, column=0, padx=5, pady=5)
        self.classic_type.set(burger_types[0])
        
        # Taille
        ttk.Label(tab, text=self.t("size_label")).grid(row=0, column=1, padx=5, pady=5)
        self.size_var = ttk.Combobox(tab, values=["Simple", "Double", "Triple"], state="readonly")
        self.size_var.grid(row=1, column=1, padx=5, pady=5)
        self.size_var.set("Simple")
        
        # Sauce
        ttk.Label(tab, text=self.t("sauce_label")).grid(row=0, column=2, padx=5, pady=5)
        self.sauce_combo = ttk.Combobox(tab, values=list(self.trans["sauces"].keys()), state="readonly")
        self.sauce_combo.grid(row=1, column=2, padx=5, pady=5)
        self.sauce_combo.set(list(self.trans["sauces"].keys())[0])
        
        # Bouton info sauce
        ttk.Button(tab, text="ℹ️", width=3, command=self.show_sauce_info).grid(row=1, column=3)
        
        # Bouton générer
        ttk.Button(tab, text=self.t("generate_btn"), command=self.generate_classic).grid(row=2, columnspan=4, pady=10)

    def setup_extreme_tab(self):
        """Onglet des burgers extrêmes"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=self.t("extreme_tab"))
        
        # Niveau de folie
        ttk.Label(tab, text=self.t("crazy_level")).pack()
        self.crazy_level = ttk.Scale(tab, from_=1, to=10, orient="horizontal")
        self.crazy_level.pack()
        self.crazy_level.set(5)
        
        # Option végan
        self.vegan_extreme = tk.BooleanVar()
        ttk.Checkbutton(tab, text=self.t("vegan_option"), variable=self.vegan_extreme).pack(pady=5)
        
        # Bouton générer
        ttk.Button(tab, text=self.t("generate_btn"), command=self.generate_extreme).pack(pady=15)

    def setup_zodiac_tab(self):
        """Onglet des burgers du zodiaque"""
        tab = ttk.Frame(self.notebook, style="Zodiac.TFrame")
        self.notebook.add(tab, text=self.t("zodiac_tab"))
        
        # Signe du zodiaque
        ttk.Label(tab, text=self.t("choose_sign"), font=("Georgia", 14)).pack(pady=10)
        self.sign_var = ttk.Combobox(tab, values=list(self.trans["zodiac_signs"].keys()), state="readonly")
        self.sign_var.pack(pady=5)
        self.sign_var.set(list(self.trans["zodiac_signs"].keys())[0])
        self.sign_var.bind("<<ComboboxSelected>>", self.update_zodiac_display)
        
        # Élément
        self.element_label = ttk.Label(tab, text="", font=('Helvetica', 12))
        self.element_label.pack(pady=5)
        
        # Bouton générer
        ttk.Button(tab, text=self.t("generate_btn"), command=self.generate_zodiac).pack(pady=15)
        
        self.update_zodiac_display()

    def show_sauce_info(self):
        """Affiche les informations de la sauce sélectionnée"""
        sauce = self.sauce_combo.get()
        sauce_desc = self.trans["sauces"].get(sauce, self.t("no_description"))
        messagebox.showinfo(
            f"{sauce} Info",
            sauce_desc,
            parent=self.root
        )

    def setup_result_display(self):
        """Configure la zone d'affichage des résultats"""
        self.result_frame = ttk.Frame(self.root)
        self.result_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Image du burger
        self.img_label = ttk.Label(self.result_frame)
        self.img_label.pack(side="left", padx=10)
        
        # Texte descriptif
        self.result_text = tk.Text(
            self.result_frame,
            height=15,
            width=60,
            wrap="word",
            bg="white",
            fg="#333333",
            font=('Helvetica', 10)
        )
        self.result_text.pack(side="left", fill="both", expand=True)
        
        # Tags pour le style du texte
        self.result_text.tag_configure("title", font=('Helvetica', 14, 'bold'))
        self.result_text.tag_configure("bold", font=('Helvetica', 10, 'bold'))

    def setup_history_section(self):
        """Configure la section historique"""
        history_frame = ttk.LabelFrame(self.root, text=self.t("history_title"))
        history_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.history_list = tk.Listbox(
            history_frame,
            height=6,
            font=('Helvetica', 10)
        )
        self.history_list.pack(fill="both", expand=True, padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(self.history_list)
        scrollbar.pack(side="right", fill="y")
        self.history_list.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.history_list.yview)
        
        btn_frame = ttk.Frame(history_frame)
        btn_frame.pack(fill="x", pady=5)
        
        ttk.Button(btn_frame, text=self.t("view_btn"), command=self.show_history).pack(side="left", padx=5)
        ttk.Button(btn_frame, text=self.t("delete_btn"), command=self.delete_history).pack(side="left", padx=5)
        ttk.Button(btn_frame, text=self.t("save_btn"), command=self.save_burger).pack(side="left", padx=5)
        ttk.Button(btn_frame, text=self.t("pdf_btn"), command=self.export_pdf).pack(side="left", padx=5)
        ttk.Button(btn_frame, text=self.t("share_btn"), command=self.share_burger).pack(side="left", padx=5)

    def generate_classic(self):
        """Génère un burger classique"""
        burger_type = self.classic_type.get()
        size = self.size_var.get()
        sauce = self.sauce_combo.get()
        
        # Base des ingrédients
        ingredients = self.trans["ingredients"]["classic"][burger_type].copy()
        
        # Ajustement de la taille
        if size == "Double":
            if "steak" in ingredients[1].lower() or "haché" in ingredients[1].lower():
                ingredients.insert(1, self.trans["ingredients"]["classic"]["Double steak"])
            elif "filet" in ingredients[1].lower() or "fillet" in ingredients[1].lower():
                ingredients.insert(1, self.trans["ingredients"]["classic"]["Double filet"])
        elif size == "Triple":
            if "steak" in ingredients[1].lower() or "haché" in ingredients[1].lower():
                ingredients[1:1] = [self.trans["ingredients"]["classic"]["Triple steak"]]
            elif "filet" in ingredients[1].lower() or "fillet" in ingredients[1].lower():
                ingredients[1:1] = [self.trans["ingredients"]["classic"]["Triple filet"]]
        
        # Calcul des calories
        base_calories = {
            "Hamburger": 500,
            "Cheeseburger": 600,
            "Bacon Burger": 750,
            "Chicken Burger": 450,
            "Fish Burger": 400,
            "Veggie Burger": 350
        }.get(burger_type, 500)

        calories = {
            "Simple": base_calories,
            "Double": int(base_calories * 1.8),
            "Triple": int(base_calories * 2.5)
        }.get(size, base_calories)

        self.current_burger = {
            "name": f"{size} {burger_type}",
            "ingredients": ingredients,
            "sauce": sauce,
            "sauce_desc": self.trans["sauces"][sauce],
            "calories": calories,
            "type": "classic"
        }
        self.show_result()

    def generate_extreme(self):
        """Génère un burger extrême"""
        level = int(self.crazy_level.get())
        vegan = self.vegan_extreme.get()

        # Sélection des ingrédients
        ingredient_type = "vegan" if vegan else "non_vegan"
        ingredients = []
        for lvl, items in self.trans["ingredients"]["extreme"][ingredient_type].items():
            if level >= int(lvl):
                ingredients.extend(items)

        # Sauce
        sauces = [
            "Rainbow mayo",
            "Banana ketchup", 
            "1000-spice sauce"
        ]
        sauce = random.choice(sauces[:min(level, len(sauces))])

        self.current_burger = {
            "name": f"{'Vegan ' if vegan else ''}Crazy Burger Level {level}",
            "ingredients": ingredients[:4],  # Limite à 4 ingrédients
            "sauce": sauce,
            "calories": 500 + level * 150,
            "type": "extreme"
        }
        self.show_result()

    def generate_zodiac(self):
        """Génère un burger du zodiaque"""
        sign_name = self.sign_var.get()
        sign_data = self.trans["zodiac_signs"][sign_name]
        
        # Ingrédients par élément
        element = sign_data["element"]
        ingredients = self.trans["ingredients"]["zodiac"][element]

        # Sauce par élément
        sauce = random.choice({
            "Fire": ["Spicy sauce", "BBQ sauce"],
            "Earth": ["Forest sauce", "Truffle sauce"],
            "Air": ["Light sauce", "Lemon sauce"],
            "Water": ["Hollandaise", "Tartar sauce"]
        }[element])

        self.current_burger = {
            "name": f"{sign_name} Burger {sign_data['emoji']}",
            "ingredients": ingredients,
            "sauce": sauce,
            "calories": random.randint(600, 900),
            "prediction": self.trans["zodiac_predictions"][sign_name],
            "type": "zodiac"
        }
        self.show_result()

    def show_result(self):
        """Affiche le résultat généré"""
        self.result_text.delete(1.0, tk.END)
        burger = self.current_burger
        
        # Titre avec emoji
        emoji = {
            "classic": "🍔",
            "extreme": "🌶️",
            "zodiac": "♈"
        }.get(burger["type"], "🍔")
        
        self.result_text.insert(tk.END, f"{emoji} {burger['name']} {emoji}\n\n", "title")
        
        # Ingrédients
        self.result_text.insert(tk.END, f"{self.t('ingredients_label')}\n", "bold")
        for ing in burger["ingredients"]:
            self.result_text.insert(tk.END, f"- {ing}\n")
        
        # Sauce
        if "sauce" in burger:
            self.result_text.insert(tk.END, f"\n{self.t('sauce_label')}: {burger['sauce']}\n", "bold")
            if "sauce_desc" in burger:
                self.result_text.insert(tk.END, f"({burger['sauce_desc']})\n")
        
        # Calories
        self.result_text.insert(tk.END, f"\n{self.t('calories_label')}: {burger['calories']} kcal\n", "bold")
        
        # Prédiction zodiac
        if burger["type"] == "zodiac":
            self.result_text.insert(tk.END, f"\n{self.t('prediction_label')}: {burger['prediction']}\n", "bold")
        
        # Charger une image aléatoire
        self.load_random_image()

    def load_random_image(self):
        """Charge une image aléatoire de burger"""
        try:
            img_dir = "burger_images"
            if os.path.exists(img_dir):
                images = [f for f in os.listdir(img_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]
                if images:
                    img_path = os.path.join(img_dir, random.choice(images))
                    img = Image.open(img_path)
                    img.thumbnail((300, 300))
                    self.burger_photo = ImageTk.PhotoImage(img)
                    self.img_label.config(image=self.burger_photo)
        except Exception as e:
            print(f"Error loading image: {e}")

    def load_history(self):
        """Charge l'historique depuis la base de données"""
        try:
            self.history_list.delete(0, tk.END)
            for row in self.cursor.execute("SELECT id, name FROM burgers ORDER BY created_at DESC LIMIT 20"):
                self.history_list.insert(tk.END, f"{row[0]} - {row[1]}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load history: {str(e)}")

    def show_history(self):
        """Affiche le burger sélectionné dans l'historique"""
        selection = self.history_list.curselection()
        if not selection:
            return
            
        item_id = self.history_list.get(selection[0]).split(" - ")[0]
        try:
            self.cursor.execute("SELECT * FROM burgers WHERE id=?", (item_id,))
            burger_data = self.cursor.fetchone()
            
            if burger_data:
                burger = {
                    "name": burger_data[1],
                    "ingredients": json.loads(burger_data[2]),
                    "sauce": burger_data[3],
                    "calories": burger_data[5],
                    "type": burger_data[7]
                }
                
                if burger["type"] == "zodiac":
                    burger["prediction"] = "Burger zodiacal" if self.language == "FR" else "Zodiac burger"
                
                self.current_burger = burger
                self.show_result()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load burger: {str(e)}")

    def delete_history(self):
        """Supprime le burger sélectionné de l'historique"""
        selection = self.history_list.curselection()
        if not selection:
            return
            
        if not messagebox.askyesno(
            "Confirmation",
            "Supprimer ce burger ?" if self.language == "FR" else "Delete this burger?"
        ):
            return
            
        item_id = self.history_list.get(selection[0]).split(" - ")[0]
        try:
            self.cursor.execute("DELETE FROM burgers WHERE id=?", (item_id,))
            self.conn.commit()
            self.load_history()
            messagebox.showinfo("Success", "Burger supprimé !" if self.language == "FR" else "Burger deleted!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete: {str(e)}")

    def update_zodiac_display(self, event=None):
        """Met à jour l'affichage du signe zodiacal"""
        sign_name = self.sign_var.get()
        sign_data = self.trans["zodiac_signs"].get(sign_name)
        if sign_data:
            self.element_label.config(
                text=f"{self.t('element')}: {sign_data['element']} {sign_data['emoji']}"
            )

    def save_burger(self):
        """Sauvegarde le burger actuel dans la base de données"""
        if self.current_burger:
            try:
                self.cursor.execute('''INSERT INTO burgers 
                                    (name, ingredients, sauce, diet, calories, created_at, burger_type)
                                    VALUES (?, ?, ?, ?, ?, ?, ?)''',
                                    (
                                        self.current_burger['name'],
                                        json.dumps(self.current_burger['ingredients']),
                                        self.current_burger.get('sauce', ''),
                                        self.current_burger.get('diet', ''),
                                        self.current_burger['calories'],
                                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                        self.current_burger['type']
                                    ))
                self.conn.commit()
                messagebox.showinfo("Success", "Burger sauvegardé !" if self.language == "FR" else "Burger saved!")
                self.load_history()
            except Exception as e:
                messagebox.showerror("Error", f"Erreur de sauvegarde : {str(e)}" if self.language == "FR" else f"Save error: {str(e)}")

    def export_pdf(self):
        """Exporte le burger actuel en PDF"""
        if not self.current_burger:
            return
            
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            
            burger = self.current_burger
            
            # Titre
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(200, 10, txt=burger['name'], ln=1, align='C')
            pdf.ln(10)
            
            # Ingrédients
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(200, 10, txt=self.t("ingredients_label"), ln=1)
            pdf.set_font("Arial", size=12)
            
            for ing in burger['ingredients']:
                pdf.cell(200, 10, txt=f"- {ing}", ln=1)
            
            # Sauce
            if 'sauce' in burger:
                pdf.ln(5)
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(40, 10, txt=self.t("sauce_label") + ":", ln=0)
                pdf.set_font("Arial", size=12)
                pdf.cell(0, 10, txt=burger['sauce'], ln=1)
            
            # Calories
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(40, 10, txt=self.t("calories_label") + ":", ln=0)
            pdf.set_font("Arial", size=12)
            pdf.cell(0, 10, txt=str(burger['calories']), ln=1)
            
            # Prédiction zodiac
            if burger.get('type') == "zodiac":
                pdf.ln(5)
                pdf.set_font("Arial", 'I', 12)
                pdf.multi_cell(0, 10, txt=burger['prediction'])
            
            # Sauvegarde du fichier
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                title="Enregistrer le PDF" if self.language == "FR" else "Save PDF"
            )
            
            if file_path:
                pdf.output(file_path)
                messagebox.showinfo("Success", f"PDF sauvegardé :\n{file_path}" if self.language == "FR" else f"PDF saved:\n{file_path}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Erreur PDF : {str(e)}" if self.language == "FR" else f"PDF error: {str(e)}")

    def share_burger(self):
        """Partage le burger sur les réseaux sociaux"""
        if self.current_burger:
            ingredients = ", ".join(self.current_burger['ingredients'])
            message = (f"Check out my burger: {self.current_burger['name']}!\n"
                      f"Ingredients: {ingredients}\n"
                      f"Calories: {self.current_burger['calories']} kcal\n"
                      f"#BurgerGenerator")
            
            if self.language == "FR":
                message = (f"Mon burger créé : {self.current_burger['name']} !\n"
                          f"Ingrédients : {ingredients}\n"
                          f"Calories : {self.current_burger['calories']} kcal\n"
                          f"#GénérateurDeBurger")
            
            webbrowser.open(f"https://twitter.com/intent/tweet?text={message}")

    def t(self, key):
        """Raccourci pour les traductions"""
        return self.trans.get(key, f"[{key}]")

    def set_language(self, lang):
        """Change la langue de l'application"""
        self.language = lang
        self.load_translations()
        # Reconstruit l'interface
        for widget in self.root.winfo_children():
            widget.destroy()
        self.setup_ui()

if __name__ == "__main__":
    root = tk.Tk()
    app = UltimateBurgerApp(root)
    root.mainloop()