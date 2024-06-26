# https://medium.com/@martinkeywood/fine-tuning-a-t5-small-model-to-generate-sql-from-natural-language-with-92-3-accuracy-fb29e062c638

import os
from datasets import set_caching_enabled

set_caching_enabled(False)

os.environ['CUDA_DEVICE_ORDER'] = 'PCI_BUS_ID'
os.environ['CUDA_VISIBLE_DEVICES'] = '0'

import torch
from math import log, exp
import random
import data
import numpy as np
from tqdm import tqdm
import time
import argparse

from trl import PPOTrainer
from trl import PPOConfig
from trl.models import AutoModelForSeq2SeqLMWithValueHead

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from transformers import DataCollatorWithPadding
from transformers import AutoTokenizer, AutoModelForSequenceClassification

from datasets import Dataset
from datasets import DatasetDict
from datasets import load_dataset

import rulebased_reward_model

DEVICE = "cuda:0"

parser = argparse.ArgumentParser(description='Train PPO')
parser.add_argument('--model', default=None, help='which model to open')
parser.add_argument('--rule_reward_fac',
                    default=0.01,
                    type=float,
                    help='which model to open')
parser.add_argument('--reward_model', default=None, help='which model to open')
parser.add_argument('--suffix', default='001', help='suffix')
parser.add_argument('--prompts_fn', default=None, help='prompts_fn')
parser.add_argument('--low_rule_reward_override',
                    default=False,
                    help='low_rule_reward_override')
parser.add_argument('--use_score_scaling',
                    default=False,
                    help='use_score_scaling')
parser.add_argument('--use_score_norm', default=False, help='use_score_norm')
parser.add_argument('--init_kl_coef',
                    default=0.2,
                    type=float,
                    help='init_kl_coef')
parser.add_argument('--target_kl', default=1.0, type=float, help='target_kl')
parser.add_argument('--kl_horizon',
                    default=1000.0,
                    type=float,
                    help='kl_horizon')
parser.add_argument('--max_ppo_steps',
                    default=20,
                    type=int,
                    help='max_ppo_steps')
parser.add_argument('--max_len', default=35, type=int, help='maximum length')
parser.add_argument('--batch_size', default=128, type=int)
parser.add_argument('--mini_batch_size', default=8, type=int)
parser.add_argument('--learning_rate', default=0.000015, type=float)

args = parser.parse_args()

dataset = Dataset.from_generator(data.prompt_gen(
    args.prompts_fn)).shuffle(seed=42)
dataset = dataset.train_test_split(test_size=0.05, shuffle=True, seed=42)
dataset = dataset.map(data.tokenize_input_function,
                      load_from_cache_file=False)  #, batched=True)
dataset = dataset.remove_columns(["source_text"])


def collator(data):
  result = {key: [d[key] for d in data] for key in data[0]}
  return result


ppo_config = PPOConfig(
    model_name=f'{args.model}.{args.suffix}.ppo',
    log_with='tensorboard',
    learning_rate=args.learning_rate,
    target=args.target_kl,
    target_kl=args.target_kl,
    horizon=args.kl_horizon,
    init_kl_coef=args.init_kl_coef,
    #score_clip = 1.0,
    #cliprange=0.1,
    #cliprange_value=0.1,
    #    max_grad_norm=1.0,
    ratio_threshold=10.0,
    batch_size=args.batch_size,
    use_score_scaling=args.use_score_scaling,
    use_score_norm=args.use_score_norm,
    mini_batch_size=args.mini_batch_size,
    adap_kl_ctrl=True,
    kl_penalty='abs',
    project_kwargs={
        "logging_dir":
            f'{args.model}.{args.suffix}.ppo.tensorboard/bs{args.batch_size}-rewardfac-{args.rule_reward_fac}-rulereward{args.use_score_scaling}{args.use_score_norm}-initklcoeff-{args.init_kl_coef}-klhorizon{args.kl_horizon}-lr{args.learning_rate}'
    },
)

reward_model = None
if args.reward_model != None:
  reward_model = AutoModelForSequenceClassification.from_pretrained(
      args.reward_model)
else:
  print("using rule based rewards")

model = AutoModelForSeq2SeqLMWithValueHead.from_pretrained(
    args.model).to(DEVICE)
model.eval()

ppo_trainer = PPOTrainer(
    model=model,
    config=ppo_config,
    dataset=dataset["train"],
    data_collator=collator,
    #data_collator=data_collator,
    tokenizer=data.tokenizer,
)

generation_kwargs = {
    "min_length": -1,
    #    "max_length": 25,
    "max_new_tokens": args.max_len,
    #"length_penalty": 0.1,
    "top_k": 0.0,
    "top_p": 1.0,
    "pad_token_id": data.tokenizer.pad_token_id,
    "eos_token_id": data.tokenizer.eos_token_id,
    #"pad_token_id": tokenizer.eos_token_id,
    #    "pad_token_id": -1, #data.tokenizer.pad_token_id,
    #    "eos_token_id": -1, # data.tokenizer.eos_token_id,
    #"eos_token_id": -1,
    "do_sample": True,
    "begin_suppress_tokens": [data.tokenizer.eos_token_id],
    #"return_prompt": False,
    "no_repeat_ngram_size": 2,
    "batch_size": 1,
}


