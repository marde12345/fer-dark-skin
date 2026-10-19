from pathlib import Path
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "docs/reports/qc_strict_review_2026-10-19"
SHEETS = OUT / "contact_sheets"

doc = Document()
style = doc.styles["Normal"]
style.font.name = "Calibri"
style.font.size = Pt(11)


def h1(t):
    doc.add_heading(t, level=1)


def h2(t):
    doc.add_heading(t, level=2)


def p(t):
    doc.add_paragraph(t)


def bullet(t):
    doc.add_paragraph(t, style="List Bullet")


doc.add_heading("Tinjauan QC Ketat — Ambang Resolusi Wajah PAPUAN V2", level=0)
p("Tanggal: 2026-10-19. Disusun oleh: reviewer QA independen (persona fer-dataset-reviewer). Status: dokumen kerja untuk mendukung keputusan supervisor, BUKAN keputusan final mengenai ambang QC.")

h1("1. Ringkasan Eksekutif")
p("Inspeksi manual menemukan bahwa sejumlah wajah pada delivery v1 (231 sampel, FROZEN/disetujui) dan kandidat v2 (668 sampel, belum direview) memiliki resolusi piksel ASLI (sebelum di-resize ke 224x224) yang terlalu kecil untuk anotasi ekspresi wajah yang andal. Dokumen ini meninjau ulang ambang resolusi dan ketajaman (blur) secara kuantitatif dari pool penuh (v1: 645 wajah terdeteksi, v2: 3413 wajah terdeteksi) -- bukan hanya dari subset yang sudah lolos filter sebelumnya -- lalu memverifikasinya dengan inspeksi visual langsung (contact sheet).")
p("Catatan istilah: 'min_dim' = sisi terpendek dari crop wajah dalam piksel ASLI, sebelum gambar di-resize ke ukuran standar 224x224 untuk delivery. 'blur_variance' = varians hasil filter Laplacian pada gambar grayscale; angka lebih tinggi = gambar lebih tajam (fokus), angka rendah = gambar buram.")
p("Temuan utama: pada ambang resolusi dan ketajaman yang sama, persentase wajah yang lolos di pool v1 dan v2 SANGAT MIRIP (misalnya di >=80px: v1 40.47%, v2 41.49%). Namun v2 memiliki jumlah ABSOLUT jauh lebih besar karena pool deteksi mentahnya 5.3x lebih besar (3413 vs 645), BUKAN karena kualitas per-wajah lebih baik. v2 juga baru mencakup ~4.8% durasi video sumber dan belum direview manusia sama sekali, sedangkan v1 sudah direview sebagian. Jumlah kandidat yang lebih banyak di v2 TIDAK BOLEH ditafsirkan sebagai cakupan lebih luas atau kualitas lebih tinggi.")
p("Dokumen ini TIDAK mengadopsi satu ambang akhir. Tiga kandidat ambang disajikan dengan trade-off masing-masing (Bagian 6), dan pilot review manusia direkomendasikan sebagai langkah berikutnya sebelum keputusan otomatis diambil.")

