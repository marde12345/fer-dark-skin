window.DASHBOARD_DATA = {
  "common_subset": {
    "n": 135,
    "arcface": {
      "accuracy": 0.4074074074074074,
      "macro_precision": 0.28027479766610197,
      "macro_recall": 0.2930921052631579,
      "macro_f1": 0.27174636721406253
    },
    "hsemotion": {
      "accuracy": 0.362962962962963,
      "macro_precision": 0.5897849462365592,
      "macro_recall": 0.20576441102756898,
      "macro_f1": 0.24891015417331203
    }
  },
  "historical": {
    "n": 227,
    "accuracy": 0.22466960352422907,
    "false_angry_rate": 0.1762114537444934,
    "fairness_gap": 0.29714285714285715,
    "neutral_to_angry_count": 18,
    "neutral_to_angry_total": 76,
    "neutral_to_angry_rate": 0.23684210526315788
  },
  "per_class_metrics": {
    "Fear": {
      "HSEmotion": {
        "precision": 0.03225806451612903,
        "recall": 0.14285714285714285,
        "f1": 0.05263157894736842,
        "support": 7
      },
      "ArcFace+LR": {
        "precision": 0.0,
        "recall": 0.0,
        "f1": 0.0,
        "support": 7
      }
    },
    "Happy": {
      "HSEmotion": {
        "precision": 1.0,
        "recall": 0.125,
        "f1": 0.2222222222222222,
        "support": 32
      },
      "ArcFace+LR": {
        "precision": 0.40476190476190477,
        "recall": 0.53125,
        "f1": 0.4594594594594595,
        "support": 32
      }
    },
    "Neutral": {
      "HSEmotion": {
        "precision": 0.75,
        "recall": 0.5526315789473685,
        "f1": 0.6363636363636364,
        "support": 76
      },
      "ArcFace+LR": {
        "precision": 0.717391304347826,
        "recall": 0.4342105263157895,
        "f1": 0.5409836065573771,
        "support": 76
      }
    },
    "Sad": {
      "HSEmotion": {
        "precision": 0.16666666666666666,
        "recall": 0.08333333333333333,
        "f1": 0.1111111111111111,
        "support": 12
      },
      "ArcFace+LR": {
        "precision": 0.13636363636363635,
        "recall": 0.25,
        "f1": 0.17647058823529413,
        "support": 12
      }
    },
    "Surprise": {
      "HSEmotion": {
        "precision": 1.0,
        "recall": 0.125,
        "f1": 0.2222222222222222,
        "support": 8
      },
      "ArcFace+LR": {
        "precision": 0.14285714285714285,
        "recall": 0.25,
        "f1": 0.18181818181818182,
        "support": 8
      }
    }
  },
  "overall_error_by_model": {
    "ArcFace+LR": [
      {
        "ground_truth": "Fear",
        "n": 7,
        "correct": 0,
        "incorrect": 7,
        "accuracy": 0.0,
        "error_rate": 1.0
      },
      {
        "ground_truth": "Happy",
        "n": 32,
        "correct": 17,
        "incorrect": 15,
        "accuracy": 0.53125,
        "error_rate": 0.46875
      },
      {
        "ground_truth": "Neutral",
        "n": 76,
        "correct": 33,
        "incorrect": 43,
        "accuracy": 0.4342105263157895,
        "error_rate": 0.5657894736842105
      },
      {
        "ground_truth": "Sad",
        "n": 12,
        "correct": 3,
        "incorrect": 9,
        "accuracy": 0.25,
        "error_rate": 0.75
      },
      {
        "ground_truth": "Surprise",
        "n": 8,
        "correct": 2,
        "incorrect": 6,
        "accuracy": 0.25,
        "error_rate": 0.75
      }
    ],
    "HSEmotion": [
      {
        "ground_truth": "Fear",
        "n": 7,
        "correct": 1,
        "incorrect": 6,
        "accuracy": 0.14285714285714285,
        "error_rate": 0.8571428571428571
      },
      {
        "ground_truth": "Happy",
        "n": 32,
        "correct": 4,
        "incorrect": 28,
        "accuracy": 0.125,
        "error_rate": 0.875
      },
      {
        "ground_truth": "Neutral",
        "n": 76,
        "correct": 42,
        "incorrect": 34,
        "accuracy": 0.5526315789473685,
        "error_rate": 0.4473684210526316
      },
      {
        "ground_truth": "Sad",
        "n": 12,
        "correct": 1,
        "incorrect": 11,
        "accuracy": 0.08333333333333333,
        "error_rate": 0.9166666666666666
      },
      {
        "ground_truth": "Surprise",
        "n": 8,
        "correct": 1,
        "incorrect": 7,
        "accuracy": 0.125,
        "error_rate": 0.875
      }
    ]
  },
  "neutral_analysis": {
    "arcface": {
      "n": 76,
      "correct": 33,
      "error_rate": 0.5657894736842105,
      "dominant_wrong_class": "Happy",
      "dominant_wrong_count": 15
    },
    "hsemotion": {
      "n": 76,
      "correct": 42,
      "error_rate": 0.4473684210526316,
      "dominant_wrong_class": "Angry",
      "dominant_wrong_count": 18,
      "neutral_to_angry_count": 18,
      "neutral_to_angry_rate": 0.23684210526315788
    },
    "breakdown": [
      {
        "predicted_class": "Neutral",
        "arcface": "33",
        "hsemotion": "42"
      },
      {
        "predicted_class": "Happy",
        "arcface": "15",
        "hsemotion": "0"
      },
      {
        "predicted_class": "Sad",
        "arcface": "14",
        "hsemotion": "3"
      },
      {
        "predicted_class": "Surprise",
        "arcface": "6",
        "hsemotion": "0"
      },
      {
        "predicted_class": "Fear",
        "arcface": "8",
        "hsemotion": "13"
      },
      {
        "predicted_class": "Angry",
        "arcface": "N/A",
        "hsemotion": "18"
      },
      {
        "predicted_class": "Disgust",
        "arcface": "N/A",
        "hsemotion": "0"
      }
    ]
  },
  "skin_tone": [
    {
      "skin_tone": "Dark",
      "n": 46,
      "arcface_accuracy": 0.45652173913043476,
      "hsemotion_accuracy": 0.45652173913043476,
      "arcface_neutral_error_rate": 0.56,
      "hsemotion_neutral_error_rate": 0.31999999999999995
    },
    {
      "skin_tone": "Medium-Dark",
      "n": 32,
      "arcface_accuracy": 0.3125,
      "hsemotion_accuracy": 0.125,
      "arcface_neutral_error_rate": 0.8461538461538461,
      "hsemotion_neutral_error_rate": 0.8461538461538461
    },
    {
      "skin_tone": "Unknown",
      "n": 57,
      "arcface_accuracy": null,
      "hsemotion_accuracy": null,
      "arcface_neutral_error_rate": null,
      "hsemotion_neutral_error_rate": null
    }
  ],
  "statistics": {
    "mcnemar": {
      "a_both_correct": 29,
      "b_hsemotion_only": 20,
      "c_arcface_only": 26,
      "d_both_wrong": 60,
      "p_value": 0.4613911821367651
    },
    "bootstrap_accuracy_arcface": "(0.4074074074074074, 0.3383458646616541, 0.48091603053435117)",
    "bootstrap_accuracy_hsemotion": "(0.362962962962963, 0.2692307692307692, 0.4672210985735576)",
    "fisher_exact": "OR=5.8800, p=0.0027, table=[[21, 25], [4, 28]]"
  },
  "findings": [
    {
      "finding": "ArcFace achieved 40.74% accuracy",
      "metric": "accuracy=0.4074",
      "population": "N=135 common subset",
      "evidence_strength": "Moderate",
      "thesis_use": "Report as observed accuracy, always paired with HSEmotion figure and McNemar result"
    },
    {
      "finding": "HSEmotion achieved 36.30% on the same population",
      "metric": "accuracy=0.3630",
      "population": "N=135 common subset",
      "evidence_strength": "Moderate",
      "thesis_use": "Report alongside ArcFace figure; do not present in isolation from the 227-sample historical figure"
    },
    {
      "finding": "The paired accuracy difference was not statistically significant",
      "metric": "McNemar p=0.4614 (b=20, c=26)",
      "population": "N=135 paired",
      "evidence_strength": "Strong (as a null result)",
      "thesis_use": "Report explicitly as not statistically significant; do not omit"
    },
    {
      "finding": "ArcFace errors were distributed across multiple wrong classes",
      "metric": "Neutral: Happy=15, Sad=14, Fear=8, Surprise=6",
      "population": "N=76 (Neutral subset of 135)",
      "evidence_strength": "Moderate",
      "thesis_use": "Descriptive error-pattern evidence only"
    },
    {
      "finding": "HSEmotion showed a strong Neutral->Angry pattern",
      "metric": "18/76=23.7% of Neutral; 52.9% of HSEmotion Neutral errors",
      "population": "N=76 (both 227 and 135 populations)",
      "evidence_strength": "Strong",
      "thesis_use": "Central motivating finding; always state population size"
    },
    {
      "finding": "Neutral->Angry = 18/76 = 23.7%",
      "metric": "count=18, rate=0.2368",
      "population": "N=76 (identical in historical N=227 and common-subset N=135)",
      "evidence_strength": "Strong",
      "thesis_use": "Report once, note it holds in both populations"
    },
    {
      "finding": "Dark vs Medium-Dark HSEmotion performance differed descriptively/statistically",
      "metric": "accuracy 0.4565 vs 0.1250; Fisher exact OR=5.88, p=0.0027",
      "population": "N=46 (Dark) / N=32 (Medium-Dark)",
      "evidence_strength": "Moderate",
      "thesis_use": "Report as in-sample statistical association; not causal, not demographic"
    },
    {
      "finding": "Papuan-specific quantitative error rate cannot be established",
      "metric": "no ethnicity field in any dataset artifact",
      "population": "N/A",
      "evidence_strength": "Unsupported",
      "thesis_use": "Must not be quantitatively claimed; researcher observation only"
    },
    {
      "finding": "ArcFace false-Angry = 0 is not a valid improvement claim",
      "metric": "Angry excluded from ArcFace 5-class label space (1 GT sample)",
      "population": "N=135",
      "evidence_strength": "Unsupported (as improvement claim)",
      "thesis_use": "Must always be presented with the structural-limitation caveat"
    },
    {
      "finding": "7-class ArcFace evaluation is not currently defensible",
      "metric": "Angry=1, Disgust=2 GT samples in every population stage",
      "population": "N=227/144/138",
      "evidence_strength": "Strong (as a limitation finding)",
      "thesis_use": "Report as a dataset limitation requiring more data to resolve"
    }
  ],
  "limitations": [
    {
      "limitation": "N=135 primary comparison population",
      "impact": "Limits statistical power for all metrics",
      "severity": "High",
      "thesis_handling": "Report N explicitly with every metric; frame findings as observed-in-this-sample"
    },
    {
      "limitation": "Angry/Disgust scarcity (1 and 2 GT samples)",
      "impact": "Prevents any 7-class evaluation; root cause of the 5-class restriction",
      "severity": "High",
      "thesis_handling": "State explicitly as a dataset limitation, not a modeling choice"
    },
    {
      "limitation": "5-class rather than 7-class evaluation",
      "impact": "ArcFace cannot be evaluated for Angry/Disgust behavior at all",
      "severity": "High",
      "thesis_handling": "Frame every ArcFace-vs-HSEmotion claim as scoped to 5 classes"
    },
    {
      "limitation": "40 Ambiguous samples excluded",
      "impact": "Reduces usable ground truth from 178 embedded to 138 validly labeled",
      "severity": "Medium",
      "thesis_handling": "Report exclusion count; do not treat Ambiguous as a class"
    },
    {
      "limitation": "48 ArcFace crop re-detection failures (excluded_no_face)",
      "impact": "Reduces embedded population from 227 to 178",
      "severity": "Medium",
      "thesis_handling": "Report as a pipeline-stage exclusion, distinct from label-based exclusions"
    },
    {
      "limitation": "57 unknown skin-tone samples (of 135)",
      "impact": "Skin-tone analysis covers only 78/135 (58%) of the common subset",
      "severity": "Medium",
      "thesis_handling": "Report Unknown as its own category, never impute"
    },
    {
      "limitation": "Small Fear (7) and Surprise (8) classes",
      "impact": "Per-class precision/recall/F1 for these classes are unstable",
      "severity": "Medium",
      "thesis_handling": "Flag explicitly wherever these classes are reported individually"
    },
    {
      "limitation": "No formal ethnicity metadata",
      "impact": "Cannot test any ethnicity-specific hypothesis quantitatively",
      "severity": "High",
      "thesis_handling": "Never present skin-tone findings as ethnicity findings"
    },
    {
      "limitation": "Papuan-specific effect cannot be quantitatively isolated",
      "impact": "Central research motivation partially unverifiable with current data",
      "severity": "High",
      "thesis_handling": "State as researcher observation, distinct from quantitative finding"
    },
    {
      "limitation": "HSEmotion and ArcFace have different original label spaces",
      "impact": "HSEmotion:7 classes, ArcFace:5 classes (as configured for this experiment)",
      "severity": "High",
      "thesis_handling": "Never compare cross-space metrics (e.g. false-Angry) as if equivalent"
    },
    {
      "limitation": "HSEmotion Neutral->Angry cannot be directly compared to ArcFace",
      "impact": "ArcFace structurally cannot produce this prediction",
      "severity": "High",
      "thesis_handling": "Present Neutral->Angry as HSEmotion-specific evidence only"
    },
    {
      "limitation": "No person-identity metadata; temporal-block grouping used as proxy",
      "impact": "Cannot fully guarantee zero identity leakage in cross-validation",
      "severity": "Medium",
      "thesis_handling": "State explicitly as an accepted, documented limitation (R4/R6)"
    },
    {
      "limitation": "Probability outputs are not calibrated",
      "impact": "Prediction probabilities/confidence cannot be interpreted as true likelihoods",
      "severity": "Medium",
      "thesis_handling": "Label explicitly as raw model outputs, not calibrated confidence"
    },
    {
      "limitation": "Dataset originates from one film/source context (Pesta Babi)",
      "impact": "No generalization beyond this specific video/session is established",
      "severity": "High",
      "thesis_handling": "State explicitly as a single-source-context limitation"
    }
  ],
  "class_distribution": {
    "final_classes": {
      "Neutral": 76,
      "Happy": 32,
      "Sad": 12,
      "Surprise": 8,
      "Fear": 7
    },
    "rare_excluded": {
      "Angry": 1,
      "Disgust": 2
    },
    "ambiguous_excluded": 40
  },
  "population_funnel": [
    {
      "stage": "All face crops",
      "n": 227
    },
    {
      "stage": "ArcFace embeddings created",
      "n": 178
    },
    {
      "stage": "Valid ground-truth label (not Ambiguous)",
      "n": 138
    },
    {
      "stage": "Final evaluation set (5 classes)",
      "n": 135
    }
  ]
};
