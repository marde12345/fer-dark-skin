"""Regression tests for the softmax post-processing used in emotion prediction.

Protects: src/emotion_classifier.py softmax() (lines 11-14), which converts
raw HSEmotion logits into the confidence score stored in the dataset.
Per docs/EXPERIMENT.md, softmax behavior is classified as a "Behavioral
change" boundary if altered.
"""

import numpy as np
import pytest

from fer_dataset.pipeline.emotion_classifier import softmax


def test_softmax_sums_to_one():
    logits = np.array([1.0, 2.0, 3.0])
    probs = softmax(logits)
    assert probs.sum() == pytest.approx(1.0)


def test_softmax_known_values():
    # Ground truth computed directly from the current implementation.
    logits = np.array([1.0, 2.0, 3.0])
    probs = softmax(logits)
    expected = np.array([0.09003057, 0.24472847, 0.66524096])
    np.testing.assert_allclose(probs, expected, atol=1e-6)


def test_softmax_is_shift_invariant():
    """The max-subtraction step must keep behavior stable for large logits."""
    logits_low = np.array([1.0, 2.0, 3.0])
    logits_shifted = np.array([1000.0, 1001.0, 1002.0])
    np.testing.assert_allclose(softmax(logits_low), softmax(logits_shifted), atol=1e-6)


def test_softmax_argmax_matches_input_argmax():
    logits = np.array([-5.0, 0.2, 3.7, 3.6])
    probs = softmax(logits)
    assert int(np.argmax(probs)) == int(np.argmax(logits))
