class Node:

    def __init__(self, state, parent=None, action=None, path_cost=0, depth = 0):
        self.state = state
        self.parent = parent
        self.action = action
        self.path_cost = path_cost
        self.depth = depth

    def __lt__(self, other):
        return self.path_cost < other.path_cost

    def __eq__(self, other):
        return self.state == other.state

    def __hash__(self):
        return hash(self.state)


def expand(node, problem_graph):

    children = []

    for action, (child_state, cost) in problem_graph.get(node.state, {}).items():
        child_node = Node(
            child_state,
            parent=node,
            action=action,
            path_cost=node.path_cost + cost
        )
        children.append(child_node)

    return children


def breadth_first_search(initial_state, goal_state, problem_graph, heuristics=None):

    node = Node(initial_state)
    frontier = deque([node])
    explored = set()

    while frontier:
        node = frontier.popleft()

        if node.state == goal_state:
            return node

        explored.add(node.state)

        for child in expand(node, problem_graph):
            if child.state not in explored and child.state not in [n.state for n in frontier]:
                frontier.append(child)

    return None


def uniform_cost_search(initial_state, goal_state, problem_graph, heuristics=None):

    pass


def a_star_search(initial_state, goal_state, problem_graph, heuristics):

    pass


def ida_star_search(initial_state, goal_state, problem_graph, heuristics):

    pass


def rbfs_search(initial_state, goal_state, problem_graph, heuristics):

   pass
