import sys
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches

project_root = Path(__file__).resolve().parents[1]
output_pdf = project_root / "docs" / "architecture_diagram.pdf"
output_png = project_root / "docs" / "architecture_diagram.png"

# Setup Figure (Landscape 16:9 for clean presentation in Streamlit & PDF viewers)
plt.rcParams["font.sans-serif"] = "DejaVu Sans"
plt.rcParams["font.family"] = "sans-serif"
fig, ax = plt.subplots(figsize=(16, 9.5), dpi=300)
ax.set_xlim(0, 16)
ax.set_ylim(0, 10)
ax.axis("off")

# Background styling
fig.patch.set_facecolor("#F8FAFC")
ax.set_facecolor("#F8FAFC")

# Title Header
ax.text(
    8.0, 9.6,
    "Agente SRAG DataSUS — Arquitetura de Inteligência Epidemiológica v2.0.0",
    fontsize=15, fontweight="bold", ha="center", va="center", color="#0F172A"
)
ax.text(
    8.0, 9.25,
    "Sistema Multi-Agente (LangGraph + Subagentes Agent Reach) • RAG Híbrido (ChromaDB + BM25) • Guardrails Enterprise • Observabilidade & EVALs",
    fontsize=9.2, ha="center", va="center", color="#475569"
)

# Helper function to draw rounded boxes with shadow/border
def draw_box(x, y, w, h, title, subtitle_items, bg_color="#EFF6FF", border_color="#3B82F6", title_color="#0F172A", title_size=9.2):
    # Box
    box = patches.FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.08,rounding_size=0.15",
        facecolor=bg_color, edgecolor=border_color, linewidth=1.5,
        mutation_aspect=1.0, zorder=2
    )
    ax.add_patch(box)
    
    # Title
    header_y = y + h - 0.25
    ax.text(
        x + w / 2, header_y,
        title,
        fontsize=title_size, fontweight="bold", ha="center", va="center",
        color=title_color, zorder=3
    )
    
    # Content text
    line_y = header_y - 0.28
    for item in subtitle_items:
        ax.text(
            x + 0.15, line_y,
            f"• {item}",
            fontsize=7.6, ha="left", va="center",
            color="#334155", zorder=3
        )
        line_y -= 0.21

# Arrow helper
def draw_arrow(x1, y1, x2, y2, color="#64748B", style="-|>", lw=1.6):
    ax.annotate(
        "", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(
            arrowstyle=style, color=color, lw=lw,
            shrinkA=4, shrinkB=4,
            mutation_scale=12,
        ),
        zorder=4
    )

# -------------------------------------------------------------------------
# ROW 1: INGESTION, GOVERNANCE & DATA LAYER (y: 6.8 to 8.9)
# -------------------------------------------------------------------------
ax.text(0.6, 8.85, "1. CAMADA DE DADOS & GOVERNANÇA (Medallion Architecture)", fontsize=10, fontweight="bold", color="#1E3A8A")

draw_box(
    0.6, 6.85, 3.4, 1.85,
    "Fontes & Ingestão",
    [
        "OpenDataSUS CSV (2019-2026)",
        "Séries Históricas Complementares",
        "Ingestão resiliente com fallback",
        "Validação de schema & encoding"
    ],
    bg_color="#EFF6FF", border_color="#3B82F6", title_color="#1E3A8A"
)

draw_box(
    4.3, 6.85, 3.4, 1.85,
    "Landing Zone & Hashes",
    [
        "Persistência em data/landing",
        "Assinatura SHA-256 (manifest.json)",
        "Rastreabilidade de linhagem",
        "Imutabilidade de dados brutos"
    ],
    bg_color="#EFF6FF", border_color="#3B82F6", title_color="#1E3A8A"
)

draw_box(
    8.0, 6.85, 3.4, 1.85,
    "Pré-Processamento & DQ",
    [
        "Datas canônicas & semana epidem.",
        "Derivação etiológica & faixas etárias",
        "Normalização de códigos SUS",
        "data_quality_report.json (0 descartes)"
    ],
    bg_color="#EFF6FF", border_color="#3B82F6", title_color="#1E3A8A"
)

draw_box(
    11.7, 6.85, 3.7, 1.85,
    "Refined Parquet Storage",
    [
        "srag_total.parquet (473k+ registros)",
        "Compressão colunar Snappy",
        "Anonimização estrita (Zero PII/CPF)",
        "Base otimizada para analytical tools"
    ],
    bg_color="#EFF6FF", border_color="#3B82F6", title_color="#1E3A8A"
)

draw_arrow(4.0, 7.75, 4.3, 7.75)
draw_arrow(7.7, 7.75, 8.0, 7.75)
draw_arrow(11.4, 7.75, 11.7, 7.75)

# -------------------------------------------------------------------------
# ROW 2: LANGGRAPH MULTI-AGENT ORCHESTRATOR & SUBAGENTS (y: 3.8 to 6.3)
# -------------------------------------------------------------------------
ax.text(0.6, 6.45, "2. ORQUESTRAÇÃO MULTI-AGENTE (LangGraph) & AGENT REACH (Subagentes)", fontsize=10, fontweight="bold", color="#065F46")

# Supervisor Box
draw_box(
    0.6, 4.15, 3.0, 2.15,
    "LangGraph Supervisor",
    [
        "StateGraph supervisionado",
        "Validação de contratos de nós",
        "Execução de traces auditáveis",
        "OpenInference step tracking",
        "agent_trace.jsonl logging"
    ],
    bg_color="#ECFDF5", border_color="#10B981", title_color="#065F46"
)