def pad_sequences(sequences, max_length):
  padding_needed = [max_length - seq.size(0) for seq in sequences]
  padded_sequences = torch.stack([
      torch.nn.functional.pad(seq, (0, pad), value=data.tokenizer.pad_token_id)
      if pad > 0 else seq for seq, pad in zip(sequences, padding_needed)
  ])

  return padded_sequences


assert reward_model != None

initial_stats = None
reward_mean_max = None

for step, batch in tqdm(enumerate(ppo_trainer.dataloader)):
  if step >= args.max_ppo_steps:
    break

  if step % 5 == 0:
    prompt_tensors = [torch.tensor(p[0]) for p in dataset["test"]["input_ids"]]
    prompt_strs = [
        data.tokenizer.decode(p[0], skip_special_tokens=True)
        for p in dataset["test"]["input_ids"]
    ]
    response_tensors = ppo_trainer.generate(prompt_tensors,
                                            return_prompt=False,
                                            **generation_kwargs)

    response_strs = data.tokenizer.batch_decode(response_tensors,
                                                skip_special_tokens=True)
    example_num = 0
    for q_str, r_str in zip(prompt_strs, response_strs):
      print()
      print(q_str.replace("Negate:", ""))
      print(r_str)
      example_num += 1
      if example_num > 19:
        break

  prompt_tensors = [torch.tensor(p[0]) for p in batch["input_ids"]]
  print("max prompt len:", max([len(x) for x in prompt_tensors]))

  prompt_strs = [
      data.tokenizer.decode(p[0], skip_special_tokens=True)
      for p in batch["input_ids"]
  ]
  batch["query"] = prompt_strs

  response_tensors = ppo_trainer.generate(prompt_tensors,
                                          return_prompt=False,
                                          **generation_kwargs)

  response_strs = data.tokenizer.batch_decode(response_tensors,
                                              skip_special_tokens=True)
  batch["response"] = response_strs

  reward_tensors = []
  padded_response_tensors = pad_sequences(response_tensors, max_length=256)
  padded_input_ids = pad_sequences(prompt_tensors, max_length=256)

  q_num = 0
  for q_str, q, r_str, r in zip(prompt_strs, padded_input_ids, response_strs,
                                padded_response_tensors):
    cur_rule_reward = rulebased_reward_model.ppo_reward(q_str, r_str)
    outputs_attention_mask = (r != data.tokenizer.pad_token_id).int()
    reward_outputs = reward_model(
        input_ids=q.unsqueeze(0).to(reward_model.device),
        decoder_input_ids=r.unsqueeze(0).to(reward_model.device),
        decoder_attention_mask=outputs_attention_mask.unsqueeze(0).to(
            reward_model.device))
    reward_probs = torch.nn.functional.softmax(reward_outputs.logits, dim=-1)
    cur_reward = reward_probs[0][1].item()
    total_reward = rulebased_reward_model.combine(cur_rule_reward, cur_reward,
                                                  args.rule_reward_fac,
                                                  args.low_rule_reward_override)
    reward_tensors.append(torch.tensor(total_reward))
    if q_num < 5:
      print("===")
      print(q_str.replace("Negate: ", ""))
      print(r_str)
      print()
      print(f'cur_rule_reward: {cur_rule_reward}')
      print(f'cur_reward: {cur_reward}')
      print(f'total_reward: {total_reward}')
      print()
    q_num += 1

  # reward_tensors == scores
  reward_mean = sum(reward_tensors) / len(reward_tensors)

  # Run PPO step.
  print("KL CTL:", ppo_trainer.kl_ctl.value)
  if ppo_trainer.kl_ctl.value < 0.0001:
    ppo_trainer.kl_ctl.value = 0.0001
    print("KL CTL Override:", ppo_trainer.kl_ctl.value)

  if reward_mean_max == None:
    reward_mean_max = reward_mean

  # save if a better checkpoint observed
  if reward_mean > reward_mean_max:
    out_fn = f'{args.model}.{args.suffix}.ppo-step{step}'
    ppo_trainer.save_pretrained(out_fn)
    reward_mean_max = reward_mean

  stats = ppo_trainer.step(prompt_tensors, response_tensors, reward_tensors)
  ppo_trainer.log_stats(stats, batch, reward_tensors)
  if not initial_stats:
    initial_stats = stats

  def print_info(what):
    print(
        f'{what}: {stats[what]:.4f} vs {initial_stats[what]:.4f} (delta: {stats[what] - initial_stats[what]:.4f}'
    )

  print()
  print_info('objective/kl')
  print_info('ppo/returns/mean')
  print_info('ppo/mean_scores')
  print_info('ppo/policy/advantages_mean')
  print('-'.join('' for x in range(100)))

out_fn = f'{args.model}.{args.suffix}.ppo-final'
ppo_trainer.save_pretrained(out_fn)
