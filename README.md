# Projeto de Análise de Dados de Fotopletismografia (PPG)

Este projeto foi desenvolvido para automatizar o processamento e a análise de dados de PPG coletados em um experimento sobre detecção de mentiras, envolvendo diferentes condições de valência (positiva/negativa) e veracidade (mentira/verdade).

##  Visão Geral

O objetivo principal é consolidar múltiplos arquivos CSV, cada um contendo dados de um participante em uma condição específica, em uma única tabela de análise (`master_analysis_table.csv`). Esta tabela é formatada para facilitar análises estatísticas subsequentes, com uma linha por participante e colunas representando as métricas fisiológicas em cada condição experimental.

## Estrutura de Pastas

Para que o script funcione corretamente, os arquivos de dados brutos (`.csv`) devem ser organizados na seguinte estrutura de pastas:

```
/
├── merge_csv.py
├── master_analysis_table.csv  (gerado pelo script)
├── README.md
|
├── Negative Lies/
│   ├── PPG_BF001_2NL_....csv
│   └── ...
|
├── Negative Truth/
│   ├── PPG_BF001_3NT_....csv
│   └── ...
|
├── Positive Lies/
│   ├── PPG_BF001_4PL_....csv
│   └── ...
|
└── Positive Truth/
    ├── PPG_BF001_1PT_....csv
    └── ...
```

O nome de cada subpasta é usado para identificar a condição experimental (Valência e Veracidade).

## Como Usar

### Pré-requisitos

- Python 3.x
- Biblioteca `pandas`

### Instalação

Se você não tiver a biblioteca `pandas` instalada, pode instalá-la usando `pip`:

```bash
pip install pandas
```

### Execução

1.  Coloque o script `merge_csv.py` na pasta raiz do projeto, conforme a estrutura mostrada acima.
2.  Abra um terminal ou prompt de comando nessa pasta.
3.  Execute o script com o seguinte comando:

```bash
python merge_csv.py
```

O script irá processar todos os arquivos, exibir um resumo no console e gerar o arquivo `master_analysis_table.csv` na pasta raiz.

## Funcionamento do Script (`merge_csv.py`)

O script executa as seguintes etapas:

1.  **Busca de Arquivos**: Percorre recursivamente todas as subpastas em busca de arquivos que terminam com `.csv`.
2.  **Extração de Metadados**: Para cada arquivo encontrado:
    - Lê o arquivo CSV para um DataFrame do `pandas`.
    - Extrai o **ID do participante** (ex: `BF001`) do nome do arquivo usando expressões regulares.
    - Extrai a **condição experimental** a partir do nome da pasta pai (ex: `Positive Lies`).
3.  **Criação de Novas Colunas**: Adiciona colunas ao DataFrame de cada arquivo para identificar o participante e a condição (`Participant`, `Valence`, `Veracity`, `Condition`).
4.  **Consolidação Inicial**: Agrupa todos os DataFrames individuais em uma única tabela longa.
5.  **Criação da Tabela Master**:
    - Calcula a **média** das métricas de interesse (`Heart Rate (BPM)`, `Face Movement (avg)`, `Eye Movement (avg)`) para cada participante em cada uma das quatro condições.
    - Pivota os dados para criar uma tabela em formato "wide", onde cada linha corresponde a um participante único.
    - As colunas são formatadas como `Métrica_Condição` (ex: `Heart Rate (BPM)_Positive_Lie`), contendo o valor médio calculado.
6.  **Geração do Arquivo Final**: Salva a tabela master no arquivo `master_analysis_table.csv`.

## Arquivo de Saída: `master_analysis_table.csv`

O resultado final é uma tabela consolidada, pronta para ser importada em softwares de análise estatística (como R, SPSS, JASP) ou para análises posteriores em Python.

A estrutura do arquivo de saída é a seguinte:

| Participant | Heart Rate (BPM)\_Positive\_Lie | Heart Rate (BPM)\_Negative\_Lie | ... | Eye Movement (avg)\_Negative\_Truth |
| :---------- | :------------------------------ | :------------------------------ | :-- | :---------------------------------- |
| BF001       | 75.4                            | 82.1                            | ... | 0.23                                |
| BF002       | 68.9                            | 77.3                            | ... | 0.19                                |
| ...         | ...                             | ...                             | ... | ...                                 |

