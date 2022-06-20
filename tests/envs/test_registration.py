import re

import numpy as np
import pytest

import gym
from gym import envs, error
from gym.envs import register, registration, registry, spec
from gym.envs.classic_control import cartpole
from gym.wrappers import HumanRendering
from tests.wrappers.utils import has_wrapper


class ArgumentEnv(gym.Env):
    observation_space = gym.spaces.Box(low=0, high=1, shape=(1,))
    action_space = gym.spaces.Box(low=0, high=1, shape=(1,))

    def __init__(self, arg1, arg2, arg3):
        self.arg1 = arg1
        self.arg2 = arg2
        self.arg3 = arg3


# Environments to test render_mode
class NoHuman(gym.Env):
    """Environment that does not have human-rendering."""

    metadata = {"render_modes": ["rgb_array"], "render_fps": 4}

    def __init__(self, render_mode=None):
        assert render_mode in self.metadata["render_modes"]
        self.render_mode = render_mode


class NoHumanOldAPI(gym.Env):
    """Environment that does not have human-rendering."""

    metadata = {"render_modes": ["rgb_array"], "render_fps": 4}

    def __init__(self):
        pass


class NoHumanNoRGB(gym.Env):
    """Environment that has neither human- nor rgb-rendering"""

    metadata = {"render_modes": ["ascii"], "render_fps": 4}

    def __init__(self, render_mode=None):
        assert render_mode in self.metadata["render_modes"]
        self.render_mode = render_mode


gym.register(
    id="test.ArgumentEnv-v0",
    entry_point="tests.envs.test_registration:ArgumentEnv",
    kwargs={
        "arg1": "arg1",
        "arg2": "arg2",
    },
)
gym.register(
    id="test/NoHuman-v0",
    entry_point="tests.envs.test_registration:NoHuman",
)
gym.register(
    id="test/NoHumanOldAPI-v0",
    entry_point="tests.envs.test_registration:NoHumanOldAPI",
)

gym.register(
    id="test/NoHumanNoRGB-v0",
    entry_point="tests.envs.test_registration:NoHumanNoRGB",
)


@pytest.fixture(scope="function")
def register_some_envs():
    namespace = "MyAwesomeNamespace"
    versioned_name = "MyAwesomeVersionedEnv"
    unversioned_name = "MyAwesomeUnversionedEnv"
    versions = [1, 3, 5]
    for version in versions:
        env_id = f"{namespace}/{versioned_name}-v{version}"
        gym.register(
            id=env_id,
            entry_point="tests.envs.test_registration:ArgumentEnv",
            kwargs={
                "arg1": "arg1",
                "arg2": "arg2",
                "arg3": "arg3",
            },
        )
    gym.register(
        id=f"{namespace}/{unversioned_name}",
        entry_point="tests.env.test_registration:ArgumentEnv",
        kwargs={
            "arg1": "arg1",
            "arg2": "arg2",
            "arg3": "arg3",
        },
    )

    yield

    for version in versions:
        env_id = f"{namespace}/{versioned_name}-v{version}"
        del gym.envs.registry[env_id]
    del gym.envs.registry[f"{namespace}/{unversioned_name}"]


def test_make():
    env = envs.make("CartPole-v1", disable_env_checker=True)
    assert env.spec.id == "CartPole-v1"
    assert isinstance(env.unwrapped, cartpole.CartPoleEnv)


@pytest.mark.parametrize(
    "env_id, namespace, name, version",
    [
        (
            "MyAwesomeNamespace/MyAwesomeEnv-v0",
            "MyAwesomeNamespace",
            "MyAwesomeEnv",
            0,
        ),
        ("MyAwesomeEnv-v0", None, "MyAwesomeEnv", 0),
        ("MyAwesomeEnv", None, "MyAwesomeEnv", None),
        ("MyAwesomeEnv-vfinal-v0", None, "MyAwesomeEnv-vfinal", 0),
        ("MyAwesomeEnv-vfinal", None, "MyAwesomeEnv-vfinal", None),
        ("MyAwesomeEnv--", None, "MyAwesomeEnv--", None),
        ("MyAwesomeEnv-v", None, "MyAwesomeEnv-v", None),
    ],
)
def test_register(env_id, namespace, name, version):
    register(env_id)
    assert gym.envs.spec(env_id).id == env_id
    full_name = f"{name}"
    if namespace:
        full_name = f"{namespace}/{full_name}"
    if version is not None:
        full_name = f"{full_name}-v{version}"
    assert full_name in gym.envs.registry.keys()
    del gym.envs.registry[env_id]


