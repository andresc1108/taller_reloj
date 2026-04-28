import json
import math
import os
import platform
import threading
import time
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import messagebox, simpledialog, ttk
from tkinter import font as tkfont

try:
    import cairosvg
    from PIL import Image, ImageTk
    from io import BytesIO
    SVG_AVAILABLE = True
except (ImportError, OSError):
    SVG_AVAILABLE = False


class ClockConfig:
    """Configuration management for the clock application."""
    def __init__(self):
        self.config_file = os.path.join(os.path.dirname(__file__), 'clock_config.json')
        self.default_config = {
            'theme': 'light',
            'alarms': [],
            'world_clocks': ['UTC', 'America/New_York', 'Europe/London', 'Asia/Tokyo'],
            'sound_enabled': True,
            'fullscreen': False,
            'animations': True
        }
        self.config = self.load_config()

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return {**self.default_config, **json.load(f)}
            except:
                pass
        return self.default_config.copy()

    def save_config(self):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except:
            pass

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save_config()


class AlarmManager:
    """Manages alarms with persistence and notifications."""
    def __init__(self, config):
        self.config = config
        self.alarms = self.config.get('alarms', [])
        self.history = []
        self.check_thread = None
        self.running = False

    def add_alarm(self, time_str, label, sound='default'):
        alarm = {
            'time': time_str,
            'label': label,
            'sound': sound,
            'enabled': True,
            'created': datetime.now().isoformat()
        }
        self.alarms.append(alarm)
        self.save_alarms()
        return alarm

    def delete_alarm(self, index):
        if 0 <= index < len(self.alarms):
            deleted = self.alarms.pop(index)
            self.save_alarms()
            return deleted
        return None

    def save_alarms(self):
        self.config.set('alarms', self.alarms)

    def start_monitoring(self, callback):
        self.running = True
        self.check_thread = threading.Thread(target=self._monitor_alarms, args=(callback,))
        self.check_thread.daemon = True
        self.check_thread.start()

    def stop_monitoring(self):
        self.running = False
        if self.check_thread:
            self.check_thread.join(timeout=1)

    def _monitor_alarms(self, callback):
        last_minute = None
        while self.running:
            now = datetime.now()
            current_time = now.strftime('%H:%M')

            if current_time != last_minute:
                last_minute = current_time
                for alarm in self.alarms:
                    if alarm['enabled'] and alarm['time'] == current_time:
                        self.history.append({
                            'alarm': alarm,
                            'triggered': now.isoformat()
                        })
                        callback(alarm)

            time.sleep(1)


class WorldClockManager:
    """Manages multiple world clocks with proper timezone support."""
    # Timezone offsets respecto a UTC 
    TIMEZONES = {
        'America/Bogota': -5,          # Colombia (predeterminado)
        'America/New_York': -5,        # Nueva York
        'America/Chicago': -6,         # Chicago
        'America/Los_Angeles': -8,     # Los Ángeles
        'America/Mexico_City': -6,     # México
        'America/Sao_Paulo': -3,       # São Paulo, Brasil
        'Europe/London': 0,            # Londres
        'Europe/Paris': 1,             # París
        'Europe/Berlin': 1,            # Berlín
        'Europe/Moscow': 3,            # Moscú
        'Asia/Dubai': 4,               # Dubái
        'Asia/Bangkok': 7,             # Bangkok
        'Asia/Singapore': 8,           # Singapur
        'Asia/Shanghai': 8,            # Shanghai
        'Asia/Hong_Kong': 8,           # Hong Kong
        'Asia/Tokyo': 9,               # Tokio
        'Asia/Seoul': 9,               # Seúl
        'Australia/Sydney': 10,        # Sídney
        'Pacific/Auckland': 12,        # Auckland
    }

    def __init__(self, config):
        self.config = config
        # Bogotá como predeterminado, luego las más importantes
        default_clocks = ['America/Bogota', 'America/New_York', 'Europe/London', 'Asia/Tokyo', 'Australia/Sydney']
        self.clocks = self.config.get('world_clocks', default_clocks)

    def add_clock(self, timezone):
        if timezone not in self.clocks and timezone in self.TIMEZONES:
            self.clocks.append(timezone)
            self.save_clocks()
            return True
        return False

    def remove_clock(self, timezone):
        # No permitir eliminar la última ciudad
        if timezone in self.clocks and len(self.clocks) > 1:
            self.clocks.remove(timezone)
            self.save_clocks()
            return True
        return False

    def save_clocks(self):
        self.config.set('world_clocks', self.clocks)

    def get_time(self, timezone):
        """Retorna la hora actual para una zona horaria específica."""
        offset = self.TIMEZONES.get(timezone, 0)
        return datetime.now() + timedelta(hours=offset)
    
    def get_display_name(self, timezone):
        """Retorna nombre amigable de la zona horaria."""
        names = {
            'America/Bogota': 'Bogotá, Colombia',
            'America/New_York': 'Nueva York, USA',
            'America/Chicago': 'Chicago, USA',
            'America/Los_Angeles': 'Los Ángeles, USA',
            'America/Mexico_City': 'México, México',
            'America/Sao_Paulo': 'São Paulo, Brasil',
            'Europe/London': 'Londres, Reino Unido',
            'Europe/Paris': 'París, Francia',
            'Europe/Berlin': 'Berlín, Alemania',
            'Europe/Moscow': 'Moscú, Rusia',
            'Asia/Dubai': 'Dubái, UAE',
            'Asia/Bangkok': 'Bangkok, Tailandia',
            'Asia/Singapore': 'Singapur',
            'Asia/Shanghai': 'Shanghai, China',
            'Asia/Hong_Kong': 'Hong Kong',
            'Asia/Tokyo': 'Tokio, Japón',
            'Asia/Seoul': 'Seúl, Corea',
            'Australia/Sydney': 'Sídney, Australia',
            'Pacific/Auckland': 'Auckland, Nueva Zelanda',
        }
        return names.get(timezone, timezone)


