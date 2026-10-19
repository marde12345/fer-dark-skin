from pathlib import Path
import pandas as pd
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import Font, Alignment, PatternFill

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "docs/reports/qc_strict_review_2026-10-19"

wb = Workbook()
wb.remove(wb.active)

HEADER_FILL = PatternFill("solid", fgColor="D9E1F2")
HEADER_FONT = Font(bold=True)


def write_df(ws, df, start_row=1):
    for r in dataframe_to_rows(df, index=False, header=True):
        ws.append(r)
    for cell in ws[start_row]:
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
    for col in ws.columns:
        maxlen = max((len(str(c.value)) if c.value is not None else 0) for c in col)
        ws.column_dimensions[col[0].column_letter].width = min(max(maxlen + 2, 10), 50)


# Threshold_Analysis
thr = pd.read_csv(OUT / "threshold_analysis.csv")
ws = wb.create_sheet("Threshold_Analysis")
ws.append(["Analisis ambang resolusi (min_dim crop ASLI) dan blur_variance -- dihitung dari pool penuh (v1=645, v2=3413) sebelum filter lain. TIDAK ADA ambang yang diadopsi di sini."])
ws.append([])
write_df(ws, thr, start_row=3)

# Funnel_V1
fv1 = pd.read_csv(OUT / "funnel_v1.csv")
fv1_sub = pd.read_csv(OUT / "funnel_v1_landmark_subset.csv")
ws = wb.create_sheet("Funnel_V1")
ws.append(["Funnel v1 -- denominator = 645 (total pool) di semua baris, bukan tahap sebelumnya."])
ws.append(["Frontalitas TIDAK dievaluasi untuk seluruh pool v1 (tidak ada skor tersimpan untuk 645 wajah)."])
ws.append(["Landmark AI (belum direview) HANYA tersedia untuk 104/645 wajah v1 (16.1%); frontalitas dihitung ULANG di bawah KHUSUS untuk 104 wajah ini saja, dengan formula yang SAMA seperti v2 (analyze_frontality_qc_v2.py), menggunakan landmarks_xy dari experiments/EXP-PAP-005/*.json."])
ws.append([])
write_df(ws, fv1, start_row=5)
r2 = ws.max_row + 3
ws.cell(row=r2, column=1, value="Funnel v1 SUBSET (hanya 104 wajah dengan landmark tersedia) -- denominator=104, BUKAN representatif seluruh pool v1")
write_df(ws, fv1_sub, start_row=r2+2)

# Funnel_V2
fv2 = pd.read_csv(OUT / "funnel_v2.csv")
ws = wb.create_sheet("Funnel_V2")
ws.append(["Funnel v2 -- denominator = 3413 (total pool) di semua baris. frontal_bucket tersedia untuk semua baris (dihitung sebelumnya di extraction_v2_2026-10-19)."])
ws.append(["PENTING: pool v2 hanya mencakup ~277.8 detik dari ~5763 detik total video sumber (~4.8%), dan BELUM direview manusia sama sekali."])
ws.append([])
write_df(ws, fv2, start_row=4)

