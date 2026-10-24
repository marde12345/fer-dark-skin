# Data Lineage

Two independent lineages exist in this repository. They share a source video but do **not** share any downstream artifact — Papuan V2 is a separate extraction run, not a continuation, superset, or subset of the legacy dataset.

## Lineage A — Legacy Dataset (D-LEGACY)

```
Source video (Pesta Babi documentary, 1920x1080, ~96 min, 144,084 frames @25fps)
  │
  │  [debug.max_frames=100 — a smoke-test-scale sample, NOT the full video]
  ▼
100 sampled frames
  │  [InsightFace buffalo_l / SCRFD detection, 20% bbox padding]
  ▼
227 detected face crops  ← this is the unit counted everywhere as "N=227"
  │                          one crop = one detected face in one sampled frame;
  │                          NOT verified to be 227 distinct subjects (see
  │                          DATA_DICTIONARY.md — no subject-ID field exists)
  │
  ├──[HSEmotion pretrained inference, ONNX enet_b0_8_best_vgaf]──▶ 227 pseudo-labels
  │                                                                  (baseline predictions,
  │                                                                   evaluated, never
  │                                                                   treated as ground truth)
  │
  ├──[single human annotator, manual review]──▶ 227 manual labels
  │                                                (ground truth for all downstream
  │                                                 evaluation; manual_labels_export.csv)
  │
  ├──[CLAHE: LAB L-channel, adaptive clip 1.5-3.5, 8x8 tiles]──▶ 227 CLAHE-preprocessed crops
  │                                                                 ──▶ HSEmotion inference
  │                                                                     ──▶ EXP-006 result
  │                                                                         (accuracy 19.82%,
  │                                                                          WORSE than original)
  │
  └──[227 → −83 Ambiguous → 144 → −1 Angry/−2 Disgust → 141 → −6 ArcFace
       re-detection/alignment failures → 135; chain resolved and cross-corroborated
       between EXP-007_ARCFACE_EVALUATION.md §2 and ARCFACE_EXPERIMENT_DESIGN.md's
       prescribed filter order — see DATA_DISCREPANCIES D-2 for residual row-level gap]
       ▼
     N=135 common subset (5-class taxonomy: Angry, Disgust excluded;
     CONFIRMED to be drawn from THIS SAME 227-crop legacy population,
     NOT a separate Papuan V2 reconstruction — provenance question raised
     and resolved 2026-10-09, see RESEARCH_DECISIONS.md; NOT independent
     of N=227 — it is a strict filtered subset of it)
                                                                        │
                                                                        ├──[ArcFace buffalo_l/w600k_r50,
                                                                        │   frozen 512-d embedding]
                                                                        │     ──▶ [Logistic Regression,
                                                                        │          trained on this
                                                                        │          project's own
                                                                        │          N=135 manual labels,
                                                                        │          StratifiedGroupKFold
                                                                        │          5-fold CV grouped by
                                                                        │          3-frame temporal block,
                                                                        │          seed=42]
                                                                        │     ──▶ EXP-007 predictions
                                                                        │
                                                                        └──[HSEmotion pretrained
                                                                            inference, same N=135]
                                                                            ──▶ EXP-007 predictions
                                                                                (baseline arm)
                                                                        │
                                                                        ▼
                                                       EXP-007: paired comparison,
                                                       McNemar p=0.4614 (not significant),
                                                       Fisher's exact p=0.0027 (skin-tone assoc.)
```

**No train/validation/test split exists anywhere in Lineage A.** The Logistic Regression classifier's "test" performance is cross-validated (5-fold) on the full N=135 set, not held out against a separately reserved test partition. This is a methodological limitation, not an oversight to paper over (see Chapter 3 §Methodological Limitations of the thesis manuscript).

**Count losses/transformations:**
- 144,084 frames → 100 sampled frames: explained (debug-mode frame cap).
- 100 frames → 227 face crops: more crops than frames is expected (multiple faces per frame) and is consistent with multi-subject scenes in a documentary; not independently re-verified by counting detections per frame in this pass.
- 227 → 135: **resolved** (see chain above and `DATA_DISCREPANCIES.md` D-2) — `Ambiguous` exclusion (83), rare-class exclusion (Angry 1 + Disgust 2), and ArcFace alignment-failure exclusion (6, within the eligible subset) account for the full 92-sample reduction. Residual gap: the specific row-level identity of the 6 alignment-loss samples was not independently re-derived from the raw CSV in this pass.

