import random

class Environment:
    def __init__(self, n=2):
        """Inizializza l'ambiente con N stanze. Posizione dell'agente e stato dello sporco randomici."""
        self.n = n
        self.rooms = ["SPORCO" if random.random() < 0.5 else "PULITO" for _ in range(self.n)]
        self.agent_position = random.randint(0, self.n - 1)

    def get_percept(self):
        """Restituisce la percezione locale: (posizione, stato_della_stanza)"""
        return (self.agent_position, self.rooms[self.agent_position])

    def execute_action(self, action):
        """Aggiorna lo stato dell'ambiente in base all'azione dell'agente."""
        if action == "ASPIRA":
            self.rooms[self.agent_position] = "PULITO"
        elif action == "DESTRA":
            if self.agent_position < self.n - 1:
                self.agent_position += 1
        elif action == "SINISTRA":
            if self.agent_position > 0:
                self.agent_position -= 1
        # Se NOOP (Nessuna operazione), non fa nulla

    def is_clean(self):
        """Verifica se tutte le stanze sono state pulite."""
        return all(room == "PULITO" for room in self.rooms)
