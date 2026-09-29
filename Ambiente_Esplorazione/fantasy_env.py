import matplotlib.pyplot as plt
from matplotlib.widgets import Button, RadioButtons, Slider
import networkx as nx
import math
import random
import textwrap
from search_agents_empty import breadth_first_search, uniform_cost_search, a_star_search, ida_star_search, rbfs_search

# Vocabolario per la generazione procedurale di stringhe fantasy
PREFIXES = ["Aethel", "Bal", "Cor", "Dorn", "El", "Fael", "Gor", "Hal", "Ili", "Jor", "Kael", "Lor", "Mor", "Nor", "Olo", "Pel", "Quin", "Riv", "Sil", "Tor", "Ul", "Val", "Win", "Xyl", "Yar", "Zan"]
SUFFIXES = ["dor", "rond", "th", "wyn", "ia", "gard", "heim", "wood", "fell", "mont", "vale", "keep", "hold", "grad", "polis", "stead", "ton", "burg"]

def generate_fantasy_name():
    """Genera casualmente un prefisso e un suffisso assemblando un nome fantasy inventato."""
    return random.choice(PREFIXES) + random.choice(SUFFIXES)


def generate_map(n_cities):
    """
    Funzione core per la generazione procedurale del grafo (Mappa).
    Prende in input il numero desiderato di città e restituisce le coordinate, il grafo NetworkX e i dizionari necessari.
    """
    cities = []
    names = set() # Set per garantire unicità dei nomi generati
    
    # 1. GENERAZIONE NOMI
    while len(names) < n_cities:
        name = generate_fantasy_name()
        if name not in names:
            names.add(name)
            cities.append(name)
            
    width, height = 1000, 1000
    
    # 2. CALCOLO DISTANZA MINIMA (Dart Throwing / Spaziatura intelligente)
    # Imposta un raggio "di sicurezza" per evitare che due città vengano generate appiccicate o sovrapposte.
    min_dist = math.sqrt((width * height) / n_cities) * 0.7 
    
    pos_list = []
    # 3. SPARPAGLIAMENTO COORDINATE 
    # Lancia punti casuali (freccette) sul piano
    for _ in range(n_cities * 150): 
        if len(pos_list) == n_cities:
            break # Abbiamo piazzato tutte le città!
            
        x = random.uniform(50, width - 50)
        y = random.uniform(50, height - 50)
        
        # Se questo nuovo punto (x,y) dista più di min_dist da TUTTI i punti posizionati in precedenza, è valido!
        if all(math.dist((x, y), (px, py)) >= min_dist for px, py in pos_list):
            pos_list.append((x, y))
            
    # Se il limite rigido di tentativi è fallito, le ultime città le piazziamo forzatamente ignorando la distanza di sicurezza
    while len(pos_list) < n_cities:
        pos_list.append((random.uniform(50, width-50), random.uniform(50, height-50)))
        
    # Unisce i nomi alle coordinate appena calcolate in un dizionario
    positions = {cities[i]: pos_list[i] for i in range(n_cities)}
    
    # 4. CREAZIONE STRADE TRAMITE MST (Minimum Spanning Tree)
    # Crea un grafo temporaneo con TUTTI i possibili collegamenti diretti valutandone il peso (Distanza 2D in linea d'aria)
    temp_G = nx.Graph()
    for i, city1 in enumerate(cities):
        for j, city2 in enumerate(cities):
            if i < j:
                p1, p2 = positions[city1], positions[city2]
                dist = math.dist(p1, p2) # Il peso stradale è l'effettiva Geometria Spaziale Euclidea
                temp_G.add_edge(city1, city2, weight=dist)
                
    # Applica l'algoritmo di copertura minima (MST). 
    # Questo restringe le strade a formare uno schema ad albero che tocca tutte le città garantendo 100% Connettività senza cicli
    mst = nx.minimum_spanning_tree(temp_G)
    G = mst.copy()
    
    # 5. AGGIUNTA RAMI EXTRA (CICLI)
    # Senza archi extra, esisterebbe 1 e un solo percorso possibile. Lo rendiamo un labirinto realistico aggiungendo strade.
    if temp_G.number_of_edges() > 0:
        avg_dist = sum(data['weight'] for _, _, data in temp_G.edges(data=True)) / temp_G.number_of_edges()
    else:
        avg_dist = 0
    threshold = avg_dist * 0.8 # Prende solo le strade mediamente brevi, non colleghiamo città da un capo all'altro
    
    for u, v, d in temp_G.edges(data=True):
        if not G.has_edge(u, v) and d['weight'] < threshold:
            if random.random() < 0.2: # Probabilità del 20% di piazzare una strada
                G.add_edge(u, v, weight=d['weight'] + random.uniform(0, 15)) # Aggiungiamo rumore al peso base
                
    # 6. SELEZIONE DEGLI ESTREMI DEL VIAGGIO (Partenza / Obiettivo)
    max_dist = -1
    start_city = cities[0]
    goal_city = cities[1] if len(cities) > 1 else cities[0]
    
    # Trova le 2 posizioni spazialmente e oggettivamente più distanti del grafo su cui lanciare le simulazioni
    for i, c1 in enumerate(cities):
        for j, c2 in enumerate(cities):
            if i < j:
                dist = math.dist(positions[c1], positions[c2])
                if dist > max_dist:
                    max_dist = dist
                    start_city = c1
                    goal_city = c2
                    
    # 7. CALCOLO DELL'EURISTICA AMMISSIBILE
    heuristics = {}
    for city in cities:
        # L'A* e varianti hanno bisogno di un navigatore (h(n)). Gli diamo l'esatta distanza geometrica in linea d'aria all'obiettivo.
        # È 100% Ammissibile matematicamente.
        heuristics[city] = math.dist(positions[city], positions[goal_city])
        
    # Costruiamo il dizionario annidato compatibile nativamente per search_agents.py
    problem_graph = {}
    for node in G.nodes():
        problem_graph[node] = {}
        for neighbor in G.neighbors(node):
            problem_graph[node][neighbor] = G[node][neighbor]['weight']
            
    return G, positions, problem_graph, heuristics, start_city, goal_city

