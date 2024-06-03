import random

def randomly_merge_successive_words(sentence):
  words = sentence.split()
  if len(words) < 2:
    return sentence

  index = random.randint(0, len(words) - 2)
  merged_word = words[index] + words[index + 1]
  words[index] = merged_word
  del words[index + 1]

  return ' '.join(words)