@pytest.mark.parametrize(
    "env_id",
    [
        "“Breakout-v0”",
        "MyNotSoAwesomeEnv-vNone\n",
        "MyNamespace///MyNotSoAwesomeEnv-vNone",
    ],
)
def test_register_error(env_id):
    with pytest.raises(error.Error, match="Malformed environment ID"):
        register(env_id)


@pytest.mark.parametrize(
    "env_id_input, env_id_suggested",
    [
        ("cartpole-v1", "CartPole"),
        ("blackjack-v1", "Blackjack"),
        ("Blackjock-v1", "Blackjack"),
        ("mountaincarcontinuous-v0", "MountainCarContinuous"),
        ("taxi-v3", "Taxi"),
        ("taxi-v30", "Taxi"),
        ("MyAwesomeNamspce/MyAwesomeVersionedEnv-v1", "MyAwesomeNamespace"),
        ("MyAwesomeNamspce/MyAwesomeUnversionedEnv", "MyAwesomeNamespace"),
        ("MyAwesomeNamespace/MyAwesomeUnversioneEnv", "MyAwesomeUnversionedEnv"),
        ("MyAwesomeNamespace/MyAwesomeVersioneEnv", "MyAwesomeVersionedEnv"),
    ],
)
def test_env_suggestions(register_some_envs, env_id_input, env_id_suggested):
    with pytest.raises(
        error.UnregisteredEnv, match=f"Did you mean: `{env_id_suggested}` ?"
    ):
        gym.make(env_id_input, disable_env_checker=True)


@pytest.mark.parametrize(
    "env_id_input, suggested_versions, default_version",
    [
        ("CartPole-v12", "`v0`, `v1`", False),
        ("Blackjack-v10", "`v1`", False),
        ("MountainCarContinuous-v100", "`v0`", False),
        ("Taxi-v30", "`v3`", False),
        ("MyAwesomeNamespace/MyAwesomeVersionedEnv-v6", "`v1`, `v3`, `v5`", False),
        ("MyAwesomeNamespace/MyAwesomeUnversionedEnv-v6", "", True),
    ],
)
def test_env_version_suggestions(
    register_some_envs, env_id_input, suggested_versions, default_version
):
    if default_version:
        match_str = "provides the default version"
        with pytest.raises(
            error.DeprecatedEnv,
            match=match_str,
        ):
            envs.make(env_id_input, disable_env_checker=True)
    else:
        match_str = f"versioned environments: \\[ {suggested_versions} \\]"
        with pytest.raises(
            error.UnregisteredEnv,
            match=match_str,
        ):
            envs.make(env_id_input, disable_env_checker=True)


def test_make_with_kwargs():
    env = envs.make(
        "test.ArgumentEnv-v0",
        arg2="override_arg2",
        arg3="override_arg3",
        disable_env_checker=True,
    )
    assert env.spec.id == "test.ArgumentEnv-v0"
    assert isinstance(env.unwrapped, ArgumentEnv)
    assert env.arg1 == "arg1"
    assert env.arg2 == "override_arg2"
    assert env.arg3 == "override_arg3"


@pytest.mark.filterwarnings(
    "ignore:.*The environment Humanoid-v0 is out of date. You should consider upgrading to "
    "version `v3` with the environment ID `Humanoid-v3`.*"
)
def test_make_deprecated():
    try:
        envs.make("Humanoid-v0")
    except error.Error:
        pass
    else:
        assert False


def test_spec():
    spec = envs.spec("CartPole-v1")
    assert spec.id == "CartPole-v1"


def test_spec_with_kwargs():
    map_name_value = "8x8"
    env = gym.make(
        "FrozenLake-v1",
        map_name=map_name_value,
    )
    assert env.spec.kwargs["map_name"] == map_name_value


def test_missing_lookup():
    register(id="Test1-v0", entry_point=None)
    register(id="Test1-v15", entry_point=None)
    register(id="Test1-v9", entry_point=None)
    register(id="Other1-v100", entry_point=None)

    with pytest.raises(error.DeprecatedEnv):
        spec("Test1-v1")

    try:
        spec("Test1-v1000")
    except error.UnregisteredEnv:
        pass
    else:
        assert False

    try:
        spec("Unknown1-v1")
    except error.UnregisteredEnv:
        pass
    else:
        assert False


