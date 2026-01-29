import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, timedelta
from calendar import monthrange
import locale
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "compras.db")

# Configurar locale a español
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_TIME, 'Spanish_Spain.1252')
    except:
        pass


class GestorCompras:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestor de Compras y Cuotas")
        self.root.geometry("950x600")

        self.init_db()
        self.fecha_actual = datetime.now()

        self.crear_interfaz()
        self.actualizar_vista()

    # ===============================
    # BASE DE DATOS
    # ===============================
    def init_db(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS compras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descripcion TEXT NOT NULL,
                monto REAL NOT NULL,
                tipo TEXT NOT NULL,
                mes_desde TEXT,
                mes_hasta TEXT,
                fecha_creacion TEXT,
                estado TEXT
            )
        """)
        self.conn.commit()

    # ===============================
    # INTERFAZ
    # ===============================
    def crear_interfaz(self):
        frame_ingreso = tk.LabelFrame(self.root, text="Gasto Fijo o Compra", padx=10, pady=10)
        frame_ingreso.pack(fill="x", padx=10, pady=5)

        tk.Label(frame_ingreso, text="Descripción:").grid(row=0, column=0, sticky="w")
        self.entry_desc = tk.Entry(frame_ingreso, width=30)
        self.entry_desc.grid(row=0, column=1, padx=5)

        tk.Label(frame_ingreso, text="Monto:").grid(row=0, column=2, sticky="w")
        self.entry_monto = tk.Entry(frame_ingreso, width=15)
        self.entry_monto.grid(row=0, column=3, padx=5)

        tk.Label(frame_ingreso, text="Tipo:").grid(row=1, column=0, sticky="w")
        self.tipo_var = tk.StringVar(value="fijo")

        frame_tipo = tk.Frame(frame_ingreso)
        frame_tipo.grid(row=1, column=1, columnspan=3, sticky="w")

        tk.Radiobutton(frame_tipo, text="Fijo", variable=self.tipo_var,
                       value="fijo", command=self.toggle_cuotas).pack(side="left")
        tk.Radiobutton(frame_tipo, text="Cuotas", variable=self.tipo_var,
                       value="cuotas", command=self.toggle_cuotas).pack(side="left")

        self.frame_cuotas = tk.Frame(frame_ingreso)
        self.frame_cuotas.grid(row=2, column=0, columnspan=4, pady=5)

        tk.Label(self.frame_cuotas, text="Desde:").pack(side="left")
        self.entry_desde = tk.Entry(self.frame_cuotas, width=10)
        self.entry_desde.pack(side="left", padx=5)
        self.entry_desde.insert(0, datetime.now().strftime("%m/%Y"))

        tk.Label(self.frame_cuotas, text="Hasta:").pack(side="left")
        self.entry_hasta = tk.Entry(self.frame_cuotas, width=10)
        self.entry_hasta.pack(side="left", padx=5)

        tk.Button(
            frame_ingreso,
            text="Agregar Compra",
            command=self.agregar_compra,
            bg="#4CAF50",
            fg="white"
        ).grid(row=3, column=0, columnspan=4, pady=10)

        self.frame_cuotas.grid_remove()

        frame_nav = tk.Frame(self.root)
        frame_nav.pack(fill="x", padx=10, pady=10)

        tk.Button(frame_nav, text="◄ Mes Anterior", command=self.mes_anterior).pack(side="left")
        self.label_mes = tk.Label(frame_nav, text="", font=("Arial", 14, "bold"))
        self.label_mes.pack(side="left", expand=True)
        tk.Button(frame_nav, text="Hoy", command=self.ir_hoy).pack(side="right")
        tk.Button(frame_nav, text="Mes Siguiente ►", command=self.mes_siguiente).pack(side="right")

        frame_tabla = tk.Frame(self.root)
        frame_tabla.pack(fill="both", expand=True, padx=10)

        scrollbar = tk.Scrollbar(frame_tabla)
        scrollbar.pack(side="right", fill="y")

        self.tree = ttk.Treeview(
            frame_tabla,
            columns=("Descripción", "Monto", "Tipo", "Periodo", "Estado"),
            show="headings",
            yscrollcommand=scrollbar.set
        )
        scrollbar.config(command=self.tree.yview)

        for col in ("Descripción", "Monto", "Tipo", "Periodo", "Estado"):
            self.tree.heading(col, text=col)

        self.tree.column("Descripción", width=280)
        self.tree.column("Monto", width=100)
        self.tree.column("Tipo", width=80)
        self.tree.column("Periodo", width=180)
        self.tree.column("Estado", width=220)

        self.tree.tag_configure("pendiente", background="#ffe5e5")
        self.tree.tag_configure("pagado", background="#e6ffe6")

        self.tree.pack(fill="both", expand=True)

        tk.Button(self.root, text="Marcar como Pagado",
                  command=self.marcar_pagado,
                  bg="#2196F3", fg="white").pack(pady=5)

        tk.Button(self.root, text="Eliminar Seleccionado",
                  command=self.eliminar_compra,
                  bg="#f44336", fg="white").pack(pady=5)

        self.label_total = tk.Label(self.root, text="Total: $0.00",
                                    font=("Arial", 16, "bold"))
        self.label_total.pack(pady=10)

    # ===============================
    # FUNCIONALIDAD
    # ===============================
    def toggle_cuotas(self):
        if self.tipo_var.get() == "cuotas":
            self.frame_cuotas.grid()
        else:
            self.frame_cuotas.grid_remove()

    def agregar_compra(self):
        desc = self.entry_desc.get().strip()
        monto = self.entry_monto.get().strip()
        tipo = self.tipo_var.get()

        if not desc or not monto:
            messagebox.showwarning("Advertencia", "Completa descripción y monto")
            return

        try:
            monto = float(monto)
        except ValueError:
            messagebox.showerror("Error", "Monto inválido")
            return

        mes_desde = mes_hasta = None
        if tipo == "cuotas":
            mes_desde = self.entry_desde.get().strip()
            mes_hasta = self.entry_hasta.get().strip()

        self.cursor.execute("""
            INSERT INTO compras
            (descripcion, monto, tipo, mes_desde, mes_hasta, fecha_creacion, estado)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            desc, monto, tipo, mes_desde, mes_hasta,
            datetime.now().strftime("%Y-%m-%d"),
            "Pendiente"
        ))
        self.conn.commit()

        self.entry_desc.delete(0, tk.END)
        self.entry_monto.delete(0, tk.END)
        self.actualizar_vista()

    def actualizar_vista(self):
        self.tree.delete(*self.tree.get_children())

        meses = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]
        self.label_mes.config(text=f"{meses[self.fecha_actual.month-1]} {self.fecha_actual.year}")

        mes_actual = self.fecha_actual.strftime("%m/%Y")
        self.cursor.execute("SELECT * FROM compras")
        compras = self.cursor.fetchall()

        total = 0
        for c in compras:
            idc, desc, monto, tipo, desde, hasta, _, estado = c

            incluir = tipo == "fijo" or (
                tipo == "cuotas" and self.mes_en_rango(mes_actual, desde, hasta)
            )

            if incluir:
                tag = "pagado" if estado.startswith("Pagado") else "pendiente"
                periodo = "Fijo" if tipo == "fijo" else f"{desde} - {hasta}"

                self.tree.insert(
                    "", "end",
                    values=(desc, f"${monto:.2f}", tipo.capitalize(), periodo, estado),
                    tags=(idc, tag)
                )
                total += monto

        self.label_total.config(text=f"Total: ${total:.2f}")

    def mes_en_rango(self, actual, desde, hasta):
        try:
            a = datetime.strptime(actual, "%m/%Y")
            d = datetime.strptime(desde, "%m/%Y")
            h = datetime.strptime(hasta, "%m/%Y")
            return d <= a <= h
        except:
            return False

    def marcar_pagado(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Advertencia", "Selecciona una compra")
            return

        item = self.tree.item(sel[0])
        estado_actual = item["values"][4]

        if estado_actual.startswith("Pagado"):
            messagebox.showinfo("Info", "Esta compra ya está pagada")
            return

        id_compra = item["tags"][0]
        fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
        estado = f"Pagado, {fecha}"

        self.cursor.execute(
            "UPDATE compras SET estado = ? WHERE id = ?",
            (estado, id_compra)
        )
        self.conn.commit()
        self.actualizar_vista()

    def eliminar_compra(self):
        sel = self.tree.selection()
        if not sel:
            return

        if messagebox.askyesno("Confirmar", "¿Eliminar esta compra?"):
            id_compra = self.tree.item(sel[0])["tags"][0]
            self.cursor.execute("DELETE FROM compras WHERE id = ?", (id_compra,))
            self.conn.commit()
            self.actualizar_vista()

    def mes_anterior(self):
        self.fecha_actual = self.fecha_actual.replace(day=1) - timedelta(days=1)
        self.actualizar_vista()

    def mes_siguiente(self):
        ultimo = monthrange(self.fecha_actual.year, self.fecha_actual.month)[1]
        self.fecha_actual = self.fecha_actual.replace(day=ultimo) + timedelta(days=1)
        self.actualizar_vista()

    def ir_hoy(self):
        self.fecha_actual = datetime.now()
        self.actualizar_vista()

    def __del__(self):
        if hasattr(self, "conn"):
            self.conn.close()


if __name__ == "__main__":
    root = tk.Tk()
    app = GestorCompras(root)
    root.mainloop()
