import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.nn.utils.rnn import pad_sequence, pack_padded_sequence
import numpy as np

class generator(nn.Module):
	def __init__(self, embedding_dim, hidden_size=400, n_layers=2, lr=0.001):
		super(generator, self).__init__()

		self.embedding_dim = embedding_dim
		self.out_size = embedding_dim
		self.hidden_size = hidden_size
		self.n_layers = n_layers
		self.lr = lr
		self.losses = []
		self.discount = 0.9
		self.pretrained_path = "models/Generator_pretrained.pt"
		self.chkpt_path = "models/Generator.pt"

		self.lstm = nn.LSTM(self.embedding_dim, self.hidden_size, self.n_layers, batch_first=True)
		self.mean = nn.Sequential(
			nn.Linear(self.hidden_size, 400),
			nn.ReLU(),
			nn.Linear(400, 300),
			nn.ReLU(),
			nn.Linear(300, 128),
			nn.ReLU(),
			nn.Linear(128, embedding_dim),
			nn.Softmax(dim=1)
		)
		self.std = nn.Sequential(
			nn.Linear(self.hidden_size, 400),
			nn.ReLU(),
			nn.Linear(400, 300),
			nn.ReLU(),
			nn.Linear(300, 128),
			nn.ReLU(),
			nn.Linear(128, embedding_dim),
			nn.Softmax(dim=1)
		)

		self.criterion = nn.CrossEntropyLoss()
		self.optimizer = optim.Adam(self.parameters(), self.lr)

	def forward(self, input):
		# take the last values from the lstm-forward pass
		lstm_out, _ = self.lstm(input)
		lstm_out = lstm_out[:, -1].view(-1, self.hidden_size)

		# get the mean and standard deviation
		mean = self.mean(lstm_out)
		std = torch.exp(self.std(lstm_out))

		# sample the action based on the output from the networks
		distributions = torch.distributions.Normal(mean, std)
		actions = distributions.sample()

		# initialize the memories needed for REINFORCE
		self.action_memory[:, input.shape[1]-1] = torch.mean(distributions.log_prob(actions))
		self.reward_memory = torch.empty_like(self.action_memory)
		return actions

	def generate(self, batch_size, seed=None):
		"""returns one generated sequence and optimizes the generator"""
		# ADD SUPPORT FOR <end> HERE

		haiku_length = np.random.randint(12, 16)  # length boundaries are arbitrary
		output = torch.zeros(batch_size, haiku_length + 1, self.out_size) # first element from the output is the inital seed
		self.action_memory = torch.zeros(batch_size, haiku_length)

		# generate sequence starting from a given seed
		for i in range(1, haiku_length + 1):
			# forward pass
			input = output[:, :i].clone()  # inplace operation, clone is necessary
			output[:, i] = self(input).view(batch_size, self.out_size)		

		#remove the seed again
		return output[:, 1:]

	def learn(self, fake_sample, discriminator):
		# This is just plain REINFORCE
		batch_size = fake_sample.shape[0]
		seq_length = fake_sample.shape[1]

		# fill the reward memory using Monte Carlo
		self.reward_memory = torch.zeros_like(self.action_memory)
		for seq_ix in range(fake_sample.shape[1]): # the generator didnt take the first action, it was the seed

			#the amount of rollouts performed is proportional to their length
			num_rollouts = fake_sample.shape[1] - seq_ix
			qualities = torch.zeros(batch_size, num_rollouts)

			for rollout_ix in range(num_rollouts):
				# initiate starting sequence + seed
				completed = torch.zeros(batch_size, seq_length + 1, self.out_size)
				completed[:, 1:seq_ix + 1] = fake_sample[:, :seq_ix]


				# rollout the remaining part of the sequence, rollout policy = generator policy
				for j in range(seq_ix + 1, fake_sample.shape[1] + 1):
					input = completed[:, :j].clone().view(batch_size, j, self.out_size)

					# choose action
					action = self(input)
					completed[:, j] = action

				# get the estimated reward for that rollout from the discriminator
				qualities[:, rollout_ix] = discriminator(completed[:, 1:]).detach()

			self.reward_memory[:, seq_ix] = torch.mean(qualities, dim=1)

		# normalize the rewards
		std, mean = torch.std_mean(self.reward_memory, dim=1, unbiased=False)  # avoid bessel
		std[std == 0] = 1  # remove zeros from std
		self.reward_memory = (self.reward_memory - mean.view(-1, 1)) / std.view(-1, 1)

		# calculate the discounted future rewards for every action
		discounted_rewards = torch.zeros(batch_size, seq_length)
		for batch_ix in range(batch_size):
			for seq_ix in range(seq_length):
				discounted_reward = 0
				for t in range(seq_ix, seq_length):
					discounted_reward += (self.discount**(t-seq_ix)) * self.reward_memory[batch_ix, t]
				discounted_rewards[batch_ix, seq_ix] = discounted_reward

		# calculate the loss using the REINFORCE Algorithm
		total_loss = 0
		for batch_ix in range(batch_size):
			for seq_ix in range(seq_length):
				total_loss += -1 * discounted_rewards[batch_ix, seq_ix] * self.action_memory[batch_ix, seq_ix]

		# optimize the agent
		self.optimizer.zero_grad()
		total_loss.backward()
		self.optimizer.step()

		self.losses.append(total_loss.item())
		if total_loss.item() < 0:
			print("--")
			print(discounted_rewards, self.reward_memory)
		return total_loss, self.action_memory, discounted_rewards, completed

	def loadModel(self, path=None):
		if path is None:
			path = self.pretrained_path
		self.load_state_dict(torch.load(path))

	def saveModel(self, path=None):
		if path is None:
			path = self.chkpt_path
		torch.save(self.state_dict(), path)