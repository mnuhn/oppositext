from collections import defaultdict
from copy import deepcopy

pairs = []

for l in open("./data/antonyms-list.txt"):
  f = l.strip().split()
  s = f[0].lower()
  for t in f[1:]:
    t = t.lower()
    pairs.append((s, t))
    pairs.append((t, s))

negate = defaultdict(set)

for s, t in sorted(list(set(pairs))):
  print(s, t)
  negate[s].add(t)
  negate[t].add(s)


def expand(negates):
  negates_out = deepcopy(negates)
  for s in negates:
    for ss in negates[s]:
      for sss in negates[ss]:
        if s == sss:
          continue
        print("new", s, sss, "via", ss)
        negates_out[s].add(sss)
        negates_out[sss].add(s)
  return negates_out


def write(fn, negate):
  cnt = 0
  with open(fn, "w") as f:
    for s in negate:
      for t in negate[s]:
        f.write(f'{s} {t}\n')
        f.write(f'{t} {s}\n')
        cnt += 1
  print(cnt)


write("./data/final_0.txt", negate)

negate = expand(negate)
write("./data/final_1.txt", negate)
