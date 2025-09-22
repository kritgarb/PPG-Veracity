import os
import re
import pandas as pd
from collections import Counter

# ===========================
# Config
# ===========================
COLUMN_ALIASES = {
    "bpm": [
        "Heart Rate (BPM)", "BPM", "HeartRate", "Heart_Rate_BPM",
        "heart_rate_bpm", "hr_bpm"
    ],
    "face": [
        "Face Movement (avg)", "Face_Movement", "Face Movement",
        "face_movement_avg", "face_avg"
    ],
    "eye": [
        "Eye Movement (avg)", "Eye_Movement", "Eye Movement",
        "eye_movement_avg", "eye_avg"
    ],
}

# Ordem fixa pedida para as colunas wide
DESIRED_GROUP_COLS = ["Positive Lie", "Negative Lie", "Positive Truth", "Negative Truth"]

# Padrões ampliados para PT/EN/abreviações (singular/plural)
VALENCE_PATTERNS = {
    "Positive": [r"\bpos(itive)?s?\b", r"\bpositivo?s?\b", r"\bplus\b", r"\b\+ve\b"],
    "Negative": [r"\bneg(ative)?s?\b", r"\bnegativo?s?\b", r"\bminus\b", r"\b\-ve\b"],
}
VERACITY_PATTERNS = {
    "Truth": [
        r"\btruth(s)?\b", r"\bverdade(s)?\b", r"\bvdd\b", r"\btrue\b",
        r"(?<!\w)T(?!\w)", r"\btruthful(ness)?\b", r"\bhonest(y)?\b", r"\breal\b"
    ],
    "Lie": [
        r"\blie(s)?\b", r"\bmentira(s)?\b", r"\bmt\b", r"\bfalse\b",
        r"(?<!\w)F(?!\w)", r"\blying\b", r"\bdecept(ion|ive)\b", r"\bfake\b"
    ],
}

# Códigos curtos no caminho/arquivo (PL, PT, NL, NT)
SHORT_CODE_MAP = {
    "PL": ("Positive", "Lie"),
    "PT": ("Positive", "Truth"),
    "NL": ("Negative", "Lie"),
    "NT": ("Negative", "Truth"),
}
# casa 'PL', 'PT', 'NL', 'NT' quando não estão colados a letras
SHORT_CODE_REGEX = re.compile(r"(?<![A-Za-z])(P[LT]|N[LT])(?![A-Za-z])", re.IGNORECASE)

# Padrões de ID de participante (2 letras + 2–3 dígitos)
PARTICIPANT_PATTERNS = [
    r"PPG_([A-Z]{2}\d{2,3})",       # PPG_WM13, PPG_BF001
    r"PPG[-_\s]?([A-Z]{2}\d{2,3})", # PPG-WM13, PPG BF001
    r"\b([A-Z]{2}\d{2,3})\b",       # WM13, BF001 solto
]

# ===========================
# Helpers de parsing/IO
# ===========================
def match_any(patterns, text):
    for pat in patterns:
        if re.search(pat, text, flags=re.I):
            return True
    return False

def walk_csvs(root_folder: str, ignore_dirs=("summaries",)):
    """Itera CSVs ignorando diretórios de saída."""
    ignore = {d.lower() for d in ignore_dirs}
    for dirpath, dirnames, filenames in os.walk(root_folder, topdown=True):
        dirnames[:] = [d for d in dirnames if d.lower() not in ignore]
        for filename in filenames:
            if filename.lower().endswith(".csv"):
                yield os.path.join(dirpath, filename), dirpath, filename

