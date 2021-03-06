![Python Linting with flake8](https://github.com/Wuelle/hAIku_generator/workflows/Python%20Linting%20with%20flake8/badge.svg)
[![Open Source? Yes!](https://badgen.net/badge/Open%20Source%20%3F/Yes%21/blue?icon=github)](https://github.com/Naereen/badges/)
# Haiku Generator
## Description
This Repository contains an implementation of the SeqGan Architecture proposed in [this Paper](https://arxiv.org/pdf/1609.05473.pdf) for generating Haikus. This Branch, `master`, generates word vectors using multivariate Gaussian Distributions.
The `charlevel` branch is a somewhat working implementation of the original SeqGAN and `Èmbeddings` is similar to `master` but
utilizes Deep Deterministic Policy Gradients (DDPG) in order to generate the word vectors. Because DDPG takes a long time to train
and involves a second non-generator mode, the Critic, this Branch will likely be deleted in the future.
This project is my submission for the [BW-KI 2020](https://bw-ki.de/) Competition.

## Functionality
The SeqGAN Algorithm was first proposed by [this Paper](https://arxiv.org/pdf/1609.05473.pdf). Like in a normal GAN, the Discrimnator Model 
rates the samples produced by the Generator on a scale from zero to one based on how realistic they seem. However, since the samples are
sequential and the Discriminator cannot judge partial Sequences, it is unable to directly provide a reward for each timestep to the Generator.
This Problem is solved by using the classic RL-Algorithm REINFORCE as a Generator Model and rolling out the sequences using Monte-Carlo.
![SeqGAN-image](https://www.researchgate.net/publication/325709720/figure/fig1/AS:636539755302912@1528774312038/An-illustration-of-SeqGAN-for-text-generation-27-Compared-to-one-step-generation-of.png)
One Downside of this Procedure is that a REINFORCE Agent can only act in a discrete environment since its output is a probability distribution over a 
finite number of actions. A somewhat working Implementation of the classic Algorithm can be found in the `charlevel` Branch. I am trying to extend the
Generator into a continuous Action Space by having the Generator output a multivariate Gaussian Distribution. Exploration can be ensured
by having the Model only output the mean but not the standard deviation for each of the `num_actions` distributions.


## Usage
For the sake of keeping it simple, I am not uploading my dataset here. However, you can just use the dataset from
[this Repository](https://github.com/docmarionum1/haikurnn) and preprocess it using
`DatasetPreparation.ipynb`. The resulting file should be placed in the `data/` directory unless specified otherwise.

To make sure you have all the required dependencies installed, run `pip install -r requirements.txt`

The training is done in `main.py`. Run `python3 main.py -h` to see a list of all parameters you can set.
Since i am not uploading my Word2Vec Model, you need to set the `--pretrain_w2v` parameter on your first run to
train one yourself.
Unless the `path_model` Parameter is set, the trained models will be stored in `models/`.

## Future Goals
* Have the model output a full Covariance Matrix instead of only the diagonal values
* Use Pandas for handling the dataset (.csv instead of .txt)
* Maybe use something more advanced than REINFORCE
* Scrape Haikus from Twitter
* Improve charlevel branch
* Create contributing guidelines

## Training Images
![Main Training Image](https://github.com/Wuelle/hAIku_generator/blob/master/training_img/main.png)

## Credits
Though i plan to use my own data eventually, right now i am using a processed version of the dataset from
this [HaikuRNN Repository](https://github.com/docmarionum1/haikurnn) for training my model.

## License
This program is licensed under the GNU General Public License v3.0. For more Information, see
[LICENSE.txt](https://github.com/Wuelle/BW-KI-2020/blob/Embeddings/LICENSE.txt)