# Comparison_V1_V2
ws = wb.create_sheet("Comparison_V1_V2")
comp_rows = [
    ["Aspek", "v1", "v2"],
    ["Total pool (wajah terdeteksi)", 645, 3413],
    ["Cakupan video sumber", "Full video (durasi penuh direkam)", "~277.8 detik dari ~5763 detik total (~4.8%)"],
    ["Status review manusia", "Sebagian: 26/231 landmark direview, 52/231 label diberikan (delivery v1)", "BELUM ada review manusia sama sekali"],
    ["Status delivery", "231 kandidat FROZEN/APPROVED", "668 kandidat, BELUM direview"],
    ["Frontalitas tersimpan", "TIDAK (hanya 104/645=16.1% punya landmark AI utk dihitung ulang di sini)", "YA, untuk semua 3413 (frontal_bucket)"],
    ["Pass resolusi>=60px", "372/645 (57.67%)", "1964/3413 (57.54%)"],
    ["Pass resolusi>=80px", "261/645 (40.47%)", "1416/3413 (41.49%)"],
    ["Pass resolusi>=96px", "207/645 (32.09%)", "1156/3413 (33.87%)"],
    ["Pass resolusi>=112px", "176/645 (27.29%)", "1005/3413 (29.45%)"],
    ["Pass blur>75", "443/645 (68.68%)", "2233/3413 (65.43%)"],
    ["Pass blur>P75(325.35)", "161/645 (24.96%)", "850/3413 (24.90%)"],
    ["Kandidat B (res>=80 & blur>75)", "142/645 (22.0%)", "N/A tanpa frontal filter -- lihat Threshold_Analysis"],
    ["Kandidat B (res>=80 & blur>75 & frontal)", "N/A (frontal tidak dievaluasi utk full pool)", "448/3413 (13.1%)"],
    ["Catatan penting", "Jumlah kandidat TIDAK boleh dipakai sebagai ukuran kualitas tunggal -- lihat cakupan & review manusia di atas.", ""],
]
for row in comp_rows:
    ws.append(row)
write_df(ws, pd.DataFrame(comp_rows[1:], columns=comp_rows[0]), start_row=1)

# Sample_List (subset representative)
v1s = pd.read_csv(OUT / "v1_pool_full_with_candidateB.csv")
v2s = pd.read_csv(OUT / "v2_pool_full_with_candidateB.csv")
cols_common = ["sample_id", "source_video_id", "frame_timestamp_seconds", "min_dim" if "min_dim" in v1s.columns else "qc_min_dim",
               "qc_blur_variance", "frontal_bucket", "pass_candidate_B", "candidate_B_status"]
v1_small = v1s[["sample_id", "source_video_id", "frame_timestamp_seconds", "min_dim", "qc_blur_variance", "frontal_bucket", "pass_candidate_B", "candidate_B_status"]].copy()
v1_small.insert(0, "pool", "v1")
v2_small = v2s[["sample_id", "source_video_id", "frame_timestamp_seconds", "qc_min_dim", "qc_blur_variance", "frontal_bucket", "pass_candidate_B", "candidate_B_status"]].copy()
v2_small.columns = ["sample_id", "source_video_id", "frame_timestamp_seconds", "min_dim", "qc_blur_variance", "frontal_bucket", "pass_candidate_B", "candidate_B_status"]
v2_small.insert(0, "pool", "v2")

# subset: stratified sample of 150 per pool (all passed + random rejected) to keep file practical, label explicitly
import numpy as np
rng = np.random.default_rng(7)

def stratified_subset(df, n_target=150):
    passed = df[df["pass_candidate_B"]]
    rejected = df[~df["pass_candidate_B"]]
    n_pass = min(len(passed), n_target // 2)
    n_rej = min(len(rejected), n_target - n_pass)
    pick_pass = passed.sample(n=n_pass, random_state=7) if n_pass < len(passed) else passed
    pick_rej = rejected.sample(n=n_rej, random_state=7) if n_rej < len(rejected) else rejected
    return pd.concat([pick_pass, pick_rej]).sort_values("sample_id")

v1_sub = stratified_subset(v1_small)
v2_sub = stratified_subset(v2_small)
sample_list = pd.concat([v1_sub, v2_sub])

ws = wb.create_sheet("Sample_List")
ws.append([f"DISUBSET: ini bukan daftar lengkap (v1 total 645, v2 total 3413). Disajikan subset acak (random_state=7) + SEMUA sampel yang lolos (jika <75), max {len(v1_sub)} baris v1 dan {len(v2_sub)} baris v2, untuk menjaga file tetap praktis dibaca. Daftar LENGKAP ada di CSV: v1_pool_full_with_candidateB.csv dan v2_pool_full_with_candidateB.csv."])
ws.append([])
write_df(ws, sample_list, start_row=3)

wb.save(OUT / "Papuan_V2_QC_Strict_Review.xlsx")
print("xlsx written. rows sample_list:", len(sample_list))