class AudioManager:
    """Manages audio playback for alarms and notifications."""
    def __init__(self):
        self.sounds = {}
        self.load_sounds()

    def load_sounds(self):
        self.sound_freqs = {
            'default': (880, 500),
            'gentle': (660, 300),
            'urgent': (1000, 800)
        }

    def play_sound(self, sound_name='default', enabled=True):
        if not enabled:
            return

        if platform.system() == "Windows" and winsound:
            freq, duration = self.sound_freqs.get(sound_name, (880, 500))
            winsound.Beep(freq, duration)
        else:
            # Fallback: system bell
            print('\a')


class ClockApp:
    def __init__(self):
        self.config = ClockConfig()
        self.alarm_manager = AlarmManager(self.config)
        self.world_clock_manager = WorldClockManager(self.config)
        self.audio_manager = AudioManager()

        self.root = tk.Tk()
        self.root.title("ACHICHAY TIME")
        self.root.geometry("1200x800")
        self.root.resizable(True, True)

        # Theme and style setup
        self.style = ttk.Style()
        self.setup_themes()

        # Load SVG icons if available
        self.svg_icons = {
            'add': '''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 4V20M4 12H20" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>''',
            'delete': '''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M3 6H5H21" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><path d="M8 6V4C8 3.44772 8.44772 3 9 3H15C15.5523 3 16 3.44772 16 4V6M19 6V20C19 20.5523 18.5523 21 18 21H6C5.44772 21 5 20.5523 5 20V6H19Z" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><path d="M10 11V17" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><path d="M14 11V17" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>''',
            'history': '''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 8V12L15 15M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>''',
            'clear': '''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M3 6H5H21" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><path d="M8 6V4C8 3.44772 8.44772 3 9 3H15C15.5523 3 16 3.44772 16 4V6M19 6V20C19 20.5523 18.5523 21 18 21H6C5.44772 21 5 20.5523 5 20V6H19Z" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><path d="M10 11V17" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><path d="M14 11V17" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>'''
        }
        self.icons = {}
        if SVG_AVAILABLE:
            for name, svg in self.svg_icons.items():
                self.icons[name] = self.load_svg(svg)

        # UI variables
        self.mode = "analog"
        self.current_tab = "clock"
        self.stopwatch_running = False
        self.stopwatch_start = None
        self.stopwatch_elapsed = timedelta()

        self.timer_running = False
        self.timer_duration = None
        self.timer_end = None

        self.offset_var = tk.IntVar(value=0)

        # Language support
        self.language = self.config.get('language', 'es')
        self.languages = {
            'es': {
                'date_format': '%A, %d de %B de %Y',
                'tabs': ['Reloj Principal', 'Relojes Mundiales', 'Alarmas', 'Cronómetro', 'Temporizador', 'Configuración'],
                'buttons': {
                    'add_alarm': 'Agregar Alarma',
                    'delete_alarm': 'Eliminar Alarma Seleccionada',
                    'start': 'Iniciar',
                    'pause': 'Pausar',
                    'reset': 'Reiniciar',
                    'record_lap': 'Registrar Vuelta',
                    'clear_history': 'Limpiar Historial'
                }
            },
            'en': {
                'date_format': '%A, %B %d, %Y',
                'tabs': ['Main Clock', 'World Clocks', 'Alarms', 'Stopwatch', 'Timer', 'Settings'],
                'buttons': {
                    'add_alarm': 'Add Alarm',
                    'delete_alarm': 'Delete Selected Alarm',
                    'start': 'Start',
                    'pause': 'Pause',
                    'reset': 'Reset',
                    'record_lap': 'Record Lap',
                    'clear_history': 'Clear History'
                }
            }
        }

        # World clock labels for updates
        self.world_clock_labels = {}

        # Animation variables
        self.animation_angle = 0
        self.pendulum_angle = 0
        self.animations_var = tk.BooleanVar(value=self.config.get('animations', True))

        self.create_widgets()
        self.apply_theme()
        self.update_clock()

        # Start alarm monitoring
        self.alarm_manager.start_monitoring(self.on_alarm_trigger)

        self.root.mainloop()

    def setup_themes(self):
        self.themes = {
            "light": {
                "bg": "#f8f9fa",
                "fg": "#212529",
                "accent": "#007bff",
                "secondary": "#6c757d",
                "success": "#28a745",
                "warning": "#ffc107",
                "danger": "#dc3545",
                "canvas_bg": "#ffffff",
                "card_bg": "#ffffff",
                "shadow": "#e9ecef"
            },
            "dark": {
                "bg": "#212529",
                "fg": "#f8f9fa",
                "accent": "#0d6efd",
                "secondary": "#6c757d",
                "success": "#198754",
                "warning": "#fd7e14",
                "danger": "#dc3545",
                "canvas_bg": "#343a40",
                "card_bg": "#495057",
                "shadow": "#343a40"
            }
        }

    def load_svg(self, svg_string, size=(24, 24)):
        """Convierte SVG a PhotoImage usando cairosvg y PIL."""
        png_bytes = cairosvg.svg2png(bytestring=svg_string.encode('utf-8'), output_width=size[0], output_height=size[1])
        image = Image.open(BytesIO(png_bytes))
        return ImageTk.PhotoImage(image)

    def create_widgets(self):
        # Main container
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Top bar with controls
        self.create_top_bar(main_frame)

        # Tabbed interface
        self.create_tabs(main_frame)

        # Status bar
        self.create_status_bar(main_frame)

    def create_top_bar(self, parent):
        top_frame = tk.Frame(parent, relief=tk.RAISED, bd=2)
        top_frame.pack(fill=tk.X, pady=(0, 10))

        # Theme selector
        theme_frame = tk.Frame(top_frame)
        theme_frame.pack(side=tk.LEFT, padx=10)

        tk.Label(theme_frame, text="Tema:", font=("Segoe UI", 10)).pack(side=tk.LEFT)
        self.theme_var = tk.StringVar(value=self.config.get('theme', 'green'))
        theme_combo = ttk.Combobox(theme_frame, textvariable=self.theme_var,
                                 values=list(self.themes.keys()), state="readonly", width=10)
        theme_combo.pack(side=tk.LEFT, padx=(5, 0))
        theme_combo.bind('<<ComboboxSelected>>', self.change_theme)

        # Mode toggle
        mode_frame = tk.Frame(top_frame)
        mode_frame.pack(side=tk.LEFT, padx=20)

        self.mode_var = tk.StringVar(value="analog")
        tk.Radiobutton(mode_frame, text="Analógico", variable=self.mode_var,
                      value="analog", command=self.toggle_mode).pack(side=tk.LEFT)
        tk.Radiobutton(mode_frame, text="Digital", variable=self.mode_var,
                      value="digital", command=self.toggle_mode).pack(side=tk.LEFT, padx=(10, 0))

        # Sound toggle
        sound_frame = tk.Frame(top_frame)
        sound_frame.pack(side=tk.LEFT, padx=20)

        self.sound_var = tk.BooleanVar(value=self.config.get('sound_enabled', True))
        tk.Checkbutton(sound_frame, text="Sonido", variable=self.sound_var,
                      command=self.toggle_sound).pack(side=tk.LEFT)

        # Fullscreen button
        tk.Button(top_frame, text="Pantalla Completa", command=self.toggle_fullscreen,
                 relief=tk.FLAT, padx=10).pack(side=tk.RIGHT, padx=10)

    def create_tabs(self, parent):
        tab_control = ttk.Notebook(parent)

        # Clock tab
        clock_tab = ttk.Frame(tab_control)
        self.create_clock_tab(clock_tab)
        tab_control.add(clock_tab, text='Reloj Principal')

        # World clocks tab
        world_tab = ttk.Frame(tab_control)
        self.create_world_clocks_tab(world_tab)
        tab_control.add(world_tab, text='Relojes Mundiales')

        # Alarms tab
        alarm_tab = ttk.Frame(tab_control)
        self.create_alarms_tab(alarm_tab)
        tab_control.add(alarm_tab, text='Alarmas')

        # Stopwatch tab
        stopwatch_tab = ttk.Frame(tab_control)
        self.create_stopwatch_tab(stopwatch_tab)
        tab_control.add(stopwatch_tab, text='Cronómetro')

        # Timer tab
        timer_tab = ttk.Frame(tab_control)
        self.create_timer_tab(timer_tab)
        tab_control.add(timer_tab, text='Temporizador')

        tab_control.pack(fill=tk.BOTH, expand=True)

    def create_clock_tab(self, parent):
        # Clock display area
        clock_frame = tk.Frame(parent)
        clock_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Canvas for analog clock
        self.canvas = tk.Canvas(clock_frame, width=400, height=400,
                               bg=self.themes[self.theme_var.get()]["canvas_bg"],
                               highlightthickness=0)
        self.canvas.pack(pady=10)

        # Digital display
        self.digital_label = tk.Label(clock_frame, text="00:00:00",
                                    font=("Segoe UI", 48, "bold"),
                                    bg=self.themes[self.theme_var.get()]["bg"],
                                    fg=self.themes[self.theme_var.get()]["fg"])
        self.digital_label.pack(pady=10)

        # Toggle to analog button 
        self.analog_btn = tk.Button(clock_frame, text="Ver Analógico", command=self.toggle_to_analog,
                                   relief=tk.FLAT, padx=10, pady=5)
        # Initially hidden

        # Date display
        self.date_label = tk.Label(clock_frame, text="",
                                 font=("Segoe UI", 16),
                                 bg=self.themes[self.theme_var.get()]["bg"],
                                 fg=self.themes[self.theme_var.get()]["fg"])
        self.date_label.pack()

    def create_world_clocks_tab(self, parent):
        # World clocks display
        self.world_frame = tk.Frame(parent)
        self.world_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Add clock button
        add_frame = tk.Frame(self.world_frame)
        add_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(add_frame, text="Agregar zona horaria:", font=("Segoe UI", 10)).pack(side=tk.LEFT)
        
        self.timezone_var = tk.StringVar()
        timezone_values = [self.world_clock_manager.get_display_name(tz) for tz in self.world_clock_manager.TIMEZONES.keys()]
        timezone_combo = ttk.Combobox(add_frame, textvariable=self.timezone_var,
                                    values=timezone_values,
                                    state="readonly", width=30)
        timezone_combo.pack(side=tk.LEFT, padx=(10, 0))

        tk.Button(add_frame, text="Agregar", command=self.add_world_clock_from_combo,
                 relief=tk.FLAT, padx=15, pady=8).pack(side=tk.LEFT, padx=(10, 0))

        # Separator
        ttk.Separator(self.world_frame, orient='horizontal').pack(fill=tk.X, pady=10)

        # Clocks container with scrollbar
        canvas_frame = tk.Frame(self.world_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(canvas_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.world_canvas = tk.Canvas(canvas_frame, yscrollcommand=scrollbar.set, highlightthickness=0)
        self.world_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.world_canvas.yview)

        self.world_clocks_container = tk.Frame(self.world_canvas, bg=self.themes[self.theme_var.get()]["bg"])
        self.world_canvas.create_window((0, 0), window=self.world_clocks_container, anchor="nw")

        # Update scroll region
        self.world_clocks_container.bind("<Configure>", 
            lambda e: self.world_canvas.configure(scrollregion=self.world_canvas.bbox("all")))

        # Store references for updating
        self.world_clock_labels = {}
        self.update_world_clocks()

    def create_alarms_tab(self, parent):
        alarms_frame = tk.Frame(parent)
        alarms_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Buttons frame
        buttons_frame = tk.Frame(alarms_frame)
        buttons_frame.pack(fill=tk.X, pady=(0, 20))

        # Add alarm button with icon
        add_text = "" if self.icons.get('add') else "➕ " + self.languages[self.language]['buttons']['add_alarm']
        self.add_alarm_btn = tk.Button(buttons_frame, text=add_text, command=self.add_alarm,
                 relief=tk.FLAT, padx=20, pady=10, bg=self.themes[self.theme_var.get()]["success"], fg="white",
                 image=self.icons.get('add'), compound=tk.LEFT)
        self.add_alarm_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Delete button with icon
        delete_text = "" if self.icons.get('delete') else "🗑️ " + self.languages[self.language]['buttons']['delete_alarm']
        self.delete_alarm_btn = tk.Button(buttons_frame, text=delete_text,
                 command=self.delete_alarm, relief=tk.FLAT, padx=20, pady=10, bg=self.themes[self.theme_var.get()]["danger"], fg="white",
                 image=self.icons.get('delete'), compound=tk.LEFT)
        self.delete_alarm_btn.pack(side=tk.LEFT)

        # Alarms list
        list_frame = tk.Frame(alarms_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.alarms_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set,
                                        font=("Segoe UI", 11), selectmode=tk.SINGLE)
        self.alarms_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.alarms_listbox.yview)

        # Separator
        ttk.Separator(alarms_frame, orient='horizontal').pack(fill=tk.X, pady=10)

        # Alarm history
        history_frame = tk.Frame(alarms_frame)
        history_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(history_frame, text="📋 Historial de Alarmas:", font=("Segoe UI", 14, "bold")).pack(anchor=tk.W, pady=(0, 10))

        scrollbar_hist = tk.Scrollbar(history_frame)
        scrollbar_hist.pack(side=tk.RIGHT, fill=tk.Y)

        self.history_listbox = tk.Listbox(history_frame, yscrollcommand=scrollbar_hist.set,
                                         font=("Segoe UI", 10), height=10)
        self.history_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar_hist.config(command=self.history_listbox.yview)

        clear_text = "" if self.icons.get('clear') else "🧹 " + self.languages[self.language]['buttons']['clear_history']
        tk.Button(history_frame, text=clear_text,
                 command=self.clear_history, relief=tk.FLAT, padx=15, pady=5,
                 image=self.icons.get('clear'), compound=tk.LEFT).pack(pady=(10, 0))

        self.update_alarms_list()
        self.update_history_list()

    def create_stopwatch_tab(self, parent):
        stopwatch_frame = tk.Frame(parent)
        stopwatch_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Display
        self.stopwatch_display = tk.Label(stopwatch_frame, text="00:00:00.000",
                                        font=("Segoe UI", 48, "bold"),
                                        bg=self.themes[self.theme_var.get()]["card_bg"])
        self.stopwatch_display.pack(pady=50)

        # Controls
        controls_frame = tk.Frame(stopwatch_frame)
        controls_frame.pack()

        self.stopwatch_start_btn = tk.Button(controls_frame, text="Iniciar",
                                           command=self.toggle_stopwatch,
                                           relief=tk.FLAT, padx=20, pady=10)
        self.stopwatch_start_btn.pack(side=tk.LEFT, padx=10)

        tk.Button(controls_frame, text="Reiniciar", command=self.reset_stopwatch,
                 relief=tk.FLAT, padx=20, pady=10).pack(side=tk.LEFT, padx=10)

        # Lap times
        lap_frame = tk.Frame(stopwatch_frame)
        lap_frame.pack(fill=tk.BOTH, expand=True, pady=(20, 0))

        tk.Label(lap_frame, text="Vueltas:", font=("Segoe UI", 14, "bold")).pack(anchor=tk.W)

        scrollbar = tk.Scrollbar(lap_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.laps_listbox = tk.Listbox(lap_frame, yscrollcommand=scrollbar.set,
                                      font=("Segoe UI", 10), height=10)
        self.laps_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.laps_listbox.yview)

        tk.Button(lap_frame, text="Registrar Vuelta", command=self.record_lap,
                 relief=tk.FLAT, padx=15, pady=5).pack(pady=(10, 0))

    def create_timer_tab(self, parent):
        timer_frame = tk.Frame(parent)
        timer_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Time input
        input_frame = tk.Frame(timer_frame)
        input_frame.pack(pady=20)

        tk.Label(input_frame, text="Horas:").grid(row=0, column=0, padx=5)
        self.timer_hours = tk.Spinbox(input_frame, from_=0, to=23, width=5)
        self.timer_hours.grid(row=0, column=1, padx=5)

        tk.Label(input_frame, text="Minutos:").grid(row=0, column=2, padx=5)
        self.timer_minutes = tk.Spinbox(input_frame, from_=0, to=59, width=5)
        self.timer_minutes.grid(row=0, column=3, padx=5)

        tk.Label(input_frame, text="Segundos:").grid(row=0, column=4, padx=5)
        self.timer_seconds = tk.Spinbox(input_frame, from_=0, to=59, width=5)
        self.timer_seconds.grid(row=0, column=5, padx=5)

        # Display
        self.timer_display = tk.Label(timer_frame, text="00:00:00",
                                    font=("Segoe UI", 48, "bold"),
                                    bg=self.themes[self.theme_var.get()]["card_bg"])
        self.timer_display.pack(pady=30)

        # Controls
        controls_frame = tk.Frame(timer_frame)
        controls_frame.pack()

        self.timer_start_btn = tk.Button(controls_frame, text="Iniciar",
                                       command=self.start_timer,
                                       relief=tk.FLAT, padx=20, pady=10)
        self.timer_start_btn.pack(side=tk.LEFT, padx=10)

        tk.Button(controls_frame, text="Detener", command=self.stop_timer,
                 relief=tk.FLAT, padx=20, pady=10).pack(side=tk.LEFT, padx=10)

        tk.Button(controls_frame, text="Reiniciar", command=self.reset_timer,
                 relief=tk.FLAT, padx=20, pady=10).pack(side=tk.LEFT, padx=10)

    def create_status_bar(self, parent):
        self.status_bar = tk.Label(parent, text="Listo", bd=1, relief=tk.SUNKEN, anchor=tk.W,
                                 font=("Segoe UI", 9))
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    def apply_theme(self):
        theme = self.themes[self.theme_var.get()]
        self.root.configure(bg=theme["bg"])

        # Update all widgets with new theme
        self._update_widget_colors(self.root, theme)

        # Update canvas background
        if hasattr(self, 'canvas'):
            self.canvas.configure(bg=theme["canvas_bg"])

    def _update_widget_colors(self, widget, theme):
        try:
            if isinstance(widget, tk.Frame):
                widget.configure(bg=theme["bg"])
            elif isinstance(widget, tk.Label):
                widget.configure(bg=theme["bg"], fg=theme["fg"])
            elif isinstance(widget, tk.Button):
                widget.configure(bg=theme["accent"], fg="white")
            elif isinstance(widget, tk.Listbox):
                widget.configure(bg=theme["card_bg"], fg=theme["fg"])
        except:
            pass

        for child in widget.winfo_children():
            self._update_widget_colors(child, theme)

    def change_theme(self, event=None):
        self.config.set('theme', self.theme_var.get())
        self.apply_theme()

    def change_language(self, event=None):
        self.language = self.lang_var.get()
        self.config.set('language', self.language)
        # Rebuild UI with new language
        self.rebuild_ui()

    def rebuild_ui(self):
        # This is a simple way; in a real app, you'd update all labels
        # For now, just update the date format
        pass

    def toggle_mode(self):
        self.mode = self.mode_var.get()
        if self.mode == "analog":
            # Mostrar SOLO el reloj analógico
            self.canvas.pack(pady=10)
            self.digital_label.pack_forget()
            self.analog_btn.pack_forget()
            self.date_label.pack()
        else:
            # Mostrar SOLO el reloj digital
            self.canvas.pack_forget()
            self.digital_label.pack(pady=50)
            self.analog_btn.pack(pady=5)
            self.date_label.pack()

    def toggle_to_analog(self):
        self.mode_var.set("analog")
        self.toggle_mode()

    def toggle_sound(self):
        self.config.set('sound_enabled', self.sound_var.get())

    def toggle_fullscreen(self):
        self.config.set('fullscreen', not self.config.get('fullscreen', False))
        self.root.attributes('-fullscreen', self.config.get('fullscreen', False))

    def toggle_animations(self):
        self.config.set('animations', self.animations_var.get())

    def update_offset(self, value):
        pass  

    def update_clock(self):
        offset = self.offset_var.get()
        now = datetime.now() + timedelta(hours=offset)

        if self.mode == "analog":
            self.draw_analog_clock(now)

        self.digital_label.configure(text=now.strftime('%H:%M:%S'))
        date_format = self.languages[self.language]['date_format']
        self.date_label.configure(text=now.strftime(date_format))

        # Update world clocks
        self.update_world_clock_time()

        # Update stopwatch if running
        if self.stopwatch_running:
            self.update_stopwatch()

        # Update timer if running
        if self.timer_running:
            self.update_timer()

        # Update status bar with current time
        self.status_bar.configure(text=f"Hora actual: {now.strftime('%H:%M:%S')} | Tema: {self.theme_var.get()}")

        self.root.after(100, self.update_clock)

    def draw_analog_clock(self, now):
        self.canvas.delete("all")
        theme = self.themes[self.theme_var.get()]

        center_x, center_y = 200, 200
        radius = 180

        # Draw clock face
        self.canvas.create_oval(center_x - radius, center_y - radius,
                              center_x + radius, center_y + radius,
                              fill=theme["canvas_bg"], outline=theme["fg"], width=3)

        # Draw hour markers and numbers
        for hour in range(12):
            angle = math.radians(hour * 30 - 90)
            x1 = center_x + math.cos(angle) * (radius - 20)
            y1 = center_y + math.sin(angle) * (radius - 20)
            x2 = center_x + math.cos(angle) * (radius - 40)
            y2 = center_y + math.sin(angle) * (radius - 40)

            self.canvas.create_line(x1, y1, x2, y2, fill=theme["fg"], width=3)

            # Hour numbers
            num_x = center_x + math.cos(angle) * (radius - 60)
            num_y = center_y + math.sin(angle) * (radius - 60)
            self.canvas.create_text(num_x, num_y, text=str(hour if hour != 0 else 12),
                                  fill=theme["fg"], font=("Segoe UI", 16, "bold"))

        # Draw minute markers
        for minute in range(60):
            if minute % 5 != 0:
                angle = math.radians(minute * 6 - 90)
                x1 = center_x + math.cos(angle) * (radius - 10)
                y1 = center_y + math.sin(angle) * (radius - 10)
                x2 = center_x + math.cos(angle) * (radius - 15)
                y2 = center_y + math.sin(angle) * (radius - 15)
                self.canvas.create_line(x1, y1, x2, y2, fill=theme["secondary"], width=1)

        # Calculate hand angles
        seconds = now.second + now.microsecond / 1_000_000
        minutes = now.minute + seconds / 60
        hours = (now.hour % 12) + minutes / 60

        # Draw hands with animation
        if self.animations_var.get():
            self.animation_angle += 0.01
            self.pendulum_angle = 10 * math.sin(self.animation_angle)

        # Hour hand
        hour_angle = math.radians(hours * 30 - 90)
        self.canvas.create_line(center_x, center_y,
                              center_x + math.cos(hour_angle) * radius * 0.5,
                              center_y + math.sin(hour_angle) * radius * 0.5,
                              fill=theme["fg"], width=8, capstyle=tk.ROUND)

        # Minute hand
        minute_angle = math.radians(minutes * 6 - 90)
        self.canvas.create_line(center_x, center_y,
                              center_x + math.cos(minute_angle) * radius * 0.7,
                              center_y + math.sin(minute_angle) * radius * 0.7,
                              fill=theme["accent"], width=6, capstyle=tk.ROUND)

        # Second hand
        second_angle = math.radians(seconds * 6 - 90)
        self.canvas.create_line(center_x, center_y,
                              center_x + math.cos(second_angle) * radius * 0.9,
                              center_y + math.sin(second_angle) * radius * 0.9,
                              fill=theme["danger"], width=2, capstyle=tk.ROUND)

        # Center dot
        self.canvas.create_oval(center_x - 10, center_y - 10, center_x + 10, center_y + 10,
                              fill=theme["accent"], outline=theme["fg"], width=2)

        # Pendulum (decorative)
        if self.animations_var.get():
            pendulum_x = center_x
            pendulum_y = center_y + radius + 20
            pendulum_end_x = pendulum_x + 60 * math.sin(math.radians(self.pendulum_angle))
            pendulum_end_y = pendulum_y + 60

            self.canvas.create_line(pendulum_x, pendulum_y, pendulum_end_x, pendulum_end_y,
                                  fill=theme["secondary"], width=3)
            self.canvas.create_oval(pendulum_end_x - 8, pendulum_end_y - 8,
                                  pendulum_end_x + 8, pendulum_end_y + 8,
                                  fill=theme["accent"])

    def add_world_clock_from_combo(self):
        """Agregar reloj mundial desde el combobox."""
        display_name = self.timezone_var.get()
        if not display_name:
            return
        
        # Encontrar la zona horaria correspondiente
        for tz in self.world_clock_manager.TIMEZONES.keys():
            if self.world_clock_manager.get_display_name(tz) == display_name:
                if self.world_clock_manager.add_clock(tz):
                    self.update_world_clocks()
                    self.timezone_var.set('')
                    messagebox.showinfo("Éxito", f"Zona horaria {display_name} agregada.")
                else:
                    messagebox.showwarning("Aviso", "Esta zona horaria ya existe.")
                return

    def add_world_clock(self, timezone):
        if self.world_clock_manager.add_clock(timezone):
            self.update_world_clocks()

    def update_world_clocks(self):
        """Actualiza los widgets de relojes mundiales."""
        for widget in self.world_clocks_container.winfo_children():
            widget.destroy()

        self.world_clock_labels = {}
        
        # Agregar un reloj para cada zona horaria
        for timezone in self.world_clock_manager.clocks:
            clock_frame = tk.Frame(self.world_clocks_container,
                                 bg=self.themes[self.theme_var.get()]["card_bg"],
                                 relief=tk.RAISED, bd=2)
            clock_frame.pack(fill=tk.X, pady=8, padx=10)

            # Nombre de la zona
            display_name = self.world_clock_manager.get_display_name(timezone)
            tk.Label(clock_frame, text=display_name, font=("Segoe UI", 12, "bold"),
                    bg=self.themes[self.theme_var.get()]["card_bg"],
                    fg=self.themes[self.theme_var.get()]["fg"]).pack(anchor=tk.W, padx=10, pady=(5, 2))

            # Display de hora
            time_label = tk.Label(clock_frame, text="00:00:00", font=("Segoe UI", 24, "bold"),
                                bg=self.themes[self.theme_var.get()]["card_bg"],
                                fg=self.themes[self.theme_var.get()]["accent"])
            time_label.pack(anchor=tk.W, padx=10, pady=(2, 8))

            # Botón eliminar 
            if len(self.world_clock_manager.clocks) > 1:
                btn_frame = tk.Frame(clock_frame, bg=self.themes[self.theme_var.get()]["card_bg"])
                btn_frame.pack(anchor=tk.E, padx=10, pady=5)
                tk.Button(btn_frame, text="Eliminar", command=lambda tz=timezone: self.remove_world_clock(tz),
                         relief=tk.FLAT, padx=10, pady=4, bg=self.themes[self.theme_var.get()]["danger"],
                         fg="white", font=("Segoe UI", 9)).pack()

            # Guardar referencia
            self.world_clock_labels[timezone] = time_label

        # Actualizar región de scroll
        if hasattr(self, 'world_canvas'):
            self.world_clocks_container.update_idletasks()
            self.world_canvas.configure(scrollregion=self.world_canvas.bbox("all"))

    def remove_world_clock(self, timezone):
        if self.world_clock_manager.remove_clock(timezone):
            self.update_world_clocks()

    def update_world_clock_time(self):
        """Actualiza las horas de los relojes mundiales."""
        for timezone, label in self.world_clock_labels.items():
            time_obj = self.world_clock_manager.get_time(timezone)
            label.configure(text=time_obj.strftime('%H:%M:%S'))

    def add_alarm(self):
        time_str = simpledialog.askstring("Nueva Alarma", "Ingresa la hora (HH:MM):")
        if not time_str:
            return

        try:
            # Validate time format
            datetime.strptime(time_str, '%H:%M')
            label = simpledialog.askstring("Etiqueta", "Nombre de la alarma:", initialvalue="Alarma")
            if label:
                self.alarm_manager.add_alarm(time_str, label)
                self.update_alarms_list()
        except ValueError:
            messagebox.showerror("Error", "Formato de hora inválido. Usa HH:MM")

    def delete_alarm(self):
        selection = self.alarms_listbox.curselection()
        if selection:
            index = selection[0]
            self.alarm_manager.delete_alarm(index)
            self.update_alarms_list()

    def update_alarms_list(self):
        self.alarms_listbox.delete(0, tk.END)
        for alarm in self.alarm_manager.alarms:
            status = "✓" if alarm['enabled'] else "✗"
            self.alarms_listbox.insert(tk.END, f"{status} {alarm['time']} - {alarm['label']}")

    def on_alarm_trigger(self, alarm):
        # Play sound
        sound_enabled = self.config.get('sound_enabled', True)
        self.audio_manager.play_sound(alarm.get('sound', 'default'), sound_enabled)

        # Show notification
        messagebox.showinfo("¡Alarma!", f"{alarm['label']}\nHora: {alarm['time']}")

        # Update history
        self.update_history_list()

    def toggle_stopwatch(self):
        if self.stopwatch_running:
            self.stopwatch_running = False
            self.stopwatch_start_btn.configure(text=self.languages[self.language]['buttons']['start'])
        else:
            if self.stopwatch_start is None:
                self.stopwatch_start = datetime.now()
            else:
                self.stopwatch_elapsed += datetime.now() - self.stopwatch_start
                self.stopwatch_start = datetime.now()
            self.stopwatch_running = True
            self.stopwatch_start_btn.configure(text=self.languages[self.language]['buttons']['pause'])

    def update_stopwatch(self):
        """Actualiza la display del cronómetro."""
        if self.stopwatch_running:
            current_elapsed = self.stopwatch_elapsed + (datetime.now() - self.stopwatch_start)
            self.stopwatch_display.configure(text=self.format_timedelta(current_elapsed, True))

    def reset_stopwatch(self):
        self.stopwatch_running = False
        self.stopwatch_start = None
        self.stopwatch_elapsed = timedelta()
        self.stopwatch_display.configure(text="00:00:00.000")
        self.stopwatch_start_btn.configure(text="Iniciar")
        self.laps_listbox.delete(0, tk.END)

    def record_lap(self):
        if self.stopwatch_running or self.stopwatch_elapsed.total_seconds() > 0:
            current_time = self.stopwatch_elapsed
            if self.stopwatch_running:
                current_time += datetime.now() - self.stopwatch_start

            lap_time = f"{len(self.laps_listbox.get(0, tk.END)) + 1:2d}: {self.format_timedelta(current_time, True)}"
            self.laps_listbox.insert(tk.END, lap_time)

    def start_timer(self):
        try:
            hours = int(self.timer_hours.get())
            minutes = int(self.timer_minutes.get())
            seconds = int(self.timer_seconds.get())

            total_seconds = hours * 3600 + minutes * 60 + seconds
            if total_seconds > 0:
                self.timer_duration = timedelta(seconds=total_seconds)
                self.timer_end = datetime.now() + self.timer_duration
                self.timer_running = True
                self.timer_start_btn.configure(text=self.languages[self.language]['buttons']['pause'])
        except ValueError:
            messagebox.showerror("Error", "Ingresa valores numéricos válidos")

    def update_timer(self):
        """Actualiza la display del temporizador."""
        if self.timer_running and self.timer_end:
            remaining = self.timer_end - datetime.now()
            if remaining.total_seconds() <= 0:
                self.on_timer_end()
            else:
                self.timer_display.configure(text=self.format_timedelta(remaining))

    def stop_timer(self):
        self.timer_running = False
        self.timer_start_btn.configure(text="Iniciar")

    def reset_timer(self):
        self.timer_running = False
        self.timer_duration = None
        self.timer_end = None
        self.timer_display.configure(text="00:00:00")
        self.timer_start_btn.configure(text="Iniciar")

    def on_timer_end(self):
        """Se ejecuta cuando el temporizador llega a cero."""
        self.timer_running = False
        self.timer_duration = None
        self.timer_end = None
        self.timer_display.configure(text="¡Tiempo terminado!")
        self.timer_start_btn.configure(text="Iniciar")

        # Reproducir sonido
        sound_enabled = self.config.get('sound_enabled', True)
        self.audio_manager.play_sound('urgent', sound_enabled)

        # Mostrar notificación
        messagebox.showinfo("¡Temporizador!", "El tiempo ha terminado")

    def update_history_list(self):
        self.history_listbox.delete(0, tk.END)
        for entry in self.alarm_manager.history[-20:]:  # Show last 20 entries
            alarm = entry['alarm']
            triggered = datetime.fromisoformat(entry['triggered'])
            self.history_listbox.insert(0, f"{triggered.strftime('%d/%m %H:%M')} - {alarm['label']}")

    def clear_history(self):
        self.alarm_manager.history.clear()
        self.update_history_list()

    @staticmethod
    def format_timedelta(td, include_ms=False):
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        milliseconds = int((td.total_seconds() - total_seconds) * 1000)

        if include_ms:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
        else:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def __del__(self):
        self.alarm_manager.stop_monitoring()


if __name__ == "__main__":
    ClockApp()
