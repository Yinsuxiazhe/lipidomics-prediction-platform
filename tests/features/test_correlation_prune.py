import pandas as pd


def test_prune_correlated_features_keeps_highest_ranked_feature():
    from src.features.correlation_prune import prune_correlated_features

    X = pd.DataFrame(
        {
            "f1": [1, 2, 3, 4, 5],
            "f2": [1.01, 2.01, 3.01, 4.01, 5.01],
            "f3": [5, 1, 4, 2, 3],
        }
    )
    ranking = pd.DataFrame(
        {
            "feature": ["f1", "f2", "f3"],
            "direction_free_auc": [0.9, 0.8, 0.7],
        }
    )

    kept = prune_correlated_features(X, ranking, threshold=0.95)

    assert kept == ["f1", "f3"]
