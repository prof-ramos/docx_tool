# Sistema de Cache - Legal Bot

## Visão Geral

O sistema de cache foi implementado para reduzir custos de API e melhorar a performance do bot, armazenando resultados de embeddings e respostas RAG.

## Arquitetura

```
┌─────────────────────────────────────────────┐
│         CacheManager                        │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────────────┐  ┌─────────────────┐ │
│  │ Embedding Cache  │  │ Response Cache  │ │
│  │                  │  │                 │ │
│  │ • TTL: 7 dias    │  │ • TTL: 1 hora   │ │
│  │ • Max: 10K       │  │ • Max: 1K       │ │
│  │ • LRU eviction   │  │ • LRU eviction  │ │
│  └──────────────────┘  └─────────────────┘ │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │   Persistência em Disco (JSON)       │  │
│  │   ~/.cache/legal_bot/                │  │
│  │   • embeddings.json                  │  │
│  │   • responses.json                   │  │
│  │   • stats.json                       │  │
│  └──────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

## Componentes

### 1. Cache Manager (`src/bot/core/cache_manager.py`)

Gerenciador central de cache com duas camadas:

#### Cache de Embeddings
- **Propósito**: Armazenar embeddings de texto para evitar chamadas repetidas à API OpenAI
- **Chave**: Hash SHA256 do texto
- **Valor**: Lista de floats (vetor de 1536 dimensões)
- **TTL**: 7 dias (configurável, 0 = sem expiração)
- **Tamanho máximo**: 10.000 entradas
- **Eviction**: LRU (Least Recently Used)

#### Cache de Respostas
- **Propósito**: Armazenar respostas completas RAG para queries repetidas
- **Chave**: Hash SHA256 da query + hash do contexto
- **Valor**: Dict com `{answer, sources, confidence}`
- **TTL**: 1 hora (configurável)
- **Tamanho máximo**: 1.000 entradas
- **Eviction**: LRU (Least Recently Used)

### 2. Integração com RAG Engine

O cache está integrado em:

**`src/bot/core/rag_engine.py`**
```python
# Embedding cache em generate_embedding()
cached_embedding = self.cache.get_embedding(text)
if cached_embedding:
    return cached_embedding  # Cache hit!

# Response cache em query()
cached_response = self.cache.get_response(question, context_hash)
if cached_response:
    return cached_response  # Cache hit!
```

**`src/bot/core/ingestion.py`**
```python
# Cache de embeddings durante ingestão
# Útil ao re-processar documentos duplicados
cached_embedding = self.cache.get_embedding(chunk_text)
```

## Uso

### No Discord Bot

#### Comandos Admin

**Ver estatísticas do cache:**
```
/cache_stats
```

Retorna:
- Hits/Misses por tipo de cache
- Hit rate (%)
- Tamanho do cache
- Evictions
- Economia estimada de API calls

**Limpar cache:**
```
/clear_cache [embeddings|responses|all]
```

Opções:
- `embeddings`: Limpa apenas cache de embeddings
- `responses`: Limpa apenas cache de respostas
- `all`: Limpa ambos

### No Dashboard

Acesse `📊 Dashboard` → Seção `💾 Estatísticas de Cache`

**Visualizações:**
- Métricas de hits/misses
- Hit rate por tipo de cache
- Tamanho total do cache (MB)
- Gráfico de performance (hits vs misses)
- Economia estimada (API calls + custo em USD)

### Programaticamente

**Usar cache no RAG engine:**
```python
from src.bot.core.rag_engine import RAGEngine

# Cache habilitado por padrão
rag = RAGEngine(enable_cache=True)
await rag.initialize()

# Fazer query (usa cache automaticamente)
result = await rag.query("O que é desapropriação?")

# Ver estatísticas
stats = rag.get_cache_stats()
print(f"Hit rate: {stats['embeddings']['hit_rate']:.1%}")

# Limpar cache
rag.clear_cache("all")
```

**Usar cache no ingestion pipeline:**
```python
from src.bot.core.ingestion import DocumentIngestionPipeline

# Cache habilitado por padrão
pipeline = DocumentIngestionPipeline(enable_cache=True)
await pipeline.initialize()

