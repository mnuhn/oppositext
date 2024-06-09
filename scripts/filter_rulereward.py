from collections import defaultdict
import rulebased_reward_model

word_count = defaultdict(int)

A = None
B = None
C = None
for l in open("./examples.txt"):
  l = l.strip()
  if A is None:
    A = l
  elif B is None:
    B = l
    reward = rulebased_reward_model.ppo_reward(A,B)
    if reward > 1.9:
      print(A)
      print(B)
    A = None
    B = None
