Gym is now being maintained, but new major features are not intended. See [this post](https://github.com/openai/gym/issues/2259) for more information.

## Gym

Gym is an open source Python library for developing and comparing reinforcement learning algorithms by providing a standard API to communicate between learning algorithms and environments, as well as a standard set of environments compliant with that API. Since its release, Gym's API has become the field standard for doing this.

Gym currently has two pieces of documentation: the [documentation website](http://gym.openai.com) and the [FAQ](https://github.com/openai/gym/wiki/FAQ). A new and more comprehensive documentation website is in the works.

## Installation

To install the base Gym library, use `pip install gym`.

This does not include dependencies for all families of environments (there's a massive number, and some can be problematic to install on certain systems). You can install these dependencies for one family like `pip install gym[atari]` or use `pip install pettingzoo[gym]` to install all dependencies.

We support Python 3.6, 3.7, 3.8 and 3.9 on Linux and macOS. We will accept PRs related to Windows, but do not officially support it.

## API

If someone would be willing to make a PR for this section in the style of same section the PettingZoo readme.md I would greatly appreciate it. If not, I'll deal with this later.

The Gym API is a minimal and flexible way to interact with environments. A Gym `Env` (environment) subclass must provide the following methods: 

- `reset(self)`: Reset environment state; returns initial observation for next episode. 
- `step(self, action)`: Step the environment by one timestep. Returns tuple `(observation, reward, done, info)`.
- `render(self, mode='human')`: Render one frame of the environment. The default mode will do something human friendly, such as pop up a window.

See [Env](https://github.com/openai/gym/blob/3133e99a64be1a9b794bf62cc3e5fb8c8abd21b9/gym/core.py#L8) implementation for a full list of environment methods. You can see the environments already registered with Gym via `gym.envs.registry.all()`. You can register your own Gym environment with `gym.register(id=env_name, entry_point='module.path:EnvClass')`. See docs for more details. 

Creating environment instances and interacting with them is very simple. Here's an example using the "CartPole-v1" environment: 

```python
import gym 
env = gym.make('CartPole-v1')

# env is created, now we can use it: 
for episode in range(10): 
    obs = env.reset()
    for step in range(50):
        action = env.action_space.sample() # your agent goes here 
        new_obs, reward, done, info = env.step(action)
```

## Notable Related Libraries

* [Stable Baselines 3](https://github.com/DLR-RM/stable-baselines3) is a learning library based on the Gym API. It is our recommendation for beginners who want to start learning things quickly.
* [RL Baselines3 Zoo](https://github.com/DLR-RM/rl-baselines3-zoo) builds upon SB3, containing optimal hyperparameters for Gym environments as well as code to easily find new ones. Such tuning is almost always required.
* The [Autonomous Learning Library](https://github.com/cpnota/autonomous-learning-library) and [Tianshou](https://github.com/thu-ml/tianshou) are two reinforcement learning libraries I like that are generally geared towards more experienced users.
* [PettingZoo](https://github.com/PettingZoo-Team/PettingZoo) is like Gym, but for environments with multiple agents.
* [SuperSuit](https://github.com/PettingZoo-Team/SuperSuit) contains preprocessing wrappers for Gym (and PettingZoo) environments. They're like the old ones in Gym except comprehensive, documented, versioning for reproducibility and are better in almost every way. The built in wrappers in Gym are being deprecated in favor of these. 

## Environment Versioning

Gym keeps strict versioning for reproducibility reasons. All environments end in a suffix like "\_v0".  When changes are made to environments that might impact learning results, the number is increased by one to prevent potential confusion.

## Citation

A whitepaper from when OpenAI Gym just came out is available http://arxiv.org/abs/1606.0154, and can be cited with the following bibtex entry:

```
@misc{1606.01540,
  Author = {Greg Brockman and Vicki Cheung and Ludwig Pettersson and Jonas Schneider and John Schulman and Jie Tang and Wojciech Zaremba},
  Title = {OpenAI Gym},
  Year = {2016},
  Eprint = {arXiv:1606.01540},
}
```

## Release Notes

There used to be release notes for all the new Gym versions here. New release notes are being moved to [releases page](https://github.com/openai/gym/releases) on GitHub, like most other libraries do. Old notes can be viewed [here](https://github.com/openai/gym/blob/31be35ecd460f670f0c4b653a14c9996b7facc6c/README.rst).
