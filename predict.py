import torch
from torch.nn.functional import log_softmax
import sys
import numpy as np
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, AutoModelForSequenceClassification
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from InquirerPy.separator import Separator
import prompt_db
from collections import defaultdict
from tqdm import tqdm
import skip_file
import random
import rulebased_reward_model
import random

import argparse
import force_words
from transformers.utils import logging

logging.set_verbosity_error()

parser = argparse.ArgumentParser(description='add predictions to database')
parser.add_argument('--model', default=None, help='which model to open')
parser.add_argument('--model2', default=None, help='which model to open')
parser.add_argument('--reward_model', default=None, help='which model to open')
parser.add_argument('--print_average_reward',
                    default=False,
                    type=bool,
                    help='which model to open')
parser.add_argument('--rule_reward_fac',
                    default=0.01,
                    type=float,
                    help='which model to open')
parser.add_argument('--low_rule_reward_override',
                    default=False,
                    help='low_rule_reward_override')
parser.add_argument('--db', default=None, help='db to write predictions to')
parser.add_argument('--force_antonyms', default=None, help='force antonyms')
parser.add_argument('--skip_file', default=None, help='prompts to skip')
parser.add_argument('--num_to_generate_per_type',
                    default=1,
                    type=int,
                    help='number of completions per prompt')
parser.add_argument('--num_to_keep_per_type',
                    default=1,
                    type=int,
                    help='number of completions per prompt')
parser.add_argument('--num_beams',
                    default=5,
                    type=int,
                    help='number of completions per prompt')
parser.add_argument('--max_len', default=100, type=int, help='maximum length')
parser.add_argument('--prompts', default=None, help='file with prompts')
parser.add_argument('--interactive', default=None, help='file with prompts')

args = parser.parse_args()

if args.interactive:
  print("""
     __   __   __   __   __    ___  ___     ___
    /  \ |__) |__) /  \ /__` |  |  |__  \_/  |
    \__/ |    |    \__/ .__/ |  |  |___ / \  |
 """)

tokenizer = AutoTokenizer.from_pretrained("t5-small")
model = AutoModelForSeq2SeqLM.from_pretrained(args.model)
if args.model2:
  model2 = AutoModelForSeq2SeqLM.from_pretrained(args.model2)
else:
  model2 = None

if args.reward_model:
  reward_model = AutoModelForSequenceClassification.from_pretrained(
      args.reward_model)
else:
  reward_model = None

candidates = []
skip_set = skip_file.skipSet(args.skip_file)

db = None

if args.db:
  db = prompt_db.prompt_db(args.db)

if not args.interactive:
  prompts = []
  for l in open(args.prompts, "r"):
    input_str = l.strip()
    if skip_set.should_skip(input_str):
      continue

    prompts.append(input_str)

#random.shuffle(prompts)


def predict(m, input_str, input_ids, force_words_ids, bad_words_ids, name):
  try:
    outputs = m.generate(
        input_ids,
        return_dict_in_generate=True,
        output_scores=True,
        max_length=args.max_len,
        force_words_ids=force_words_ids,
        bad_words_ids=bad_words_ids,
        #temperature=1.0,
        remove_invalid_values=True,
        #do_sample=True,
        num_beams=args.num_beams,
        num_return_sequences=args.num_to_generate_per_type,
        no_repeat_ngram_size=2,
        repetition_penalty=1.5)
  except Exception as e:
    print(e)
    return None

  def pad_sequences(sequences, max_length):
    padding_needed = [max_length - seq.size(0) for seq in sequences]
    padded_sequences = torch.stack([
        torch.nn.functional.pad(seq, (0, pad), value=tokenizer.pad_token_id)
        if pad > 0 else seq for seq, pad in zip(sequences, padding_needed)
    ])
    return padded_sequences

  padded_outputs = pad_sequences(outputs.sequences, max_length=128)

  results = []
  for i in range(len(outputs.sequences)):
    outputs_attention_mask = (padded_outputs[i] != tokenizer.pad_token_id).int()
    if reward_model:
      reward_outputs = reward_model(
          input_ids=input_ids,
          decoder_input_ids=padded_outputs[i].unsqueeze(0),
          decoder_attention_mask=outputs_attention_mask.unsqueeze(0))

      reward_probs = torch.nn.functional.softmax(reward_outputs.logits, dim=-1)
      reward = reward_probs[0][1].item(
      )  #reward_model.overall_reward(input_str, output_str)
    else:
      reward = 0.0

    output_str = tokenizer.decode(outputs.sequences[i],
                                  skip_special_tokens=True)
    input_length = input_ids.shape[1]
    generated_tokens = outputs.sequences[i, 0:]
    overall_score = outputs.sequences_scores[i].item()
    rule_reward = rulebased_reward_model.ppo_reward(input_str, output_str)
    results.append((output_str, reward, rule_reward, overall_score, name))
  return results


if args.interactive:
  pbar = sys.stdin
