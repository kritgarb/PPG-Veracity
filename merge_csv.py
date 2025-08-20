import os
import pandas as pd
import re

def merge_csv_files(root_folder):
    all_files = []
    for dirpath, _, filenames in os.walk(root_folder):
        for filename in filenames:
            if filename.endswith('.csv'):
                all_files.append(os.path.join(dirpath, filename))

    if not all_files:
        print("Nenhum CSV encontrado.")
        return

    df_list = []
    
    for file in all_files:
        try:
            df = pd.read_csv(file)
            fname = os.path.basename(file)
            match = re.search(r"PPG_([A-Z]{2}\d{3})", fname)
            if match:
                participant_id = match.group(1)
            else:
                participant_id = "UNKNOWN"

            group_name = os.path.basename(os.path.dirname(file))
            valence, veracity = parse_group_name(group_name)

            df["Participant"] = participant_id
            df["Valence"] = valence
            df["Veracity"] = veracity
            df["Condition"] = f"{valence} {veracity}"

            df_list.append(df)

        except Exception as e:
            print(f"Erro lendo {file}: {e}")

    if not df_list:
        print("Nada para juntar.")
        return

    merged_df = pd.concat(df_list, ignore_index=True)
    create_wide_tables(merged_df, root_folder)


def create_wide_tables(df, root_folder):
    """
    Cria 3 tabelas wide: BPM, Face, Eye
    Linhas = participantes
    Colunas = condições
    """
    metrics = {
        "Heart Rate (BPM)": "bpm_summary.csv",
        "Face Movement (avg)": "face_summary.csv",
        "Eye Movement (avg)": "eye_summary.csv"
    }

    for metric, fname in metrics.items():
        if metric not in df.columns:
            print(f"Aviso: {metric} não encontrado nos dados.")
            continue

        summary = (
            df.groupby(["Participant", "Condition"])[metric]
            .mean()
            .reset_index()
        )

        wide = summary.pivot(index="Participant", columns="Condition", values=metric)
        ordered_cols = ["Positive Lie", "Negative Lie", "Positive Truth", "Negative Truth"]
        wide = wide.reindex(columns=ordered_cols)
        wide = wide.reset_index()
        outpath = os.path.join(root_folder, fname)
        wide.to_csv(outpath, index=False)
        print(f"Tabela criada: {fname}")


def parse_group_name(group_name):
    """
    Extrai Valence e Veracity de nomes tipo:
    'Positive Lies', 'Negative Truth', etc.
    """
    original_name = group_name
    group_name = group_name.lower().replace(" ", "")

    if "positive" in group_name:
        valence = "Positive"
    elif "negative" in group_name:
        valence = "Negative"
    else:
        valence = "Unknown"
        print(f"⚠️ Valence não identificado: {original_name}")

    if "lie" in group_name:
        veracity = "Lie"
    elif "truth" in group_name:
        veracity = "Truth"
    else:
        veracity = "Unknown"
        print(f"⚠️ Veracity não identificado: {original_name}")

    return valence, veracity


if __name__ == "__main__":
    root_folder = os.getcwd()
    merge_csv_files(root_folder)
