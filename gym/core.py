"""Core API for Environment, Wrapper, ActionWrapper, RewardWrapper and ObservationWrapper."""
from __future__ import annotations

from abc import abstractmethod
from typing import Generic, Optional, SupportsFloat, TypeVar, Union

from gym import spaces
from gym.logger import deprecation
from gym.utils import seeding
from gym.utils.seeding import RandomNumberGenerator

ObsType = TypeVar("ObsType")
ActType = TypeVar("ActType")


class Env(Generic[ObsType, ActType]):
    r"""The main OpenAI Gym class.

    It encapsulates an environment with arbitrary behind-the-scenes dynamics.
    An environment can be partially or fully observed.

    The main API methods that users of this class need to know are:
    - :meth:`step` - Takes a step in the environment using an action returning the next observation,
        reward, if the environment terminated and more information.
    - :meth:`reset` - Resets the environment to an initial state, returning the initial observation.
    - :meth:`render` - Renders the environment observation with modes depending on the output
    - :meth:`close` - Closes the environment, important for rendering where pygame is imported
    - :meth:`seed` - Seeds the environment's random number generator, this is deprecated function for :meth:`reset(seed)`.

    And set the following attributes:
    - :attr:`action_space` - The Space object corresponding to valid actions
    - :attr:`observation_space` - The Space object corresponding to valid observations
    - :attr:`reward_range` - A tuple corresponding to the minimum and maximum possible rewards
    - :attr:`spec` - An environment spec that contains the information used to initialise the environment from `gym.make`
    - :attr:`metadata` - The metadata of the environment, i.e. render modes
    - :attr:`np_random` - The random number generator for the environment

    Note: a default reward range set to [-\inf,+\inf] already exists. Set it if you want a narrower range.
    """

    # Set this in SOME subclasses
    metadata = {"render_modes": []}
    reward_range = (-float("inf"), float("inf"))
    spec = None

    # Set these in ALL subclasses
    action_space: spaces.Space[ActType]
    observation_space: spaces.Space[ObsType]

    # Created
    _np_random: Optional[RandomNumberGenerator] = None

    @property
    def np_random(self) -> RandomNumberGenerator:
        """Returns the environment's internal :attr:`_np_random` that if not set will initialises with a random seed."""
        if self._np_random is None:
            self._np_random, seed = seeding.np_random()
        return self._np_random

    @np_random.setter
    def np_random(self, value: RandomNumberGenerator):
        self._np_random = value

    @abstractmethod
    def step(self, action: ActType) -> tuple[ObsType, float, bool, dict]:
        """Run one timestep of the environment's dynamics.

        When end of episode is reached, you are responsible for calling :meth:`reset` to reset this environment's state.
        Accepts an action and returns a tuple `(observation, reward, done, info)`.

        Args:
            action (object): an action provided by the agent

        Returns:
            ``(observation, reward, done, info)``: A tuple containing the environment's current `observation`, `reward` for the previous step,
            `done` if the episode has terminated and `info` for more information about the step.
            For the `observation` this will be an element of the environment's :attr:`observation_space`. This may, for instance, be a numpy array containing the positions and velocities of certain objects.
            For the `reward` will be the amount of reward returned after previous action.
            `done` is whether the episode has ended, in which case further :meth:`step` calls will return undefined results.
            A done signal may be emitted for different reasons: Maybe the task underlying the environment was solved successfully, a certain timelimit was exceeded, or the physics simulation has entered an invalid state.
            `info` may contain additional information regarding the reason for a ``done`` signal.
            `info` contains auxiliary diagnostic information (helpful for debugging, learning, and logging). This might, for instance, contain: metrics that describe the agent's performance state, variables that are hidden from observations,
            information that distinguishes truncation and termination or individual reward terms that are combined to produce the total reward
        """
        raise NotImplementedError

    @abstractmethod
    def reset(
        self,
        *,
        seed: Optional[int] = None,
        return_info: bool = False,
        options: Optional[dict] = None,
    ) -> Union[ObsType, tuple[ObsType, dict]]:
        """Resets the environment to an initial state and returns the initial observation.

        This method can reset the environment's random number
        generator(s) if :param:`seed` is an integer or if the environment has not
        yet initialized a random number generator. If the environment already
        has a random number generator and :meth:`reset` is called with ``seed=None``,
        the RNG should not be reset.
        Moreover, :meth:`reset` should (in the typical use case) be called with an
        integer seed right after initialization and then never again.

        Args:
            seed (int or None): The seed that is used to initialize the environment's PRNG.
                If the environment does not already have a PRNG and ``seed=None`` (the default option) is passed, a seed will be chosen from some source of entropy (e.g. timestamp or /dev/urandom).
                However, if the environment already has a PRNG and ``seed=None`` is passed, the PRNG will *not* be reset. If you pass an integer, the PRNG will be reset even if it already exists.
                Usually, you want to pass an integer *right after the environment has been initialized and then never again*. Please refer to the minimal example above to see this paradigm in action.
            return_info (bool): If true, return additional information along with initial observation. This info should be analogous to the info returned in :meth:`step`
            options (dict or None): Additional information to specify how the environment is reset (optional, depending on the specific environment)


        Returns:
            observation (object): Observation of the initial state. This will be an element of :attr:`observation_space` (usually a numpy array) and is analogous to the observation returned by :meth:`step`.
            info (optional dictionary): This will *only* be returned if ``return_info=True`` is passed. It contains auxiliary information complementing ``observation``. This dictionary should be analogous to the ``info`` returned by :meth:`step`.
        """
        # Initialize the RNG if the seed is manually passed
        if seed is not None:
            self._np_random, seed = seeding.np_random(seed)

    @abstractmethod
    def render(self, mode="human"):
        """Renders the environment.

        A set of supported modes varies per environment. (And some
        third-party environments may not support rendering at all.)
        By convention, if mode is:

        - human: render to the current display or terminal and
          return nothing. Usually for human consumption.
        - rgb_array: Return an numpy.ndarray with shape (x, y, 3),
          representing RGB values for an x-by-y pixel image, suitable
          for turning into a video.
        - ansi: Return a string (str) or StringIO.StringIO containing a
          terminal-style text representation. The text can include newlines
          and ANSI escape sequences (e.g. for colors).

        Note:
            Make sure that your class's metadata 'render_modes' key includes
              the list of supported modes. It's recommended to call super()
              in implementations to use the functionality of this method.

        Example:
            >>> class MyEnv(Env):
            ...    metadata = {'render_modes': ['human', 'rgb_array']}
            ...
            ...    def render(self, mode='human'):
            ...        if mode == 'rgb_array':
            ...            return np.array(...) # return RGB frame suitable for video
            ...        elif mode == 'human':
            ...            ... # pop up a window and render
            ...        else:
            ...            super(MyEnv, self).render(mode=mode) # just raise an exception

        Args:
            mode: the mode to render with, valid modes are `env.metadata["render_modes"]`
        """
        raise NotImplementedError

    def close(self):
        """Override close in your subclass to perform any necessary cleanup.

        Environments will automatically close() themselves when
        garbage collected or when the program exits.
        """
        pass

    def seed(self, seed=None):
        """Deprecated function that sets the seed for the env's random number generator(s).

        Use `env.reset(seed=seed)` as the new API for setting the seed of the environment.

        Note:
            Some environments use multiple pseudorandom number generators.
            We want to capture all such seeds used in order to ensure that
            there aren't accidental correlations between multiple generators.

        Returns:
            list<bigint>: Returns the list of seeds used in this env's random
              number generators. The first value in the list should be the
              "main" seed, or the value which a reproducer should pass to
              'seed'. Often, the main seed equals the provided 'seed', but
              this won't be true if seed=None, for example.
        """
        deprecation(
            "Function `env.seed(seed)` is marked as deprecated and will be removed in the future. "
            "Please use `env.reset(seed=seed)` instead."
        )
        self._np_random, seed = seeding.np_random(seed)
        return [seed]

    @property
    def unwrapped(self) -> Env:
        """Returns the base non-wrapped environment.

        Returns:
            gym.Env: The base non-wrapped gym.Env instance
        """
        return self

    def __str__(self):
        """Returns a string of the environment with the spec id if specified."""
        if self.spec is None:
            return f"<{type(self).__name__} instance>"
        else:
            return f"<{type(self).__name__}<{self.spec.id}>>"

    def __enter__(self):
        """Support with-statement for the environment."""
        return self

    def __exit__(self, *args):
        """Support with-statement for the environment."""
        self.close()
        # propagate exception
        return False


