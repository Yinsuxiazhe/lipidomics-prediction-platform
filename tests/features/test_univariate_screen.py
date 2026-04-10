import pandas as pd


def test_rank_features_by_auc_places_signal_feature_first():
    from src.features.univariate_screen import rank_features_by_auc

    X = pd.DataFrame(
        {
            "signal": [0, 0, 0, 1, 1, 1],
            "noise": [0, 1, 0, 1, 0, 1],
        }
    )
    y = pd.Series([0, 0, 0, 1, 1, 1])

    ranking = rank_features_by_auc(X, y, top_k=2)

    assert ranking.iloc[0]["feature"] == "signal"
    assert ranking.iloc[0]["direction_free_auc"] >= 0.99

