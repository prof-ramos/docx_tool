# 🤖 Legal Bot - Discord RAG para Legislação Brasileira

Bot do Discord com RAG (Retrieval-Augmented Generation) para consultar documentos legais brasileiros.

## 📋 Visão Geral

Este projeto combina:
- **Bot Discord** com comandos slash para consultas legais
- **Sistema RAG** usando embeddings OpenAI + Supabase pgvector
- **Pipeline de processamento** para converter DOCX → Markdown
- **Dashboard admin** Streamlit para monitoramento

### Arquitetura

```
Usuário (Discord) → Bot → RAG Engine → Supabase (pgvector) → OpenAI GPT-4
                                             ↓
                                    Resposta com fontes
```

## 🚀 Quick Start

### 1. Instalação

```bash
# Clone o repositório
git clone <repo-url>
cd docx_tool

# Instale UV (gerenciador de pacotes Python moderno)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Instale dependências
uv sync
```

### 2. Configuração

```bash
# Configure variáveis de ambiente
cp .env.example .env
# Edite .env com suas credenciais
```

Credenciais necessárias:
- `DISCORD_TOKEN` - Token do bot Discord
- `SUPABASE_URL` - URL do projeto Supabase
- `SUPABASE_ANON_KEY` - Chave anônima do Supabase
- `SUPABASE_SERVICE_ROLE_KEY` - Chave de serviço do Supabase
- `OPENAI_API_KEY` - Chave da API OpenAI

### 3. Setup do Banco de Dados

```bash
# Aplique a migration no Supabase
# (Use o dashboard do Supabase ou psql)
psql $DATABASE_URL < supabase/migrations/001_create_documents_table.sql
```

### 4. Processamento de Documentos

```bash
# Converta DOCX para Markdown
./run_cli.sh process Administrativo --output-dir Output --format md

# Ingira documentos no banco vetorial
./run_ingestion.sh Output
```

### 5. Execute o Bot

```bash
# Inicie o bot Discord
./run_bot.sh

# Em outro terminal: Dashboard admin (opcional)
./run_dashboard.sh
```

## 📚 Comandos do Discord

### Comandos de Usuário (Slash Commands)

#### `/perguntar <pergunta>`
Faça uma pergunta sobre legislação brasileira

**Exemplo:**
```
/perguntar O que é desapropriação por utilidade pública?
```

#### `/buscar <palavras-chave> [limite]`
Busca documentos por palavras-chave

**Exemplo:**
```
/buscar licitações 5
```

#### `!ajuda_legal`
Mostra ajuda sobre os comandos

### Comandos Admin (Requer permissão de administrador)

- `/status` - Status do bot e sistema
- `/sync` - Sincroniza comandos slash
- `/reload_rag` - Recarrega o RAG engine
- `/stats` - Estatísticas de uso
- `!ping` - Verifica latência

## 🏗️ Estrutura do Projeto

```
legal-bot/
├── src/
│   ├── bot/                      # Bot Discord
│   │   ├── main.py              # Entry point
│   │   ├── cogs/                # Comandos
│   │   │   ├── rag_commands.py  # Comandos RAG
│   │   │   └── admin_commands.py
│   │   └── core/
│   │       ├── rag_engine.py    # Motor RAG
│   │       └── ingestion.py     # Pipeline de ingestão
│   ├── docx_cli/                # Processamento de documentos
│   │   ├── main.py
│   │   ├── commands/
│   │   └── core/
│   └── dashboard/               # Dashboard admin
│       └── admin.py
├── supabase/
│   └── migrations/              # SQL schemas
├── Administrativo/              # Documentos DOCX de entrada
├── Output/                      # Markdown processado
├── .env                         # Variáveis de ambiente
├── pyproject.toml               # Configuração do projeto
└── run_*.sh                     # Scripts de execução
```

## 🔧 Tecnologias

### Backend
- **Python 3.14** com UV package manager
- **discord.py** - Framework do bot Discord
- **OpenAI API** - Embeddings (text-embedding-3-small) + GPT-4o-mini
- **Supabase** - PostgreSQL com extensão pgvector
- **Docling** - Conversão DOCX → Markdown

### Frontend
- **Streamlit** - Dashboard administrativo
- **Plotly** - Gráficos e visualizações

### Infrastructure
- **Supabase** - Hospedagem do banco vetorial
- **Discord** - Plataforma do bot

## 📖 Pipeline RAG

### 1. Processamento de Documentos
```bash
DOCX (Administrativo/)
  → Normalização (remove cores, formata)
  → Conversão (Docling)
  → Markdown (Output/)
```

### 2. Ingestão Vetorial
```bash
Markdown
  → Chunking (1000 chars, overlap 200)
  → Embeddings (OpenAI text-embedding-3-small, 1536 dims)
  → Supabase (pgvector com índice IVFFlat)
```