# -- VARIABILI GLOBALI DI STATO --
# Mantengono traccia permanente dell'ambiente caricato tra una chiamata e l'altra della UI
current_algo = 'BFS'
G = None
positions = {}
problem_graph = {}
heuristics = {}
start_city = None
goal_city = None

# Variabili per gestire l'iterazione logico/visuale "Frame by Frame" del simulatore
is_running = False         # Toggle Play/Pause automatico
search_generator = None    # Istanza del thread dell'agente che fornisce i dati ad ogni yield
current_path = None        # Popolato con il tracking all'indietro se abbiamo finito il labirinto
current_node_state = None  # Città processata al momento (Rosso)
frontier_state = []        # Città papabili (Arancione)
explored_state = set()     # Città ispezionate per intero (Verde)
current_info = {}          # Dizionario delle metriche (profondità, costi, f_lim, f_n)
max_depth = 0              # Tracker del fondo pozzo raggiunto dalla discesa

def draw_graph(current_node=None, frontier_states=[], explored_set=set(), ax_graph=None, final_path=None):
    """
    Motore di Rendering per Matplotlib: disegna la rete geografica
    colorandola istante per istante in base allo stato iniettato.
    """
    if ax_graph is None:
        ax_graph = plt.gca()
    ax_graph.clear() # Cancella il vecchio frame dal buffer prima di sovrascrivere
    
    if not G: return
        
    # CALCOLO CROMATICO NODI
    node_colors = []
    for node in G.nodes():
        if final_path and node in final_path:
            node_colors.append('#ffd700') # Oro lucido per la strada finale vincente
        elif current_node and node == current_node.state:
            node_colors.append('#ff4d4d') # Rosso per lo slot del processore attualmente in elaborazione
        elif node in explored_set:
            node_colors.append('#79ff4d') # Verde chiaro per i nodi dismessi (Closed List)
        elif node in frontier_states:
            node_colors.append('#ffb84d') # Arancione pallido per l'orizzonte eventi (Fringe)
        else:
            if node == start_city: node_colors.append('#b3ccff')  # Azzurro di partenza
            elif node == goal_city: node_colors.append('#ffb3ff') # Fucsia dell'arrivo
            else: node_colors.append('#e6e6e6') # Grigio nebbia di guerra

    # TRACCIAMENTO EDGES (STRADE)
    path_edges = set()
    if final_path:
        for i in range(len(final_path)-1):
            path_edges.add((final_path[i], final_path[i+1]))
            path_edges.add((final_path[i+1], final_path[i]))
            
    edge_colors = []
    edge_widths = []
    for u, v in G.edges():
        if (u, v) in path_edges or (v, u) in path_edges:
            edge_colors.append('#ff0000') # Le strade vincenti diventano rosso sangue per risaltare
            edge_widths.append(4.0)       # e spesse 4 px
        else:
            edge_colors.append('gray')    # Strade standard
            edge_widths.append(1.0)

    # SCALATURA AUTOMATICA RESPONSIVE
    # Contrae font e cerchi se i nodi generati aumentano a dismisura (previene che le icone si mangino a vicenda)
    n_nodes = len(G.nodes())
    node_size = 1200 if n_nodes <= 20 else max(200, 1200 - (n_nodes * 10))
    font_size = 9 if n_nodes <= 20 else max(5, 9 - int(n_nodes / 15))

    # PITTURA NETWORKX VERA E PROPRIA
    nx.draw(G, pos=positions, with_labels=True, 
            node_color=node_colors, node_size=node_size, 
            font_size=font_size, font_weight='bold', 
            edge_color=edge_colors, width=edge_widths, ax=ax_graph)
    
    # ETICHETTE PESO (Costi): Evitiamo la scrittura se le strade sono un'inondazione illeggibile (>50)
    if n_nodes <= 50:
        edge_labels = { (u, v): f"{d['weight']:.0f}" for u, v, d in G.edges(data=True) }
        nx.draw_networkx_edge_labels(
            G, pos=positions, edge_labels=edge_labels, 
            font_size=7, 
            bbox=dict(facecolor='white', edgecolor='none', alpha=0.8, pad=0.3), # Un backbox opaco per contrastare il tratto della linea
            ax=ax_graph
        )
    
    # TITOLO FINESTRA
    curr_state = current_node.state if current_node else 'N/A'
    status_text = "Percorso Trovato!" if final_path else f"Nodo Corrente: {curr_state}"
    ax_graph.set_title(f"Mappa Fantasy | Partenza: {start_city} | Destinazione: {goal_city}\n{status_text}")