h1("2. Metode")
bullet("Sumber data: pool penuh v1 (docs/reports/extraction_audit_2026-10-19/per_face_sample_manifest.csv, 645 baris) dan v2 (docs/reports/extraction_v2_2026-10-19/per_face_sample_manifest_v2_qc.csv, 3413 baris). Kedua manifest ini sudah ada sebelumnya dan diverifikasi ulang di sini, bukan dibuat ulang dari nol.")
bullet("Dimensi ASLI (crop_width/crop_height atau qc_width/qc_height) diverifikasi langsung dengan membuka file gambar nyata menggunakan Python PIL, pada sampel acak (25 gambar v1, 25 gambar v2, plus 15 pasangan asli-vs-resize dari delivery v1 dan v2). Hasil: 0 dari 65 sampel yang diperiksa menunjukkan ketidakcocokan dimensi (lihat dimension_verification_sample.csv).")
bullet("Ambang resolusi yang diuji: sisi terpendek crop ASLI >= 60px, 80px, 96px, 112px.")
bullet("Ambang ketajaman yang diuji (PERBANDINGAN SAJA, tidak diadopsi): blur_variance > 75 (ambang lama yang sudah divalidasi visual sebelumnya) dan blur_variance > 325.3481 (persentil-75 dari distribusi, belum pernah diadopsi).")
bullet("Semua tahap funnel dihitung dari DENOMINATOR YANG SAMA (total pool masing-masing: 645 untuk v1, 3413 untuk v2), bukan dari hasil tahap sebelumnya -- supaya ambang bisa dibandingkan secara adil. Joint pass-rate (kombinasi resolusi x ketajaman x frontalitas) dihitung LANGSUNG dari data, bukan dengan mengalikan persentase masing-masing tahap (karena tahap-tahap ini tidak independen secara statistik).")
bullet("Frontalitas (seberapa menghadap-kamera suatu wajah) untuk v2 sudah tersedia dari analisis sebelumnya (tools/papuan_v2/analyze_frontality_qc_v2.py). Untuk v1, TIDAK ADA skor frontalitas tersimpan untuk pool 645 wajah secara keseluruhan. Namun 104 dari 645 wajah v1 (16.1%) memiliki landmark 68-titik AI (belum direview) dari experiments/EXP-PAP-005/*.json -- untuk 104 wajah INI SAJA, skor frontalitas dihitung ulang dengan FORMULA YANG SAMA PERSIS seperti v2 (offset hidung terhadap titik tengah mata, dinormalisasi jarak antar-mata). Hasil ini TIDAK merepresentasikan seluruh pool v1 dan ditandai terpisah sebagai subset.")
bullet("Inspeksi visual: contact sheet dibuat untuk wajah tepat DI BAWAH vs tepat DI ATAS setiap ambang resolusi (60/80/96/112px), untuk v1 dan v2 terpisah, plus satu sheet perbandingan gabungan pada ambang 80px.")

h1("3. Hasil per Pool")
h2("3.1 Pool v1 (645 wajah terdeteksi)")
tbl_data = [
    ("Ambang resolusi >=60px", "372 / 645 (57.67%)"),
    ("Ambang resolusi >=80px", "261 / 645 (40.47%)"),
    ("Ambang resolusi >=96px", "207 / 645 (32.09%)"),
    ("Ambang resolusi >=112px", "176 / 645 (27.29%)"),
    ("Ambang blur>75 (lama)", "443 / 645 (68.68%)"),
    ("Ambang blur>P75=325.35 (belum diadopsi)", "161 / 645 (24.96%)"),
    ("JOINT res>=80 AND blur>75", "142 / 645 (22.02%)"),
    ("JOINT res>=96 AND blur>75", "104 / 645 (16.12%)"),
    ("JOINT res>=112 AND blur>75", "77 / 645 (11.94%)"),
]
t = doc.add_table(rows=1, cols=2)
t.style = "Light Grid Accent 1"
t.rows[0].cells[0].text = "Metrik"
t.rows[0].cells[1].text = "Hasil"
for a, b in tbl_data:
    row = t.add_row()
    row.cells[0].text = a
    row.cells[1].text = b
p("Frontalitas TIDAK dievaluasi untuk seluruh pool v1 dalam proses sebelumnya. Dari 104/645 wajah (16.1%) yang punya landmark AI, perhitungan ulang dengan formula v2 menghasilkan: FRONTAL 46, NEAR_FRONTAL 29, PROFILE 29 (dari 104). Pada subset 104 ini, JOINT res>=80 AND blur>75 AND frontal = 20/104 (19.23%). Angka ini TIDAK BOLEH digeneralisasi ke seluruh 645 wajah karena subset landmark bukan sampel acak representatif (dipilih dari batch eksperimen tertentu).")
p("Status review manusia: dari 231 kandidat yang sudah masuk delivery v1 (frozen/approved), baru 26/231 memiliki landmark direview manusia dan 52/231 memiliki label ekspresi. Ini adalah status delivery, BUKAN status pool 645 yang diaudit di sini (lihat docs/reports/extraction_audit_2026-10-19 untuk rincian status per-wajah).")