class Wrapper(Env[ObsType, ActType]):
    """Wraps an environment to allow a modular transformation of the :meth:`step` and :meth:`reset` methods.

    This class is the base class for all wrappers. The subclass could override
    some methods to change the behavior of the original environment without touching the
    original code.

    Note:
        Don't forget to call ``super().__init__(env)`` if the subclass overrides :meth:`__init__`.
    """

    def __init__(self, env: Env):
        """Wraps an environment to allow a modular transformation of the :meth:`step` and :meth:`reset` methods.

        Args:
            env: The environment to wrap
        """
        self.env = env

        self._action_space: Optional[spaces.Space] = None
        self._observation_space: Optional[spaces.Space] = None
        self._reward_range: Optional[tuple[SupportsFloat, SupportsFloat]] = None
        self._metadata: Optional[dict] = None

    def __getattr__(self, name):
        """Returns an attribute with :param:`name`, unless :param:`name` starts with an underscore."""
        if name.startswith("_"):
            raise AttributeError(f"accessing private attribute '{name}' is prohibited")
        return getattr(self.env, name)

    @property
    def spec(self):
        """Returns the environment specification."""
        return self.env.spec

    @classmethod
    def class_name(cls):
        """Returns the class name of the wrapper."""
        return cls.__name__

    @property
    def action_space(self) -> spaces.Space[ActType]:
        """Returns the action space of the environment."""
        if self._action_space is None:
            return self.env.action_space
        return self._action_space

    @action_space.setter
    def action_space(self, space: spaces.Space):
        self._action_space = space

    @property
    def observation_space(self) -> spaces.Space:
        """Returns the observation space of the environment."""
        if self._observation_space is None:
            return self.env.observation_space
        return self._observation_space

    @observation_space.setter
    def observation_space(self, space: spaces.Space):
        self._observation_space = space

    @property
    def reward_range(self) -> tuple[SupportsFloat, SupportsFloat]:
        """Return the reward range of the environment."""
        if self._reward_range is None:
            return self.env.reward_range
        return self._reward_range

    @reward_range.setter
    def reward_range(self, value: tuple[SupportsFloat, SupportsFloat]):
        self._reward_range = value

    @property
    def metadata(self) -> dict:
        """Returns the environment metadata."""
        if self._metadata is None:
            return self.env.metadata
        return self._metadata

    @metadata.setter
    def metadata(self, value):
        self._metadata = value

    def step(self, action: ActType) -> tuple[ObsType, float, bool, dict]:
        """Steps through the environment with action."""
        return self.env.step(action)

    def reset(self, **kwargs) -> Union[ObsType, tuple[ObsType, dict]]:
        """Resets the environment with kwargs."""
        return self.env.reset(**kwargs)

    def render(self, **kwargs):
        """Renders the environment with kwargs."""
        return self.env.render(**kwargs)

    def close(self):
        """Closes the environment."""
        return self.env.close()

    def seed(self, seed=None):
        """Seeds the environment."""
        return self.env.seed(seed)

    def __str__(self):
        """Returns the wrapper name and the unwrapped environment string."""
        return f"<{type(self).__name__}{self.env}>"

    def __repr__(self):
        """Returns the string representation of the wrapper."""
        return str(self)

    @property
    def unwrapped(self) -> Env:
        """Returns the base environment of the wrapper."""
        return self.env.unwrapped