# Ingerir documentos (reutiliza embeddings em cache)
stats = await pipeline.ingest_directory(Path("Output"))
# Mostra estatísticas de cache ao final
```

## Configuração

### Parâmetros do CacheManager

```python
CacheManager(
    cache_dir=Path.home() / ".cache" / "legal_bot",  # Diretório de cache
    embedding_ttl=86400 * 7,          # 7 dias (0 = sem expiração)
    response_ttl=3600,                 # 1 hora (0 = sem expiração)
    max_embedding_cache_size=10000,    # Máximo de embeddings
    max_response_cache_size=1000,      # Máximo de respostas
    enable_persistence=True            # Persistir em disco
)
```

### Variáveis de Ambiente

Nenhuma variável de ambiente adicional necessária. O cache usa o diretório padrão do usuário:

```bash
~/.cache/legal_bot/
├── embeddings.json    # Cache de embeddings
├── responses.json     # Cache de respostas
└── stats.json         # Estatísticas
```

## Performance

### Economia Esperada

**Embeddings:**
- Custo por embedding: ~$0.00002 USD
- Com 50% hit rate em 1000 queries: ~$0.01 economizado
- Em produção (10K queries/dia): ~$0.10-0.20/dia economizado

**Respostas:**
- Evita 1 embedding + 1 LLM call por hit
- Custo por resposta completa: ~$0.001 USD
- Com 30% hit rate em 1000 queries: ~$0.30 economizado
- Em produção (10K queries/dia): ~$3-5/dia economizado

### Latência

**Com cache:**
- Embedding hit: ~0.1ms (vs ~200ms API call)
- Response hit: ~0.1ms (vs ~2000ms RAG completo)

**Speedup:**
- Embedding: ~2000x mais rápido
- Response completa: ~20000x mais rápido

## Manutenção

### Persistência Automática

O cache é automaticamente salvo em disco:
- Ao destruir o objeto CacheManager (`__del__`)
- Pode ser salvo manualmente: `cache.save_to_disk()`

### Carregamento Automático

O cache é automaticamente carregado ao inicializar:
- Se `enable_persistence=True`
- Busca em `~/.cache/legal_bot/`

### Limpeza Manual

**Via código:**
```python
cache.clear_embeddings()  # Limpa embeddings
cache.clear_responses()   # Limpa respostas
cache.clear_all()         # Limpa tudo
```

**Via Discord:**
```
/clear_cache all
```

**Via filesystem:**
```bash
rm -rf ~/.cache/legal_bot/*.json
```

### Monitoramento

**Verificar tamanho do cache:**
```bash
du -sh ~/.cache/legal_bot/
```

**Ver estatísticas:**
```bash
cat ~/.cache/legal_bot/stats.json | jq
```

**Exemplo de output:**
```json
{
  "embeddings": {
    "hits": 450,
    "misses": 550,
    "size": 550,
    "evictions": 0,
    "hit_rate": 0.45
  },
  "responses": {
    "hits": 120,
    "misses": 280,
    "size": 280,
    "evictions": 0,
    "hit_rate": 0.3
  },
  "total_size_bytes": 8880640
}
```

## Troubleshooting

### Cache não está funcionando

**Verificar se está habilitado:**
```python
rag = RAGEngine()
print(rag.cache_enabled)  # Deve ser True
```

**Verificar diretório:**
```bash
ls -la ~/.cache/legal_bot/
# Deve ter embeddings.json, responses.json, stats.json
```

### Hit rate muito baixo

**Possíveis causas:**
- Queries sempre diferentes (esperado)
- TTL muito curto
- Cache foi limpo recentemente
- Bot foi reiniciado (cache em memória perdido, mas disco mantém)

**Soluções:**
- Aumentar TTL
- Verificar se persistência está habilitada
- Aguardar mais queries para popular o cache

### Cache crescendo muito

**Verificar tamanho:**
```bash
du -sh ~/.cache/legal_bot/
```

**Ajustar limites:**
```python
cache = CacheManager(
    max_embedding_cache_size=5000,  # Reduzir de 10K
    max_response_cache_size=500     # Reduzir de 1K
)
```

**Limpar periodicamente:**
```bash
# Cron job para limpar cache mensalmente
0 0 1 * * rm -rf ~/.cache/legal_bot/*.json
```

### Erro ao carregar cache

**Corrupção de arquivo:**
```bash
# Remover arquivos corrompidos
rm ~/.cache/legal_bot/*.json
# Cache será recriado automaticamente
```

## Boas Práticas

1. **Manter persistência habilitada** em produção para sobreviver a reinicializações
2. **Monitorar hit rate** via dashboard para otimizar TTL
3. **Limpar cache** após mudanças no modelo de embeddings
4. **Ajustar TTL** baseado em padrões de uso:
   - Embeddings: TTL longo (documentos não mudam)
   - Respostas: TTL curto (contexto pode mudar)
5. **Backup do cache** antes de fazer limpezas massivas

## Roadmap Futuro

- [ ] Cache distribuído (Redis)
- [ ] Compressão de embeddings (quantização)
- [ ] Cache warming (pre-popular queries comuns)
- [ ] Métricas de cache no banco de dados
- [ ] Auto-ajuste de TTL baseado em padrões
- [ ] Cache de contexto intermediário
- [ ] Integração com CDN para assets estáticos