h2("3.2 Pool v2 (3413 wajah terdeteksi)")
tbl_data2 = [
    ("Ambang resolusi >=60px", "1964 / 3413 (57.54%)"),
    ("Ambang resolusi >=80px", "1416 / 3413 (41.49%)"),
    ("Ambang resolusi >=96px", "1156 / 3413 (33.87%)"),
    ("Ambang resolusi >=112px", "1005 / 3413 (29.45%)"),
    ("Ambang blur>75 (lama)", "2233 / 3413 (65.43%)"),
    ("Ambang blur>P75=325.35 (belum diadopsi)", "850 / 3413 (24.90%)"),
    ("Pass frontalitas (FRONTAL/NEAR_FRONTAL)", "2267 / 3413 (66.42%)"),
    ("JOINT res>=80 AND blur>75 AND frontal", "448 / 3413 (13.13%)"),
    ("JOINT res>=96 AND blur>75 AND frontal", "324 / 3413 (9.49%)"),
    ("JOINT res>=112 AND blur>75 AND frontal", "243 / 3413 (7.12%)"),
]
t2 = doc.add_table(rows=1, cols=2)
t2.style = "Light Grid Accent 1"
t2.rows[0].cells[0].text = "Metrik"
t2.rows[0].cells[1].text = "Hasil"
for a, b in tbl_data2:
    row = t2.add_row()
    row.cells[0].text = a
    row.cells[1].text = b
p("PENTING: pool v2 ini hanya mencakup ~277.8 detik dari total ~5763 detik durasi video sumber (~4.8% dari seluruh video) dan 668 kandidat yang sudah lolos filter QC lama BELUM pernah direview manusia sama sekali -- tidak ada landmark yang direview, tidak ada label ekspresi yang diberikan annotator manusia.")

h1("4. Perbandingan v1 vs v2")
p("Pada ambang resolusi dan ketajaman yang identik, tingkat lolos (%) antara v1 dan v2 HAMPIR SAMA (selisih di bawah 2 poin persentase di semua ambang resolusi yang diuji, dan di bawah 4 poin di ambang blur). Ini mengindikasikan bahwa kedua pool punya distribusi kualitas kamera/jarak pengambilan yang serupa -- bukan bahwa v2 'lebih baik'.")
p("Perbedaan jumlah KANDIDAT ABSOLUT (v2 668 vs v1 231 pada delivery saat ini) terutama didorong oleh ukuran pool mentah v2 yang 5.3x lebih besar (3413 vs 645), bukan oleh perbaikan kualitas ekstraksi per-wajah.")
p("v1 sudah melalui proses review manusia parsial (landmark dan label untuk sebagian sampel delivery); v2 belum sama sekali. Karena itu, v2 TIDAK dapat dianggap 'siap pakai' hanya berdasarkan jumlah kandidat yang lolos filter otomatis -- review manusia (pilot) tetap diperlukan sebelum keputusan apa pun mengenai kelayakan v2 untuk anotasi penuh.")
p("Cakupan video: v1 diambil dari rekaman penuh; v2 baru mencakup sebagian kecil (~4.8%) dari total durasi video sumber yang tersedia. v2 TIDAK merepresentasikan cakupan temporal/konten penuh dari video sumber.")

h1("5. Contoh Kasus Visual")
p("Contact sheet berikut membandingkan wajah tepat di bawah vs tepat di atas masing-masing ambang resolusi. File PNG resolusi penuh tersedia di docs/reports/qc_strict_review_2026-10-19/contact_sheets/.")

for fname, caption in [
    ("v1_threshold_60px.png", "v1 pada ambang 60px: pada ~59px, wajah sudah sangat kecil; detail mata/mulut sulit dibedakan pada beberapa sampel (meski blur_variance bisa tinggi karena tekstur rambut/latar, bukan ketajaman wajah itu sendiri)."),
    ("v1_threshold_80px.png", "v1 pada ambang 80px: pada ~79-80px, fitur wajah (mata, hidung, mulut) mulai cukup jelas dibedakan, meski detail halus (kerutan, arah pandang presisi) masih terbatas."),
    ("v1_threshold_112px.png", "v1 pada ambang 112px: fitur wajah tampak jelas dan dapat dianotasi dengan percaya diri lebih tinggi pada sebagian besar sampel."),
    ("v2_threshold_60px.png", "v2 pada ambang 60px: pola serupa dengan v1 -- wajah sangat kecil, beberapa sudut profil, detail ekspresi sulit dinilai."),
    ("v2_threshold_80px.png", "v2 pada ambang 80px: kualitas visual sebanding dengan v1 pada ambang yang sama."),
    ("comparison_v1_v2_80px.png", "Perbandingan langsung v1 (baris atas) vs v2 (baris bawah) pada ambang 80px -- kualitas visual tampak sebanding, mendukung temuan Bagian 4 bahwa persentase lolos hampir sama."),
]:
    h2(fname)
    p(caption)
    img_path = SHEETS / fname
    if img_path.exists():
        doc.add_picture(str(img_path), width=Inches(6.2))