### 3. Query Flow
```bash
Pergunta do usuário
  → Embedding da pergunta
  → Busca vetorial (cosine similarity)
  → Top-5 documentos (threshold 0.7)
  → Contexto + Prompt
  → GPT-4o-mini
  → Resposta com fontes
```

## 🎨 Dashboard Admin

Acesse em `http://localhost:8501` após executar `./run_dashboard.sh`

**Funcionalidades:**
- 📊 Estatísticas em tempo real
- 📚 Gerenciamento de documentos
- 🔍 Teste de busca vetorial
- ⚙️ Verificação de configurações
- 📈 Visualização de distribuição de fontes

## 🛠️ Desenvolvimento

### Adicionar Novo Comando Discord

1. Edite `src/bot/cogs/rag_commands.py` ou `admin_commands.py`
2. Adicione método com decorator `@app_commands.command()`
3. Reinicie o bot
4. Execute `/sync` no Discord

**Exemplo:**
```python
@app_commands.command(name="meucomando", description="Descrição")
async def meu_comando(self, interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    # Lógica aqui
    await interaction.followup.send("Resposta")
```

### Atualizar Modelo RAG

1. Edite `src/bot/core/rag_engine.py`
2. Altere `EMBEDDING_MODEL` ou `GENERATION_MODEL`
3. Se mudou embedding, re-ingira documentos
4. Reload: `/reload_rag` no Discord

### Adicionar Nova Fonte de Documentos

1. Coloque arquivos DOCX em pasta
2. Processe: `./run_cli.sh process <pasta>`
3. Ingira: `./run_ingestion.sh Output`

## 🧪 Testes

### Teste Manual

```bash
# Teste processamento (dry run)
./run_cli.sh process Administrativo --dry-run

# Teste ingestão (dataset pequeno)
./run_ingestion.sh Output "lei_9784*.md"

# Teste bot localmente
./run_bot.sh
# Use Discord para testar comandos
```

### Testes Unitários (TODO)

```bash
pytest tests/
pytest tests/test_rag_engine.py -v
pytest --cov=src --cov-report=html
```

## 📊 Monitoramento

### Dashboard Streamlit
```bash
./run_dashboard.sh
# Acesse http://localhost:8501
```

### Discord
```
/status - Status do sistema
/stats - Estatísticas de uso
```

### Supabase Dashboard
- Acesse seu projeto Supabase
- Verifique tabela `documents`
- Monitore queries no SQL Editor

## ⚠️ Troubleshooting

### Bot não responde
```bash
# Verifique se está rodando
ps aux | grep "src.bot.main"

# Verifique token
echo $DISCORD_TOKEN

# Logs
./run_bot.sh
```

### RAG não encontra documentos
```bash
# Teste conexão Supabase
uv run python -c "from supabase import create_client; import os; client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY')); print(client.table('documents').select('count').execute())"

# Verifique se documentos foram ingeridos
# Use dashboard ou psql
```

### Embeddings falhando
```bash
# Teste OpenAI
uv run python -c "import openai; import os; openai.api_key = os.getenv('OPENAI_API_KEY'); print(openai.Model.list())"
```

### Dashboard não carrega
```bash
# Verifique políticas RLS no Supabase
# Garanta que ANON_KEY tem acesso SELECT à tabela documents
```

## 📝 Configuração Avançada

### Ajustar Parâmetros RAG

Edite `src/bot/core/rag_engine.py`:

```python
# Tamanho dos chunks
CHUNK_SIZE = 1000  # caracteres
CHUNK_OVERLAP = 200

# Busca
TOP_K = 5  # documentos retornados
SIMILARITY_THRESHOLD = 0.7  # 0.0-1.0

# Modelos
EMBEDDING_MODEL = "text-embedding-3-small"
GENERATION_MODEL = "gpt-4o-mini"
```

### Rate Limits

- **OpenAI:** 500 RPM (embeddings), 200 RPM (chat)
- **Discord:** 50 slash commands/segundo
- **Supabase:** Depende do plano

## 🔒 Segurança

- **SERVICE_ROLE_KEY:** Use apenas para ingestão (bypassa RLS)
- **ANON_KEY:** Use no dashboard (respeita RLS)
- **Nunca commite .env** no git
- **Token Discord:** Mantenha seguro no .env

## 📚 Recursos

- [discord.py docs](https://discordpy.readthedocs.io)
- [OpenAI API](https://platform.openai.com/docs)
- [Supabase Vector](https://supabase.com/docs/guides/ai)
- [Docling](https://github.com/DS4SD/docling)
- [UV](https://github.com/astral-sh/uv)

## 📄 Licença

MIT

## 👥 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 🆘 Suporte

Para problemas ou dúvidas:
- Abra uma issue no GitHub
- Consulte o arquivo CLAUDE.md para detalhes técnicos

---

**Desenvolvido com ❤️ usando Python, Discord.py, OpenAI e Supabase**
