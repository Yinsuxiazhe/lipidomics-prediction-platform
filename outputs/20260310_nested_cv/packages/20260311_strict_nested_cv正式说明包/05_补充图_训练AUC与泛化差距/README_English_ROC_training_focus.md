# English ROC figures focused on the best training result

These figures were generated for the model with the highest mean training AUC in the current strict nested CV results.

- Model: Expanded fusion model (fusion_full_elastic_net)
- Mean training AUC: 0.850 ± 0.038
- Mean outer-test AUC: 0.526 ± 0.045

Recommended use:
1. Use `20260311_BestTrainingModel_English_ROC.png` when you want an English two-panel ROC figure.
2. Use `20260311_BestTrainingModel_English_ROC_overlay.png` when you want a compact English figure showing how much better the training ROC looks than the outer-test ROC.

Important note:
The training ROC is visually stronger because it reflects model fit on training folds. It should be presented together with the outer-test ROC, not as a standalone formal performance claim.