def smart_extract_participant_id(fname: str, dirpath: str):
    """
    Extrai e padroniza ID (ex.: BF001, WM13 -> WM013) do nome do arquivo ou caminho.
    """
    base = os.path.basename(fname)
    extracted_id = None

    # 1. Tenta direto no nome do arquivo com padrões regex
    if not extracted_id:
        for pat in PARTICIPANT_PATTERNS:
            m = re.search(pat, base)
            if m:
                extracted_id = m.group(1).upper()
                break

    # 2. Tenta por tokens no nome do arquivo (separados por _, -, espaço, .)
    if not extracted_id:
        tokens = re.split(r"[-_\s\.]+", base)
        for t in tokens:
            if re.match(r"^[A-Z]{2}\d{2,3}$", t.upper()):
                extracted_id = t.upper()
                break

    # 3. Tenta no caminho completo (flatten)
    if not extracted_id:
        flat_path = dirpath.replace(os.sep, "_")
        for pat in PARTICIPANT_PATTERNS:
            m = re.search(pat, flat_path)
            if m:
                extracted_id = m.group(1).upper()
                break

    # 4. Tenta por tokens no caminho
    if not extracted_id:
        path_tokens = re.split(r"[-_\s\.\/\\]+", dirpath)
        for t in path_tokens:
            if re.match(r"^[A-Z]{2}\d{2,3}$", t.upper()):
                extracted_id = t.upper()
                break

    # Se encontrou um ID, padroniza e retorna
    if extracted_id:
        # Garante que IDs com 2 letras e 2 dígitos recebam um zero (ex: WM13 -> WM013)
        if len(extracted_id) == 4 and extracted_id[:2].isalpha() and extracted_id[2:].isdigit():
            return f"{extracted_id[:2]}0{extracted_id[2:]}"
        return extracted_id

    return "UNKNOWN"

def parse_group_name_smart(dirpath: str, filename: str = ""):
    """
    Extrai (Valence, Veracity) olhando:
    - códigos curtos (PL/PT/NL/NT) no filename e no caminho,
    - até 5 níveis de diretórios,
    - PT/EN no singular/plural.
    Retorna (valence, veracity, matched_component).
    """
    # 1) códigos curtos no filename
    if filename:
        m = SHORT_CODE_REGEX.search(filename)
        if m:
            code = m.group(1).upper()
            if code in SHORT_CODE_MAP:
                v1, v2 = SHORT_CODE_MAP[code]
                return v1, v2, f"{filename} [{code}]"

    # 2) códigos curtos no caminho
    flat_path = dirpath.replace(os.sep, " ")
    m = SHORT_CODE_REGEX.search(flat_path)
    if m:
        code = m.group(1).upper()
        if code in SHORT_CODE_MAP:
            v1, v2 = SHORT_CODE_MAP[code]
            return v1, v2, f"path [{code}]"

    # 3) varre até 5 níveis
    parts = []
    d = dirpath
    for _ in range(5):
        b = os.path.basename(d)
        if b:
            parts.append(b)
        new_d = os.path.dirname(d)
        if not new_d or new_d == d:
            break
        d = new_d

    candidates = []
    if filename:
        candidates.append(filename)
    candidates.append(" ".join(parts))  # tudo junto
    candidates.extend(parts)            # cada parte separada

    valence = None
    veracity = None
    matched_component = None

    for txt in candidates:
        low = txt.lower()

        if valence is None:
            if match_any(VALENCE_PATTERNS["Positive"], low):
                valence, matched_component = "Positive", txt
            elif match_any(VALENCE_PATTERNS["Negative"], low):
                valence, matched_component = "Negative", txt

        if veracity is None:
            if match_any(VERACITY_PATTERNS["Truth"], low):
                veracity = "Truth"
                if matched_component is None:
                    matched_component = txt
            elif match_any(VERACITY_PATTERNS["Lie"], low):
                veracity = "Lie"
                if matched_component is None:
                    matched_component = txt

        if valence and veracity:
            break

    return (valence or "Unknown", veracity or "Unknown", matched_component)

def load_conditions_mapping(csv_path: str):
    """
    CSV opcional com colunas: folder_key,valence,veracity
    Ex:
      folder_key,valence,veracity
      PT,Positive,Truth
      PL,Positive,Lie
      NT,Negative,Truth
      NL,Negative,Lie
      pos_mentira,Positive,Lie
    """
    if not os.path.exists(csv_path):
        return {}
    df = pd.read_csv(csv_path)
    mp = {}
    for _, row in df.iterrows():
        key = str(row["folder_key"]).strip().lower()
        mp[key] = (str(row["valence"]).strip().title(), str(row["veracity"]).strip().title())
    return mp

def apply_conditions_mapping(valence: str, veracity: str, path_parts, mapping: dict):
    """Override via mapping.csv usando nome da pasta atual/pai ou ambos concatenados."""
    if not mapping:
        return valence, veracity, None
    for p in path_parts:
        key = p.strip().lower()
        if key in mapping:
            v1, v2 = mapping[key]
            return v1, v2, p
    joined = "/".join([x.strip().lower() for x in path_parts])
    if joined in mapping:
        v1, v2 = mapping[joined]
        return v1, v2, joined
    return valence, veracity, None

