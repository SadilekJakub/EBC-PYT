import datetime
import sqlite3
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
import database_manager as dat


class GUI:
    def __init__(self, root, conn):
        self.db = dat.DatabaseManager(conn)
        self.master = root
        self.master.title('Správa financí')
        self.master.resizable(False, False)

        # Načtení kategorií
        self.categories_list = self.get_categories_from_db() or []

        self.sort_var = ttk.StringVar(value="DESC")
        self.filter_cat_var = ttk.StringVar(value="all")

        # Boční panel
        self.sidebar = ttk.Frame(self.master, width=320, padding=20)
        self.sidebar.pack_propagate(False)
        self.sidebar.pack(side=LEFT, fill=Y)

        ttk.Separator(self.master, orient=VERTICAL).pack(side=LEFT, fill=Y, pady=20)

        # Hlavní plocha
        self.main_content = ttk.Frame(self.master, padding=20)
        self.main_content.pack(side=LEFT, fill=BOTH, expand=YES)

        self.top_dashboard = ttk.Frame(self.main_content)
        self.top_dashboard.pack(fill=X, pady=(0, 20))

        self.bottom_table_area = ttk.Frame(self.main_content)
        self.bottom_table_area.pack(fill=BOTH, expand=YES)

        self.add_transaction_menu()
        self.setup_dashboard_header()
        self.setup_filter_menu()
        self.setup_treeview()
        self.refresh_dashboard()
        self.master.state('zoomed')

    def setup_dashboard_header(self):
        # Karta pro zůstatek
        balance_card = ttk.Labelframe(self.top_dashboard, text="Zůstatek", padding=20)
        balance_card.pack(side=LEFT, fill=BOTH, expand=YES, padx=(0, 10))

        self.balance_label = ttk.Label(
            balance_card,
            text="- Kč",
            font=("Helvetica", 36, "bold"),
            bootstyle="success",
            anchor=CENTER
        )
        self.balance_label.pack(expand=YES, fill=BOTH)

        # Karta pro graf
        self.chart_container = ttk.Labelframe(self.top_dashboard, text="Přehled výdajů", padding=10)
        self.chart_container.pack(side=RIGHT, fill=BOTH, expand=YES, padx=(10, 0))

        self.pie_canvas = tk.Canvas(
            self.chart_container,
            width=200,
            height=200,
            bg=self.master.style.colors.bg,
            highlightthickness=0
        )
        self.pie_canvas.pack(side=LEFT, pady=10, padx=20)

        self.legend_frame = ttk.Frame(self.chart_container)
        self.legend_frame.pack(side=LEFT, fill=BOTH, expand=True, pady=10)

    def apply_filters(self):
        self.refresh_dashboard()

    def setup_treeview(self):
        columns = ("amount", "date", "name", "category")
        self.tree = ttk.Treeview(
            self.bottom_table_area,
            columns=columns,
            show="headings",
            bootstyle="primary"
        )

        self.tree.heading("amount", text="Částka")
        self.tree.heading("date", text="Datum")
        self.tree.heading("name", text="Název")
        self.tree.heading("category", text="Kategorie")

        self.tree.column("amount", width=120, anchor=CENTER)
        self.tree.column("date", width=120, anchor=CENTER)
        self.tree.column("name", width=300, anchor=CENTER)
        self.tree.column("category", width=250, anchor=CENTER)

        self.tree.pack(side=LEFT, fill=BOTH, expand=YES)

        scrollbar = ttk.Scrollbar(self.bottom_table_area, orient=VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=RIGHT, fill=Y)
        # když double click otevři okno
        self.tree.bind("<Double-1>", self.open_edit_window)

    def get_categories_from_db(self):
        if dat:
            try:
                categories = self.db.select_all_from_category()
                if categories:
                    list_from_db = [c[0] if isinstance(c, tuple) else c for c in categories]
                    return list_from_db + ["+ Přidat novou..."]
            except Exception as e:
                print(f"Chyba při načítání kategorií: {e}")
        return ["+ Přidat novou..."]

    def add_transaction_menu(self):
        menu_frame = ttk.Labelframe(self.sidebar, text="Přidat záznam", padding=15)
        menu_frame.pack(fill=X, pady=10)

        ttk.Label(menu_frame, text="Částka:").pack(anchor=W)
        self.entry_amount = ttk.Entry(menu_frame, font=("Helvetica", 14))
        self.entry_amount.pack(fill=X, pady=(5, 15))

        date_str = datetime.datetime.now().strftime('%Y-%m-%d')
        ttk.Label(menu_frame, text="Datum:").pack(anchor=W)
        self.entry_date = ttk.Entry(menu_frame)
        self.entry_date.pack(fill=X, pady=(5, 15))
        self.entry_date.insert(0, date_str)

        ttk.Label(menu_frame, text="Název:").pack(anchor=W)
        self.entry_name = ttk.Entry(menu_frame)
        self.entry_name.pack(fill=X, pady=(5, 15))

        ttk.Label(menu_frame, text="Kategorie:").pack(anchor=W)
        self.combo_category = ttk.Combobox(
            menu_frame,
            values=self.categories_list,
            state="readonly"
        )
        self.combo_category.pack(fill=X, pady=(5, 25))
        if self.categories_list:
            self.combo_category.current(0)
        #při změne kategorie se spustí on_category_change ktery otevře okno na přidani pokud se vybere přidani katagorie
        self.combo_category.bind("<<ComboboxSelected>>", self.on_category_change)

        submit_btn = ttk.Button(
            menu_frame,
            text="Uložit",
            bootstyle=SUCCESS,
            command=self.save_transaction_data,
            width=20
        )
        submit_btn.pack(pady=10)

    def setup_filter_menu(self):
        filter_frame = ttk.Frame(self.bottom_table_area, padding=(0, 0, 0, 10))
        filter_frame.pack(fill=X)

        ttk.Label(filter_frame, text="Kategorie:").pack(side=LEFT, padx=(0, 5))
        #přidani all a odstraneni "+ Přidat novou..."
        filter_values = ["all"] + list(filter(lambda x: x != "+ Přidat novou...", self.categories_list))
        self.filter_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.filter_cat_var,
            values=filter_values,
            state="readonly",
            width=20
        )
        self.filter_combo.pack(side=LEFT, padx=(0, 20))
        #Když se zmeni kategorie aplikují se změny
        self.filter_combo.bind("<<ComboboxSelected>>", self.apply_filters)

        ttk.Label(filter_frame, text="Seřadit:").pack(side=LEFT, padx=(0, 5))

        rb_desc = ttk.Radiobutton(
            filter_frame,
            text="Nejnovější",
            variable=self.sort_var,
            value="DESC",
            bootstyle="info-toolbutton",
            command=self.apply_filters
        )
        rb_desc.pack(side=LEFT, padx=2)

        rb_asc = ttk.Radiobutton(
            filter_frame,
            text="Nejstarší",
            variable=self.sort_var,
            value="ASC",
            bootstyle="info-toolbutton",
            command=self.apply_filters
        )
        rb_asc.pack(side=LEFT, padx=2)

    def save_transaction_data(self):
        try:
            raw_amount = self.entry_amount.get().replace(',', '.')
            if not raw_amount:
                raise ValueError("Prázdné pole")

            amount = float(raw_amount)

            if amount <= 0:
                Messagebox.show_error("Částka musí být větší než nula.", title="Chyba zadání")
                return

        except ValueError:
            Messagebox.show_error("Zadejte platné číslo.", title="Chyba zadání")
            return

        date_str = self.entry_date.get()
        try:
            datetime.datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            Messagebox.show_error("Datum musí být ve formátu RRRR-MM-DD.", title="Špatné datum")
            return

        name = self.entry_name.get().strip()
        if not name:
            Messagebox.show_warning("Zadejte název.", title="Chybí údaje")
            return

        try:
            category = self.combo_category.get()
            self.db.add_transaction(name, amount, category, date_str)
            # Po uložení vyčistí formulář
            self.entry_amount.delete(0, END)
            self.entry_name.delete(0, END)

            self.refresh_dashboard()
        except Exception as e:
            Messagebox.show_error(f"Nepodařilo se uložit data: {e}", title="Chyba databáze")

    def on_category_change(self, event):
        if self.combo_category.get() == "+ Přidat novou...":
            self.open_add_category_window()

    def open_add_category_window(self):
        new_win = ttk.Toplevel(self.master)
        new_win.title("Nová kategorie")
        new_win.geometry("300x320")

        ttk.Label(new_win, text="Název:").pack(pady=(10, 5))
        cat_name_entry = ttk.Entry(new_win)
        cat_name_entry.pack(pady=5, padx=10, fill=X)

        ttk.Label(new_win, text="Barva (Hex, např. ff0000):").pack(pady=5)
        cat_color_entry = ttk.Entry(new_win)
        cat_color_entry.pack(pady=5, padx=10, fill=X)

        ttk.Label(new_win, text="Typ:").pack(pady=5)
        is_income = ttk.BooleanVar(value=True)
        ttk.Radiobutton(new_win, text="Příjem", variable=is_income, value=True).pack()
        ttk.Radiobutton(new_win, text="Výdaj", variable=is_income, value=False).pack()

        def save_new_cat():
            name = cat_name_entry.get()
            color = cat_color_entry.get()

            if name:
                try:
                    self.db.add_category(name, color, is_income.get())
                    self.categories_list = self.get_categories_from_db()
                    self.combo_category['values'] = self.categories_list
                    self.combo_category.set(name)

                    filter_values = ["all"] + list(filter(lambda x: x != "+ Přidat novou...", self.categories_list))
                    self.filter_combo['values'] = filter_values

                    new_win.destroy()
                except Exception as e:
                    print(f"Chyba: {e}")

        ttk.Button(new_win, text="Uložit", command=save_new_cat, bootstyle=SUCCESS).pack(pady=20)

    def load_transactions(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        data = self.db.select_all_from_transaction(
            asc_desc=self.sort_var.get(),
            category=self.filter_cat_var.get()
        )
        if data:
            for row in data:
                self.tree.insert('', END, iid=row[0], values=(f"{row[1]} Kč", row[2], row[3], row[4]))

    def draw_chart(self, data_list):
        self.pie_canvas.delete("all")

        # Smaže starou legendu
        for widget in self.legend_frame.winfo_children():
            widget.destroy()

        if not data_list:
            self.pie_canvas.create_text(100, 100, text="Zatím žádná data.", fill="white")
            return

        total = sum(row[2] for row in data_list)
        if total <= 0:
            return

        start_angle = 0
        for name, hex_color, value in data_list:
            extent = (value / total) * 360

            clean_color = str(hex_color).strip()
            if clean_color.startswith('#'):
                color = clean_color
            elif len(clean_color) in (3, 6):
                color = f"#{clean_color}"
            else:
                color = "gray"

            self.pie_canvas.create_arc(
                (10, 10, 190, 190),
                start=start_angle,
                extent=extent,
                fill=color,
                outline="white"
            )
            start_angle += extent


            row_frame = ttk.Frame(self.legend_frame)
            row_frame.pack(fill=X, pady=2)

            color_box = tk.Canvas(row_frame, width=15, height=15, bg=color, highlightthickness=1,
                                  highlightbackground="white")
            color_box.pack(side=LEFT, padx=(0, 5))

            ttk.Label(row_frame, text=f"{name} ({value} Kč)", font=("Arial", 10)).pack(side=LEFT)

    def refresh_dashboard(self):
        self.load_transactions()

        # Vykresleni grafu
        if hasattr(self, 'pie_canvas'):
            exp_data = self.db.sum_by_category()
            self.draw_chart(exp_data)

        # Aktualizace zůstatku
        new_balance = self.db.sum_all()
        val = new_balance[0][0] if isinstance(new_balance, list) else new_balance

        color = "success" if float(val) >= 0 else "danger"
        self.balance_label.config(text=f"{val} Kč", bootstyle=color)

    # uprava či odstraneni transakce
    def open_edit_window(self, event):
        selected_item = self.tree.selection()
        if not selected_item:
            return

        transaction_id = selected_item[0]
        values = self.tree.item(transaction_id, 'values')

        old_amount = values[0].replace(' Kč', '').strip()
        old_date = values[1]
        old_name = values[2]
        old_category = values[3]

        edit_win = ttk.Toplevel(self.master)
        edit_win.title("Úprava transakce")
        edit_win.geometry("350x450")

        ttk.Label(edit_win, text="Částka:").pack(pady=(10, 5), anchor=W, padx=20)
        entry_amount = ttk.Entry(edit_win, font=("Helvetica", 14))
        entry_amount.insert(0, old_amount)
        entry_amount.pack(fill=X, padx=20)

        ttk.Label(edit_win, text="Datum:").pack(pady=(10, 5), anchor=W, padx=20)
        entry_date = ttk.Entry(edit_win)
        entry_date.insert(0, old_date)
        entry_date.pack(fill=X, padx=20)

        ttk.Label(edit_win, text="Název:").pack(pady=(10, 5), anchor=W, padx=20)
        entry_name = ttk.Entry(edit_win)
        entry_name.insert(0, old_name)
        entry_name.pack(fill=X, padx=20)

        ttk.Label(edit_win, text="Kategorie:").pack(pady=(10, 5), anchor=W, padx=20)
        combo_category = ttk.Combobox(edit_win, values=self.categories_list, state="readonly")
        combo_category.set(old_category)
        combo_category.pack(fill=X, padx=20)

        def save_changes():
            try:
                new_amount = float(entry_amount.get().replace(',', '.'))
                new_date = entry_date.get()
                new_name = entry_name.get()
                new_category = combo_category.get()

                self.db.update_transaction( transaction_id, new_name, new_amount, new_category, new_date)

                self.refresh_dashboard()
                edit_win.destroy()
                Messagebox.show_info("Transakce upravena.", title="Úspěch", parent=self.master)
            except Exception as e:
                Messagebox.show_error(f"Chyba: {e}", title="Chyba", parent=edit_win)

        # smazání transakce
        def delete_record():
            self.db.delete_transaction( transaction_id)
            self.refresh_dashboard()
            edit_win.destroy()
            Messagebox.show_info("Transakce smazána.", title="Smazáno", parent=self.master)

        # Tlačítka
        btn_frame = ttk.Frame(edit_win)
        btn_frame.pack(fill=X, pady=30, padx=20)

        ttk.Button(btn_frame, text="Uložit změny", bootstyle=SUCCESS, command=save_changes).pack(side=LEFT, expand=YES, fill=X, padx=(0, 5))
        ttk.Button(btn_frame, text="Smazat", bootstyle=DANGER, command=delete_record).pack(side=RIGHT, expand=YES, fill=X, padx=(5, 0))