def test_malformed_lookup():
    try:
        spec("“Breakout-v0”")
    except error.Error as e:
        assert "Malformed environment ID" in f"{e}", f"Unexpected message: {e}"
    else:
        assert False


def test_versioned_lookups():
    register("test/Test2-v5")

    with pytest.raises(error.VersionNotFound):
        spec("test/Test2-v9")

    with pytest.raises(error.DeprecatedEnv):
        spec("test/Test2-v4")

    assert spec("test/Test2-v5")


def test_default_lookups():
    register("test/Test3")

    with pytest.raises(error.DeprecatedEnv):
        spec("test/Test3-v0")

    # Lookup default
    spec("test/Test3")


def test_register_versioned_unversioned():
    # Register versioned then unversioned
    versioned_env = "Test/MyEnv-v0"
    register(versioned_env)
    assert gym.envs.spec(versioned_env).id == versioned_env
    unversioned_env = "Test/MyEnv"
    with pytest.raises(error.RegistrationError):
        register(unversioned_env)

    # Clean everything
    del gym.envs.registry[versioned_env]

    # Register unversioned then versioned
    register(unversioned_env)
    assert gym.envs.spec(unversioned_env).id == unversioned_env
    with pytest.raises(error.RegistrationError):
        register(versioned_env)

    # Clean everything
    del gym.envs.registry[unversioned_env]


def test_return_latest_versioned_env(register_some_envs):
    with pytest.warns(UserWarning):
        env = envs.make(
            "MyAwesomeNamespace/MyAwesomeVersionedEnv", disable_env_checker=True
        )
    assert env.spec.id == "MyAwesomeNamespace/MyAwesomeVersionedEnv-v5"


def test_namespace():
    # Check if the namespace context manager works
    with registration.namespace("MyDefaultNamespace"):
        register("MyDefaultEnvironment-v0")
    register("MyDefaultEnvironment-v1")
    assert "MyDefaultNamespace/MyDefaultEnvironment-v0" in registry
    assert "MyDefaultEnvironment-v1" in registry

    del registry["MyDefaultNamespace/MyDefaultEnvironment-v0"]
    del registry["MyDefaultEnvironment-v1"]


def test_import_module_during_make():
    # Test custom environment which is registered at make
    gym.make(
        "tests.envs.register_during_make_env:RegisterDuringMakeEnv-v0",
        disable_env_checker=True,
    )


def test_make_render_mode():
    # Make sure that render_mode is applied correctly
    env = gym.make("CartPole-v1", render_mode="rgb_array", disable_env_checker=True)
    assert env.render_mode == "rgb_array"
    env.reset()
    renders = env.render()
    assert isinstance(
        renders, list
    )  # Make sure that the `render` method does what is supposed to
    assert isinstance(renders[0], np.ndarray)
    env.close()

    # Make sure that native rendering is used when possible
    env = gym.make("CartPole-v1", render_mode="human", disable_env_checker=True)
    assert not has_wrapper(env, HumanRendering)  # Should use native human-rendering
    assert env.render_mode == "human"
    env.close()

    # Make sure that `HumanRendering` is applied here
    env = gym.make(
        "test/NoHuman-v0", render_mode="human", disable_env_checker=True
    )  # This environment doesn't use native rendering
    assert has_wrapper(env, HumanRendering)
    assert env.render_mode == "human"
    env.close()

    # Make sure that an error is thrown a user tries to use the wrapper on an environment with old API
    with pytest.raises(
        AttributeError,
        match=re.escape(
            "You\\ passed\\ render_mode='human'\\ although\\ .* doesn't\\ implement\\ human\\-rendering\\ natively\\."
        ),
    ):
        gym.make("test/NoHumanOldAPI-v0", render_mode="human", disable_env_checker=True)

    # Make sure that the `HumanRendering` is not applied if the environment doesn't have rgb-rendering
    with pytest.raises(
        gym.error.Error,
        match=re.escape(
            "Invalid render_mode provided: human. Valid render_modes: None, ascii"
        ),
    ):
        gym.make("test/NoHumanNoRGB-v0", render_mode="human", disable_env_checker=True)

    # Make sure that an error is thrown if the mode is not supported
    with pytest.raises(
        gym.error.Error,
        match=re.escape(
            "Invalid render_mode provided: ascii. Valid render_modes: None, rgb_array"
        ),
    ):
        gym.make("test/NoHuman-v0", render_mode="ascii", disable_env_checker=True)
