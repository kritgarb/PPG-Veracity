# Projeto de Automação para Análise de Dados de Fotopletismografia (PPG)

## 1. Objetivo

Este projeto foi criado para resolver um desafio comum em pesquisas experimentais: a consolidação de dados brutos dispersos em múltiplos arquivos. O objetivo é transformar dezenas de arquivos CSV, cada um representando uma medição individual, em tabelas de análise robustas e prontas para uso em softwares estatísticos (como R, SPSS, JASP) ou para modelagem em Python.

A automação lida com a complexidade de nomes de arquivos e pastas inconsistentes, extraindo de forma inteligente as informações cruciais e reestruturando os dados em formatos "wide" e "long".

### 1.1 Contexto da Pesquisa

Este projeto é parte de um estudo sobre detecção de mentiras utilizando o dataset Miami University Deception Detection Dataset — MU3D, que contém 320 vídeos de pessoas contando verdades e mentiras. A amostragem possui 80 participantes (40 homens e 40 mulheres) que foram gravados ao contar narrativas sobre relacionamento social (Lloyd et al., 2017).

### 1.2 Tecnologia de Fotopletismografia Remota (rPPG)

A fotopletismografia remota (rPPG) é utilizada para extrair informações fisiológicas relacionadas às oscilações de fluxo sanguíneo a partir da alteração do reflexo de luz pela pele dos participantes (Liu, et al., 2023). Esta técnica não-invasiva permite detectar sinais sutis de estresse e alterações fisiológicas que podem estar associados ao comportamento de mentir.

---

## 2. Funcionalidades Principais

- **Extração Inteligente de Metadados**: Identifica automaticamente o **ID do participante** e as **condições experimentais** (Valência e Veracidade) a partir da estrutura de pastas e nomes de arquivos.
- **Flexibilidade de Nomenclatura**: O sistema é robusto a variações, reconhecendo termos em português e inglês, abreviações e diferentes padrões de formatação (ex: `Positive Lies`, `Positive_Lie`, `PL`).
- **Processamento em Lote**: Processa todos os arquivos CSV de uma vez, calculando as médias das métricas de interesse (`Heart Rate (BPM)`, `Face Movement (avg)`, `Eye Movement (avg)`).
- **Diagnóstico e Depuração**: Gera um relatório (`_diagnostics_unknowns.csv`) que detalha quais arquivos foram processados com sucesso e quais falharam na identificação, permitindo corrigir rapidamente problemas de nomenclatura.
- **Dupla Formatação de Saída**: Produz duas tabelas de análise principais:
    1.  `master_wide.csv`: Formato "largo", com uma linha por participante e colunas para cada combinação de métrica e condição.
    2.  `all_channels_long.csv`: Formato "longo" (ou "tidy"), ideal para análises de medidas repetidas e modelos mistos.

### 2.1 Processamento de Sinais rPPG

O sistema processa dados de fotopletismografia remota (rPPG) extraídos de vídeos faciais, utilizando as seguintes técnicas:

- **Detecção Facial com MediaPipe Face Mesh**: Mapeamento de 468 pontos específicos da face em 3D (landmarks) nas regiões do nariz, olhos, contorno da face e bochechas.
- **Extração de Regiões de Interesse (ROI)**: Seleção automática das áreas faciais com maior sinal pulsátil.
- **Processamento de Canais RGB**: Extração de séries temporais para cada canal de cor (R, G, B), com foco no canal verde (G) que melhor correlaciona-se com a pulsação cardíaca.
- **Melhoria da Razão Sinal-Ruído**: Combinação linear dos componentes de cor com os vetores X=3G-2(R+B) e Y=1.5(R+B)-G, seguida de normalização para isolar o componente pulsátil.
- **Filtragem de Sinal**: Aplicação de filtro passa-banda entre 0,7 e 4Hz (42 a 240 BPM) para eliminar ruídos de variações de luz, movimentos e artefatos musculares.
- **Análise Espectral**: Transformação do sinal para o domínio da frequência via FFT (Transformada Rápida de Fourier) e identificação do pico de frequência cardíaca.

### 2.2 Métricas Extraídas