def find_first_present_column(df: pd.DataFrame, candidates):
    # match exato (case-insensitive)
    norm_map = {col: col.strip().lower() for col in df.columns}
    for col, norm in norm_map.items():
        for c in candidates:
            if norm == c.strip().lower():
                return col
    # fallback por "contains"
    for c in candidates:
        found = [col for col in df.columns if c.strip().lower() in col.strip().lower()]
        if found:
            return found[0]
    return None

def load_target_series(file_path: str, target: str):
    """Lê CSV e retorna a Série numérica da coluna alvo + nome padronizado."""
    try:
        df = pd.read_csv(file_path, low_memory=False)
    except Exception as e:
        print(f"Erro lendo {file_path}: {e}")
        return None, None

    col = find_first_present_column(df, COLUMN_ALIASES[target])
    if not col:
        return None, None

    s = pd.to_numeric(df[col], errors="coerce").dropna()
    if s.empty:
        return None, None

    out_col = {"bpm": "BPM_Mean", "face": "Face_Movement_Mean", "eye": "Eye_Movement_Mean"}[target]
    return s, out_col

# ===========================
# Diagnóstico de Unknowns
# ===========================
def audit_unknowns(root_folder: str, mapping_csv: str = None):
    """
    Varre CSVs (exceto summaries/), tenta extrair Participant/Valence/Veracity,
    reporta Unknowns/motivos. Salva summaries/_diagnostics_unknowns.csv
    """
    mapping = load_conditions_mapping(mapping_csv) if mapping_csv else {}
    rows = []
    seen = Counter()

    ignore = {"summaries"}
    for dirpath, dirnames, filenames in os.walk(root_folder, topdown=True):
        dirnames[:] = [d for d in dirnames if d.lower() not in ignore]
        for fn in filenames:
            if not fn.lower().endswith(".csv"):
                continue

            participant = smart_extract_participant_id(fn, dirpath)
            v1, v2, matched = parse_group_name_smart(dirpath, fn)

            parts = [os.path.basename(dirpath), os.path.basename(os.path.dirname(dirpath))]
            v1, v2, mapped_from = apply_conditions_mapping(v1, v2, parts, mapping)

            reason = []
            if participant == "UNKNOWN":
                reason.append("participant_id_not_found")
            if v1 == "Unknown":
                reason.append("valence_not_found")
            if v2 == "Unknown":
                reason.append("veracity_not_found")

            rows.append({
                "File": fn,
                "Dir": dirpath,
                "Participant": participant,
                "Valence": v1,
                "Veracity": v2,
                "Matched_Component": mapped_from or matched or "",
                "Reason": "|".join(reason) if reason else ""
            })
            seen.update(reason or ["ok"])

    diag = pd.DataFrame(rows)
    os.makedirs(os.path.join(root_folder, "summaries"), exist_ok=True)
    outp = os.path.join(root_folder, "summaries", "_diagnostics_unknowns.csv")
    diag.to_csv(outp, index=False, encoding="utf-8")
    return diag

# ===========================
# Summaries (formato wide)
# ===========================
def create_modality_summary(root_folder: str, target: str, mapping_csv: str = None, drop_unknown=True):
    """
    target ∈ {'bpm','face','eye'}
    Saída (wide): Participant | Positive Lie | Negative Lie | Positive Truth | Negative Truth
    - drop_unknown: se True, remove Unknowns antes do pivot (recomendado p/ análise)
    """
    mapping = load_conditions_mapping(mapping_csv) if mapping_csv else {}
    rows = []

    for file_path, dirpath, filename in walk_csvs(root_folder):
        series, out_col = load_target_series(file_path, target)
        if series is None:
            continue

        participant_id = smart_extract_participant_id(filename, dirpath)
        v1, v2, _ = parse_group_name_smart(dirpath, filename)

        # aplica mapping com pasta atual e pai
        parts = [os.path.basename(dirpath), os.path.basename(os.path.dirname(dirpath))]
        v1, v2, _mapped = apply_conditions_mapping(v1, v2, parts, mapping)

        group = f"{v1} {v2}"
        mean_val = series.mean()

        rows.append({
            "Participant": participant_id,
            "Group": group,
            out_col: mean_val
        })

    if not rows:
        print(f"Nada encontrado para '{target}'. Verifique nomes de colunas/arquivos.")
        return None

    df = pd.DataFrame(rows)

    # sinaliza/filtra Unknowns
    unknown_mask = df["Group"].str.contains("Unknown", na=False)
    if unknown_mask.any():
        print(f"{unknown_mask.sum()} linhas com Group=Unknown* detectadas em {target}. Veja summaries/_diagnostics_unknowns.csv")
        if drop_unknown:
            df = df[~unknown_mask].copy()

    if df.empty:
        print(f"Após filtrar Unknown, não restaram dados para '{target}'.")
        return None

    metric_col = [c for c in df.columns if c.endswith("_Mean")][0]
    df = df.groupby(["Participant", "Group"], as_index=False)[metric_col].mean()

    pivot = df.pivot(index="Participant", columns="Group", values=metric_col)

    # Garante colunas e ordem fixa
    for c in DESIRED_GROUP_COLS:
        if c not in pivot.columns:
            pivot[c] = pd.NA
    pivot = pivot[DESIRED_GROUP_COLS]

    # Tipagem/round
    for c in DESIRED_GROUP_COLS:
        pivot[c] = pd.to_numeric(pivot[c], errors="coerce")
    pivot = pivot.round(6).reset_index()

    # Salva
    out_dir = os.path.join(root_folder, "summaries")
    os.makedirs(out_dir, exist_ok=True)
    out_name = {"bpm": "bpm_summary.csv", "face": "face_summary.csv", "eye": "eye_summary.csv"}[target]
    out_path = os.path.join(out_dir, out_name)
    pivot.to_csv(out_path, index=False, encoding="utf-8")

    return pivot

