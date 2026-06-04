import networkx as nx

graph = nx.Graph()

graph.add_edge(
    "RACK-A-01",
    "RACK-A-02",
    weight=5
)

graph.add_edge(
    "RACK-A-02",
    "RACK-B-01",
    weight=10
)

path = nx.shortest_path(
    graph,
    source="RACK-A-01",
    target="RACK-B-01",
    weight="weight"
)
