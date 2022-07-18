from collections import OrderedDict

import numpy as np
import pytest

from gym.spaces import Box, Dict, Discrete


def test_dict_init():
    with pytest.raises(
        AssertionError,
        match=r"^A Dict space cannot be empty and can only be initialised with a dictionary OR keywords\.$",
    ):
        Dict()

    with pytest.raises(
        AssertionError,
        match=r"^A Dict space cannot be empty and can only be initialised with a dictionary OR keywords\.$",
    ):
        Dict({"a": Discrete(2)}, b=Discrete(3))

    with pytest.raises(
        AssertionError,
        match=r"^Unexpected Dict space input, expecting dict, OrderedDict or Sequence, actual type: ",
    ):
        Dict(Discrete(2))

    with pytest.raises(
        AssertionError,
        match="Dict space element is not an instance of Space: key=b, space=Box",
    ):
        Dict(a=Discrete(2), b="Box")

    with pytest.warns(None) as warnings:
        a = Dict({"a": Discrete(2), "b": Box(low=0.0, high=1.0)})
        b = Dict(OrderedDict(a=Discrete(2), b=Box(low=0.0, high=1.0)))
        c = Dict((("a", Discrete(2)), ("b", Box(low=0.0, high=1.0))))
        d = Dict(a=Discrete(2), b=Box(low=0.0, high=1.0))

        assert a == b == c == d

    assert len(warnings) == 0


DICT_SPACE = Dict(
    {
        "a": Box(low=0, high=1, shape=(3, 3)),
        "b": Dict(
            {
                "b_1": Box(low=-100, high=100, shape=(2,)),
                "b_2": Box(low=-1, high=1, shape=(2,)),
            }
        ),
        "c": Discrete(5),
    }
)


def test_dict_seeding():
    DICT_SPACE.seed(
        {
            "a": 0,
            "b": {
                "b_1": 1,
                "b_2": 2,
            },
            "c": 3,
        }
    )

    # "Unpack" the dict sub-spaces into individual spaces
    a = Box(low=0, high=1, shape=(3, 3), seed=0)
    b_1 = Box(low=-100, high=100, shape=(2,), seed=1)
    b_2 = Box(low=-1, high=1, shape=(2,), seed=2)
    c = Discrete(5, seed=3)

    for i in range(10):
        dict_sample = DICT_SPACE.sample()
        assert np.all(dict_sample["a"] == a.sample())
        assert np.all(dict_sample["b"]["b_1"] == b_1.sample())
        assert np.all(dict_sample["b"]["b_2"] == b_2.sample())
        assert dict_sample["c"] == c.sample()


def test_int_seeding():
    seeds = DICT_SPACE.seed(1)

    # rng, seeds = seeding.np_random(1)
    # subseeds = rng.choice(np.iinfo(int).max, size=3, replace=False)
    # b_rng, b_seeds = seeding.np_random(int(subseeds[1]))
    # b_subseeds = b_rng.choice(np.iinfo(int).max, size=2, replace=False)

    # "Unpack" the dict sub-spaces into individual spaces
    a = Box(low=0, high=1, shape=(3, 3), seed=seeds[1])
    b_1 = Box(low=-100, high=100, shape=(2,), seed=seeds[3])
    b_2 = Box(low=-1, high=1, shape=(2,), seed=seeds[4])
    c = Discrete(5, seed=seeds[5])

    for i in range(10):
        dict_sample = DICT_SPACE.sample()
        assert np.all(dict_sample["a"] == a.sample())
        assert np.all(dict_sample["b"]["b_1"] == b_1.sample())
        assert np.all(dict_sample["b"]["b_2"] == b_2.sample())
        assert dict_sample["c"] == c.sample()