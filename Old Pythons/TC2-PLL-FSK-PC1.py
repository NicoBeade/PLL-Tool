import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import serial
import serial.tools.list_ports
import threading
import time
import os

class FSKInterfaceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Terminal de Control FSK - Arduino")
        self.root.geometry("800x700") # Aumenté un poco la altura para el logo
        
        # Variables de control
        self.serial_port = None
        self.is_connected = False
        self.rx_thread = None

        # --- SECCIÓN HEADER: LOGO Y TÍTULO ---
        frame_header = tk.Frame(root, bg="white")
        frame_header.pack(fill="x", side="top")
        
        # Intentar cargar logo
        self.logo_image = None
        try:
            # Busca 'logo.png' en el directorio actual
            if os.path.exists("logo.png"):
                # Cargamos la imagen original
                raw_image = tk.PhotoImage(file="logo.png")
                
                # --- Lógica de Redimensionado Automático ---
                # Tkinter estándar solo permite redimensionar por factores enteros (1/2, 1/3, etc.)
                # Calculamos el factor necesario para que la altura sea aprox 90px
                current_height = raw_image.height()
                target_height = 90
                
                if current_height > target_height:
                    # Calculamos el factor de reducción (ej: si mide 500 y queremos 90 -> factor 5)
                    scale_factor = int(current_height / target_height)
                    if scale_factor < 1: 
                        scale_factor = 1 # Evitar división por cero o errores
                    
                    self.logo_image = raw_image.subsample(scale_factor, scale_factor)
                else:
                    # Si es pequeña, la dejamos igual
                    self.logo_image = raw_image

                lbl_logo = tk.Label(frame_header, image=self.logo_image, bg="white")
                lbl_logo.pack(side="left", padx=10, pady=5)
            else:
                lbl_logo = tk.Label(frame_header, text="[LOGO]", font=("Arial", 12, "bold"), bg="#ddd", width=10)
                lbl_logo.pack(side="left", padx=10, pady=5)
        except Exception:
            pass

        lbl_title = tk.Label(frame_header, text="Transmisor FSK - 300 Baudios", font=("Helvetica", 16, "bold"), bg="white", fg="#333")
        lbl_title.pack(side="left", padx=20)


        # --- SECCIÓN SUPERIOR: CONFIGURACIÓN SERIAL ---
        frame_config = ttk.LabelFrame(root, text="Configuración de Conexión")
        frame_config.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame_config, text="Puerto:").pack(side="left", padx=5)
        
        self.combo_ports = ttk.Combobox(frame_config, width=15)
        self.combo_ports.pack(side="left", padx=5)
        self.refresh_ports()

        self.btn_refresh = ttk.Button(frame_config, text="Refrescar", command=self.refresh_ports)
        self.btn_refresh.pack(side="left", padx=5)

        ttk.Label(frame_config, text="Baudios:").pack(side="left", padx=5)
        self.combo_baud = ttk.Combobox(frame_config, values=["9600", "115200"], width=10, state="readonly")
        self.combo_baud.current(0) # Default 9600 (para coincidir con el Arduino)
        self.combo_baud.pack(side="left", padx=5)

        self.btn_connect = ttk.Button(frame_config, text="Conectar", command=self.toggle_connection)
        self.btn_connect.pack(side="left", padx=10)

        # --- SECCIÓN CENTRAL: PANTALLAS ---
        paned_window = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        paned_window.pack(fill="both", expand=True, padx=10, pady=5)

        # 1. Panel Izquierdo: Debug Arduino (RX)
        frame_rx = ttk.LabelFrame(paned_window, text="Debug Arduino (RX)")
        paned_window.add(frame_rx, weight=1)
        
        self.text_debug = scrolledtext.ScrolledText(frame_rx, height=20, state='disabled', bg="#f0f0f0", fg="#003366")
        self.text_debug.pack(fill="both", expand=True, padx=5, pady=5)

        # 2. Panel Derecho: Texto Enviado (TX)
        frame_tx = ttk.LabelFrame(paned_window, text="Historial de Envíos (TX)")
        paned_window.add(frame_tx, weight=1)
        
        self.text_sent = scrolledtext.ScrolledText(frame_tx, height=20, state='disabled', bg="#f0fff0", fg="#006600")
        self.text_sent.pack(fill="both", expand=True, padx=5, pady=5)

        # --- SECCIÓN INFERIOR: ENTRADA DE TEXTO ---
        frame_input = ttk.LabelFrame(root, text="Enviar Mensaje")
        frame_input.pack(fill="x", padx=10, pady=5)

        self.entry_msg = ttk.Entry(frame_input)
        self.entry_msg.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        self.entry_msg.bind("<Return>", lambda event: self.send_message()) # Enviar al presionar Enter

        self.btn_send = ttk.Button(frame_input, text="Enviar Texto", command=self.send_message)
        self.btn_send.pack(side="right", padx=5, pady=5)

        # --- FOOTER: CRÉDITOS ---
        lbl_credits = tk.Label(
            root, 
            text="Creado por Nicolás Beade y Javier Petrucci para la evaluación de Laboratorio de Electrónica II (25.16)", 
            font=("Arial", 9, "italic"), 
            fg="gray",
            pady=10
        )
        lbl_credits.pack(side="bottom", fill="x")

    def refresh_ports(self):
        """Busca los puertos COM disponibles."""
        ports = serial.tools.list_ports.comports()
        self.combo_ports['values'] = [port.device for port in ports]
        if ports:
            self.combo_ports.current(0)

    def toggle_connection(self):
        """Maneja la conexión y desconexión del puerto serial."""
        if not self.is_connected:
            self.connect()
        else:
            self.disconnect()

    def connect(self):
        port = self.combo_ports.get()
        baud = self.combo_baud.get()

        if not port:
            messagebox.showerror("Error", "Seleccione un puerto COM.")
            return

        try:
            self.serial_port = serial.Serial(port, baud, timeout=1)
            self.is_connected = True
            self.btn_connect.config(text="Desconectar")
            self.log_debug(f"--- CONECTADO A {port} @ {baud} ---")
            
            # Iniciar hilo de lectura
            self.rx_thread = threading.Thread(target=self.read_from_serial, daemon=True)
            self.rx_thread.start()
            
        except serial.SerialException as e:
            messagebox.showerror("Error de Conexión", str(e))

    def disconnect(self):
        self.is_connected = False
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.btn_connect.config(text="Conectar")
        self.log_debug("--- DESCONECTADO ---")

    def read_from_serial(self):
        """Función que corre en segundo plano para leer datos del Arduino."""
        while self.is_connected and self.serial_port.is_open:
            try:
                if self.serial_port.in_waiting > 0:
                    # Leer línea y decodificar
                    line = self.serial_port.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        # Usar invoke o after para actualizar la GUI desde otro hilo es más seguro
                        self.root.after(0, self.log_debug, line)
            except Exception as e:
                print("Error leyendo serial:", e)
                break
            time.sleep(0.01) # Pequeña pausa para no saturar CPU

    def send_message(self):
        """Envía el texto del cuadro de entrada al Arduino."""
        if not self.is_connected:
            messagebox.showwarning("Aviso", "No estás conectado a ningún puerto.")
            return

        msg = self.entry_msg.get()
        if not msg:
            return

        try:
            # Enviar al Arduino (codificado en bytes)
            self.serial_port.write(msg.encode('utf-8'))
            
            # Registrar en la pantalla de TX
            self.log_sent(msg)
            
            # Limpiar entrada
            self.entry_msg.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Error de Envío", str(e))
            self.disconnect()

    def log_debug(self, message):
        """Agrega mensajes a la pantalla de Debug (Izquierda)."""
        self.text_debug.config(state='normal')
        self.text_debug.insert(tk.END, message + "\n")
        self.text_debug.see(tk.END) # Auto-scroll al final
        self.text_debug.config(state='disabled')

    def log_sent(self, message):
        """Agrega mensajes a la pantalla de Enviados (Derecha)."""
        self.text_sent.config(state='normal')
        # Timestamp simple
        timestamp = time.strftime("%H:%M:%S")
        self.text_sent.insert(tk.END, f"[{timestamp}] {message}\n")
        self.text_sent.see(tk.END)
        self.text_sent.config(state='disabled')

if __name__ == "__main__":
    root = tk.Tk()
    app = FSKInterfaceApp(root)
    root.mainloop()