# Bot Discord - Comandos e Gerenciamento

Comandos para trabalhar com o bot Discord do projeto.

## Purpose

Facilita o desenvolvimento e teste do bot Discord com RAG para documentos legais.

## Usage

```
/bot-discord
```

## Comandos Disponíveis

### Iniciar o Bot
```bash
# Inicia o bot Discord
./run_bot.sh

# Ou manualmente
uv run python -m src.bot.main
```

### Testar Comandos no Discord

#### Comandos de Usuário (Slash)
```
/perguntar O que é desapropriação por utilidade pública?
/buscar licitações 5
!ajuda_legal
```

#### Comandos Admin
```
/status       # Status do bot e sistema
/sync         # Sincroniza comandos slash
/reload_rag   # Recarrega RAG engine
/stats        # Estatísticas de uso
!ping         # Testa latência
```

## Desenvolvimento

### Adicionar Novo Comando

1. **Edite o arquivo de cog:**
   ```python
   # src/bot/cogs/rag_commands.py

   @app_commands.command(name="meucomando", description="Descrição")
   @app_commands.describe(parametro="Descrição do parâmetro")
   async def meu_comando(
       self,
       interaction: discord.Interaction,
       parametro: str
   ):
       await interaction.response.defer(thinking=True)

       try:
           # Sua lógica aqui
           result = await self.bot.rag_engine.query(parametro)

           embed = discord.Embed(
               title="Título",
               description=result['answer'],
               color=discord.Color.blue()
           )

           await interaction.followup.send(embed=embed)

       except Exception as e:
           error_embed = discord.Embed(
               title="❌ Erro",
               description=f"```{str(e)}```",
               color=discord.Color.red()
           )
           await interaction.followup.send(embed=error_embed, ephemeral=True)
   ```

2. **Reinicie o bot:**
   ```bash
   # Pare o bot (Ctrl+C)
   # Inicie novamente
   ./run_bot.sh
   ```

3. **Sincronize comandos:**
   No Discord: `/sync`

### Estrutura de Embeds

```python
# Embed básico
embed = discord.Embed(
    title="📚 Título",
    description="Descrição",
    color=discord.Color.blue()
)

# Adicionar campos
embed.add_field(
    name="Nome do Campo",
    value="Valor",
    inline=True  # ou False
)

# Footer
embed.set_footer(text="Texto do footer")

# Enviar
await interaction.followup.send(embed=embed)
```

### Resposta com Thinking Status

```python
# Inicia o "thinking" status
await interaction.response.defer(thinking=True)

# ... processamento ...

# Envia resposta
await interaction.followup.send("Resposta")
```

### Resposta Efêmera (Apenas Admin)

```python
await interaction.followup.send(
    "Mensagem visível apenas para o admin",
    ephemeral=True
)
```

## Testing

### Teste Local

```bash
# 1. Configure .env
cp .env.example .env
# Edite com suas credenciais

# 2. Aplique migration Supabase
psql $DATABASE_URL < supabase/migrations/001_create_documents_table.sql

# 3. Ingira documentos de teste
./run_cli.sh process Administrativo --output-dir Output --format md
./run_ingestion.sh Output "lei_9784*.md"

# 4. Inicie o bot
./run_bot.sh

# 5. No Discord, teste:
/perguntar O que é processo administrativo?
```

### Debug

```python
# Adicione logs no código
from rich.console import Console
console = Console()

console.print(f"[cyan]Debug: {variable}[/cyan]")
console.print_exception()  # Para exceptions
```

## Configuração do Bot no Discord Developer Portal

### 1. Criar Aplicação
1. Acesse https://discord.com/developers/applications
2. Clique em "New Application"
3. Nomeie sua aplicação

### 2. Configurar Bot
1. Vá em "Bot" no menu lateral
2. Clique em "Add Bot"
3. Copie o token (DISCORD_TOKEN)
4. Ative "Message Content Intent"
5. Ative "Server Members Intent"

### 3. OAuth2
1. Vá em "OAuth2" → "URL Generator"
2. Selecione scopes:
   - `bot`
   - `applications.commands`
3. Selecione permissões:
   - Read Messages/View Channels
   - Send Messages
   - Embed Links
   - Use Slash Commands
4. Copie a URL gerada
5. Acesse a URL para adicionar o bot ao servidor

### 4. Intents Necessárias
```python
intents = discord.Intents.default()
intents.message_content = True  # Para ler mensagens
intents.members = True          # Para info de membros
```

## RAG Engine

### Query Manual
```python
from src.bot.core.rag_engine import RAGEngine

engine = RAGEngine()
await engine.initialize()

result = await engine.query("O que é licitação?")
print(result['answer'])
print(result['sources'])
print(result['confidence'])
```

### Busca de Documentos
```python
docs = await engine.search_documents(
    "desapropriação",
    top_k=5,
    threshold=0.7
)

for doc in docs:
    print(doc['metadata']['title'])
    print(doc['similarity'])
```

## Monitoring

### Logs do Bot
```bash
# Veja logs em tempo real
./run_bot.sh

# Ou com mais detalhes
uv run python -m src.bot.main --verbose
```

### Dashboard Admin
```bash
# Inicie dashboard em paralelo
./run_dashboard.sh

# Acesse: http://localhost:8501
```

### Comandos de Monitoramento no Discord
```
/status  # CPU, memória, latência, status RAG
/stats   # Estatísticas de uso (TODO)
```

## Troubleshooting

### Bot Offline
```bash
# Verifique processo
ps aux | grep "src.bot.main"

# Verifique token
echo $DISCORD_TOKEN

# Verifique intents no Developer Portal
```

### Comandos Slash Não Aparecem
```bash
# No Discord, execute:
/sync

# Ou force global sync no código:
await bot.tree.sync()
```

### RAG Não Funciona
```bash
# Teste conexões
uv run python -c "from src.bot.core.rag_engine import RAGEngine; import asyncio; e = RAGEngine(); asyncio.run(e.initialize())"

# Verifique Supabase
# Dashboard → Table Editor → documents
```

### Rate Limit Errors
- OpenAI: 500 RPM embeddings, 200 RPM chat
- Adicione retry logic ou throttling se necessário

## Best Practices

### Comandos
- Use slash commands (/) para comandos principais
- Use prefix commands (!) apenas para comandos simples
- Sempre use `defer()` para operações demoradas
- Forneça feedback visual (embeds, emojis)

### Error Handling
- Sempre catch exceptions
- Envie mensagens de erro claras
- Use embeds vermelhos para erros
- Logs detalhados no console

### Performance
- Cache resultados quando possível
- Use async/await corretamente
- Limite tamanho de respostas
- Pagine resultados longos

### Segurança
- Valide inputs do usuário
- Sanitize conteúdo de embeds
- Rate limit por usuário se necessário
- Admin commands requerem permissão

## Resources

- [discord.py docs](https://discordpy.readthedocs.io)
- [Discord Developer Portal](https://discord.com/developers/docs)
- [Slash Commands Guide](https://discordpy.readthedocs.io/en/stable/interactions/api.html)