O sistema extrai e analisa três métricas principais:

- **BPM (Batimentos por Minuto)**: Frequência cardíaca média durante o relato, calculada a partir do pico de frequência do sinal rPPG.
- **Movimento Facial**: Média de movimentação facial detectada pelos landmarks do MediaPipe Face Mesh.
- **Movimento Ocular**: Média de movimentação dos olhos durante o relato, extraída da variação dos landmarks oculares.

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

### 3.1 Categorias Experimentais

Os dados são organizados em quatro categorias experimentais principais, baseadas em um design fatorial 2x2:

1. **Verdade Positiva (Positive Truth - PT)**: Relatos verdadeiros sobre experiências positivas
2. **Mentira Positiva (Positive Lie - PL)**: Relatos falsos sobre experiências positivas
3. **Verdade Negativa (Negative Truth - NT)**: Relatos verdadeiros sobre experiências negativas
4. **Mentira Negativa (Negative Lie - NL)**: Relatos falsos sobre experiências negativas

### 3.2 Processamento de Dados Fisiológicos

O fluxo de processamento dos sinais fisiológicos segue estas etapas:

1. **Extração de ROI**: Detecção facial e seleção das regiões de interesse
2. **Processamento RGB**: Extração das séries temporais de cada canal de cor
3. **Filtragem de Sinal**: Aplicação de filtros para remoção de ruídos
4. **Análise Espectral**: Transformação do sinal via FFT
5. **Cálculo de Métricas**: Extração de BPM, movimento facial e ocular
6. **Consolidação de Dados**: Organização dos resultados por participante e condição experimental

### 3.3 Análise de Variação Temporal

Para cada série temporal extraída, calcula-se a média da taxa de variação absoluta por tempo:

𝑀é𝑑𝑖𝑎 = 1/(𝑁−1) ∑(𝑖=2 até 𝑁) |𝑥𝑖−𝑥𝑖−1|/(𝑡𝑖−𝑡𝑖−1)

Esta métrica permite quantificar a variabilidade dos sinais fisiológicos ao longo do tempo, possibilitando a comparação entre diferentes condições experimentais.

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

## 7. Fundamentação Teórica

### 7.1 Fotopletismografia Remota (rPPG)

A fotopletismografia remota é uma técnica não-invasiva que permite extrair informações sobre o fluxo sanguíneo através da análise de vídeos da pele humana. O princípio básico é que a hemoglobina no sangue absorve luz de forma diferente dependendo da sua oxigenação, criando sutis variações de cor na pele que correspondem ao ciclo cardíaco (Verkruysse, Svaasand & Nelson, 2008).

### 7.2 Processamento de Sinais

O processamento do sinal rPPG envolve várias etapas técnicas:

- **Combinação de Canais RGB**: A técnica CHROM (De Haan & Jeanne, 2013) utiliza combinações lineares dos canais de cor para melhorar a razão sinal-ruído: X=3G-2(R+B) e Y=1.5(R+B)-G.
- **Filtragem Passa-Banda**: Aplicação de filtro entre 0,7 e 4Hz para eliminar ruídos e isolar o componente pulsátil do sinal.
- **Transformada Rápida de Fourier (FFT)**: Conversão do sinal do domínio do tempo para o domínio da frequência, permitindo identificar o pico correspondente à frequência cardíaca.

### 7.3 Detecção Facial com MediaPipe

O MediaPipe Face Mesh é uma solução de machine learning que detecta 468 pontos faciais em 3D, permitindo o rastreamento preciso de movimentos faciais e oculares. Esta tecnologia é fundamental para a extração das regiões de interesse (ROI) utilizadas na análise rPPG e para a quantificação dos movimentos faciais e oculares durante os relatos.

### 7.4 Aplicação na Detecção de Mentiras

A combinação de métricas fisiológicas (BPM) e comportamentais (movimento facial e ocular) permite uma abordagem multimodal para a detecção de mentiras. Estudos anteriores sugerem que mentir pode produzir alterações sutis na frequência cardíaca e aumentar micro-expressões faciais devido à carga cognitiva e emocional associada ao engano (Lloyd et al., 2017).
