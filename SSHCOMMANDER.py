#!/usr/bin/env python3
"""
SSH COMMANDER PROFESSIONAL v6.0 - VERSION CORREGIDA
"""

import os
import sys
import threading
import time
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
import stat

try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext, messagebox, filedialog, simpledialog, Menu
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    print("Error: tkinter no está instalado")

try:
    import paramiko
    PARAMIKO_AVAILABLE = True
except ImportError:
    PARAMIKO_AVAILABLE = False
    print("Error: paramiko no está instalado. Instala con: pip3 install paramiko")

if not TKINTER_AVAILABLE or not PARAMIKO_AVAILABLE:
    sys.exit(1)

# Configuración
CONFIG_DIR = Path.home() / ".ssh_professional"
CONFIG_DIR.mkdir(exist_ok=True)
SERVERS_FILE = CONFIG_DIR / "servers.json"


class SSHCommanderProfessional:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("SSH Commander Professional v6.0")
        self.root.geometry("1400x850")
        self.root.minsize(1200, 700)
        self.root.configure(bg='#2d2d2d')
        
        # Maximizar ventana (compatible con Linux)
        try:
            self.root.attributes('-zoomed', True)
        except:
            try:
                self.root.state('zoomed')
            except:
                self.root.geometry(f"{self.root.winfo_screenwidth()}x{self.root.winfo_screenheight()}+0+0")

        # Variables de conexión
        self.client: Optional[paramiko.SSHClient] = None
        self.sftp: Optional[paramiko.SFTPClient] = None
        self.is_connected = False
        self.current_server = None
        self.transport = None

        # Directorios
        self.local_cwd = Path.home()
        self.remote_cwd = "/"

        # Historial de navegación
        self.local_history = [self.local_cwd]
        self.local_history_index = 0
        self.remote_history = [self.remote_cwd]
        self.remote_history_index = 0

        # Servidores guardados
        self.servers = self.load_servers()

        # Transferencias
        self.active_transfers = 0
        self.transfer_in_progress = False

        # Colores profesionales
        self.colors = {
            'bg': '#2d2d2d',
            'bg_dark': '#252526',
            'bg_light': '#3c3c3c',
            'fg': '#cccccc',
            'fg_light': '#ffffff',
            'accent': '#007acc',
            'accent_hover': '#1f8ad0',
            'success': '#6a9955',
            'error': '#f48771',
            'warning': '#dcdcaa',
            'terminal_bg': '#1e1e1e',
            'terminal_fg': '#d4d4d4',
            'border': '#3c3c3c',
            'selected': '#264f78',
            'header_bg': '#2d2d2d',
        }

        # Fuentes
        self.fonts = {
            'normal': ('Segoe UI', 9),
            'bold': ('Segoe UI', 9, 'bold'),
            'terminal': ('Consolas', 10),
            'small': ('Segoe UI', 8),
            'header': ('Segoe UI', 10, 'bold'),
        }

        # Comandos predefinidos (SIN EMOTICONOS)
        self.quick_commands = [
            # Sistema
            ("uptime", "uptime"),
            ("uname -a", "uname -a"),
            ("hostname", "hostname"),
            ("date", "date"),
            ("whoami", "whoami"),
            ("who", "who"),
            # Recursos
            ("df -h", "df -h"),
            ("free -h", "free -h"),
            ("top -10", "top -bn1 | head -20"),
            ("ps aux", "ps aux --sort=-%cpu | head -15"),
            ("iostat", "iostat 2>/dev/null || echo 'iostat no instalado'"),
            ("vmstat", "vmstat 1 3 2>/dev/null || echo 'vmstat no instalado'"),
            ("netstat -i", "netstat -i 2>/dev/null || echo 'netstat no instalado'"),
            # Red
            ("ifconfig", "ifconfig 2>/dev/null || ip addr"),
            ("netstat -tuln", "ss -tuln"),
            ("ip route", "ip route"),
            ("ping google", "ping -c 4 google.com"),
            ("last logins", "last -n 10"),
            ("netstat -an", "netstat -an 2>/dev/null | head -20"),
            ("ss -tuln", "ss -tuln"),
            ("arp -a", "arp -a 2>/dev/null"),
            # Archivos
            ("ls -la", "ls -la"),
            ("pwd", "pwd"),
            ("find", "find . -name"),
            ("du -sh *", "du -sh * 2>/dev/null | head -20"),
            ("tree -L 2", "tree -L 2 2>/dev/null || ls -R | head -30"),
            ("cat", "cat"),
            ("less", "less"),
            ("head", "head"),
            ("tail", "tail"),
            ("grep", "grep"),
            # Seguridad
            ("passwd", "passwd"),
            ("ssh keys", "ls -la ~/.ssh/"),
            ("auth log", "tail -20 /var/log/auth.log 2>/dev/null"),
            ("failed logins", "grep 'Failed password' /var/log/auth.log 2>/dev/null | tail -10"),
            ("sudo logs", "tail -20 /var/log/sudo.log 2>/dev/null"),
            ("lastb", "lastb -n 10 2>/dev/null"),
            ("journalctl -xe", "journalctl -xe -n 20 2>/dev/null"),
            # Procesos
            ("kill", "kill"),
            ("killall", "killall"),
            ("pkill", "pkill"),
            ("nice", "nice"),
            ("renice", "renice"),
            ("nohup", "nohup"),
            ("jobs", "jobs"),
            ("fg", "fg"),
            ("bg", "bg"),
            # Servicios
            ("systemctl status", "systemctl status --no-pager | head -30"),
            ("service status", "service --status-all 2>/dev/null | head -20"),
            ("crontab -l", "crontab -l"),
            ("journalctl", "journalctl -n 20 --no-pager"),
            ("docker ps", "docker ps 2>/dev/null"),
            ("kubectl get pods", "kubectl get pods 2>/dev/null"),
            ("systemctl list-units", "systemctl list-units --type=service --no-pager | head -20"),
            # Herramientas
            ("grep -r", "grep -r"),
            ("awk", "awk"),
            ("sed", "sed"),
            ("cut", "cut"),
            ("sort", "sort"),
            ("uniq", "uniq"),
            ("wc", "wc"),
            ("diff", "diff"),
            ("comm", "comm"),
            # Comandos útiles
            ("clear", "clear"),
            ("history", "history"),
            ("alias", "alias"),
            ("export", "export"),
            ("echo $PATH", "echo $PATH"),
            ("which", "which"),
            ("file", "file"),
            ("md5sum", "md5sum"),
            ("sha256sum", "sha256sum"),
            ("base64", "base64"),
            # Información del sistema
            ("uname -r", "uname -r"),
            ("lsblk", "lsblk 2>/dev/null"),
            ("lspci", "lspci 2>/dev/null | head -10"),
            ("lscpu", "lscpu 2>/dev/null | head -15"),
            ("dmidecode", "dmidecode -s system-manufacturer 2>/dev/null"),
            ("cat /etc/os-release", "cat /etc/os-release 2>/dev/null"),
            ("cat /proc/cpuinfo", "cat /proc/cpuinfo | head -20"),
            ("cat /proc/meminfo", "cat /proc/meminfo | head -10"),
            # Compresión
            ("tar -czf", "tar -czf"),
            ("tar -xzf", "tar -xzf"),
            ("zip", "zip"),
            ("unzip", "unzip"),
            ("gzip", "gzip"),
            ("gunzip", "gunzip"),
        ]

        # Crear interfaz
        self.setup_styles()
        self.create_menu()
        self.create_main_layout()
        self.setup_bindings()

        # Crear ventana de terminal (pero NO mostrar)
        self.create_terminal_window()
        self.terminal_window.withdraw()

        # Cargar última conexión
        self.load_last_server()

        # Cerrar
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')

        style.configure('.', background=self.colors['bg'], foreground=self.colors['fg'])
        style.configure('TFrame', background=self.colors['bg'])
        style.configure('TLabel', background=self.colors['bg'], foreground=self.colors['fg'])
        style.configure('TLabelframe', background=self.colors['bg'], foreground=self.colors['fg'])
        style.configure('TLabelframe.Label', background=self.colors['bg'], foreground=self.colors['accent'])
        style.configure('TButton', background=self.colors['bg_light'], foreground=self.colors['fg'], borderwidth=1)
        style.configure('TEntry', fieldbackground=self.colors['bg_dark'], foreground=self.colors['fg'])
        style.configure('Treeview', background=self.colors['bg_dark'], foreground=self.colors['fg'],
                       fieldbackground=self.colors['bg_dark'], rowheight=24)
        style.map('Treeview', background=[('selected', self.colors['selected'])])
        style.configure('TProgressbar', background=self.colors['accent'], troughcolor=self.colors['bg_dark'])

    def create_menu(self):
        menubar = Menu(self.root, bg=self.colors['bg'], fg=self.colors['fg'])
        self.root.config(menu=menubar)

        # Menú Conexión
        conn_menu = Menu(menubar, tearoff=0, bg=self.colors['bg'], fg=self.colors['fg'])
        menubar.add_cascade(label="Conexión", menu=conn_menu)
        conn_menu.add_command(label="Nueva Conexión", command=self.show_connection_dialog, accelerator="Ctrl+N")
        conn_menu.add_command(label="Desconectar", command=self.disconnect_ssh, accelerator="Ctrl+D")
        conn_menu.add_separator()
        conn_menu.add_command(label="Salir", command=self.on_closing, accelerator="Ctrl+Q")

        # Menú Servidores
        server_menu = Menu(menubar, tearoff=0, bg=self.colors['bg'], fg=self.colors['fg'])
        menubar.add_cascade(label="Servidores", menu=server_menu)
        server_menu.add_command(label="Guardar Servidor Actual", command=self.save_current_server)
        server_menu.add_command(label="Gestionar Servidores", command=self.manage_servers)

        # Menú Ver
        view_menu = Menu(menubar, tearoff=0, bg=self.colors['bg'], fg=self.colors['fg'])
        menubar.add_cascade(label="Ver", menu=view_menu)
        view_menu.add_command(label="Mostrar Terminal", command=self.show_terminal_window)
        view_menu.add_command(label="Ocultar Terminal", command=self.hide_terminal_window)
        view_menu.add_separator()
        view_menu.add_command(label="Refrescar", command=self.refresh_all, accelerator="F5")

        # Menú Ayuda
        help_menu = Menu(menubar, tearoff=0, bg=self.colors['bg'], fg=self.colors['fg'])
        menubar.add_cascade(label="Ayuda", menu=help_menu)
        help_menu.add_command(label="Acerca de", command=self.show_about)

    def create_main_layout(self):
        """Layout principal con exploradores duales idénticos"""
        # Panel superior - Barra de herramientas global
        top_frame = tk.Frame(self.root, bg=self.colors['bg'], height=45)
        top_frame.pack(fill=tk.X, padx=5, pady=5)
        top_frame.pack_propagate(False)

        toolbar = tk.Frame(top_frame, bg=self.colors['bg'])
        toolbar.pack(fill=tk.X, expand=True)

        # Estado de conexión
        self.conn_status = tk.Label(toolbar, text="● Desconectado",
                                    font=self.fonts['bold'], fg=self.colors['error'], bg=self.colors['bg'])
        self.conn_status.pack(side=tk.LEFT, padx=10)

        self.server_info = tk.Label(toolbar, text="", font=self.fonts['normal'],
                                    fg=self.colors['fg'], bg=self.colors['bg'])
        self.server_info.pack(side=tk.LEFT, padx=10)

        # Botones globales
        tk.Button(toolbar, text="Nueva Conexión", command=self.show_connection_dialog,
                  font=self.fonts['normal'], bg=self.colors['accent'], fg='white',
                  relief='flat', padx=15).pack(side=tk.RIGHT, padx=5)
        
        tk.Button(toolbar, text="Desconectar", command=self.disconnect_ssh,
                  font=self.fonts['normal'], bg=self.colors['error'], fg='white',
                  relief='flat', padx=15).pack(side=tk.RIGHT, padx=5)

        # Panel central con dos paneles (mismo tamaño)
        paned = tk.PanedWindow(self.root, bg=self.colors['bg'], sashwidth=6, sashrelief='raised')
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Panel izquierdo (LOCAL)
        left_frame = tk.Frame(paned, bg=self.colors['bg'])
        paned.add(left_frame, width=650)

        # Panel derecho (REMOTO) - MISMO TAMAÑO
        right_frame = tk.Frame(paned, bg=self.colors['bg'])
        paned.add(right_frame, width=650)

        # Crear ambos exploradores con herramientas de navegación IDÉNTICAS
        self.create_explorer_panel(left_frame, "UNIDAD LOCAL", is_remote=False)
        self.create_explorer_panel(right_frame, "UNIDAD REMOTA", is_remote=True)

        # Panel inferior - Barra de progreso y transferencias
        bottom_frame = tk.Frame(self.root, bg=self.colors['bg'], height=80)
        bottom_frame.pack(fill=tk.X, padx=5, pady=5)
        bottom_frame.pack_propagate(False)

        # Frame para botones de transferencia
        transfer_frame = tk.Frame(bottom_frame, bg=self.colors['bg_dark'], height=40)
        transfer_frame.pack(fill=tk.X, pady=5)
        transfer_frame.pack_propagate(False)

        tk.Label(transfer_frame, text="TRANSFERENCIAS:",
                 font=self.fonts['bold'], bg=self.colors['bg_dark'], fg=self.colors['accent']).pack(side=tk.LEFT, padx=10)

        # Flecha derecha (Local -> Remoto)
        self.right_btn = tk.Button(transfer_frame, text="LOCAL >> REMOTO",
                                   command=self.transfer_to_remote,
                                   font=self.fonts['bold'], bg=self.colors['success'], fg='white',
                                   relief='flat', padx=20, state='disabled')
        self.right_btn.pack(side=tk.LEFT, padx=10)

        # Flecha izquierda (Remoto -> Local)
        self.left_btn = tk.Button(transfer_frame, text="REMOTO << LOCAL",
                                  command=self.transfer_to_local,
                                  font=self.fonts['bold'], bg=self.colors['accent'], fg='white',
                                  relief='flat', padx=20, state='disabled')
        self.left_btn.pack(side=tk.LEFT, padx=10)

        # Barra de progreso
        progress_inner = tk.Frame(bottom_frame, bg=self.colors['bg_dark'], relief='sunken', bd=1, height=28)
        progress_inner.pack(fill=tk.X, pady=5)
        progress_inner.pack_propagate(False)

        self.progress_bar = ttk.Progressbar(progress_inner, mode='determinate', length=100)
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=3)

        self.progress_label = tk.Label(progress_inner, text="", font=self.fonts['small'],
                                       bg=self.colors['bg_dark'], fg=self.colors['fg'])
        self.progress_label.pack(side=tk.RIGHT, padx=10)

        # Estado
        self.status_label = tk.Label(bottom_frame, text="Listo", font=self.fonts['normal'],
                                     fg=self.colors['fg'], bg=self.colors['bg'])
        self.status_label.pack(side=tk.LEFT, padx=10, pady=5)

    def create_explorer_panel(self, parent, title, is_remote=False):
        """Crea un panel explorador de archivos con herramientas de navegación COMPLETAS"""
        panel = tk.Frame(parent, bg=self.colors['bg'])
        panel.pack(fill=tk.BOTH, expand=True)

        # Título del panel
        title_frame = tk.Frame(panel, bg=self.colors['header_bg'], height=30)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)

        tk.Label(title_frame, text=title, font=self.fonts['header'],
                 fg=self.colors['accent'], bg=self.colors['header_bg']).pack(side=tk.LEFT, padx=10, pady=5)

        # Barra de herramientas de navegación (IDÉNTICA para local y remoto)
        nav_frame = tk.Frame(panel, bg=self.colors['bg'], height=35)
        nav_frame.pack(fill=tk.X, pady=5)
        nav_frame.pack_propagate(False)

        # Botones de navegación
        if is_remote:
            tk.Button(nav_frame, text="Home", command=self.go_home_remote,
                     font=self.fonts['small'], bg=self.colors['bg_light'], fg=self.colors['fg'],
                     relief='flat', padx=8).pack(side=tk.LEFT, padx=2)
            tk.Button(nav_frame, text="Subir", command=self.go_up_remote,
                     font=self.fonts['small'], bg=self.colors['bg_light'], fg=self.colors['fg'],
                     relief='flat', padx=8).pack(side=tk.LEFT, padx=2)
            tk.Button(nav_frame, text="Atras", command=self.remote_back,
                     font=self.fonts['small'], bg=self.colors['bg_light'], fg=self.colors['fg'],
                     relief='flat', padx=8).pack(side=tk.LEFT, padx=2)
            tk.Button(nav_frame, text="Adelante", command=self.remote_forward,
                     font=self.fonts['small'], bg=self.colors['bg_light'], fg=self.colors['fg'],
                     relief='flat', padx=8).pack(side=tk.LEFT, padx=2)
            tk.Button(nav_frame, text="Refrescar", command=self.refresh_remote_browser,
                     font=self.fonts['small'], bg=self.colors['bg_light'], fg=self.colors['fg'],
                     relief='flat', padx=8).pack(side=tk.LEFT, padx=2)
        else:
            tk.Button(nav_frame, text="Home", command=self.go_home_local,
                     font=self.fonts['small'], bg=self.colors['bg_light'], fg=self.colors['fg'],
                     relief='flat', padx=8).pack(side=tk.LEFT, padx=2)
            tk.Button(nav_frame, text="Subir", command=self.go_up_local,
                     font=self.fonts['small'], bg=self.colors['bg_light'], fg=self.colors['fg'],
                     relief='flat', padx=8).pack(side=tk.LEFT, padx=2)
            tk.Button(nav_frame, text="Atras", command=self.local_back,
                     font=self.fonts['small'], bg=self.colors['bg_light'], fg=self.colors['fg'],
                     relief='flat', padx=8).pack(side=tk.LEFT, padx=2)
            tk.Button(nav_frame, text="Adelante", command=self.local_forward,
                     font=self.fonts['small'], bg=self.colors['bg_light'], fg=self.colors['fg'],
                     relief='flat', padx=8).pack(side=tk.LEFT, padx=2)
            tk.Button(nav_frame, text="Refrescar", command=self.refresh_local_browser,
                     font=self.fonts['small'], bg=self.colors['bg_light'], fg=self.colors['fg'],
                     relief='flat', padx=8).pack(side=tk.LEFT, padx=2)

        # Barra de direcciones
        addr_frame = tk.Frame(panel, bg=self.colors['bg'])
        addr_frame.pack(fill=tk.X, pady=5, padx=5)

        if is_remote:
            self.remote_path_var = tk.StringVar(value=self.remote_cwd)
            path_entry = tk.Entry(addr_frame, textvariable=self.remote_path_var,
                                  font=self.fonts['normal'], bg=self.colors['bg_dark'],
                                  fg=self.colors['fg'], relief='flat', bd=1)
            path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            tk.Button(addr_frame, text="Ir", command=self.navigate_remote,
                      font=self.fonts['normal'], bg=self.colors['accent'], fg='white',
                      relief='flat', padx=15).pack(side=tk.RIGHT, padx=5)
        else:
            self.local_path_var = tk.StringVar(value=str(self.local_cwd))
            path_entry = tk.Entry(addr_frame, textvariable=self.local_path_var,
                                  font=self.fonts['normal'], bg=self.colors['bg_dark'],
                                  fg=self.colors['fg'], relief='flat', bd=1)
            path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            tk.Button(addr_frame, text="Ir", command=self.navigate_local,
                      font=self.fonts['normal'], bg=self.colors['accent'], fg='white',
                      relief='flat', padx=15).pack(side=tk.RIGHT, padx=5)

        # Treeview con scrollbars
        tree_frame = tk.Frame(panel, bg=self.colors['bg'])
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Columnas
        columns = ('nombre', 'tamaño', 'modificado')
        tree = ttk.Treeview(tree_frame, columns=columns, show='tree headings', height=24)

        # Configurar headings (alineados a la izquierda)
        tree.heading('#0', text='', anchor='w')
        tree.heading('nombre', text='Nombre', anchor='w')
        tree.heading('tamaño', text='Tamaño', anchor='w')
        tree.heading('modificado', text='Modificado', anchor='w')

        # Configurar columnas
        tree.column('#0', width=40, anchor='w')
        tree.column('nombre', width=380, anchor='w')
        tree.column('tamaño', width=100, anchor='w')
        tree.column('modificado', width=150, anchor='w')

        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient='vertical', command=tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient='horizontal', command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # Eventos
        tree.bind('<Double-Button-1>', lambda e: self.enter_directory(is_remote))
        tree.bind('<Button-3>', lambda e: self.show_context_menu(e, is_remote))

        # Guardar referencias
        if is_remote:
            self.remote_tree = tree
        else:
            self.local_tree = tree

        # Inicializar el explorador local
        if not is_remote:
            self.refresh_local_browser()

    def create_terminal_window(self):
        """Crea la ventana independiente de terminal (no se muestra al inicio)"""
        self.terminal_window = tk.Toplevel(self.root)
        self.terminal_window.title("Terminal SSH - Comandos Rápidos")
        self.terminal_window.geometry("1000x700")
        self.terminal_window.minsize(800, 600)
        self.terminal_window.configure(bg=self.colors['bg'])

        self.terminal_window.protocol("WM_DELETE_WINDOW", self.hide_terminal_window)

        # Frame principal
        main_frame = tk.Frame(self.terminal_window, bg=self.colors['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Panel superior - Entrada de comandos
        cmd_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        cmd_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(cmd_frame, text=">", font=self.fonts['bold'],
                 fg=self.colors['accent'], bg=self.colors['bg']).pack(side=tk.LEFT, padx=5)

        self.cmd_entry = tk.Entry(cmd_frame, font=self.fonts['terminal'],
                                  bg=self.colors['terminal_bg'], fg=self.colors['terminal_fg'],
                                  relief='flat', bd=1, insertbackground=self.colors['terminal_fg'])
        self.cmd_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.cmd_entry.bind('<Return>', lambda e: self.execute_command())

        tk.Button(cmd_frame, text="Ejecutar", command=self.execute_command,
                  font=self.fonts['normal'], bg=self.colors['accent'], fg='white',
                  relief='flat', padx=15).pack(side=tk.LEFT, padx=5)

        tk.Button(cmd_frame, text="Limpiar", command=self.clear_terminal,
                  font=self.fonts['normal'], bg=self.colors['bg_light'], fg=self.colors['fg'],
                  relief='flat', padx=15).pack(side=tk.LEFT, padx=5)

        # Panel de comandos rápidos (scrollable)
        quick_frame = tk.LabelFrame(main_frame, text="Comandos Rápidos (Click para ejecutar)",
                                    font=self.fonts['bold'], bg=self.colors['bg'], fg=self.colors['accent'])
        quick_frame.pack(fill=tk.X, pady=(0, 10))

        # Canvas con scroll para los botones
        canvas = tk.Canvas(quick_frame, bg=self.colors['bg'], height=150, highlightthickness=0)
        scrollbar = ttk.Scrollbar(quick_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['bg'])

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Organizar botones en grid (8 columnas)
        row, col = 0, 0
        for cmd_text, cmd_value in self.quick_commands:
            btn = tk.Button(scrollable_frame, text=cmd_text,
                           command=lambda c=cmd_value: self.run_quick_command(c),
                           font=self.fonts['small'], bg=self.colors['bg_light'], fg=self.colors['fg'],
                           relief='flat', padx=6, pady=2, width=18)
            btn.grid(row=row, column=col, padx=3, pady=3, sticky='ew')
            col += 1
            if col > 7:
                col = 0
                row += 1

        # Configurar columnas del grid
        for i in range(8):
            scrollable_frame.columnconfigure(i, weight=1)

        # Área de terminal
        self.terminal = scrolledtext.ScrolledText(main_frame, font=self.fonts['terminal'],
                                                   bg=self.colors['terminal_bg'],
                                                   fg=self.colors['terminal_fg'],
                                                   wrap=tk.WORD, relief='flat', bd=1)
        self.terminal.pack(fill=tk.BOTH, expand=True)

        # Tags para colores
        self.terminal.tag_config('error', foreground=self.colors['error'])
        self.terminal.tag_config('success', foreground=self.colors['success'])
        self.terminal.tag_config('info', foreground=self.colors['accent'])

        # Banner
        self.print_terminal_banner()

    def print_terminal_banner(self):
        banner = """
================================================================================
                        TERMINAL SSH PROFESIONAL
================================================================================
  * Escribe cualquier comando y presiona Enter
  * Usa los botones de comandos rapidos para ejecutar comandos frecuentes
  * Los comandos se ejecutan en el servidor conectado
  * Mas de 80 comandos predefinidos disponibles
================================================================================
        """
        self.terminal.insert(tk.END, banner, 'info')
        self.terminal.insert(tk.END, "\n[Sistema Listo]\n", 'success')
        self.terminal.see(tk.END)

    def hide_terminal_window(self):
        self.terminal_window.withdraw()

    def show_terminal_window(self):
        self.terminal_window.deiconify()
        self.terminal_window.lift()

    def show_context_menu(self, event, is_remote):
        menu = Menu(self.root, tearoff=0, bg=self.colors['bg'], fg=self.colors['fg'])
        if is_remote:
            menu.add_command(label="Descargar", command=self.transfer_to_local)
            menu.add_command(label="Descargar Directorio", command=self.download_directory_context)
            menu.add_separator()
            menu.add_command(label="Eliminar", command=self.delete_remote_selected)
            menu.add_command(label="Copiar Ruta", command=self.copy_remote_path)
        else:
            menu.add_command(label="Subir", command=self.transfer_to_remote)
            menu.add_command(label="Subir Directorio", command=self.upload_directory_context)
            menu.add_separator()
            menu.add_command(label="Eliminar", command=self.delete_local_selected)
            menu.add_command(label="Copiar Ruta", command=self.copy_local_path)
        menu.post(event.x_root, event.y_root)

    # ============================================
    # NAVEGACIÓN LOCAL
    # ============================================
    def refresh_local_browser(self):
        thread = threading.Thread(target=self._do_refresh_local, daemon=True)
        thread.start()

    def _do_refresh_local(self):
        try:
            items = []
            path = self.local_cwd
            
            for item in sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                items.append({
                    'name': item.name,
                    'is_dir': item.is_dir(),
                    'size': item.stat().st_size if item.is_file() else 0,
                    'mtime': datetime.fromtimestamp(item.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                })

            self.root.after(0, lambda: self._update_local_tree(items))
        except Exception as e:
            self.root.after(0, lambda: self.status_label.config(text=f"Error: {e}"))

    def _update_local_tree(self, items):
        for item in self.local_tree.get_children():
            self.local_tree.delete(item)

        for item in items:
            icon = "📁" if item['is_dir'] else "📄"
            size_str = self._format_bytes(item['size']) if not item['is_dir'] else ""
            self.local_tree.insert('', 'end', text=icon, values=(item['name'], size_str, item['mtime']))

        self.local_path_var.set(str(self.local_cwd))
        self.status_label.config(text=f"Local: {len(items)} elementos")

    # ============================================
    # NAVEGACIÓN REMOTA
    # ============================================
    def refresh_remote_browser(self):
        if not self.is_connected:
            return
        thread = threading.Thread(target=self._do_refresh_remote, daemon=True)
        thread.start()

    def _do_refresh_remote(self):
        try:
            items = self.sftp.listdir_attr(self.remote_cwd)
            file_list = []

            for item in sorted(items, key=lambda x: (not stat.S_ISDIR(x.st_mode), x.filename.lower())):
                file_list.append({
                    'name': item.filename,
                    'is_dir': stat.S_ISDIR(item.st_mode),
                    'size': item.st_size if not stat.S_ISDIR(item.st_mode) else 0,
                    'mtime': datetime.fromtimestamp(item.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                })

            self.root.after(0, lambda: self._update_remote_tree(file_list))
        except Exception as e:
            self.root.after(0, lambda: self.status_label.config(text=f"Error remoto: {e}"))

    def _update_remote_tree(self, items):
        for item in self.remote_tree.get_children():
            self.remote_tree.delete(item)

        for item in items:
            icon = "📁" if item['is_dir'] else "📄"
            size_str = self._format_bytes(item['size']) if not item['is_dir'] else ""
            self.remote_tree.insert('', 'end', text=icon, values=(item['name'], size_str, item['mtime']))

        self.remote_path_var.set(self.remote_cwd)
        self.status_label.config(text=f"Remoto: {len(items)} elementos")

    # ============================================
    # NAVEGACIÓN
    # ============================================
    def enter_directory(self, is_remote):
        if is_remote:
            selection = self.remote_tree.selection()
            if selection:
                item = self.remote_tree.item(selection[0])
                name = item['values'][0]
                path = f"{self.remote_cwd}/{name}"
                try:
                    attrs = self.sftp.stat(path)
                    if stat.S_ISDIR(attrs.st_mode):
                        self.remote_history = self.remote_history[:self.remote_history_index + 1]
                        self.remote_history.append(path)
                        self.remote_history_index += 1
                        self.remote_cwd = path
                        self.refresh_remote_browser()
                except:
                    pass
        else:
            selection = self.local_tree.selection()
            if selection:
                item = self.local_tree.item(selection[0])
                name = item['values'][0]
                path = self.local_cwd / name
                if path.is_dir():
                    self.local_history = self.local_history[:self.local_history_index + 1]
                    self.local_history.append(path)
                    self.local_history_index += 1
                    self.local_cwd = path
                    self.refresh_local_browser()

    # Navegación Local
    def go_home_local(self):
        self.local_cwd = Path.home()
        self.refresh_local_browser()

    def go_up_local(self):
        self.local_cwd = self.local_cwd.parent
        self.refresh_local_browser()

    def local_back(self):
        if self.local_history_index > 0:
            self.local_history_index -= 1
            self.local_cwd = self.local_history[self.local_history_index]
            self.refresh_local_browser()

    def local_forward(self):
        if self.local_history_index < len(self.local_history) - 1:
            self.local_history_index += 1
            self.local_cwd = self.local_history[self.local_history_index]
            self.refresh_local_browser()

    # Navegación Remota
    def go_home_remote(self):
        if self.is_connected:
            self.remote_cwd = f"/home/{self.current_server['user']}"
            self.refresh_remote_browser()

    def go_up_remote(self):
        if self.is_connected:
            self.remote_cwd = str(Path(self.remote_cwd).parent)
            self.refresh_remote_browser()

    def remote_back(self):
        if self.remote_history_index > 0:
            self.remote_history_index -= 1
            self.remote_cwd = self.remote_history[self.remote_history_index]
            self.refresh_remote_browser()

    def remote_forward(self):
        if self.remote_history_index < len(self.remote_history) - 1:
            self.remote_history_index += 1
            self.remote_cwd = self.remote_history[self.remote_history_index]
            self.refresh_remote_browser()

    def navigate_local(self):
        path = Path(self.local_path_var.get())
        if path.exists() and path.is_dir():
            self.local_cwd = path
            self.refresh_local_browser()
        else:
            messagebox.showerror("Error", "Ruta no válida")

    def navigate_remote(self):
        if not self.is_connected:
            messagebox.showwarning("Advertencia", "No conectado al servidor")
            return
        path = self.remote_path_var.get()
        try:
            self.sftp.stat(path)
            self.remote_cwd = path
            self.refresh_remote_browser()
        except:
            messagebox.showerror("Error", "Ruta remota no válida")

    def refresh_all(self):
        self.refresh_local_browser()
        if self.is_connected:
            self.refresh_remote_browser()

    # ============================================
    # TRANSFERENCIAS ULTRA RÁPIDAS
    # ============================================
    def update_progress(self, transferred, total, filename=""):
        percent = (transferred / total) * 100 if total > 0 else 0
        self.progress_bar['value'] = percent
        if hasattr(self, 'transfer_start_time') and self.transfer_start_time:
            elapsed = time.time() - self.transfer_start_time
            if elapsed > 0:
                speed = transferred / elapsed
                speed_mb = speed / (1024 * 1024)
                self.progress_label.config(text=f"{filename} {self._format_bytes(transferred)} / {self._format_bytes(total)} ({percent:.1f}%) - {speed_mb:.1f} MB/s")
            else:
                self.progress_label.config(text=f"{filename} {self._format_bytes(transferred)} / {self._format_bytes(total)} ({percent:.1f}%)")
        else:
            self.progress_label.config(text=f"{filename} {self._format_bytes(transferred)} / {self._format_bytes(total)} ({percent:.1f}%)")
        self.root.update_idletasks()

    def transfer_to_remote(self):
        selection = self.local_tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Selecciona archivos/directorios para subir")
            return

        if not self.is_connected:
            messagebox.showwarning("Advertencia", "No hay conexión SSH activa")
            return

        items = []
        for sel in selection:
            item = self.local_tree.item(sel)
            name = item['values'][0]
            items.append(name)

        if messagebox.askyesno("Confirmar", f"¿Subir {len(items)} elemento(s) al servidor?"):
            self.active_transfers = len(items)
            for name in items:
                local_path = self.local_cwd / name
                remote_path = f"{self.remote_cwd}/{name}"
                if local_path.is_dir():
                    thread = threading.Thread(target=self._upload_directory_fast,
                                             args=(str(local_path), remote_path, name), daemon=True)
                else:
                    thread = threading.Thread(target=self._upload_file_fast,
                                             args=(str(local_path), remote_path, name), daemon=True)
                thread.start()

    def transfer_to_local(self):
        selection = self.remote_tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Selecciona archivos/directorios para descargar")
            return

        if not self.is_connected:
            messagebox.showwarning("Advertencia", "No hay conexión SSH activa")
            return

        items = []
        for sel in selection:
            item = self.remote_tree.item(sel)
            name = item['values'][0]
            items.append(name)

        if messagebox.askyesno("Confirmar", f"¿Descargar {len(items)} elemento(s) a local?"):
            self.active_transfers = len(items)
            for name in items:
                remote_path = f"{self.remote_cwd}/{name}"
                local_path = self.local_cwd / name
                try:
                    attrs = self.sftp.stat(remote_path)
                    if stat.S_ISDIR(attrs.st_mode):
                        thread = threading.Thread(target=self._download_directory_fast,
                                                 args=(remote_path, str(local_path), name), daemon=True)
                    else:
                        thread = threading.Thread(target=self._download_file_fast,
                                                 args=(remote_path, str(local_path), name), daemon=True)
                    thread.start()
                except:
                    pass

    def download_directory_context(self):
        selection = self.remote_tree.selection()
        if selection:
            item = self.remote_tree.item(selection[0])
            name = item['values'][0]
            remote_path = f"{self.remote_cwd}/{name}"
            local_path = self.local_cwd / name

            try:
                attrs = self.sftp.stat(remote_path)
                if stat.S_ISDIR(attrs.st_mode):
                    if messagebox.askyesno("Confirmar", f"¿Descargar directorio '{name}'?"):
                        self.active_transfers = 1
                        thread = threading.Thread(target=self._download_directory_fast,
                                                 args=(remote_path, str(local_path), name), daemon=True)
                        thread.start()
            except:
                pass

    def upload_directory_context(self):
        selection = self.local_tree.selection()
        if selection:
            item = self.local_tree.item(selection[0])
            name = item['values'][0]
            local_path = self.local_cwd / name
            remote_path = f"{self.remote_cwd}/{name}"

            if local_path.is_dir():
                if messagebox.askyesno("Confirmar", f"¿Subir directorio '{name}'?"):
                    self.active_transfers = 1
                    thread = threading.Thread(target=self._upload_directory_fast,
                                             args=(str(local_path), remote_path, name), daemon=True)
                    thread.start()

    # Transferencias ULTRA RÁPIDAS con buffer de 1MB
    def _upload_file_fast(self, local_path, remote_path, filename):
        try:
            total = os.path.getsize(local_path)
            transferred = 0
            chunk_size = 1048576  # 1MB buffer para máxima velocidad
            
            self.transfer_start_time = time.time()

            self.root.after(0, lambda: self.status_label.config(text=f"Subiendo {filename}..."))
            self.root.after(0, lambda: self.progress_bar.configure(mode='determinate', maximum=100))

            with open(local_path, 'rb') as f_local:
                with self.sftp.open(remote_path, 'wb') as f_remote:
                    while True:
                        chunk = f_local.read(chunk_size)
                        if not chunk:
                            break
                        f_remote.write(chunk)
                        transferred += len(chunk)
                        if transferred % (chunk_size * 5) == 0 or transferred == total:
                            self.root.after(0, lambda t=transferred: self.update_progress(t, total, filename))

            elapsed = time.time() - self.transfer_start_time
            speed_mb = (total / (1024 * 1024)) / elapsed if elapsed > 0 else 0
            
            self.root.after(0, lambda: self.status_label.config(text=f"Subido: {filename} - {speed_mb:.1f} MB/s"))
            self.root.after(0, self.refresh_remote_browser)
            self.root.after(0, lambda: self.terminal.insert(tk.END, f"[+] Subido: {filename} ({speed_mb:.1f} MB/s)\n", 'success'))
            self.root.after(0, lambda: self.terminal.see(tk.END))

        except Exception as e:
            self.root.after(0, lambda: self.terminal.insert(tk.END, f"[-] Error subida: {e}\n", 'error'))
        finally:
            self.active_transfers -= 1
            if self.active_transfers <= 0:
                self.root.after(0, lambda: self.progress_bar.configure(value=0))
                self.root.after(0, lambda: self.progress_label.config(text=""))

    def _download_file_fast(self, remote_path, local_path, filename):
        try:
            total = self.sftp.stat(remote_path).st_size
            transferred = 0
            chunk_size = 1048576  # 1MB buffer para máxima velocidad
            
            self.transfer_start_time = time.time()

            self.root.after(0, lambda: self.status_label.config(text=f"Descargando {filename}..."))
            self.root.after(0, lambda: self.progress_bar.configure(mode='determinate', maximum=100))

            with self.sftp.open(remote_path, 'rb') as f_remote:
                with open(local_path, 'wb') as f_local:
                    while True:
                        chunk = f_remote.read(chunk_size)
                        if not chunk:
                            break
                        f_local.write(chunk)
                        transferred += len(chunk)
                        if transferred % (chunk_size * 5) == 0 or transferred == total:
                            self.root.after(0, lambda t=transferred: self.update_progress(t, total, filename))

            elapsed = time.time() - self.transfer_start_time
            speed_mb = (total / (1024 * 1024)) / elapsed if elapsed > 0 else 0

            self.root.after(0, lambda: self.status_label.config(text=f"Descargado: {filename} - {speed_mb:.1f} MB/s"))
            self.root.after(0, self.refresh_local_browser)
            self.root.after(0, lambda: self.terminal.insert(tk.END, f"[+] Descargado: {filename} ({speed_mb:.1f} MB/s)\n", 'success'))
            self.root.after(0, lambda: self.terminal.see(tk.END))

        except Exception as e:
            self.root.after(0, lambda: self.terminal.insert(tk.END, f"[-] Error descarga: {e}\n", 'error'))
        finally:
            self.active_transfers -= 1
            if self.active_transfers <= 0:
                self.root.after(0, lambda: self.progress_bar.configure(value=0))
                self.root.after(0, lambda: self.progress_label.config(text=""))

    def _upload_directory_fast(self, local_dir, remote_dir, dirname):
        try:
            self.transfer_start_time = time.time()
            self.root.after(0, lambda: self.status_label.config(text=f"Subiendo directorio {dirname}/..."))

            try:
                self.sftp.mkdir(remote_dir)
            except:
                pass

            total_files = sum(1 for _ in Path(local_dir).rglob('*') if _.is_file())
            uploaded_files = 0

            def upload_recursive(local, remote):
                nonlocal uploaded_files
                local_path = Path(local)
                for item in local_path.iterdir():
                    remote_item = f"{remote}/{item.name}"
                    if item.is_dir():
                        try:
                            self.sftp.mkdir(remote_item)
                        except:
                            pass
                        upload_recursive(str(item), remote_item)
                    else:
                        self.sftp.put(str(item), remote_item)
                        uploaded_files += 1
                        percent = (uploaded_files / total_files) * 100 if total_files > 0 else 0
                        self.root.after(0, lambda p=percent: self.progress_bar.configure(value=p))
                        self.root.after(0, lambda: self.progress_label.config(text=f"{uploaded_files}/{total_files} archivos ({percent:.1f}%)"))

            upload_recursive(local_dir, remote_dir)
            
            elapsed = time.time() - self.transfer_start_time
            self.root.after(0, lambda: self.status_label.config(text=f"Directorio subido: {dirname}"))
            self.root.after(0, self.refresh_remote_browser)
            self.root.after(0, lambda: self.terminal.insert(tk.END, f"[+] Directorio subido: {dirname}/\n", 'success'))

        except Exception as e:
            self.root.after(0, lambda: self.terminal.insert(tk.END, f"[-] Error subida directorio: {e}\n", 'error'))
        finally:
            self.active_transfers -= 1
            if self.active_transfers <= 0:
                self.root.after(0, lambda: self.progress_bar.configure(value=0))
                self.root.after(0, lambda: self.progress_label.config(text=""))

    def _download_directory_fast(self, remote_dir, local_dir, dirname):
        try:
            self.transfer_start_time = time.time()
            self.root.after(0, lambda: self.status_label.config(text=f"Descargando directorio {dirname}/..."))

            local_path = Path(local_dir)
            local_path.mkdir(parents=True, exist_ok=True)

            total_files = 0

            def count_files(remote):
                nonlocal total_files
                items = self.sftp.listdir_attr(remote)
                for item in items:
                    if stat.S_ISDIR(item.st_mode):
                        count_files(f"{remote}/{item.filename}")
                    else:
                        total_files += 1

            count_files(remote_dir)
            downloaded_files = 0

            def download_recursive(remote, local):
                nonlocal downloaded_files
                items = self.sftp.listdir_attr(remote)
                for item in items:
                    remote_item = f"{remote}/{item.filename}"
                    local_item = local / item.filename

                    if stat.S_ISDIR(item.st_mode):
                        local_item.mkdir(exist_ok=True)
                        download_recursive(remote_item, local_item)
                    else:
                        self.sftp.get(remote_item, str(local_item))
                        downloaded_files += 1
                        percent = (downloaded_files / total_files) * 100 if total_files > 0 else 0
                        self.root.after(0, lambda p=percent: self.progress_bar.configure(value=p))
                        self.root.after(0, lambda: self.progress_label.config(text=f"{downloaded_files}/{total_files} archivos ({percent:.1f}%)"))

            download_recursive(remote_dir, local_path)

            self.root.after(0, lambda: self.status_label.config(text=f"Directorio descargado: {dirname}"))
            self.root.after(0, self.refresh_local_browser)
            self.root.after(0, lambda: self.terminal.insert(tk.END, f"[+] Directorio descargado: {dirname}/\n", 'success'))

        except Exception as e:
            self.root.after(0, lambda: self.terminal.insert(tk.END, f"[-] Error descarga directorio: {e}\n", 'error'))
        finally:
            self.active_transfers -= 1
            if self.active_transfers <= 0:
                self.root.after(0, lambda: self.progress_bar.configure(value=0))
                self.root.after(0, lambda: self.progress_label.config(text=""))

    # ============================================
    # TERMINAL
    # ============================================
    def execute_command(self):
        cmd = self.cmd_entry.get().strip()
        if not cmd:
            return

        if not self.is_connected:
            self.terminal.insert(tk.END, "[-] No conectado al servidor\n", 'error')
            self.terminal.see(tk.END)
            return

        self.cmd_entry.delete(0, tk.END)
        self.terminal.insert(tk.END, f"\n$ {cmd}\n", 'info')
        self.terminal.see(tk.END)

        thread = threading.Thread(target=self._do_execute, args=(cmd,), daemon=True)
        thread.start()

    def run_quick_command(self, cmd):
        self.cmd_entry.delete(0, tk.END)
        self.cmd_entry.insert(0, cmd)
        self.execute_command()

    def _do_execute(self, cmd):
        try:
            stdin, stdout, stderr = self.client.exec_command(cmd)
            output = stdout.read().decode()
            error = stderr.read().decode()
            self.root.after(0, lambda: self._show_output(output, error))
        except Exception as e:
            self.root.after(0, lambda: self._show_output("", str(e)))

    def _show_output(self, output, error):
        if output:
            self.terminal.insert(tk.END, output)
        if error:
            self.terminal.insert(tk.END, f"Error: {error}\n", 'error')
        self.terminal.insert(tk.END, "\n")
        self.terminal.see(tk.END)

    def clear_terminal(self):
        self.terminal.delete(1.0, tk.END)
        self.print_terminal_banner()

    # ============================================
    # ELIMINAR ARCHIVOS
    # ============================================
    def delete_local_selected(self):
        selection = self.local_tree.selection()
        if selection:
            item = self.local_tree.item(selection[0])
            name = item['values'][0]
            path = self.local_cwd / name

            if messagebox.askyesno("Confirmar", f"¿Eliminar '{name}' permanentemente?"):
                try:
                    if path.is_dir():
                        shutil.rmtree(path)
                    else:
                        path.unlink()
                    self.refresh_local_browser()
                    self.terminal.insert(tk.END, f"[+] Eliminado: {name}\n", 'success')
                except Exception as e:
                    self.terminal.insert(tk.END, f"[-] Error al eliminar: {e}\n", 'error')

    def delete_remote_selected(self):
        selection = self.remote_tree.selection()
        if selection:
            item = self.remote_tree.item(selection[0])
            name = item['values'][0]
            remote_path = f"{self.remote_cwd}/{name}"

            if messagebox.askyesno("Confirmar", f"¿Eliminar '{name}' permanentemente?"):
                thread = threading.Thread(target=self._delete_remote, args=(remote_path, name), daemon=True)
                thread.start()

    def _delete_remote(self, remote_path, name):
        try:
            attrs = self.sftp.stat(remote_path)
            if stat.S_ISDIR(attrs.st_mode):
                self._delete_recursive_remote(remote_path)
            else:
                self.sftp.remove(remote_path)
            self.root.after(0, self.refresh_remote_browser)
            self.root.after(0, lambda: self.terminal.insert(tk.END, f"[+] Eliminado: {name}\n", 'success'))
        except Exception as e:
            self.root.after(0, lambda: self.terminal.insert(tk.END, f"[-] Error al eliminar: {e}\n", 'error'))

    def _delete_recursive_remote(self, path):
        items = self.sftp.listdir_attr(path)
        for item in items:
            item_path = f"{path}/{item.filename}"
            if stat.S_ISDIR(item.st_mode):
                self._delete_recursive_remote(item_path)
            else:
                self.sftp.remove(item_path)
        self.sftp.rmdir(path)

    def copy_local_path(self):
        selection = self.local_tree.selection()
        if selection:
            item = self.local_tree.item(selection[0])
            name = item['values'][0]
            path = str(self.local_cwd / name)
            self.root.clipboard_clear()
            self.root.clipboard_append(path)
            self.status_label.config(text=f"Ruta copiada: {path}")

    def copy_remote_path(self):
        selection = self.remote_tree.selection()
        if selection:
            item = self.remote_tree.item(selection[0])
            name = item['values'][0]
            path = f"{self.remote_cwd}/{name}"
            self.root.clipboard_clear()
            self.root.clipboard_append(path)
            self.status_label.config(text=f"Ruta copiada: {path}")

    # ============================================
    # CONEXIÓN SSH
    # ============================================
    def show_connection_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Conexión SSH")
        dialog.geometry("500x520")
        dialog.configure(bg=self.colors['bg'])
        dialog.transient(self.root)
        dialog.grab_set()

        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialog.winfo_screenheight() // 2) - (520 // 2)
        dialog.geometry(f"+{x}+{y}")

        main_frame = tk.Frame(dialog, bg=self.colors['bg'], padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(main_frame, text="Conexión SSH", font=self.fonts['bold'],
                fg=self.colors['accent'], bg=self.colors['bg']).pack(pady=(0, 20))

        # Servidores guardados
        saved_frame = tk.LabelFrame(main_frame, text="Servidores Guardados", font=self.fonts['normal'],
                                    bg=self.colors['bg'], fg=self.colors['fg'])
        saved_frame.pack(fill=tk.X, pady=(0, 15))

        self.dialog_server_combo = ttk.Combobox(saved_frame, values=[s['name'] for s in self.servers], width=40)
        self.dialog_server_combo.pack(padx=10, pady=10)
        self.dialog_server_combo.bind('<<ComboboxSelected>>', self.on_server_select)

        # Datos de conexión
        conn_frame = tk.LabelFrame(main_frame, text="Parámetros de Conexión", font=self.fonts['normal'],
                                   bg=self.colors['bg'], fg=self.colors['fg'])
        conn_frame.pack(fill=tk.X, pady=(0, 15))

        tk.Label(conn_frame, text="Host/IP:", bg=self.colors['bg'], fg=self.colors['fg']).grid(row=0, column=0, sticky='w', padx=10, pady=5)
        self.dialog_host = tk.Entry(conn_frame, bg=self.colors['bg_dark'], fg=self.colors['fg'], relief='flat', bd=1, width=35)
        self.dialog_host.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(conn_frame, text="Puerto:", bg=self.colors['bg'], fg=self.colors['fg']).grid(row=1, column=0, sticky='w', padx=10, pady=5)
        self.dialog_port = tk.Entry(conn_frame, bg=self.colors['bg_dark'], fg=self.colors['fg'], relief='flat', bd=1, width=35)
        self.dialog_port.insert(0, "22")
        self.dialog_port.grid(row=1, column=1, padx=10, pady=5)

        tk.Label(conn_frame, text="Usuario:", bg=self.colors['bg'], fg=self.colors['fg']).grid(row=2, column=0, sticky='w', padx=10, pady=5)
        self.dialog_user = tk.Entry(conn_frame, bg=self.colors['bg_dark'], fg=self.colors['fg'], relief='flat', bd=1, width=35)
        self.dialog_user.grid(row=2, column=1, padx=10, pady=5)

        # Autenticación
        auth_frame = tk.LabelFrame(main_frame, text="Autenticación", font=self.fonts['normal'],
                                   bg=self.colors['bg'], fg=self.colors['fg'])
        auth_frame.pack(fill=tk.X, pady=(0, 15))

        self.auth_var = tk.StringVar(value="password")
        tk.Radiobutton(auth_frame, text="Contraseña", variable=self.auth_var, value="password",
                       bg=self.colors['bg'], fg=self.colors['fg'], selectcolor=self.colors['bg']).grid(row=0, column=0, padx=10, pady=5)
        tk.Radiobutton(auth_frame, text="Clave SSH", variable=self.auth_var, value="key",
                       bg=self.colors['bg'], fg=self.colors['fg'], selectcolor=self.colors['bg']).grid(row=0, column=1, padx=10, pady=5)

        # Password
        self.pass_frame = tk.Frame(auth_frame, bg=self.colors['bg'])
        self.pass_frame.grid(row=1, column=0, columnspan=2, pady=10)
        tk.Label(self.pass_frame, text="Contraseña:", bg=self.colors['bg'], fg=self.colors['fg']).pack(side=tk.LEFT, padx=5)
        self.dialog_password = tk.Entry(self.pass_frame, show="•", bg=self.colors['bg_dark'], fg=self.colors['fg'], width=30)
        self.dialog_password.pack(side=tk.LEFT, padx=5)

        # Key
        self.key_frame = tk.Frame(auth_frame, bg=self.colors['bg'])
        tk.Label(self.key_frame, text="Ruta Clave:", bg=self.colors['bg'], fg=self.colors['fg']).pack(side=tk.LEFT, padx=5)
        self.dialog_key = tk.Entry(self.key_frame, bg=self.colors['bg_dark'], fg=self.colors['fg'], width=25)
        self.dialog_key.pack(side=tk.LEFT, padx=5)
        tk.Button(self.key_frame, text="Examinar", command=self.browse_key_file,
                  bg=self.colors['accent'], fg='white', relief='flat', padx=10).pack(side=tk.LEFT, padx=5)
        self.key_frame.grid_forget()

        # Botones
        btn_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        tk.Button(btn_frame, text="Conectar", command=lambda: self.do_connect(dialog),
                  bg=self.colors['success'], fg='white', font=self.fonts['bold'],
                  relief='flat', padx=20, pady=5).pack(side=tk.LEFT, padx=5)

        tk.Button(btn_frame, text="Guardar Servidor", command=self.save_server_from_dialog,
                  bg=self.colors['accent'], fg='white', relief='flat', padx=20, pady=5).pack(side=tk.LEFT, padx=5)

        tk.Button(btn_frame, text="Cancelar", command=dialog.destroy,
                  bg=self.colors['bg_light'], fg=self.colors['fg'], relief='flat', padx=20, pady=5).pack(side=tk.LEFT, padx=5)

        self.auth_var.trace('w', lambda *args: self.toggle_auth_fields_dialog())

    def toggle_auth_fields_dialog(self):
        if self.auth_var.get() == "password":
            self.pass_frame.grid()
            self.key_frame.grid_forget()
        else:
            self.pass_frame.grid_forget()
            self.key_frame.grid(row=1, column=0, columnspan=2, pady=10)

    def on_server_select(self, event):
        name = self.dialog_server_combo.get()
        for server in self.servers:
            if server['name'] == name:
                self.dialog_host.delete(0, tk.END)
                self.dialog_host.insert(0, server['host'])
                self.dialog_port.delete(0, tk.END)
                self.dialog_port.insert(0, server['port'])
                self.dialog_user.delete(0, tk.END)
                self.dialog_user.insert(0, server['user'])
                break

    def browse_key_file(self):
        filename = filedialog.askopenfilename(title="Seleccionar Clave Privada SSH")
        if filename:
            self.dialog_key.delete(0, tk.END)
            self.dialog_key.insert(0, filename)

    def save_server_from_dialog(self):
        name = simpledialog.askstring("Guardar Servidor", "Nombre del servidor:")
        if name:
            server = {
                'name': name,
                'host': self.dialog_host.get(),
                'port': self.dialog_port.get(),
                'user': self.dialog_user.get(),
            }
            self.servers.append(server)
            self.save_servers()
            messagebox.showinfo("Éxito", f"Servidor '{name}' guardado")

    def save_current_server(self):
        if not self.current_server:
            messagebox.showwarning("Advertencia", "No hay conexión activa")
            return

        name = simpledialog.askstring("Guardar Servidor", "Nombre del servidor:")
        if name:
            server = {
                'name': name,
                'host': self.current_server['host'],
                'port': self.current_server['port'],
                'user': self.current_server['user'],
            }
            self.servers.append(server)
            self.save_servers()
            messagebox.showinfo("Éxito", f"Servidor '{name}' guardado")

    def manage_servers(self):
        manage_window = tk.Toplevel(self.root)
        manage_window.title("Gestionar Servidores")
        manage_window.geometry("500x400")
        manage_window.configure(bg=self.colors['bg'])

        frame = tk.Frame(manage_window, bg=self.colors['bg'], padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)

        columns = ('Nombre', 'Host', 'Usuario')
        tree = ttk.Treeview(frame, columns=columns, show='headings', height=15)

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=140)

        scroll = ttk.Scrollbar(frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        for server in self.servers:
            tree.insert('', 'end', values=(server['name'], server['host'], server['user']))

        def delete_server():
            selection = tree.selection()
            if selection:
                item = tree.item(selection[0])
                name = item['values'][0]
                if messagebox.askyesno("Confirmar", f"¿Eliminar '{name}'?"):
                    for i, s in enumerate(self.servers):
                        if s['name'] == name:
                            del self.servers[i]
                            break
                    self.save_servers()
                    tree.delete(selection[0])

        btn_frame = tk.Frame(manage_window, bg=self.colors['bg'])
        btn_frame.pack(fill=tk.X, pady=10)

        tk.Button(btn_frame, text="Eliminar", command=delete_server,
                  bg=self.colors['error'], fg='white', relief='flat', padx=20).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Cerrar", command=manage_window.destroy,
                  bg=self.colors['bg_light'], fg=self.colors['fg'], relief='flat', padx=20).pack(side=tk.LEFT, padx=10)

    def do_connect(self, dialog):
        host = self.dialog_host.get().strip()
        port = self.dialog_port.get().strip()
        user = self.dialog_user.get().strip()

        if not host or not user:
            messagebox.showerror("Error", "Host y Usuario son requeridos")
            return

        self.pending_connection = {
            'host': host,
            'port': int(port),
            'user': user,
            'auth_type': self.auth_var.get(),
            'password': self.dialog_password.get() if self.auth_var.get() == "password" else None,
            'key_path': self.dialog_key.get() if self.auth_var.get() == "key" else None,
        }

        dialog.destroy()

        self.progress_bar.configure(mode='indeterminate')
        self.progress_bar.start()
        self.status_label.config(text="Conectando...")

        thread = threading.Thread(target=self._do_connect, daemon=True)
        thread.start()

    def _do_connect(self):
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            kwargs = {
                'hostname': self.pending_connection['host'],
                'port': self.pending_connection['port'],
                'username': self.pending_connection['user'],
                'timeout': 30,
                'compress': True,
            }

            if self.pending_connection['auth_type'] == 'key':
                key_path = os.path.expanduser(self.pending_connection['key_path'])
                if os.path.exists(key_path):
                    kwargs['pkey'] = paramiko.RSAKey.from_private_key_file(key_path)
                else:
                    raise Exception("Archivo de clave no encontrado")
            else:
                kwargs['password'] = self.pending_connection['password']

            self.client.connect(**kwargs)
            self.sftp = self.client.open_sftp()
            self.is_connected = True
            self.current_server = self.pending_connection

            self.remote_cwd = f"/home/{self.pending_connection['user']}"
            self.remote_history = [self.remote_cwd]
            self.remote_history_index = 0

            self.root.after(0, self._on_connect_success)

        except Exception as connect_error:
            error_msg = str(connect_error)
            self.root.after(0, lambda: self._on_connect_error(error_msg))

    def _on_connect_success(self):
        self.progress_bar.stop()
        self.progress_bar.configure(mode='determinate')
        self.conn_status.config(text="● Conectado", fg=self.colors['success'])
        self.server_info.config(text=f"{self.current_server['user']}@{self.current_server['host']}")
        self.status_label.config(text="Conexión exitosa")
        self.right_btn.config(state='normal')
        self.left_btn.config(state='normal')

        self.remote_path_var.set(self.remote_cwd)
        self.refresh_remote_browser()

        self.terminal.insert(tk.END, f"[+] Conectado a {self.current_server['host']}\n", 'success')
        self.terminal.see(tk.END)

        self.save_last_server()

    def _on_connect_error(self, error):
        self.progress_bar.stop()
        self.progress_bar.configure(mode='determinate')
        self.conn_status.config(text="● Desconectado", fg=self.colors['error'])
        self.status_label.config(text=f"Error: {error}")
        messagebox.showerror("Error de Conexión", error)

    def disconnect_ssh(self):
        if self.client:
            try:
                self.sftp.close()
                self.client.close()
            except:
                pass
            self.client = None
            self.sftp = None

        self.is_connected = False
        self.conn_status.config(text="● Desconectado", fg=self.colors['error'])
        self.server_info.config(text="")
        self.status_label.config(text="Desconectado")
        self.right_btn.config(state='disabled')
        self.left_btn.config(state='disabled')

        for item in self.remote_tree.get_children():
            self.remote_tree.delete(item)

        self.terminal.insert(tk.END, "[-] Desconectado del servidor\n", 'error')
        self.terminal.see(tk.END)

    # ============================================
    # UTILIDADES
    # ============================================
    def _format_bytes(self, size: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"

    def load_servers(self):
        if SERVERS_FILE.exists():
            try:
                with open(SERVERS_FILE, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []

    def save_servers(self):
        try:
            with open(SERVERS_FILE, 'w') as f:
                json.dump(self.servers, f, indent=2)
        except:
            pass

    def save_last_server(self):
        last_file = CONFIG_DIR / "last_server.json"
        try:
            with open(last_file, 'w') as f:
                json.dump({
                    'host': self.current_server['host'],
                    'port': self.current_server['port'],
                    'user': self.current_server['user'],
                }, f)
        except:
            pass

    def load_last_server(self):
        last_file = CONFIG_DIR / "last_server.json"
        if last_file.exists():
            try:
                with open(last_file, 'r') as f:
                    data = json.load(f)
                    self.last_host = data.get('host', '')
                    self.last_port = data.get('port', '22')
                    self.last_user = data.get('user', '')
            except:
                pass

    def show_about(self):
        about_text = """SSH Commander Professional v6.0

Cliente SSH profesional con gestor de archivos dual.

Caracteristicas:
- Explorador de archivos dual (Local/Remoto)
- Transferencia ULTRA RAPIDA con buffer de 1MB
- Velocidad hasta 10-20MB/s en redes rapidas
- Terminal independiente con mas de 80 comandos rapidos
- Gestion de perfiles de servidores
- Subida/descarga de directorios completos
- Barra de progreso en tiempo real con velocidad
- Navegacion completa en ambos paneles

© 2026 - Todos los derechos reservados"""
        messagebox.showinfo("Acerca de", about_text)

    def setup_bindings(self):
        self.root.bind('<Control-n>', lambda e: self.show_connection_dialog())
        self.root.bind('<Control-d>', lambda e: self.disconnect_ssh())
        self.root.bind('<Control-q>', lambda e: self.on_closing())
        self.root.bind('<F5>', lambda e: self.refresh_all())
        self.root.bind('<F1>', lambda e: self.show_terminal_window())

    def on_closing(self):
        self.disconnect_ssh()
        try:
            self.terminal_window.destroy()
        except:
            pass
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    print("""
================================================================================
                    SSH Commander Professional v6.0
                              Iniciando...
================================================================================
  ✓ Transferencias ULTRA RAPIDAS (buffer 1MB + compresion)
  ✓ Velocidad hasta 10-20MB/s en redes rapidas
  ✓ Terminal con mas de 80 comandos
  ✓ Errores corregidos
================================================================================
    """)
    app = SSHCommanderProfessional()
    app.run()