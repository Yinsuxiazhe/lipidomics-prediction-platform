import numpy as np
import pandas as pd


def test_lipid_preprocessor_drops_constant_columns_and_transforms_zeros():
    from src.preprocess.lipid_transform import LipidPreprocessor

    train = pd.DataFrame(
        {
            "lipid_signal": [0.0, 1.0, 2.0, 4.0],
            "lipid_constant": [5.0, 5.0, 5.0, 5.0],
        }
    )
    test = pd.DataFrame(
        {
            "lipid_signal": [0.0, 8.0],
            "lipid_constant": [5.0, 5.0],
        }
    )

    preprocessor = LipidPreprocessor()
    transformed_train = preprocessor.fit_transform(train)
    transformed_test = preprocessor.transform(test)

    assert list(transformed_train.columns) == ["lipid_signal"]
    assert list(transformed_test.columns) == ["lipid_signal"]
    assert np.isfinite(transformed_train.to_numpy()).all()
    assert np.isfinite(transformed_test.to_numpy()).all()
    assert abs(float(transformed_train["lipid_signal"].mean())) < 1e-8

