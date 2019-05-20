import pytest

import gym
from gym.wrappers import ResizeObservation
try:
    import atari_py
except ImportError:
    atari_py = None


@pytest.mark.skipif(atari_py is None, reason='Only run this test when atari_py is installed')
@pytest.mark.parametrize('env_id', ['Pong-v0', 'SpaceInvaders-v0'])
@pytest.mark.parametrize('size', [16, 32])
def test_resize_observation(env_id, size):
    env = gym.make(env_id)
    env = ResizeObservation(env, size)

    assert env.observation_space.shape[-1] == 3
    assert env.observation_space.shape[:2] == (size, size)
    obs = env.reset()
    assert obs.shape == (size, size, 3)
