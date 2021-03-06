""" Implements data structures to save and sample previous
observations, actions, rewards and terminals.

RingBuffer implementation is from
https://github.com/matthiasplappert/keras-rl/
"""

import numpy as np

class RingBuffer(object):
  def __init__(self, max_length):
    self.max_length = max_length
    self.start = 0
    self.length = 0
    self.data = [None] * self.max_length

  def __len__(self):
    return self.length

  def __getitem__(self, index):
    if index < 0 or index >= self.length:
      raise KeyError('Index: {}'.format(index))
    return self.data[(self.start + index) % self.max_length]

  def append(self, value):
    if self.length < self.max_length:
      self.length += 1
    elif self.length == self.max_length:
      self.start = (self.start + 1) % self.max_length

    self.data[(self.start + self.length - 1) % self.max_length] = value

class ExperienceMemory(object):
  def __init__(self, memory_length=10000):
    self.memory_length = memory_length
    self.actions = RingBuffer(memory_length)
    self.rewards = RingBuffer(memory_length)
    self.observations = RingBuffer(memory_length)
    self.terminals = RingBuffer(memory_length)

  def save_experience(self, observation, action, reward, done):
    self.observations.append(observation)
    self.actions.append(action)
    self.rewards.append(reward)
    self.terminals.append(done)

  def get_exp_window(self, end, window_size):
    observations = []
    # The terminality of the last observation does not affect
    # computation. The last observation of the first window (second
    # index in this loop) determines the action, reward and
    # and terminality of the window.
    for i in range(window_size):
      # Terminals at an earlier index than end - 1 belong to another
      # episode.
      if i > 1 and self.terminals[end - i] == True:
        break
      observations.append(self.observations[end - i])

    # pad to full window_size with the first observation
    while len(observations) < window_size:
      observations = observations + [observations[-1]]

    observations.reverse()

    return observations

  def sample_minibatch(self, batch_size, window_size):
    full_window_size = window_size + 1
    mb_actions = []
    mb_rewards = []
    mb_first_obs = []
    mb_second_obs = []
    mb_terms = []

    last_index = len(self.observations) - 1
    window_ends = np.random.randint(window_size, last_index,
        size=batch_size)
    # always include the latest observation for training
    window_ends[-1] = last_index

    for end in window_ends:
      observations = self.get_exp_window(end, full_window_size)
      mb_first_obs += observations[0:-1]
      mb_second_obs += observations[1:]
      mb_actions.append(self.actions[end-1])
      mb_rewards.append(self.rewards[end-1])
      mb_terms.append(self.terminals[end-1])

    return mb_first_obs, mb_actions, mb_rewards, mb_second_obs, mb_terms