def main():
    # Richiami globali in modo che gli Event Handlers mutino l'unico stato in esecuzione
    global current_algo, is_running, max_depth
    global G, positions, problem_graph, heuristics, start_city, goal_city
    global search_generator, current_path, current_node_state, frontier_state, explored_state, current_info
    
    fig, ax_graph = plt.subplots(figsize=(15, 8))
    plt.subplots_adjust(left=0.25, bottom=0.05, top=0.95) # Apre un vasto margine a sinistra per alloggiare la barra strumenti
    
    # DEFINIZIONE AREE GEOMETRICHE (Axes) [X, Y, Larghezza, Altezza] per il Pannello Strumenti di Matplotlib
    ax_slider_n = plt.axes([0.02, 0.90, 0.18, 0.05])
    ax_btn_gen = plt.axes([0.02, 0.83, 0.18, 0.05])
    ax_radio = plt.axes([0.02, 0.58, 0.18, 0.22], facecolor='lightgray')
    ax_btn_play = plt.axes([0.02, 0.51, 0.08, 0.05])
    ax_btn_step = plt.axes([0.12, 0.51, 0.08, 0.05])
    ax_info = plt.axes([0.02, 0.35, 0.18, 0.14])
    ax_frontier = plt.axes([0.02, 0.02, 0.18, 0.31]) 
    
    # Pulisce assi di default dai contenitori di puro testo
    ax_info.axis('off')
    ax_frontier.axis('off')
    
    # POPOLAMENTO WIDGETS
    slider_n = Slider(ax_slider_n, 'Città', 5, 100, valinit=20, valstep=1)
    btn_gen = Button(ax_btn_gen, 'Nuova Mappa')
    radio = RadioButtons(ax_radio, ('BFS', 'UCS (Dijkstra)', 'A*', 'IDA*', 'RBFS'))
    btn_play = Button(ax_btn_play, 'Play', color='lightgreen', hovercolor='palegreen')
    btn_step = Button(ax_btn_step, 'Step', color='lightblue', hovercolor='skyblue')
    
    # LABEL TESTUALI DINAMICHE
    info_text = ax_info.text(0.0, 1.0, "Nodi Esplorati: 0", ha='left', va='top', 
                             fontsize=10, 
                             bbox=dict(facecolor='white', alpha=0.9, edgecolor='black', boxstyle='round,pad=0.5'))

    frontier_text = ax_frontier.text(0.0, 1.0, "Frontiera:\nNessuna", ha='left', va='top', 
                                     fontsize=9, 
                                     bbox=dict(facecolor='lightyellow', alpha=0.8, edgecolor='orange', boxstyle='round,pad=0.5'))

    def reset_simulation():
        """Resetta del tutto le cache di progresso (da chiamare ad esempio premendo Nuova Mappa)."""
        global search_generator, current_path, current_node_state, frontier_state, explored_state, current_info, is_running, max_depth
        is_running = False
        max_depth = 0
        btn_play.label.set_text('Play')
        search_generator = None
        current_path = None
        current_node_state = None
        frontier_state = []
        explored_state = set()
        current_info = {}
        info_text.set_text("Nodi Esplorati: 0\nProfondità Max: 0\nCosto: 0")
        frontier_text.set_text("Frontiera:\nNessuna")

    def algo_changed(label):
        """Callback: eseguita istantaneamente cliccando un diverso Radio Button dell'algoritmo."""
        global current_algo
        current_algo = label
        reset_simulation()
        draw_graph(ax_graph=ax_graph)
        fig.canvas.draw_idle()
        
    radio.on_clicked(algo_changed)
    
    def gen_map(event):
        """Callback: invia le istruzioni al motore procedurale estraendo N dallo Slider e resettando."""
        global G, positions, problem_graph, heuristics, start_city, goal_city
        n_cities = int(slider_n.val)
        G, positions, problem_graph, heuristics, start_city, goal_city = generate_map(n_cities)
        reset_simulation()
        draw_graph(ax_graph=ax_graph)
        fig.canvas.draw_idle()
        
    btn_gen.on_clicked(gen_map)
    
    def init_generator():
        """Inietta lo switch-case per abbinare al generatore la firma corretta dell'algoritmo dal backend Python."""
        global search_generator
        if current_algo == 'BFS':
            search_generator = breadth_first_search(start_city, goal_city, problem_graph)
        elif current_algo == 'UCS (Dijkstra)':
            search_generator = uniform_cost_search(start_city, goal_city, problem_graph)
        elif current_algo == 'A*':
            search_generator = a_star_search(start_city, goal_city, problem_graph, heuristics)
        elif current_algo == 'IDA*':
            search_generator = ida_star_search(start_city, goal_city, problem_graph, heuristics)
        elif current_algo == 'RBFS':
            search_generator = rbfs_search(start_city, goal_city, problem_graph, heuristics)

    def execute_single_step():
        """
        Motore Logico Frame. Fa avanzare di 1 passo il generatore (next).
        Se il thread di ricerca conclude lo yield, calcola le distanze di backtracking.
        """
        global current_path, current_node_state, frontier_state, explored_state, current_info
        try:
            current_node_state, frontier_state, explored_state, current_info = next(search_generator)
            
            # Condizione Esclusiva: il generatore ha emesso un frame in cui afferma di aver trovato la destinazione
            if current_node_state.state == goal_city:
                # Ricostruzione del cammino tramite puntatori Parent Pointer incatenati (da Arrivo -> Inizio)
                path = []
                temp = current_node_state
                while temp:
                    path.append(temp.state)
                    temp = temp.parent
                path.reverse() # Riallinea in base: Inizio -> Arrivo
                current_path = path 
                return False # Ferma per sempre la simulazione logica (Goal raggiunto)
            
            return True # Possiamo continuare, non ci sono Stop o Goal
        except StopIteration:
            return False # Il generatore è imploso, il labirinto è insolubile (Grafo sconnesso non raggiunto)

    def update_ui():
        """Compila e inietta i testi estratti all'interno della Graphic User Interface di Matplotlib."""
        global max_depth
        draw_graph(current_node_state, frontier_state, explored_state, ax_graph=ax_graph, final_path=current_path)
        
        # Estrazione profonda
        depth = current_info.get('depth', 0)
        if depth > max_depth:
            max_depth = depth
            
        cost = current_info.get('cost', 0)
        f_val = current_info.get('f_val', None)
        f_limit = current_info.get('f_limit', None)
        
        text_lines = [
            f"Nodi Esplorati: {len(explored_state)}",
            f"Profondità Max: {max_depth}",
            f"Costo Attuale: {cost:.1f}"
        ]
        # Mostrati unicamente nei contesti dove hanno senso o esistono
        if f_val is not None:
            text_lines.append(f"Valore f(n): {f_val:.1f}")
        if f_limit is not None and f_limit != float('inf'):
            text_lines.append(f"Soglia (f-limit): {f_limit:.1f}")
            
        info_text.set_text("\n".join(text_lines))
        
        # Word Wrap Frontiera
        if frontier_state:
            # Sfrutta textwrap.wrap per spezzare l'output ogni 35 caratteri simulando un a-capo, 
            # garantendo che la lista città si affastelli verticalmente verso il basso senza sbavare nello schema grafico
            wrapped = "\n".join(textwrap.wrap(", ".join(frontier_state), width=35))
            frontier_text.set_text(f"Frontiera ({len(frontier_state)} nodi):\n{wrapped}")
        else:
            frontier_text.set_text("Frontiera:\nVuota")
            
        fig.canvas.draw_idle()

    def step_clicked(event):
        """Callback Pulsante STEP: Forza un singolo battito (frame). Mette in Pausa il loop temporale di Play se serve."""
        global search_generator, is_running
        
        if is_running:
            is_running = False
            btn_play.label.set_text('Play')
            
        if search_generator is None:
            init_generator()
            
        if current_path is None:
            execute_single_step()
            update_ui()

    btn_step.on_clicked(step_clicked)

    def play_clicked(event):
        """Callback Pulsante PLAY/PAUSE: Accende un Loop perpetuo che avanza automaticamente frame by frame."""
        global is_running, search_generator
        
        if is_running:
            is_running = False
            btn_play.label.set_text('Play')
            return
            
        is_running = True
        btn_play.label.set_text('Pause')
        
        if search_generator is None:
            init_generator()
            
        # Loop finchè non schiaccio Pause o risolvo la Mappa
        while is_running and current_path is None:
            keep_going = execute_single_step()
            update_ui()
            fig.canvas.flush_events() # Assolutamente vitale: previene il blocco finestra (Not Responding) lasciando il SO processare la grafica
            
            # Dinamica Intelligente: La UI accelera visivamente la simulazione all'aumentare dei nodi N, stringendo i millisecondi
            sleep_time = max(0.005, 0.5 - (len(G.nodes()) * 0.01))
            plt.pause(sleep_time) # Forza la UI di disegnare ora il set su schermo e aspetta la prossima azione
            
            if not keep_going:
                is_running = False
                
        btn_play.label.set_text('Play')

    btn_play.on_clicked(play_clicked)
    
    # Ancore vitali per Python GC (Garbage Collection). 
    # Manteniamo referenze ai bottoni nel root object "fig" o la UI si freezerebbe scartandoli come orfani dopo il boot
    fig._slider = slider_n
    fig._radio = radio
    fig._btn_gen = btn_gen
    fig._btn_play = btn_play
    fig._btn_step = btn_step
    
    fig.canvas.manager.set_window_title("Pathfinding Mappe Fantasy Procedurali")
    
    # Auto-avvio all'apertura del programma Python
    gen_map(None)
    plt.show()

if __name__ == "__main__":
    main()