## Lineage B — Papuan V2 (D-PAPUANV2)

```
Source video (same film as Lineage A, re-extracted independently)
  │  [max_frames=250, target fps=2.0 — a different, larger sampling config than Lineage A's debug mode]
  ▼
~unknown number of sampled frames (not recorded in located documents)
  │  [InsightFace buffalo_l / SCRFD detection — same detector as Lineage A]
  ▼
645 face crops (EXP-PAP-001)
  │
  ├──[CLAHE, same parameters as Lineage A]──▶ 645 CLAHE crops (parallel branch, EXP-PAP-001)
  │
  └──[random sample, seed=42]──▶ 150-image pilot subset (EXP-PAP-002)
        │
        ├──[HSEmotion inference, CLAHE branch]──▶ 150/150 predictions (EXP-PAP-003, complete)
        ├──[ArcFace+LR inference, CLAHE branch, after a re-detection bugfix]──▶ 150/150 predictions
        │     (EXP-PAP-003, complete; human-vs-model agreement analysis PENDING — no completed
        │      human labels exist yet to compare against)
        │
        ├──[Label Studio, Annotator A, 150 tasks]──▶ emotion-label human annotation
        │     STATUS: reported as fully submitted in one internal record, NOT independently
        │     re-verified against the raw export in this pass — see DATA_DISCREPANCIES D-1
        │
        ├──[random overlap sample, seed=100]──▶ 75-task subset
        │     ──▶ [Label Studio, Annotator B, isolated server]──▶ emotion-label annotation
        │          STATUS: 0/75 complete at last recorded status (EXP-PAP-004)
        │
        │  [SUPERSEDED as primary target, 2026-10-02, per supervisor direction — emotion-label
        │   track's continuation status is UNDECIDED, not formally terminated]
        │
        └──[random sample, seed=200, 24 images]──▶ CVAT landmark pilot (EXP-PAP-005)
              │  [InsightFace landmark_3d_68 sub-model — automatic proposal, NOT human-verified]
              ▼
              68-point automatic landmark proposals per image (ibug-300W convention)
              │  [point-label renaming pt0..pt67 → anatomical names; verified zero coordinate drift]
              ▼
              CVAT project populated with proposals
              │
              ▼
              [HUMAN REVIEW — NOT YET PERFORMED as of time of writing]
              │
              ▼
              (no further downstream artifact exists: no reviewed/corrected landmark dataset,
               no landmark-model training, no Original-vs-CLAHE landmark-model comparison —
               none of this code exists in the repository)
```

**No train/validation/test split exists for Lineage B at any stage.** No model has been trained on any Lineage B data at the time of writing (the ArcFace+LR classifier used for EXP-PAP-003 predictions was trained on Lineage A's N=135 data and only applied, not retrained, to Lineage B images).

## Explicit Category Boundaries (apply to both lineages)

| Category | Lineage A instance | Lineage B instance |
|---|---|---|
| Original source data | Pesta Babi film | same film, separate extraction |
| Extracted frames | 100 (debug sample) | unknown count (not recorded), fps=2.0, max 250 frames |
| Detected face crops | 227 | 645 |
| Successfully processed samples | 227 (100% of detections; no filtering stage exists in this pipeline at all — see `docs/ARCHITECTURE.md`) | 645 original + 645 CLAHE |
| Model-generated pseudo-labels | HSEmotion output on all 227 | HSEmotion + ArcFace+LR output on 150-image pilot |
| Human-provided labels | 227 (single annotator, emotion) | 0 complete (Annotator B); Annotator A status unresolved (emotion); 0 complete (landmark, review not performed) |
| Reviewed/adjudicated labels | none (single-annotator, no adjudication step exists) | none |
| Final curated dataset | the 227-image manually labeled set itself (no further curation stage) | does not exist yet |
| Training/evaluation subsets | N=135 common subset (derivation incompletely documented, D-2) | none exist |
