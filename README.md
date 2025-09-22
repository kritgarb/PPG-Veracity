# Projeto de Automação para Análise de Dados de Fotopletismografia (PPG)

## 1. Objetivo

Este projeto foi criado para resolver um desafio comum em pesquisas experimentais: a consolidação de dados brutos dispersos em múltiplos arquivos. O objetivo é transformar dezenas de arquivos CSV, cada um representando uma medição individual, em tabelas de análise robustas e prontas para uso em softwares estatísticos (como R, SPSS, JASP) ou para modelagem em Python.

A automação lida com a complexidade de nomes de arquivos e pastas inconsistentes, extraindo de forma inteligente as informações cruciais e reestruturando os dados em formatos "wide" e "long".

---

## 2. Funcionalidades Principais

- **Extração Inteligente de Metadados**: Identifica automaticamente o **ID do participante** e as **condições experimentais** (Valência e Veracidade) a partir da estrutura de pastas e nomes de arquivos.
- **Flexibilidade de Nomenclatura**: O sistema é robusto a variações, reconhecendo termos em português e inglês, abreviações e diferentes padrões de formatação (ex: `Positive Lies`, `Positive_Lie`, `PL`).
- **Processamento em Lote**: Processa todos os arquivos CSV de uma vez, calculando as médias das métricas de interesse (`Heart Rate (BPM)`, `Face Movement (avg)`, `Eye Movement (avg)`).
- **Diagnóstico e Depuração**: Gera um relatório (`_diagnostics_unknowns.csv`) que detalha quais arquivos foram processados com sucesso e quais falharam na identificação, permitindo corrigir rapidamente problemas de nomenclatura.
- **Dupla Formatação de Saída**: Produz duas tabelas de análise principais:
    1.  `master_wide.csv`: Formato "largo", com uma linha por participante e colunas para cada combinação de métrica e condição.
    2.  `all_channels_long.csv`: Formato "longo" (ou "tidy"), ideal para análises de medidas repetidas e modelos mistos.

---

## 3. O Fluxo de Trabalho

O processo transforma os dados brutos em dados prontos para análise em duas etapas principais:

```
[Dados Brutos em .CSV]  -> [Etapa 1: summaries_csv.py] -> [Resumos "Wide" por Métrica] -> [Etapa 2: build_long_table.py] -> [Tabela Final "Long"]
       (Vários arquivos)                                  (bpm_summary.csv, etc.)                                        (all_channels_long.csv)
                                                                   |
                                                                   +-> master_wide.csv
                                                                   +-> _diagnostics_unknowns.csv
```

---

## 4. Guia de Uso

### Pré-requisitos

- Python 3.x
- Biblioteca `pandas`

Se necessário, instale o pandas com o comando:
```bash
pip install pandas
```

### Estrutura de Pastas

Organize seus arquivos `.csv` em subpastas que indiquem a condição experimental. O script é projetado para ser flexível, mas uma estrutura clara é recomendada.

```
/ (Pasta Raiz do Projeto)
├── summaries_csv.py
├── build_long_table.py
├── README.md
|
├── Condição A (ex: Positive Lies)/
│   ├── PPG_BF001_PL_....csv
│   └── ...
|
├── Condição B (ex: Negative Truth)/
│   ├── PPG_BF002_NT_....csv
│   └── ...
|
└── summaries/  (Esta pasta será criada automaticamente)
```

### Execução

**Etapa 1: Gerar os Resumos "Wide" e Diagnósticos**

Abra um terminal na pasta raiz do projeto e execute:

```bash
python summaries_csv.py
```

**O que acontece nesta etapa?**
- O script varre as pastas em busca de arquivos `.csv`.
- Para cada arquivo, ele extrai o ID do participante, a valência e a veracidade.
- Ele calcula a média da métrica principal em cada arquivo.
- Ao final, ele cria a pasta `summaries/` e salva os seguintes arquivos dentro dela:
    - `bpm_summary.csv`, `face_summary.csv`, `eye_summary.csv`: Tabelas "wide" para cada métrica.
    - `master_wide.csv`: Uma fusão das três tabelas acima.
    - `_diagnostics_unknowns.csv`: O relatório de diagnóstico. **Verifique este arquivo se os resultados não forem os esperados.**

**Etapa 2: Construir a Tabela Final "Long"**

Após a primeira etapa ser concluída com sucesso, execute:

```bash
python build_long_table.py
```

**O que acontece nesta etapa?**
- O script lê os resumos individuais (`bpm_summary.csv`, etc.) da pasta `summaries/`.
- Ele "derrete" (unpivots) essas tabelas, transformando-as do formato "wide" para o "long".
- Ele combina tudo em um único arquivo, `all_channels_long.csv`, e o salva na pasta `summaries/`.

---

## 5. Customização e Solução de Problemas

### `summaries_csv.py`

Este script foi projetado para ser adaptável. No topo do arquivo, você encontrará uma seção de configuração que pode ser modificada:

- `COLUMN_ALIASES`: Se seus arquivos CSV usam nomes de coluna diferentes para as métricas (ex: `HR` em vez de `Heart Rate (BPM)`), adicione os novos nomes a estas listas.
- `VALENCE_PATTERNS` e `VERACITY_PATTERNS`: Se você usa termos diferentes para as condições (ex: "Mentira" em vez de "Lie"), adicione novas expressões regulares aqui.
- `PARTICIPANT_PATTERNS`: Se o padrão de ID dos seus participantes for diferente (ex: `Subj_101`), você pode adicionar um novo padrão de regex para capturá-lo.

### Solução de Problemas Comuns

- **"Meus dados não aparecem no arquivo final!"**
    1.  **Verifique `summaries/_diagnostics_unknowns.csv`**.
    2.  Procure por linhas onde a coluna `Reason` não está vazia. Ela lhe dirá se o script não conseguiu identificar o `participant_id`, a `valence` ou a `veracity`.
    3.  Corrija os nomes dos arquivos/pastas ou ajuste os padrões no script `summaries_csv.py` conforme necessário.

- **"O script não está lendo os valores das colunas."**
    1.  Verifique se os nomes das colunas em seus arquivos CSV correspondem a algum dos apelidos definidos em `COLUMN_ALIASES` no script `summaries_csv.py`.
    2.  Adicione os nomes das suas colunas à lista apropriada se eles não estiverem lá.

---

## 6. Descrição dos Arquivos de Saída

Todos os arquivos gerados são salvos na pasta `summaries/`.

- **`_diagnostics_unknowns.csv`**:
    - **Propósito**: Ferramenta de depuração.
    - **Estrutura**: Lista cada arquivo encontrado e mostra o `Participant`, `Valence` e `Veracity` que foram extraídos, junto com o motivo da falha, se houver.

- **`master_wide.csv`**:
    - **Propósito**: Visão geral rápida de todas as métricas por participante.
    - **Estrutura**: Cada linha é um participante. As colunas são as métricas para cada condição (ex: `Positive Lie_BPM`, `Negative Truth_EYE`).

- **`all_channels_long.csv`**:
    - **Propósito**: Análise estatística detalhada (formato "tidy data").
    - **Estrutura**: Cada linha representa a medição de uma única métrica (`Channel`) para um participante em uma única condição.
        - `Participant`: ID do participante.
        - `Veracity`: `Lie` ou `Truth`.
        - `Valence`: `Positive` ou `Negative`.
        - `Channel`: A métrica medida (`BPM`, `Face`, `Eye`).
        - `Value`: O valor médio da métrica para aquela condição.
