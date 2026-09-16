import matplotlib.pyplot as plt
import networkx as nx


def generate_del_style_graph():
    G = nx.DiGraph()

    # Node Sesuai Formulasi Formal Del
    nodes = {
        "s0": "Status Awal (s0)\n([], Rp 500k)",
        "S1": "s1: [PAYDAY_20]\n(Rp 450k)",
        "S2": "s2: [MANTAP_30K]\n(Rp 470k)",
        "S3": "s3: [CASHBACK_10]\n(Rp 475k)",
        "S4": "s4: [ONGKIR_SUPER]\n(Rp 480k)",
        "S5": "s5: [PAYDAY_20, CASHBACK_10]\n(Rp 425k)",
        "Goal": "Solusi Optimal (Goal)\n[PAYDAY_20, CASHBACK_10, ONGKIR_SUPER]\n(Total Minimal: Rp 405k)",
    }

    for node, label in nodes.items():
        G.add_node(node, label=label)

    # Transisi Aksi
    edges = [
        ("s0", "S1", "Apply(PAYDAY_20)"),
        ("s0", "S2", "Apply(MANTAP_30K)"),
        ("s0", "S3", "Apply(CASHBACK_10)"),
        ("s0", "S4", "Apply(ONGKIR_SUPER)"),
        ("S1", "S5", "Apply(CASHBACK_10)"),
        ("S5", "Goal", "Apply(ONGKIR_SUPER)"),
    ]

    for u, v, label in edges:
        G.add_edge(u, v, label=label)

    # Posisi Layout Bertingkat Simetris
    pos = {
        "s0": (0, 3),
        "S1": (-2.4, 2),
        "S2": (-0.8, 2),
        "S3": (0.8, 2),
        "S4": (2.4, 2),
        "S5": (-2.4, 1),
        "Goal": (-2.4, 0),
    }

    fig, ax = plt.subplots(figsize=(12, 7.5), facecolor="white")
    ax.set_facecolor("white")

    # Gambar Garis Transisi (Edges)
    for u, v, d in G.edges(data=True):
        x1, y1 = pos[u]
        x2, y2 = pos[v]

        is_optimal = (u, v) in [("s0", "S1"), ("S1", "S5"), ("S5", "Goal")]
        edge_color = "#1b5e20" if is_optimal else "#78909c"
        edge_style = "solid" if is_optimal else "dashed"
        line_width = 2.5 if is_optimal else 1.2

        ax.annotate(
            "",
            xy=(x2, y2),
            xytext=(x1, y1),
            arrowprops=dict(
                arrowstyle="-|>",
                color=edge_color,
                lw=line_width,
                ls=edge_style,
                mutation_scale=15,
                shrinkA=30,
                shrinkB=30,
            ),
        )

        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        ax.text(
            mid_x + 0.05,
            mid_y,
            d["label"],
            fontsize=8,
            fontweight="bold" if is_optimal else "normal",
            color="#1b5e20" if is_optimal else "#37474f",
            bbox=dict(
                boxstyle="round,pad=0.3",
                facecolor="#e8f5e9" if is_optimal else "#ffffff",
                edgecolor="none",
                alpha=0.9,
            ),
        )

    # Gambar Simpul (Nodes)
    for node, (x, y) in pos.items():
        if node == "s0":
            box_color = "#e3f2fd"
            border_color = "#1565c0"
            text_color = "#0d47a1"
        elif node == "Goal":
            box_color = "#c8e6c9"
            border_color = "#2e7d32"
            text_color = "#1b5e20"
        else:
            box_color = "#f5f5f5"
            border_color = "#b0bec5"
            text_color = "#263238"

        ax.text(
            x,
            y,
            nodes[node],
            ha="center",
            va="center",
            fontsize=8,
            fontweight="bold" if node in ["s0", "Goal"] else "normal",
            color=text_color,
            bbox=dict(
                boxstyle="round,pad=0.6",
                facecolor=box_color,
                edgecolor=border_color,
                linewidth=2 if node in ["s0", "Goal"] else 1,
            ),
        )

    plt.title(
        "Graf Ruang Status (State-Space Graph) - Uniform Cost Search (UCS)",
        fontsize=12,
        fontweight="bold",
        color="#1a237e",
        pad=15,
    )
    plt.xlim(-3.4, 3.4)
    plt.ylim(-0.5, 3.5)
    plt.axis("off")
    plt.tight_layout()

    output_path = "graph_ucs_voucher.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"[INFO] Graf formal berhasil dibuat di: {output_path}")


if __name__ == "__main__":
    generate_del_style_graph()
