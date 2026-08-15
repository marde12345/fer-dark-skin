---

## 15. Hasil Eksperimen Empiris (Data Audit + Landmark + Preprocessing)

### 15.1 Status Pipeline

Pipeline RetinaFace (InsightFace buffalo_l) + HSEmotion dual-model ensemble sudah berjalan end-to-end dengan output:
- `data/1408-1010-intermediate/faces/` — 227 face crops
- `data/1408-1010-intermediate/annotations.csv` — prediksi model
- `data/1408-1010-intermediate/landmark_features.csv` — 85 face dengan 468-point landmark (MediaPipe)
- `data/1408-1010-intermediate/manual_labels_export.csv` — 227 ground truth manual
- `data/1408-1010-intermediate/clahe_predictions.csv` — prediksi setelah Strategy B CLAHE

### 15.2 Temuan Data Audit

| Metric | Value |
|--------|-------|
| Overall accuracy (HSEmotion vs ground truth) | 22.5% |
| Error rate | 77.5% |
| False Angry rate | 17.6% (40/227 sampel) |
| Fairness gap (Dark vs Medium-Dark) | 29.7 poin persentase |
| Accuracy Dark skin | 44.0% |
| Accuracy Medium-Dark skin | 14.3% |

**Temuan kunci:**
- Model over-predict Angry ke hampir semua kelas: Neutral→Angry (18 kasus), Happy→Angry (8), Sad→Angry (6)
- Model over-confident saat salah prediksi Angry: confidence false Angry (0.597) > true Angry (0.419)
- Medium-Dark adalah grup paling bermasalah, jauh di bawah Dark

### 15.3 Temuan Landmark Analysis

Dari 85 face crops dengan MediaPipe 468-point landmark:

| Feature | Angry (predicted) | Neutral (predicted) |
|---------|-------------------|---------------------|
| brow_lowering_distance | 0.131 | 0.147 |
| lip_corner_distance | 0.557 | 0.545 |
| mouth_openness | 0.036 | 0.045 |

**Interpretasi:** Tidak ada perbedaan geometri ekspresif antara wajah yang diprediksi Angry vs Neutral. Model tidak menggunakan sinyal landmark/gerakan otot untuk memprediksi Angry — kemungkinan mengandalkan sinyal tekstur/kontras periokular yang lebih tinggi pada kulit gelap.

Validasi: Happiness dan Surprise menunjukkan geometri yang konsisten (lip_corner Happiness = 0.655 tertinggi; mouth_openness Surprise = 0.311 jauh di atas kelas lain), membuktikan pipeline landmark bekerja benar.

### 15.4 Temuan Preprocessing Experiment (Strategy B CLAHE)

| Metric | Before CLAHE | After CLAHE | Delta |
|--------|-------------|-------------|-------|
| Overall accuracy | 22.5% | 19.8% | -2.6% |
| False Angry rate | 17.6% | 18.1% | +0.4% |
| Label changed | — | 25.5% (58/227) | — |

Per skin-tone false Angry rate:

| Skin Tone | Before | After |
|-----------|--------|-------|
| Dark | 10.7% | 11.3% |
| Medium-Dark | 35.4% | 35.4% |

**Interpretasi:** Strategy B CLAHE standalone tidak cukup untuk mengurangi misclassification Angry. CLAHE mengubah 25.5% prediksi namun tidak sistematis — sebagian menggeser prediksi benar menjadi salah. Medium-Dark sama sekali tidak terpengaruh CLAHE.

**Implikasi untuk tesis:** Masalah bukan semata pencahayaan/kontras, melainkan bias representasi di training data HSEmotion (dominan wajah kulit terang). Ini memperkuat justifikasi Strategy C (balanced training + skin-tone augmentation) sebagai solusi yang lebih fundamental.

### 15.5 Narasi untuk Presentasi ke Dosbing

"Kami telah melakukan tiga eksperimen empiris pada dataset dokumenter Papua (227 face crops, 100% kulit gelap):

1. **Data Audit**: Model HSEmotion off-the-shelf hanya mencapai 22.5% akurasi dengan fairness gap 29.7 poin antara Dark dan Medium-Dark. False Angry rate mencapai 17.6% — model secara sistematis salah mengklasifikasikan ekspresi sebagai Angry.

2. **Landmark Analysis**: Analisis geometri 468-point landmark membuktikan wajah yang diprediksi Angry dan Neutral tidak berbeda secara geometri ekspresif. Model tidak mengandalkan sinyal gerakan otot wajah (Action Units) melainkan kemungkinan sinyal kontras/tekstur.

3. **Preprocessing Experiment**: Strategy B CLAHE standalone tidak mengurangi masalah — akurasi justru turun 2.6% dan false Angry rate tetap/naik. Ini mengkonfirmasi bahwa solusi preprocessing saja tidak cukup dan memvalidasi perlunya Strategy C di level training."

### 15.6 Next Steps

- [ ] Presentasi temuan ke Pak Fadhil (dosbing)
- [ ] Download RAF-DB untuk training utama
- [ ] Implementasi Strategy C: skin-tone augmentation + balanced sampler
- [ ] Fine-tuning model pada dataset Papua
- [ ] Evaluasi dengan metrik fairness (worst-group accuracy, fairness gap)
- [ ] Buat protokol perekaman untuk dataset private mahasiswa Papua
