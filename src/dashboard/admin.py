"""Admin dashboard for Discord bot monitoring."""
import streamlit as st
import os
from supabase import create_client
from dotenv import load_dotenv
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta

load_dotenv()

# Page config
st.set_page_config(
    page_title="Legal Bot Admin Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Supabase
@st.cache_resource
def init_supabase():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    return create_client(url, key)

supabase = init_supabase()

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .metric-label {
        font-size: 1rem;
        color: #666;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2991/2991112.png", width=80)
    st.title("🤖 Legal Bot Admin")
    st.markdown("---")

    # Navigation
    page = st.selectbox(
        "Navegação",
        ["📊 Dashboard", "📚 Documentos", "🔍 Busca", "⚙️ Configurações"]
    )

    st.markdown("---")
    st.markdown("### Status")
    if st.button("🔄 Atualizar"):
        st.rerun()

# Helper functions
@st.cache_data(ttl=60)
def get_document_stats():
    """Get document statistics from Supabase."""
    try:
        result = supabase.rpc('get_document_statistics').execute()
        return result.data if result.data else {}
    except Exception as e:
        st.error(f"Erro ao buscar estatísticas: {e}")
        return {}

@st.cache_data(ttl=60)
def get_recent_documents(limit=10):
    """Get recently added documents."""
    try:
        result = supabase.table('documents') \
            .select('id, metadata, created_at') \
            .order('created_at', desc=True) \
            .limit(limit) \
            .execute()
        return result.data if result.data else []
    except Exception as e:
        st.error(f"Erro ao buscar documentos: {e}")
        return []

@st.cache_data(ttl=60)
def search_documents(query, limit=20):
    """Search documents by content."""
    try:
        result = supabase.table('documents') \
            .select('id, content, metadata, created_at') \
            .ilike('content', f'%{query}%') \
            .limit(limit) \
            .execute()
        return result.data if result.data else []
    except Exception as e:
        st.error(f"Erro na busca: {e}")
        return []

@st.cache_data(ttl=30)
def get_cache_stats():
    """Get cache statistics from cache files."""
    from pathlib import Path
    import json

    try:
        cache_dir = Path.home() / ".cache" / "legal_bot"
        stats_file = cache_dir / "stats.json"

        if stats_file.exists():
            with open(stats_file, 'r') as f:
                return json.load(f)
        return None
    except Exception as e:
        st.error(f"Erro ao carregar stats do cache: {e}")
        return None

# Dashboard Page
if page == "📊 Dashboard":
    st.title("📊 Dashboard do Bot Legal")
    st.markdown("Monitoramento e estatísticas em tempo real")

    # Get stats
    stats = get_document_stats()

    if stats:
        # Metrics row
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown("""
                <div class="metric-card">
                    <div class="metric-value">{}</div>
                    <div class="metric-label">Documentos</div>
                </div>
            """.format(stats.get('total_documents', 0)), unsafe_allow_html=True)

        with col2:
            st.markdown("""
                <div class="metric-card">
                    <div class="metric-value">{}</div>
                    <div class="metric-label">Fontes</div>
                </div>
            """.format(stats.get('total_sources', 0)), unsafe_allow_html=True)

        with col3:
            st.markdown("""
                <div class="metric-card">
                    <div class="metric-value">{}</div>
                    <div class="metric-label">Títulos Únicos</div>
                </div>
            """.format(stats.get('unique_titles', 0)), unsafe_allow_html=True)

        with col4:
            last_ingestion = stats.get('last_ingestion', 'N/A')
            if last_ingestion != 'N/A':
                last_ingestion = datetime.fromisoformat(last_ingestion.replace('Z', '+00:00'))
                last_ingestion = last_ingestion.strftime('%d/%m/%Y %H:%M')

            st.markdown("""
                <div class="metric-card">
                    <div class="metric-value" style="font-size: 1.2rem;">{}</div>
                    <div class="metric-label">Última Ingestão</div>
                </div>
            """.format(last_ingestion), unsafe_allow_html=True)

        st.markdown("---")

        # Source breakdown
        if 'sources_breakdown' in stats and stats['sources_breakdown']:
            st.subheader("📂 Distribuição por Fonte")

            sources = stats['sources_breakdown']
            df_sources = pd.DataFrame(list(sources.items()), columns=['Fonte', 'Quantidade'])

            col1, col2 = st.columns([2, 1])

            with col1:
                fig = px.pie(
                    df_sources,
                    values='Quantidade',
                    names='Fonte',
                    title="Documentos por Fonte"
                )
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.dataframe(df_sources, hide_index=True, use_container_width=True)

        st.markdown("---")

        # Recent documents
        st.subheader("📄 Documentos Recentes")
        recent_docs = get_recent_documents(10)

        if recent_docs:
            docs_data = []
            for doc in recent_docs:
                metadata = doc.get('metadata', {})
                created_at = datetime.fromisoformat(doc['created_at'].replace('Z', '+00:00'))

                docs_data.append({
                    'Título': metadata.get('title', 'Sem título'),
                    'Fonte': metadata.get('source', 'N/A'),
                    'Chunk': metadata.get('chunk_index', 0),
                    'Criado em': created_at.strftime('%d/%m/%Y %H:%M')
                })

            df_docs = pd.DataFrame(docs_data)
            st.dataframe(df_docs, hide_index=True, use_container_width=True)
        else:
            st.info("Nenhum documento encontrado")

        st.markdown("---")

        # Cache statistics
        st.subheader("💾 Estatísticas de Cache")
        cache_stats = get_cache_stats()

        if cache_stats:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### 🔤 Cache de Embeddings")
                emb_stats = cache_stats['embeddings']

                # Metrics
                metric_col1, metric_col2, metric_col3 = st.columns(3)
                with metric_col1:
                    st.metric("Hits", emb_stats['hits'])
                with metric_col2:
                    st.metric("Misses", emb_stats['misses'])
                with metric_col3:
                    hit_rate = emb_stats['hit_rate'] * 100
                    st.metric("Hit Rate", f"{hit_rate:.1f}%")

                # Additional info
                st.info(f"**Tamanho:** {emb_stats['size']} entradas  \n**Evictions:** {emb_stats['evictions']}")

                # API calls saved
                if emb_stats['hits'] > 0:
                    cost_saved = emb_stats['hits'] * 0.00002
                    st.success(f"💰 **API calls economizadas:** {emb_stats['hits']}  \n💰 **Custo economizado:** ${cost_saved:.4f}")

            with col2:
                st.markdown("#### 💬 Cache de Respostas")
                resp_stats = cache_stats['responses']

                # Metrics
                metric_col1, metric_col2, metric_col3 = st.columns(3)
                with metric_col1:
                    st.metric("Hits", resp_stats['hits'])
                with metric_col2:
                    st.metric("Misses", resp_stats['misses'])
                with metric_col3:
                    hit_rate = resp_stats['hit_rate'] * 100
                    st.metric("Hit Rate", f"{hit_rate:.1f}%")

                # Additional info
                st.info(f"**Tamanho:** {resp_stats['size']} entradas  \n**Evictions:** {resp_stats['evictions']}")

                # Total size
                total_size_mb = cache_stats['total_size_bytes'] / (1024 * 1024)
                st.info(f"📦 **Tamanho total estimado:** {total_size_mb:.2f} MB")

            # Cache performance chart
            st.markdown("#### 📈 Performance do Cache")

            # Create performance data
            perf_data = {
                'Cache': ['Embeddings', 'Respostas'],
                'Hits': [emb_stats['hits'], resp_stats['hits']],
                'Misses': [emb_stats['misses'], resp_stats['misses']]
            }
            df_perf = pd.DataFrame(perf_data)

            # Stacked bar chart
            fig = go.Figure(data=[
                go.Bar(name='Hits', x=df_perf['Cache'], y=df_perf['Hits'], marker_color='#2ecc71'),
                go.Bar(name='Misses', x=df_perf['Cache'], y=df_perf['Misses'], marker_color='#e74c3c')
            ])
            fig.update_layout(barmode='stack', title='Cache Hits vs Misses')
            st.plotly_chart(fig, use_container_width=True)

        else:
            st.info("📭 Cache ainda não foi utilizado ou estatísticas não disponíveis")

    else:
        st.warning("⚠️ Não foi possível carregar as estatísticas")

# Documents Page
elif page == "📚 Documentos":
    st.title("📚 Gerenciamento de Documentos")

    # Filters
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        search_term = st.text_input("🔍 Buscar por conteúdo", placeholder="Digite para buscar...")

    with col2:
        limit = st.number_input("Limite", min_value=5, max_value=100, value=20)

    with col3:
        if st.button("🔍 Buscar", type="primary"):
            st.session_state['search_performed'] = True

    # Search results
    if search_term and st.session_state.get('search_performed', False):
        with st.spinner("Buscando..."):
            results = search_documents(search_term, limit)

        if results:
            st.success(f"✅ Encontrados {len(results)} resultados")

            for i, doc in enumerate(results, 1):
                with st.expander(f"📄 {doc.get('metadata', {}).get('title', 'Documento')} (Chunk {doc.get('metadata', {}).get('chunk_index', 0)})"):
                    st.markdown(f"**ID:** `{doc['id']}`")
                    st.markdown(f"**Fonte:** {doc.get('metadata', {}).get('source', 'N/A')}")
                    st.markdown(f"**Criado em:** {doc['created_at']}")
                    st.markdown("**Conteúdo:**")
                    st.text_area("", doc['content'], height=200, key=f"content_{i}", disabled=True)
        else:
            st.info("Nenhum resultado encontrado")

# Search Page
elif page == "🔍 Busca":
    st.title("🔍 Busca Vetorial (RAG)")
    st.markdown("Teste o sistema de busca vetorial do bot")

    st.info("⚠️ Esta funcionalidade requer integração com o RAG Engine. Implemente em breve!")

    query = st.text_area("Digite sua pergunta:", placeholder="Ex: O que é desapropriação?")

    col1, col2 = st.columns([1, 3])
    with col1:
        top_k = st.slider("Resultados", 1, 10, 5)
    with col2:
        threshold = st.slider("Threshold de similaridade", 0.0, 1.0, 0.7, 0.05)

    if st.button("🔍 Buscar", type="primary"):
        if query:
            st.warning("Funcionalidade em desenvolvimento")
        else:
            st.error("Por favor, digite uma pergunta")

# Settings Page
elif page == "⚙️ Configurações":
    st.title("⚙️ Configurações do Sistema")

    st.subheader("🔐 Variáveis de Ambiente")

    # Check env variables
    env_vars = {
        "DISCORD_TOKEN": os.getenv("DISCORD_TOKEN"),
        "SUPABASE_URL": os.getenv("SUPABASE_URL"),
        "SUPABASE_ANON_KEY": os.getenv("SUPABASE_ANON_KEY"),
        "SUPABASE_SERVICE_ROLE_KEY": os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
    }

    for var, value in env_vars.items():
        col1, col2 = st.columns([3, 1])
        with col1:
            st.text_input(
                var,
                value="***" + value[-4:] if value else "Não configurado",
                disabled=True,
                type="password"
            )
        with col2:
            status = "✅" if value else "❌"
            st.markdown(f"### {status}")

    st.markdown("---")

    st.subheader("🗄️ Banco de Dados")

    if st.button("🔄 Testar Conexão Supabase"):
        try:
            result = supabase.table('documents').select('count', count='exact').execute()
            st.success(f"✅ Conexão bem-sucedida! Total de documentos: {result.count}")
        except Exception as e:
            st.error(f"❌ Erro na conexão: {e}")

    st.markdown("---")

    st.subheader("📥 Ingestão de Documentos")

    st.markdown("""
    Para ingerir novos documentos no sistema RAG:

    ```bash
    # 1. Processar documentos DOCX -> Markdown
    ./run_cli.sh process Administrativo --output-dir Output --format md

    # 2. Ingerir no Supabase
    python -m src.bot.core.ingestion Output
    ```
    """)

    if st.button("▶️ Executar Ingestão"):
        st.info("⚠️ Execute o comando manualmente no terminal")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.8rem;">
    Legal Bot Admin Dashboard | Powered by Streamlit & Supabase
</div>
""", unsafe_allow_html=True)