class ObservationWrapper(Wrapper):
    """A wrapper that can modify observations using :meth:`observation` for :meth:`reset` and :meth:`step`."""

    def reset(self, **kwargs):
        """Resets the environment, returning a modified observation using :meth:`self.observation`."""
        if kwargs.get("return_info", False):
            obs, info = self.env.reset(**kwargs)
            return self.observation(obs), info
        else:
            return self.observation(self.env.reset(**kwargs))

    def step(self, action):
        """Returns a modified observation using :meth:`self.observation` after calling :meth:`env.step`."""
        observation, reward, done, info = self.env.step(action)
        return self.observation(observation), reward, done, info

    @abstractmethod
    def observation(self, observation):
        """Returns a modified observation."""
        raise NotImplementedError


class RewardWrapper(Wrapper):
    """A wrapper that can modify the returning reward from a step."""

    def step(self, action):
        """Modifies the reward using :meth:`self.reward` after the environment :meth:`env.step`."""
        observation, reward, done, info = self.env.step(action)
        return observation, self.reward(reward), done, info

    @abstractmethod
    def reward(self, reward):
        """Returns a modified :param:`reward`."""
        raise NotImplementedError


class ActionWrapper(Wrapper):
    """A wrapper that can modify the action before :meth:`env.step`."""

    def step(self, action):
        """Runs the environment :meth:`env.step` using the modified :param:`action` from :meth:`self.action`."""
        return self.env.step(self.action(action))

    @abstractmethod
    def action(self, action):
        """Returns a modified action before :meth:`env.step` is called."""
        raise NotImplementedError

    @abstractmethod
    def reverse_action(self, action):
        """Returns a reversed :param:`action`."""
        raise NotImplementedError
