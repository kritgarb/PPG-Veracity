import os
import pandas as pd

DESIRED_GROUP_COLS = ["Positive Lie", "Negative Lie", "Positive Truth", "Negative Truth"]
CHANNEL_FILES = {
    "BPM":  "bpm_summary.csv",
    "Face": "face_summary.csv",
    "Eye":  "eye_summary.csv",
}

def load_channel_long(base_dir, channel):
    """
    Lê o summary wide do canal e devolve em formato longo:
    Participant | Veracity | Valence | Channel | Value
    """
    path = os.path.join(base_dir, CHANNEL_FILES[channel])
    if not os.path.exists(path):
        print(f"Arquivo não encontrado: {path} — pulando {channel}")
        return pd.DataFrame(columns=["Participant","Veracity","Valence","Channel","Value"])

    df = pd.read_csv(path)

    # garante colunas esperadas; se faltar alguma, cria vazia (NaN)
    for c in DESIRED_GROUP_COLS:
        if c not in df.columns:
            df[c] = pd.NA

    # derrete pro longo
    long = df.melt(
        id_vars=["Participant"],
        value_vars=DESIRED_GROUP_COLS,
        var_name="Group",
        value_name="Value"
    ).dropna(subset=["Value"])

    # separa Group -> Valence / Veracity
    # ex: "Positive Lie" -> Valence="Positive", Veracity="Lie"
    parts = long["Group"].str.split(" ", n=1, expand=True)
    long["Valence"]  = parts[0]
    long["Veracity"] = parts[1]
    long["Channel"]  = channel

    long = long[["Participant", "Veracity", "Valence", "Channel", "Value"]]
    return long

def sort_nicely(df):
    """Ordena como no exemplo: Truth/Lie, Positive/Negative, BPM/Face/Eye."""
    ver_order = pd.CategoricalDtype(categories=["Truth","Lie"], ordered=True)
    val_order = pd.CategoricalDtype(categories=["Positive","Negative"], ordered=True)
    ch_order  = pd.CategoricalDtype(categories=["BPM","Face","Eye"], ordered=True)

    df = df.copy()
    df["Veracity"] = df["Veracity"].astype(ver_order)
    df["Valence"]  = df["Valence"].astype(val_order)
    df["Channel"]  = df["Channel"].astype(ch_order)
    return df.sort_values(["Participant","Veracity","Valence","Channel"]).reset_index(drop=True)

def print_pipe_table(df, max_rows=12):
    """Preview no console com pipes | igual ao print da imagem."""
    cols = ["Participant","Veracity","Valence","Channel","Value"]
    show = df[cols].copy()
    show["Value"] = show["Value"].round(2)  # só estética do preview
    if len(show) > max_rows:
        show = show.head(max_rows)

    # larguras
    widths = {c: max(len(c), show[c].astype(str).map(len).max()) for c in cols}
    header = " | ".join(c.ljust(widths[c]) for c in cols)
    print(header)
    for _, row in show.iterrows():
        print(" | ".join(str(row[c]).ljust(widths[c]) for c in cols))

if __name__ == "__main__":
    root = os.getcwd()
    base = os.path.join(root, "summaries")

    all_long = []
    for channel in ["BPM","Face","Eye"]:
        all_long.append(load_channel_long(base, channel))
    all_long = pd.concat(all_long, ignore_index=True)

    if all_long.empty:
        print("Nada para salvar — verifique se os summaries wide existem em ./summaries/")
    else:
        all_long = sort_nicely(all_long)

        # salva CSV único
        out_path = os.path.join(base, "all_channels_long.csv")
        all_long.to_csv(out_path, index=False, encoding="utf-8")
        print(f"all_channels_long salvo em: {out_path} ({all_long.shape[0]} linhas)")