else:
  pbar = tqdm(prompts)

added_comparisons = 0
sum1 = 0
sum2 = 0
cnt = 0

GREEN = '\033[92m'
BOLD = '\033[91m\033[1m'
END = '\033[0m'


def maybe_print_prompt():
  if args.interactive:
    print()
    print()
    print(f"➡️  {GREEN}", end='', flush=True)


maybe_print_prompt()
for input_str in pbar:
  cnt += 1
  prompt_id = None
  if args.interactive:
    print(END, end='', flush=True)
  else:
    pbar.set_description(f"Processing: '{input_str}'")
  if db:
    prompt_id = db.add_prompt(input_str)
  prompt_str = f"Negate:\n{input_str}"
  input_ids = tokenizer.encode(prompt_str,
                               padding='max_length',
                               truncation=True,
                               max_length=128,
                               return_tensors="pt")
  input_ids = input_ids.to(model.device)

  #force_words = None
  #force_words = tokenizer([sys.stdin.readline()], add_special_tokens=False).input_ids

  force_words_ids = [("std", None, None)]

  if args.force_antonyms:
    force_words_ids.append(
        ("antonym-no_not", force_words.get_antonyms(input_str, tokenizer),
         force_words.get_not(tokenizer)))
    force_words_ids.append(("no_not", None, force_words.get_not(tokenizer)))
    force_words_ids.append(("not", [force_words.get_not(tokenizer)], None))

  results = []
  results2 = []
  for name, cur_force_words_ids, cur_bad_words_ids in force_words_ids:
    cur_results = predict(model,
                          input_str,
                          input_ids,
                          cur_force_words_ids,
                          cur_bad_words_ids,
                          name=name)
    if cur_results:
      results.extend(cur_results)

    if model2:
      cur_results = predict(model2,
                            input_str,
                            input_ids,
                            cur_force_words_ids,
                            cur_bad_words_ids,
                            name=name)
      if cur_results:
        results2.extend(cur_results)

  results = sorted(results, key=lambda x: x[3], reverse=True)
  results2 = sorted(results2, key=lambda x: x[3], reverse=True)
  i = 0
  previous_str = None
  print()
  print("MM | ### |  score | comb rwd | ML rwd | rule rwd | output_str")
  pos = 0

  def print_result(i,
                   output_str,
                   reward,
                   rule_reward,
                   overall_score,
                   name,
                   prefix=""):
    total_reward = rulebased_reward_model.combine(rule_reward, reward,
                                                  args.rule_reward_fac,
                                                  args.low_rule_reward_override)
    if counts[name] >= args.num_to_keep_per_type:
      return None, total_reward

    counts[name] += 1

    if args.interactive:
      output_str = BOLD + output_str + END
    print(
        f'{prefix}  {i:03d}  {overall_score:7.3f}   {total_reward:8.4f} {reward:8.4f}   {rule_reward:8.4f} | {output_str}'
    )

    if db:
      completion_id = db.add_completion(prompt_id, name, output_str, reward,
                                        rule_reward, overall_score)
      print(prompt_id, completion_id)
      return completion_id, total_reward

    return None, total_reward

  if args.print_average_reward:
    print(f"Model 1: Avg reward {sum1/cnt}")

  i = 0
  counts = defaultdict(int)
  results_ids = []
  for output_str, reward, rule_reward, overall_score, name in results:
    cur_id, total_reward = print_result(i,
                                        output_str,
                                        reward,
                                        rule_reward,
                                        overall_score,
                                        name,
                                        prefix="M1 ")
    sum1 += total_reward
    results_ids.append(cur_id)
    i += 1

  results = [r + (r2,) for r, r2 in zip(results, results_ids)]
  results = [x for x in results if x[-1] is not None]

  if args.model2 and args.print_average_reward:
    print(f"Model 2: Avg reward {sum2/cnt}")
  i = 0
  counts = defaultdict(int)
  results2_ids = []
  for output_str, reward, rule_reward, overall_score, name in results2:
    cur_id, total_reward = print_result(i,
                                        output_str,
                                        reward,
                                        rule_reward,
                                        overall_score,
                                        name,
                                        prefix="M2 ")
    sum2 += total_reward
    results2_ids.append(cur_id)
    i += 1

  results2 = [r + (r2,) for r, r2 in zip(results2, results2_ids)]
  results2 = [x for x in results2 if x[-1] is not None]
  if not args.interactive and db:
    best = random.choice(sorted(results, key=lambda x: x[2])[-5:])
    worst = sorted(results, key=lambda x: x[2])[0]
    if worst[2] <= 0.01 and best[2] > 1.0:
      print(best, worst)
      if db:
        added_comparisons += 1
        print("not adding comparison to db")
        # db.add_comparison(prompt_id, best[-1], worst[-1], 1.1, 0.0)

  if db:
    db.conn.commit()
    print("added comparisons", added_comparisons)
  maybe_print_prompt()
