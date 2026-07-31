import random

import numpy as np
import torch

from psx_ml.runtime.reproducibility import configure_reproducibility


def sample(seed):
    state=configure_reproducibility(seed,True,False)
    return state,random.random(),np.random.rand(4),torch.rand(4)


def test_same_seed_reproduces_all_generators():
    a=sample(42); b=sample(42)
    assert a[0] == b[0]
    assert a[1] == b[1]
    np.testing.assert_array_equal(a[2],b[2])
    torch.testing.assert_close(a[3],b[3],rtol=0,atol=0)
    assert torch.are_deterministic_algorithms_enabled()
    assert not torch.backends.cuda.matmul.allow_tf32


def test_different_seeds_differ():
    assert not torch.equal(sample(1)[3],sample(2)[3])
