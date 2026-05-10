import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import serial
import serial.tools.list_ports
import threading
import time
import os

class FSKReceiverApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Receptor FSK - Monitor de Datos")
        self.root.geometry("800x650") 
        
        # Variables de control
        self.serial_port = None
        self.is_connected = False
        self.rx_thread = None

        # --- SECCIÓN HEADER: LOGO Y TÍTULO ---
        frame_header = tk.Frame(root, bg="white")
        frame_header.pack(fill="x", side="top")
        
        # Intentar cargar logo (Misma lógica que la interfaz TX)
        self.logo_image = None
        try:
            if os.path.exists("logo.png"):
                raw_image = tk.PhotoImage(file="logo.png")
                # Redimensionado automático
                current_height = raw_image.height()
                target_height = 90
                if current_height > target_height:
                    scale_factor = int(current_height / target_height)
                    if scale_factor < 1: scale_factor = 1
                    self.logo_image = raw_image.subsample(scale_factor, scale_factor)
                else:
                    self.logo_image = raw_image

                lbl_logo = tk.Label(frame_header, image=self.logo_image, bg="white")
                lbl_logo.pack(side="left", padx=10, pady=5)
            else:
                lbl_logo = tk.Label(frame_header, text="[LOGO]", font=("Arial", 12, "bold"), bg="#ddd", width=10)
                lbl_logo.pack(side="left", padx=10, pady=5)
        except Exception:
            pass

        # Título adaptado para el Receptor
        lbl_title = tk.Label(frame_header, text="Receptor FSK - Monitor de Datos", font=("Helvetica", 16, "bold"), bg="white", fg="#333")
        lbl_title.pack(side="left", padx=20)


        # --- SECCIÓN SUPERIOR: CONFIGURACIÓN SERIAL ---
        frame_config = ttk.LabelFrame(root, text="Configuración de Recepción")
        frame_config.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame_config, text="Puerto:").pack(side="left", padx=5)
        
        self.combo_ports = ttk.Combobox(frame_config, width=15)
        self.combo_ports.pack(side="left", padx=5)
        self.refresh_ports()

        self.btn_refresh = ttk.Button(frame_config, text="Refrescar", command=self.refresh_ports)
        self.btn_refresh.pack(side="left", padx=5)

        ttk.Label(frame_config, text="Baudios:").pack(side="left", padx=5)
        # Agregamos 300 a la lista y lo ponemos como default
        self.combo_baud = ttk.Combobox(frame_config, values=["300", "1200", "2400", "9600", "115200"], width=10, state="readonly")
        self.combo_baud.current(0) # Default: 300 Baudios
        self.combo_baud.pack(side="left", padx=5)

        self.btn_connect = ttk.Button(frame_config, text="Iniciar Escucha", command=self.toggle_connection)
        self.btn_connect.pack(side="left", padx=10)
        
        self.btn_clear = ttk.Button(frame_config, text="Limpiar Pantalla", command=self.clear_screen)
        self.btn_clear.pack(side="right", padx=10)

        # --- SECCIÓN CENTRAL: PANTALLAS ---
        paned_window = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        paned_window.pack(fill="both", expand=True, padx=10, pady=5)

        # 1. Panel Izquierdo: Estado del Sistema (Logs de conexión)
        frame_status = ttk.LabelFrame(paned_window, text="Estado del Sistema")
        paned_window.add(frame_status, weight=1)
        
        self.text_status = scrolledtext.ScrolledText(frame_status, height=20, state='disabled', bg="#f0f0f0", fg="#555")
        self.text_status.pack(fill="both", expand=True, padx=5, pady=5)

        # 2. Panel Derecho: TEXTO RECIBIDO (Principal)
        frame_rx_data = ttk.LabelFrame(paned_window, text="Texto Recibido (Decodificado)")
        paned_window.add(frame_rx_data, weight=3) # Le damos más peso (espacio) a esta pantalla
        
        # Fuente tipo consola para ver mejor los datos
        self.text_received = scrolledtext.ScrolledText(frame_rx_data, height=20, state='disabled', bg="black", fg="#00ff00", font=("Consolas", 11))
        self.text_received.pack(fill="both", expand=True, padx=5, pady=5)

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
            # Conexión Serial
            self.serial_port = serial.Serial(port, baud, timeout=0.1) 
            self.is_connected = True
            self.btn_connect.config(text="Detener Escucha")
            self.log_status(f"--- CONECTADO A {port} @ {baud} BAUDIOS ---")
            self.log_status("Esperando datos...")
            
            # Iniciar hilo de lectura
            self.rx_thread = threading.Thread(target=self.read_from_serial, daemon=True)
            self.rx_thread.start()
            
        except serial.SerialException as e:
            messagebox.showerror("Error de Conexión", str(e))

    def disconnect(self):
        self.is_connected = False
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.btn_connect.config(text="Iniciar Escucha")
        self.log_status("--- DESCONECTADO ---")

    def read_from_serial(self):
        """Lee datos byte a byte para mostrar en tiempo real."""
        while self.is_connected and self.serial_port.is_open:
            try:
                if self.serial_port.in_waiting > 0:
                    # Leemos lo que haya en el buffer
                    data = self.serial_port.read(self.serial_port.in_waiting)
                    try:
                        # Decodificamos a texto
                        text_chunk = data.decode('utf-8', errors='replace')
                        
                        # Actualizamos la GUI
                        self.root.after(0, self.append_received_text, text_chunk)
                    except Exception:
                        pass
            except Exception as e:
                print("Error leyendo serial:", e)
                break
            time.sleep(0.01)

    def log_status(self, message):
        """Agrega mensajes al panel de estado (Izquierda)."""
        timestamp = time.strftime("%H:%M:%S")
        self.text_status.config(state='normal')
        self.text_status.insert(tk.END, f"[{timestamp}] {message}\n")
        self.text_status.see(tk.END)
        self.text_status.config(state='disabled')

    def append_received_text(self, text):
        """Agrega el texto decodificado al panel principal (Derecha)."""
        self.text_received.config(state='normal')
        self.text_received.insert(tk.END, text)
        self.text_received.see(tk.END) # Auto-scroll siempre al final
        self.text_received.config(state='disabled')

    def clear_screen(self):
        """Limpia el cuadro de texto recibido."""
        self.text_received.config(state='normal')
        self.text_received.delete(1.0, tk.END)
        self.text_received.config(state='disabled')
        self.log_status("Pantalla limpiada por el usuario.")

if __name__ == "__main__":
    root = tk.Tk()
    app = FSKReceiverApp(root)
    root.mainloop()