def create_all_summaries(root_folder: str, mapping_csv: str = None, drop_unknown=True):
    pivots = {}
    for t in ["bpm", "face", "eye"]:
        pivots[t] = create_modality_summary(root_folder, t, mapping_csv=mapping_csv, drop_unknown=drop_unknown)
    print("Summaries finalizados.\n")
    return pivots

# ===========================
# Master wide (merge 3 tabelas)
# ===========================
def build_master_wide(root_folder: str):
    """
    Junta as 3 tabelas wide adicionando sufixos por modalidade:
    Positive Lie_BPM, ..., Negative Truth_EYE, etc.
    """
    base = os.path.join(root_folder, "summaries")
    paths = {
        "bpm": os.path.join(base, "bpm_summary.csv"),
        "face": os.path.join(base, "face_summary.csv"),
        "eye": os.path.join(base, "eye_summary.csv"),
    }

    def _rename_with_suffix(df, suffix):
        rename_map = {c: f"{c}_{suffix}" for c in DESIRED_GROUP_COLS if c in df.columns}
        return df.rename(columns=rename_map)

    dfs = {}
    for key in ["bpm", "face", "eye"]:
        if os.path.exists(paths[key]):
            df = pd.read_csv(paths[key])
            dfs[key] = _rename_with_suffix(df, key.upper())
        else:
            dfs[key] = None

    master = None
    for key in ["bpm", "face", "eye"]:
        dfk = dfs[key]
        if dfk is None:
            continue
        if master is None:
            master = dfk
        else:
            master = master.merge(dfk, on="Participant", how="outer")

    if master is None:
        print("Não foi possível montar o master_wide (nenhum summary encontrado).")
        return None

    ordered_cols = ["Participant"]
    for suffix in ["BPM", "FACE", "EYE"]:
        ordered_cols += [f"{c}_{suffix}" for c in DESIRED_GROUP_COLS]
    ordered_cols = [c for c in ordered_cols if c in master.columns]
    master = master[ordered_cols]

    numeric_cols = [c for c in master.columns if c != "Participant"]
    master[numeric_cols] = master[numeric_cols].apply(pd.to_numeric, errors="coerce").round(6)

    out_path = os.path.join(base, "master_wide.csv")
    master.to_csv(out_path, index=False, encoding="utf-8")
    return master

if __name__ == "__main__":
    # Apontar para a raiz dos dados
    root_folder = os.getcwd()

    # cria summaries/conditions_mapping.csv se tiver siglas custom (PT/PL/NT/NL etc.)
    mapping_csv = os.path.join(root_folder, "summaries", "conditions_mapping.csv")

    # Auditoria: mostra quem virou Unknown e por quê
    audit_unknowns(root_folder, mapping_csv=mapping_csv)

    # Gera summaries wide por modalidade (filtra Unknown para não contaminar as médias)
    create_all_summaries(root_folder, mapping_csv=mapping_csv, drop_unknown=True)

    # Constrói o master_wide com sufixos
    build_master_wide(root_folder)
