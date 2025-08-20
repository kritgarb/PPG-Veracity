# Análise de Dados Fisiológicos para Detecção de Mentiras

Este projeto analisa dados de fotopletismografia (PPG) e movimento para identificar marcadores fisiológicos que diferenciam a verdade da mentira em contextos positivos e negativos.

## Estrutura dos Dados

Os dados brutos estão organizados em quatro pastas, representando as condições do experimento:

- `Negative Lies`
- `Negative Truth`
- `Positive Lies`
- `Positive Truth`

Cada arquivo CSV dentro dessas pastas corresponde a um vídeo/ensaio individual. Os nomes de arquivo seguem o padrão:

```
PPG_<ID>_<timestamp>.csv
```

Onde `<ID>` identifica o participante:
- `BF` = Black Female
- `BM` = Black Male
- `WF` = White Female
- `WM` = White Male

**Exemplo:** `PPG_BF001_20250724_113953.csv` → Participante **BF001**.

## Como Reproduzir a Análise

### 1. Instalar Dependências

Certifique-se de que você tem Python instalado. Depois, instale as bibliotecas necessárias:

```bash
pip install pandas matplotlib seaborn scipy
```

### 2. Unificar os Arquivos CSV

O script `merge_csv.py` combina todos os arquivos `.csv` individuais, extraindo automaticamente:

- **Participant**: ID do participante (ex: `BF001`)
- **Valence**: Positiva ou Negativa
- **Veracity**: Verdade ou Mentira
- **Condition**: Combinação de valência + veracidade (ex: `Positive Lie`)

Além disso, o script gera **três tabelas no formato wide**, já preparadas para análise estatística:

- `bpm_summary.csv` – médias da frequência cardíaca (BPM)
- `face_summary.csv` – médias do movimento facial
- `eye_summary.csv` – médias do movimento ocular

Cada tabela tem uma linha por participante e colunas para cada condição experimental:

| Participant | Positive Lie | Negative Lie | Positive Truth | Negative Truth |
|-------------|--------------|--------------|----------------|----------------|
| BF001       | 4.09         | 4.03         | 2.82           | 2.83           |
| BM001       | ...          | ...          | ...            | ...            |

Para executar:

```bash
python merge_csv.py
```

### 3. Gerar Visualizações

O script `visualize_data.py` gera gráficos (como boxplots) para comparar a distribuição das métricas entre os quatro grupos.

```bash
python visualize_data.py
```

### 4. Executar a Análise Estatística

O script `statistical_analysis.py` calcula estatísticas descritivas e realiza testes estatísticos (ex: ANOVA) para verificar diferenças entre os grupos.

```bash
python statistical_analysis.py
```

## Resultados da Análise Estatística (ANOVA)

O teste ANOVA foi usado para determinar se existem diferenças significativas nas médias das métricas fisiológicas entre os quatro grupos. Um p-valor abaixo de 0.05 indica diferença estatisticamente significante.

### Frequência Cardíaca (Heart Rate - BPM)
- **Resultado:** Estatisticamente Significante (p-valor = 0.0000)
- **Observação:** Existem diferenças reais entre os grupos. O grupo "Positive Lies" apresentou a média mais elevada.

### Movimento dos Olhos (Eye Movement - avg)
- **Resultado:** Estatisticamente Significante (p-valor = 0.0007)
- **Observação:** A movimentação dos olhos também varia de forma significativa entre os grupos.

### Movimento Facial (Face Movement - avg)
- **Resultado:** Não Estatisticamente Significante (p-valor = 0.0593)
- **Observação:** Não foram encontradas evidências suficientes para afirmar que o movimento facial difere entre os grupos.

## Conclusão

A análise sugere que a **frequência cardíaca** e o **movimento dos olhos** são os indicadores fisiológicos mais promissores neste conjunto de dados para diferenciar entre os grupos de verdade/mentira. O movimento facial não se mostrou um diferenciador confiável.