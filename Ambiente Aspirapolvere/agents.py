import random
import abc

class Agent(abc.ABC):
    """Classe base astratta per un Agente"""
    @abc.abstractmethod
    def act(self, percept):
        pass


class UserAgent(Agent):
    """Agente controllato dall'utente tramite tastiera."""
    def __init__(self):
        self.next_action = "ATTENDI"
        
    def act(self, percept):
        action = self.next_action
        self.next_action = "ATTENDI"
        return action