h1("6. Rekomendasi Ambang")
p("Berdasarkan bukti kuantitatif (funnel) dan inspeksi visual di atas, TIGA kandidat ambang disajikan. Dokumen ini TIDAK memilih satu angka final -- keputusan akhir memerlukan pilot review manusia pada contoh nyata di setiap kandidat.")
bullet("Kandidat A (longgar, setara ambang lama): min_dim>=60px, blur>75. v1: 231/645 (35.81%); v2: 1090/3413 (31.94%). Risiko: dari inspeksi visual, sejumlah wajah pada ~60px punya detail mata/mulut yang marginal untuk anotasi ekspresi halus.")
bullet("Kandidat B (moderat, DIREKOMENDASIKAN untuk pilot lanjutan): min_dim>=80px, blur>75. v1: 142/645 (22.02%); v2: 448/3413 (13.13%, dengan filter frontalitas tambahan -- 696/3413=20.39% tanpa filter frontalitas). Inspeksi visual pada ambang ini menunjukkan fitur wajah mulai cukup jelas dibedakan pada mayoritas sampel.")
bullet("Kandidat C (ketat): min_dim>=96px atau 112px, blur>75. v1 112px: 77/645 (11.94%); v2 112px: 400/3413 (11.72%). Kualitas visual terbaik namun mengurangi jumlah kandidat signifikan -- mungkin perlu dikombinasikan dengan ekstraksi ulang/frame tambahan jika jumlah kandidat jadi terlalu sedikit untuk tujuan riset.")
p("Manifest passed/rejected pada dokumen ini (v1_candidates_passed_manifest.csv, dst.) MENGGUNAKAN Kandidat B (min_dim>=80, blur>75, dan untuk v2 ditambah filter frontalitas FRONTAL/NEAR_FRONTAL) sebagai label kerja sementara -- diberi label eksplisit 'NOT YET ADOPTED' di kolom threshold_label. Ini BUKAN keputusan final; supervisor dapat memilih Kandidat A atau C.")
p("Rekomendasi proses: lakukan pilot review manusia (misalnya 30-50 sampel per kandidat ambang, diambil dari contact sheet atau manifest passed/rejected di atas) untuk menilai apakah anotator benar-benar bisa memberi label ekspresi yang andal pada resolusi tersebut, SEBELUM mengadopsi satu ambang secara otomatis berdasarkan angka saja.")

h1("7. Keterbatasan")
bullet("Frontalitas v1 hanya dapat dihitung untuk 104/645 wajah (16.1%) yang punya landmark AI tersimpan -- subset ini TIDAK diambil secara acak dari pool 645, sehingga TIDAK dapat digeneralisasi sebagai representasi frontalitas seluruh pool v1.")
bullet("Verifikasi dimensi gambar hanya dilakukan pada sampel (25 v1 + 25 v2 + 15 pasang delivery asli/resize v1 + 15 baris transform v2 = total 80 baris dicatat di dimension_verification_sample.csv), bukan keseluruhan 645+3413+231+668 file -- dipilih karena membuka dan memverifikasi seluruh file secara manual tidak praktis dalam waktu review ini. 0 ketidakcocokan ditemukan pada sampel yang diperiksa.")
bullet("Sheet Sample_List pada file XLSX adalah SUBSET (300 baris: ~150 v1 dari 645, ~150 v2 dari 3413), bukan daftar lengkap -- daftar lengkap ada di file CSV terpisah (v1_pool_full_with_candidateB.csv, v2_pool_full_with_candidateB.csv) di direktori yang sama.")
bullet("blur_variance dapat tinggi akibat tekstur latar belakang/rambut, bukan semata ketajaman wajah -- metrik ini adalah proxy, bukan ukuran ketajaman wajah yang sempurna; ditegaskan kembali oleh temuan ketidaksesuaian visual-numerik pada beberapa sampel di contact sheet (misalnya wajah blur_variance tinggi namun secara visual tetap buram pada area wajah).")
bullet("Dokumen ini TIDAK melakukan ekstraksi ulang, anotasi baru, pelatihan model, atau penetapan person_id baru -- sesuai batasan ruang lingkup review.")
bullet("Rekomendasi ambang di Bagian 6 adalah HIPOTESIS kerja berbasis bukti kuantitatif+visual terbatas, BUKAN hasil studi reliabilitas antar-annotator formal -- pilot review manusia tetap diperlukan sebelum adopsi.")

doc.save(OUT / "Papuan_V2_QC_Strict_Review.docx")
print("docx written")
