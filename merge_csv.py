import os
import pandas as pd
import re

def merge_csv_files(root_folder):
    """
    Processa todos os CSVs e cria uma tabela única com todos os participantes
    """
    all_files = []
    
    # Coleta todos os arquivos CSV
    for dirpath, _, filenames in os.walk(root_folder):
        for filename in filenames:
            if filename.endswith('.csv'):
                all_files.append(os.path.join(dirpath, filename))
    
    if not all_files:
        print("Nenhum CSV encontrado.")
        return
    
    print(f"Encontrados {len(all_files)} arquivos CSV")
    
    df_list = []
    
    for file in all_files:
        try:
            df = pd.read_csv(file)
            
            # Extrai o ID do participante do nome do arquivo
            fname = os.path.basename(file)
            match = re.search(r"PPG_([A-Z]{2}\d{3})", fname)
            if match:
                participant_id = match.group(1)
            else:
                participant_id = "UNKNOWN"
            
            # Extrai condição do nome da pasta
            group_name = os.path.basename(os.path.dirname(file))
            valence, veracity = parse_group_name(group_name)
            
            # Adiciona informações de identificação
            df["Participant"] = participant_id
            df["Valence"] = valence
            df["Veracity"] = veracity
            df["Condition"] = f"{valence} {veracity}"
            df["Source_File"] = fname
            
            df_list.append(df)
            
        except Exception as e:
            print(f"Erro lendo {file}: {e}")
    
    if not df_list:
        print("Nada para processar.")
        return
    
    # Combina todos os dados
    merged_df = pd.concat(df_list, ignore_index=True)
    print(f"Total de registros processados: {len(merged_df)}")
    
    # Cria a tabela consolidada única
    create_master_table(merged_df, root_folder)

def create_master_table(df, root_folder):
    """
    Cria UMA tabela única com todos os participantes e todas as métricas
    Cada linha = um participante
    Colunas = todas as métricas para todas as condições
    """
    
    # Define as métricas principais que queremos analisar
    metrics = ["Heart Rate (BPM)", "Face Movement (avg)", "Eye Movement (avg)"]
    conditions = ["Positive Lie", "Negative Lie", "Positive Truth", "Negative Truth"]
    
    # Calcula médias por participante e condição
    participant_summary = df.groupby(["Participant", "Condition"]).agg({
        "Heart Rate (BPM)": "mean",
        "Face Movement (avg)": "mean", 
        "Eye Movement (avg)": "mean"
    }).reset_index()
    
    # Lista para armazenar todas as colunas da tabela final
    all_columns = ["Participant"]
    
    # Para cada métrica e cada condição, cria uma coluna
    for metric in metrics:
        for condition in conditions:
            col_name = f"{metric}_{condition.replace(' ', '_')}"
            all_columns.append(col_name)
    
    # Obtém lista única de participantes
    all_participants = sorted(df["Participant"].unique())
    print(f"Total de participantes encontrados: {len(all_participants)}")
    
    # Cria DataFrame final
    master_table = pd.DataFrame(columns=all_columns)
    master_table["Participant"] = all_participants
    
    # Preenche os dados
    for _, row in participant_summary.iterrows():
        participant = row["Participant"]
        condition = row["Condition"]
        
        # Encontra a linha do participante na tabela master
        participant_idx = master_table[master_table["Participant"] == participant].index[0]
        
        # Preenche as colunas para cada métrica
        for metric in metrics:
            col_name = f"{metric}_{condition.replace(' ', '_')}"
            if col_name in master_table.columns:
                master_table.loc[participant_idx, col_name] = row[metric]
    
    # Salva a tabela consolidada
    output_path = os.path.join(root_folder, "master_analysis_table.csv")
    master_table.to_csv(output_path, index=False)
    
    print(f"\n📊 TABELA MASTER CRIADA!")
    print(f"📁 Arquivo: master_analysis_table.csv")
    print(f"📏 Dimensões: {master_table.shape[0]} linhas x {master_table.shape[1]} colunas")
    print(f"👥 Participantes: {len(all_participants)}")
    
    # Mostra preview da tabela
    print("\n🔍 PREVIEW DA TABELA:")
    print("Primeiras colunas:")
    print(master_table.iloc[:5, :6].to_string())
    
    # Estatísticas básicas
    print(f"\n📈 ESTATÍSTICAS:")
    print(f"- Total de participantes: {len(all_participants)}")
    print(f"- Total de colunas: {master_table.shape[1]}")
    print(f"- Colunas por métrica: {len(conditions)} condições")
    print(f"- Métricas analisadas: {len(metrics)}")
    
    # Verifica dados faltantes
    missing_data = master_table.isnull().sum().sum()
    total_cells = master_table.shape[0] * master_table.shape[1]
    print(f"- Dados completos: {((total_cells - missing_data) / total_cells * 100):.1f}%")
    
    return master_table

def parse_group_name(group_name):
    """
    Extrai Valence e Veracity de nomes de pastas
    """
    original_name = group_name
    group_name = group_name.lower().replace(" ", "")
    
    # Determina Valence
    if "positive" in group_name:
        valence = "Positive"
    elif "negative" in group_name:
        valence = "Negative"
    else:
        valence = "Unknown"
        print(f"⚠️ Valence não identificado: {original_name}")
    
    # Determina Veracity
    if "lie" in group_name:
        veracity = "Lie"
    elif "truth" in group_name:
        veracity = "Truth"
    else:
        veracity = "Unknown"
        print(f"⚠️ Veracity não identificado: {original_name}")
    
    return valence, veracity

def analyze_master_table(root_folder):
    """
    Função extra para analisar a tabela master criada
    """
    file_path = os.path.join(root_folder, "master_analysis_table.csv")
    
    if not os.path.exists(file_path):
        print("Tabela master não encontrada. Execute primeiro merge_csv_files()")
        return
    
    df = pd.read_csv(file_path)
    
    print("🔬 ANÁLISE DA TABELA MASTER")
    print(f"📊 Dimensões: {df.shape}")
    print(f"👥 Participantes: {df['Participant'].nunique()}")
    
    # Lista todas as colunas por métrica
    metrics = ["Heart Rate (BPM)", "Face Movement (avg)", "Eye Movement (avg)"]
    
    for metric in metrics:
        metric_cols = [col for col in df.columns if metric in col]
        print(f"\n{metric}:")
        for col in metric_cols:
            non_null = df[col].notna().sum()
            print(f"  - {col}: {non_null} valores")

if __name__ == "__main__":
    root_folder = os.getcwd()  # ou o caminho para sua pasta de dados
    
    # Executa a consolidação
    merge_csv_files(root_folder)
    
    # Opcionalmente, analisa a tabela criada
    analyze_master_table(root_folder)
