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
        pass  # Si no se puede configurar, usar inglés

class GestorCompras:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestor de Compras y Cuotas")
        self.root.geometry("900x600")
        
        # Inicializar BD
        self.init_db()
        
        # Fecha actual
        self.fecha_actual = datetime.now()
        
        # Crear interfaz
        self.crear_interfaz()
        
        # Cargar datos del mes actual
        self.actualizar_vista()
    
    def init_db(self):
        """Inicializa la base de datos"""
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS compras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descripcion TEXT NOT NULL,
                monto REAL NOT NULL,
                tipo TEXT NOT NULL,
                mes_desde TEXT,
                mes_hasta TEXT,
                fecha_creacion TEXT
            )
        ''')
        self.conn.commit()
    
    def crear_interfaz(self):
        """Crea la interfaz gráfica"""
        # Frame superior para ingreso de datos
        frame_ingreso = tk.LabelFrame(self.root, text="Gasto Fijo o Compra", padx=10, pady=10)
        frame_ingreso.pack(fill="x", padx=10, pady=5)
        
        # Descripción
        tk.Label(frame_ingreso, text="Descripción:").grid(row=0, column=0, sticky="w", pady=5)
        self.entry_desc = tk.Entry(frame_ingreso, width=30)
        self.entry_desc.grid(row=0, column=1, pady=5, padx=5)
        
        # Monto
        tk.Label(frame_ingreso, text="Monto:").grid(row=0, column=2, sticky="w", pady=5)
        self.entry_monto = tk.Entry(frame_ingreso, width=15)
        self.entry_monto.grid(row=0, column=3, pady=5, padx=5)
        
        # Tipo
        tk.Label(frame_ingreso, text="Tipo:").grid(row=1, column=0, sticky="w", pady=5)
        self.tipo_var = tk.StringVar(value="fijo")
        frame_tipo = tk.Frame(frame_ingreso)
        frame_tipo.grid(row=1, column=1, columnspan=3, sticky="w")
        
        tk.Radiobutton(frame_tipo, text="Fijo", variable=self.tipo_var, 
                      value="fijo", command=self.toggle_cuotas).pack(side="left")
        tk.Radiobutton(frame_tipo, text="Cuotas", variable=self.tipo_var, 
                      value="cuotas", command=self.toggle_cuotas).pack(side="left")
        
        # Frame para cuotas
        self.frame_cuotas = tk.Frame(frame_ingreso)
        self.frame_cuotas.grid(row=2, column=0, columnspan=4, pady=5)
        
        tk.Label(self.frame_cuotas, text="Desde:").pack(side="left", padx=5)
        self.entry_desde = tk.Entry(self.frame_cuotas, width=10)
        self.entry_desde.pack(side="left", padx=5)
        self.entry_desde.insert(0, datetime.now().strftime("%m/%Y"))
        
        tk.Label(self.frame_cuotas, text="Hasta:").pack(side="left", padx=5)
        self.entry_hasta = tk.Entry(self.frame_cuotas, width=10)
        self.entry_hasta.pack(side="left", padx=5)
        
        # Botón agregar
        tk.Button(frame_ingreso, text="Agregar Compra", command=self.agregar_compra,
                 bg="#4CAF50", fg="white", padx=20).grid(row=3, column=0, columnspan=4, pady=10)
        
        # Ocultar frame de cuotas inicialmente
        self.frame_cuotas.grid_remove()
        
        # Frame de navegación
        frame_nav = tk.Frame(self.root)
        frame_nav.pack(fill="x", padx=10, pady=10)
        
        tk.Button(frame_nav, text="◄ Mes Anterior", command=self.mes_anterior).pack(side="left", padx=5)
        self.label_mes = tk.Label(frame_nav, text="", font=("Arial", 14, "bold"))
        self.label_mes.pack(side="left", expand=True)
        tk.Button(frame_nav, text="Mes Siguiente ►", command=self.mes_siguiente).pack(side="right", padx=5)
        tk.Button(frame_nav, text="Hoy", command=self.ir_hoy).pack(side="right", padx=5)
        
        # Frame para la tabla
        frame_tabla = tk.Frame(self.root)
        frame_tabla.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(frame_tabla)
        scrollbar.pack(side="right", fill="y")
        
        # Treeview
        self.tree = ttk.Treeview(frame_tabla, columns=("Descripción", "Monto", "Tipo", "Periodo"),
                                show="headings", yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.tree.yview)
        
        self.tree.heading("Descripción", text="Descripción")
        self.tree.heading("Monto", text="Monto")
        self.tree.heading("Tipo", text="Tipo")
        self.tree.heading("Periodo", text="Periodo")
        
        self.tree.column("Descripción", width=300)
        self.tree.column("Monto", width=100)
        self.tree.column("Tipo", width=100)
        self.tree.column("Periodo", width=200)
        
        self.tree.pack(fill="both", expand=True)
        
        # Botón eliminar
        tk.Button(self.root, text="Eliminar Seleccionado", command=self.eliminar_compra,
                 bg="#f44336", fg="white").pack(pady=5)
        
        # Label total
        self.label_total = tk.Label(self.root, text="Total: $0.00", 
                                   font=("Arial", 16, "bold"))
        self.label_total.pack(pady=10)
    
    def toggle_cuotas(self):
        """Muestra u oculta el frame de cuotas según el tipo"""
        if self.tipo_var.get() == "cuotas":
            self.frame_cuotas.grid()
        else:
            self.frame_cuotas.grid_remove()
    
    def agregar_compra(self):
        """Agrega una nueva compra a la BD"""
        desc = self.entry_desc.get().strip()
        monto = self.entry_monto.get().strip()
        tipo = self.tipo_var.get()
        
        if not desc or not monto:
            messagebox.showwarning("Advertencia", "Completa descripción y monto")
            return
        
        try:
            monto = float(monto)
        except ValueError:
            messagebox.showerror("Error", "El monto debe ser un número")
            return
        
        mes_desde = None
        mes_hasta = None
        
        if tipo == "cuotas":
            mes_desde = self.entry_desde.get().strip()
            mes_hasta = self.entry_hasta.get().strip()
            
            if not mes_desde or not mes_hasta:
                messagebox.showwarning("Advertencia", "Completa las fechas de las cuotas")
                return
        
        self.cursor.execute('''
            INSERT INTO compras (descripcion, monto, tipo, mes_desde, mes_hasta, fecha_creacion)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (desc, monto, tipo, mes_desde, mes_hasta, datetime.now().strftime("%Y-%m-%d")))
        
        self.conn.commit()
        
        # Limpiar campos
        self.entry_desc.delete(0, tk.END)
        self.entry_monto.delete(0, tk.END)
        self.entry_desde.delete(0, tk.END)
        self.entry_hasta.delete(0, tk.END)
        self.entry_desde.insert(0, datetime.now().strftime("%m/%Y"))
        
        self.actualizar_vista()
        messagebox.showinfo("Éxito", "Compra agregada correctamente")
    
    def mes_anterior(self):
        """Navega al mes anterior"""
        primer_dia = self.fecha_actual.replace(day=1)
        self.fecha_actual = primer_dia - timedelta(days=1)
        self.actualizar_vista()
    
    def mes_siguiente(self):
        """Navega al mes siguiente"""
        ultimo_dia = monthrange(self.fecha_actual.year, self.fecha_actual.month)[1]
        self.fecha_actual = self.fecha_actual.replace(day=ultimo_dia) + timedelta(days=1)
        self.actualizar_vista()
    
    def ir_hoy(self):
        """Vuelve al mes actual"""
        self.fecha_actual = datetime.now()
        self.actualizar_vista()
    
    def actualizar_vista(self):
        """Actualiza la vista con las compras del mes actual"""
        # Limpiar tabla
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Actualizar label del mes con nombres en español
        meses = {
            1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
            5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
            9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
        }
        mes_texto = f"{meses[self.fecha_actual.month]} {self.fecha_actual.year}"
        self.label_mes.config(text=mes_texto)
        
        # Obtener compras
        mes_actual = self.fecha_actual.strftime("%m/%Y")
        
        self.cursor.execute('SELECT * FROM compras')
        compras = self.cursor.fetchall()
        
        total = 0
        
        for compra in compras:
            id_compra, desc, monto, tipo, mes_desde, mes_hasta, fecha_creacion = compra
            
            incluir = False
            periodo_texto = ""
            
            if tipo == "fijo":
                incluir = True
                periodo_texto = "Fijo"
            elif tipo == "cuotas":
                if self.mes_en_rango(mes_actual, mes_desde, mes_hasta):
                    incluir = True
                    periodo_texto = f"{mes_desde} - {mes_hasta}"
            
            if incluir:
                self.tree.insert("", "end", values=(desc, f"${monto:.2f}", tipo.capitalize(), periodo_texto),
                               tags=(id_compra,))
                total += monto
        
        self.label_total.config(text=f"Total: ${total:.2f}")
    
    def mes_en_rango(self, mes_actual, mes_desde, mes_hasta):
        """Verifica si un mes está en el rango de cuotas"""
        try:
            mes_act = datetime.strptime(mes_actual, "%m/%Y")
            desde = datetime.strptime(mes_desde, "%m/%Y")
            hasta = datetime.strptime(mes_hasta, "%m/%Y")
            return desde <= mes_act <= hasta
        except:
            return False
    
    def eliminar_compra(self):
        """Elimina la compra seleccionada"""
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Selecciona una compra para eliminar")
            return
        
        if messagebox.askyesno("Confirmar", "¿Eliminar esta compra?"):
            item = self.tree.item(seleccion[0])
            id_compra = item['tags'][0]
            
            self.cursor.execute('DELETE FROM compras WHERE id = ?', (id_compra,))
            self.conn.commit()
            
            self.actualizar_vista()
            messagebox.showinfo("Éxito", "Compra eliminada")
    
    def __del__(self):
        """Cierra la conexión a la BD"""
        if hasattr(self, 'conn'):
            self.conn.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = GestorCompras(root)
    root.mainloop()