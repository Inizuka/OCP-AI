"""Wrapper for recording videos."""
import os
from typing import Callable

import gym
from gym import logger
from gym.wrappers.monitoring import video_recorder


def capped_cubic_video_schedule(episode_id: int) -> bool:
    """Checks if the video schedule if cubic capped."""
    if episode_id < 1000:
        return int(round(episode_id ** (1.0 / 3))) ** 3 == episode_id
    else:
        return episode_id % 1000 == 0


class RecordVideo(gym.Wrapper):
    """This wrapper records videos of rollouts.

    Usually, you only want to record episodes intermittently, say every hundreth episode.
    To do this, you can specify **either** `episode_trigger` **or** `step_trigger` (not both).
    They should be functions returning a boolean that indicates whether a recording should be started at the
    current episode or step, respectively.
    If neither `episode_trigger` nor `step_trigger` is passed, a default `episode_trigger` will be employed.
    By default, the recording will be stopped once a `done` signal has been emitted by the environment. However, you can
    also create recordings of fixed length (possibly spanning several episodes) by passing a strictly positive value for
    `video_length`.

    Args:
        env: The environment that will be wrapped
        video_folder (str): The folder where the recordings will be stored
        episode_trigger: Function that accepts an integer and returns `True` iff a recording should be started at this episode
        step_trigger: Function that accepts an integer and returns `True` iff a recording should be started at this step
        video_length (int): The length of recorded episodes. If 0, entire episodes are recorded. Otherwise, snippets of the specified length are captured
        name_prefix (str): Will be prepended to the filename of the recordings
    """

    def __init__(
        self,
        env: gym.Env,
        video_folder: str,
        episode_trigger: Callable[[int], bool] = None,
        step_trigger: Callable[[int], bool] = None,
        video_length: int = 0,
        name_prefix: str = "rl-video",
    ):
        """Wrapper records videos of rollouts.

        Args:
            env: The environment that will be wrapped
            video_folder (str): The folder where the recordings will be stored
            episode_trigger: Function that accepts an integer and returns `True` iff a recording should be started at this episode
            step_trigger: Function that accepts an integer and returns `True` iff a recording should be started at this step
            video_length (int): The length of recorded episodes. If 0, entire episodes are recorded. Otherwise, snippets of the specified length are captured
            name_prefix (str): Will be prepended to the filename of the recordings
        """
        super().__init__(env)

        if episode_trigger is None and step_trigger is None:
            episode_trigger = capped_cubic_video_schedule

        trigger_count = sum(x is not None for x in [episode_trigger, step_trigger])
        assert trigger_count == 1, "Must specify exactly one trigger"

        self.episode_trigger = episode_trigger
        self.step_trigger = step_trigger
        self.video_recorder = None

        self.video_folder = os.path.abspath(video_folder)
        # Create output folder if needed
        if os.path.isdir(self.video_folder):
            logger.warn(
                f"Overwriting existing videos at {self.video_folder} folder (try specifying a different `video_folder` for the `RecordVideo` wrapper if this is not desired)"
            )
        os.makedirs(self.video_folder, exist_ok=True)

        self.name_prefix = name_prefix
        self.step_id = 0
        self.video_length = video_length

        self.recording = False
        self.recorded_frames = 0
        self.is_vector_env = getattr(env, "is_vector_env", False)
        self.episode_id = 0

    def reset(self, **kwargs):
        """Reset the environment using kwargs and then starts recording if video enabled."""
        observations = super().reset(**kwargs)
        if not self.recording and self._video_enabled():
            self.start_video_recorder()
        return observations

    def start_video_recorder(self):
        """Starts video recorder using video_recorder.VideoRecorder."""
        self.close_video_recorder()

        video_name = f"{self.name_prefix}-step-{self.step_id}"
        if self.episode_trigger:
            video_name = f"{self.name_prefix}-episode-{self.episode_id}"

        base_path = os.path.join(self.video_folder, video_name)
        self.video_recorder = video_recorder.VideoRecorder(
            env=self.env,
            base_path=base_path,
            metadata={"step_id": self.step_id, "episode_id": self.episode_id},
        )

        self.video_recorder.capture_frame()
        self.recorded_frames = 1
        self.recording = True

    def _video_enabled(self):
        if self.step_trigger:
            return self.step_trigger(self.step_id)
        else:
            return self.episode_trigger(self.episode_id)

    def step(self, action):
        """Steps through the environment using action, recording observations if self.recording."""
        observations, rewards, dones, infos = super().step(action)

        # increment steps and episodes
        self.step_id += 1
        if not self.is_vector_env:
            if dones:
                self.episode_id += 1
        elif dones[0]:
            self.episode_id += 1

        if self.recording:
            self.video_recorder.capture_frame()
            self.recorded_frames += 1
            if self.video_length > 0:
                if self.recorded_frames > self.video_length:
                    self.close_video_recorder()
            else:
                if not self.is_vector_env:
                    if dones:
                        self.close_video_recorder()
                elif dones[0]:
                    self.close_video_recorder()

        elif self._video_enabled():
            self.start_video_recorder()

        return observations, rewards, dones, infos

    def close_video_recorder(self):
        """Closes the video recorder if currently recording."""
        if self.recording:
            self.video_recorder.close()
        self.recording = False
        self.recorded_frames = 1

    def close(self):
        """Closes the wrapper then the video recorder."""
        super().close()
        self.close_video_recorder()

    def __del__(self):
        """Closes the video recorder."""
        self.close_video_recorder()
