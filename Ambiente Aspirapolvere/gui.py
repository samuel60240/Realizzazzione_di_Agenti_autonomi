import tkinter as tk
from tkinter import ttk
from environment import Environment
from agents import UserAgent

class VacuumGUI:
    def __init__(self, root, n_rooms=4):
        self.root = root
        self.root.title("Vacuum Cleaner World Simulation")
        self.n_rooms = n_rooms
        
        self.env = None
        self.agent = None
        self.is_running = False
        self.step_count = 0
        self.delay_ms = 500
        
        self.setup_ui()
        self.root.bind('<Key>', self.on_key_press)
        self.root.focus_set()
        
    def on_key_press(self, event):
        if not self.is_running or not isinstance(self.agent, UserAgent):
            return
            
        key = event.keysym
        if key == 'Left':
            self.agent.next_action = "SINISTRA"
        elif key == 'Right':
            self.agent.next_action = "DESTRA"
        elif key.lower() == 'a':
            self.agent.next_action = "ASPIRA"
    def setup_ui(self):
        # Controls Frame
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.pack(fill=tk.X)
        
        ttk.Label(control_frame, text="Numero stanze:").grid(row=0, column=0, padx=5)
        self.rooms_var = tk.IntVar(value=self.n_rooms)
        self.rooms_entry = ttk.Entry(control_frame, textvariable=self.rooms_var, width=5)
        self.rooms_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(control_frame, text="Agente:").grid(row=0, column=2, padx=5)
        self.agent_var = tk.StringVar(value="User Controlled")
        self.agent_combo = ttk.Combobox(control_frame, textvariable=self.agent_var, values=["User Controlled", "Simple Reflex", "Model Based"], state="readonly")
        self.agent_combo.grid(row=0, column=3, padx=5)
        
        self.start_btn = ttk.Button(control_frame, text="Inizia Simulazione", command=self.start_simulation)
        self.start_btn.grid(row=0, column=4, padx=5)
        
        self.stop_btn = ttk.Button(control_frame, text="Ferma", command=self.stop_simulation, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=5, padx=5)
        
        # Environment Frame (Visualization)
        self.env_frame = ttk.Frame(self.root, padding="20")
        self.env_frame.pack(fill=tk.BOTH, expand=True)
        self.room_labels = []
        
        # Log Frame
        log_frame = ttk.Frame(self.root, padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(log_frame, text="Log di esecuzione:").pack(anchor=tk.W)
        self.log_text = tk.Text(log_frame, height=15, width=70, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
    def log(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        
    def start_simulation(self):
        try:
            self.n_rooms = self.rooms_var.get()
        except ValueError:
            self.log("Errore: Numero stanze non valido.")
            return
            
        if self.n_rooms < 1:
            self.log("Errore: Numero stanze deve essere >= 1.")
            return

        self.env = Environment(self.n_rooms)
        
        agent_type = self.agent_var.get()
        if agent_type == "Simple Reflex":
            from agents import SimpleReflexAgent 
            self.agent = SimpleReflexAgent()
        elif agent_type == "Model Based":
            from agents import ModelBasedAgent
            self.agent = ModelBasedAgent(self.n_rooms)
        else:
            self.agent = UserAgent()
            self.root.focus_set()
            
        self.step_count = 0
        self.is_running = True
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        
        self.log(f"--- Inizio Simulazione: {agent_type} (N={self.n_rooms}) ---")
        
        self.start_btn.config(state=tk.DISABLED)
        self.rooms_entry.config(state=tk.DISABLED)
        self.agent_combo.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        self.init_env_grid()
        self.update_env_grid()
        self.root.after(self.delay_ms, self.run_step)
        
    def stop_simulation(self):
        self.is_running = False
        self.log("--- Simulazione interrotta dall'utente ---")
        self.reset_controls()
        
    def reset_controls(self):
        self.start_btn.config(state=tk.NORMAL)
        self.rooms_entry.config(state=tk.NORMAL)
        self.agent_combo.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        
    def init_env_grid(self):
        for widget in self.env_frame.winfo_children():
            widget.destroy()
            
        self.room_labels = []
        for i in range(self.n_rooms):
            frame = tk.Frame(self.env_frame, borderwidth=2, relief="groove", width=100, height=100)
            frame.grid_propagate(False)
            frame.grid(row=0, column=i, padx=5, pady=5)
            
            lbl = tk.Label(frame, text="", font=("Arial", 32))
            lbl.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
            self.room_labels.append(lbl)
            
    def update_env_grid(self):
        for i in range(self.n_rooms):
            status = "💩" if self.env.rooms[i] == "SPORCO" else "✨"
            agent = "🤖" if i == self.env.agent_position else ""
            
            display_text = f"{agent} {status}" if agent else status
            self.room_labels[i].config(text=display_text)
            
    def run_step(self):
        if not self.is_running:
            return
            
        if self.env.is_clean():
            self.log(f"🎉 Obiettivo raggiunto! Tutte le stanze pulite al passo {self.step_count}.")
            self.is_running = False
            self.reset_controls()
            return
            
        self.step_count += 1
        percept = self.env.get_percept()
        action = self.agent.act(percept)
        
        if action == "ATTENDI":
            self.step_count -= 1
            self.root.after(self.delay_ms, self.run_step)
            return
            
        if action == "FATTO":
            self.log(f"Passo {self.step_count}: L'agente ritiene di aver finito.")
            if self.env.is_clean():
                self.log("🎉 Obiettivo raggiunto in modo efficiente!")
            else:
                self.log("❌ L'agente si sbagliava. Ci sono ancora stanze sporche.")
            self.is_running = False
            self.reset_controls()
            return
            
        self.log(f"Passo {self.step_count}: Percezione {percept} -> Azione '{action}'")
        self.env.execute_action(action)
        self.update_env_grid()
        
        if self.step_count >= 50:
             self.log("⚠️ Limite massimo di step raggiunto (50). Simulazione interrotta.")
             self.is_running = False
             self.reset_controls()
             return
             
        self.root.after(self.delay_ms, self.run_step)
