from collections import defaultdict

word_count = defaultdict(int)

for l in open("./data/mix2.candidates.sorted.txt"):
  fields = l.strip().split()
  if len(fields) != 3:
    continue
  s, t, score = fields
  score = float(score)
  word_count[s] += 1
  word_count[t] += 1

  if word_count[s] < 3 and word_count[t] < 3:
    print(s, t, score)