# Subagents
draw_box(
    3.9, 4.15, 2.7, 2.15,
    "Subagente Determinístico",
    [
        "Taxa de crescimento móvel 7d",
        "Mortalidade conhecida vs. bruta",
        "Proxy de UTI e Vacinação",
        "Detecção de Surtos / Z-Score",
        "4 Gráficos Matplotlib HD"
    ],
    bg_color="#F0FDF4", border_color="#22C55E", title_color="#0F766E"
)

draw_box(
    6.85, 4.15, 2.8, 2.15,
    "Agent Reach: Mídia & Social",
    [
        "Subagente Fontes Oficiais (.gov, WHO)",
        "Subagente Redes Sociais (Reddit)",
        "Subagente Transcrições (Fiocruz)",
        "Filtro por Allowlist Estrita",
        "Extração semântica de notícias"
    ],
    bg_color="#F0FDF4", border_color="#22C55E", title_color="#0F766E"
)

draw_box(
    9.9, 4.15, 2.7, 2.15,
    "RAG Híbrido Retriever",
    [
        "Dense: ChromaDB + MiniLM",
        "Sparse: BM25 Lexical",
        "Reciprocal Rank Fusion (RRF)",
        "Re-ranking contextual top-k",
        "Indexação de todos os artefatos"
    ],
    bg_color="#F0FDF4", border_color="#22C55E", title_color="#0F766E"
)

draw_box(
    12.85, 4.15, 2.55, 2.15,
    "Enterprise Guardrails",
    [
        "Input Guardrail (Scope & PII)",
        "Anti-Prompt Injection",
        "Output Guardrail (Compliance)",
        "Allowlist de domínios",
        "Filtro de exfiltração .env"
    ],
    bg_color="#FFFBEB", border_color="#F59E0B", title_color="#B45309"
)

draw_arrow(3.6, 5.25, 3.9, 5.25)
draw_arrow(6.6, 5.25, 6.85, 5.25)
draw_arrow(9.65, 5.25, 9.9, 5.25)
draw_arrow(12.6, 5.25, 12.85, 5.25)

# Connect Row 1 to Row 2
draw_arrow(13.5, 6.85, 13.5, 6.3, color="#059669")

# -------------------------------------------------------------------------
# ROW 3: INTELLIGENCE SUITE, OBSERVABILITY & STREAMLIT UI (y: 0.8 to 3.4)
# -------------------------------------------------------------------------
ax.text(0.6, 3.65, "3. SUÍTE MULTI-ARTEFATO, OBSERVABILIDADE/EVALs & STREAMLIT UI", fontsize=10, fontweight="bold", color="#5B21B6")

draw_box(
    0.6, 1.0, 4.8, 2.5,
    "Suíte de Artefatos de Inteligência",
    [
        "executive_bulletin.md — Boletim Estratégico e KPIs",
        "epidemiological_deepdive.md — Patógenos & Faixas Etárias",
        "anomaly_alerts.md — Alertas Estatísticos & Z-Scores",
        "media_and_social_signals.md — Inteligência Comunitária",
        "data_governance_report.md — Linhagem, Hashes & Auditoria",
        "report.pdf / report.md — Relatório Oficial Consolidado"
    ],
    bg_color="#F5F3FF", border_color="#8B5CF6", title_color="#5B21B6"
)

draw_box(
    5.7, 1.0, 4.7, 2.5,
    "Observabilidade & Framework de EVALs",
    [
        "EVALs Pré-Recuperação: Roteamento & Intenção",
        "EVALs Em-Recuperação: MRR, Context Relevance, Recall",
        "EVALs Pós-Recuperação: Groundedness & Faithfulness",
        "Contabilidade de Tokens (Prompt, Completion, Total)",
        "Custos Financeiros Calculados em USD e BRL",
        "Latência por Nó do Grafo & OpenInference Spans"
    ],
    bg_color="#F5F3FF", border_color="#8B5CF6", title_color="#5B21B6"
)

draw_box(
    10.7, 1.0, 4.7, 2.5,
    "Interface Web Interativa (Streamlit)",
    [
        "Sobre o Projeto — Documentação e Arquitetura",
        "Pipeline & Execução — Disparo em Tempo Real",
        "Suíte de Relatórios — Tela Cheia com Abas Largas",
        "Chat RAG Híbrido — Prompt Amplo & Respostas Recentes Topo",
        "Painel de Observabilidade, Traces & KPIs Financeiros"
    ],
    bg_color="#FFFFFF", border_color="#0F172A", title_color="#0F172A"
)

# Connect Row 2 to Row 3
draw_arrow(4.5, 4.15, 3.0, 3.5, color="#7C3AED")
draw_arrow(8.5, 4.15, 8.0, 3.5, color="#7C3AED")
draw_arrow(11.5, 4.15, 12.0, 3.5, color="#7C3AED")

draw_arrow(5.4, 2.25, 5.7, 2.25)
draw_arrow(10.4, 2.25, 10.7, 2.25)

# Footer Note
ax.text(
    8.0, 0.4,
    "Princípio de Segurança e Confiabilidade: O LLM nunca calcula métricas ou acessa dados brutos diretamente. Ele consome resultados de tools e subagentes auditáveis sob guardrails estritos.",
    fontsize=8.2, ha="center", va="center", color="#475569", style="italic"
)

plt.tight_layout()
plt.savefig(output_pdf, format="pdf", bbox_inches="tight")
plt.savefig(output_png, format="png", dpi=300, bbox_inches="tight")
plt.close()

print(f"Diagramas gerados com sucesso:\n- {output_pdf}\n- {output_png}")
