# Remoção de Cores em Arquivos DOCX

Este projeto contém um script Python desenvolvido para remover formatações de cores de arquivos DOCX, mantendo a estrutura original e os comentários.

## O que foi feito

Foi criado um script chamado `remove_colors.py` que utiliza a biblioteca `python-docx` para processar o documento. O script realiza as seguintes ações:

1.  **Remove Cores da Fonte**: Define a cor do texto para o padrão (automático/preto).
2.  **Remove Realces (Highlight)**: Remove qualquer cor de realce aplicada ao texto.
3.  **Remove Sombreamento de Fundo**: Limpa a cor de fundo de parágrafos e células de tabelas.
4.  **Preserva Estrutura**: Mantém tabelas, listas, cabeçalhos e comentários intactos.

## Como Usar

### Pré-requisitos

É necessário ter o Python instalado. O script utiliza a biblioteca `python-docx`.

Se estiver usando o ambiente virtual configurado:

```bash
source venv/bin/activate
```

### Executando o Script

O script está configurado para processar o arquivo `Processo Administrativo (Lei 9784).docx`.

Execute o comando:

```bash
python remove_colors.py
```

### Resultado

O arquivo processado será salvo como `Processo Administrativo (Lei 9784)_clean.docx` no mesmo diretório.
