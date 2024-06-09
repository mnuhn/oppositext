* T5-Base SFT: ./data/t5base.sft.model
* T5-Base PPO: ./data/mix23.txt.augmented3.t5base.model-final.rewardmodel2c-no-avoid-not.ppo-step73

* T5-Base SFT: Wins 1
* T5-Base PPO: Wins 6
* Draw: 14

* Prompt: He is nice.
   * T5-Base SFT: He is not nice.
   * T5-Base PPO: He is not nice.
   * Result: -

* Prompt: He is my best friend.
   * T5-Base SFT: He is not my best friend.
   * T5-Base PPO: He is not my best friend.
   * Result: -

* Prompt: Thomas is my best friend.
   * T5-Base SFT: Thomas is not my best friend.
   * T5-Base PPO: Thomas is not my best friend.
   * Result: -

* Prompt: Thomas is real nice.
   * T5-Base SFT: Thomas is not very nice.
   * T5-Base PPO: Thomas is not real nice.
   * Result: 2

* Prompt: I am super relaxed.
   * T5-Base SFT: I am not super relaxed.
   * T5-Base PPO: I am not super relaxed.
   * Result: -

* Prompt: He walked down the street.
   * T5-Base SFT: He walked up the street.
   * T5-Base PPO: He did not walk down the street.
   * Result: 2

* Prompt: He is extremely rich.
   * T5-Base SFT: He is not extremely rich.
   * T5-Base PPO: He is not extremely rich.
   * Result: -

* Prompt: Bitter.
   * T5-Base SFT: Sweet.
   * T5-Base PPO: Sweet.
   * Result: -

* Prompt: In the morning, eat two tablespoons of vitamin C.
   * T5-Base SFT: In the morning, don't eat two tablespoons of vitamin C.
   * T5-Base PPO: In the morning, do not eat two tablespoons of vitamin C.
   * Result: -

* Prompt: The coffee should be served hot.
   * T5-Base SFT: The coffee should not be served hot.
   * T5-Base PPO: The coffee should not be served hot.
   * Result: -

* Prompt: Eat the rich.
   * T5-Base SFT: Eat the poor.
   * T5-Base PPO: Avoid eating the poor.
   * Result: -

* Prompt: The older you get, the more you appreciate life.
   * T5-Base SFT: The younger you get, the less you enjoy life.
   * T5-Base PPO: The younger you get, the less you enjoy life.
   * Result: -

* Prompt: Try to earn as much money as possible.
   * T5-Base SFT: Do not try to earn as much money as possible.
   * T5-Base PPO: Do not try to earn as much money as possible.
   * Result: -

* Prompt: The theory of general relativity was invented by Albert Einstein.
   * T5-Base SFT: The theory of general relativity was not invented by Albert Einstein.
   * T5-Base PPO: The theory of general relativity was not invented by Albert Einstein.
   * Result: -

* Prompt: I need holidays to relax.
   * T5-Base SFT: I don't need vacations to relax.
   * T5-Base PPO: I don't need holidays to relax.
   * Result: 2

* Prompt: I hope to get a promotion soon.
   * T5-Base SFT: I hope to get a promotion soon.
   * T5-Base PPO: I hope to not get a promotion soon.
   * Result: 2

* Prompt: Switzerland has a beautiful landscape.
   * T5-Base SFT: Swiss has a terrible landscape.
   * T5-Base PPO: Switzerland doesn't have a beautiful landscape.
   * Result: 2

* Prompt: After work, I have to catch the train to visit a new apartment.
   * T5-Base SFT: After work, I have to catch the train to visit a new apartment.
   * T5-Base PPO: After work, I do not have to catch the train to visit a new apartment.
   * Result: 2

* Prompt: I try intermittent fasting to heal faster.
   * T5-Base SFT: I do not try intermittent fasting to heal faster.
   * T5-Base PPO: I don't try intermittent fasting to heal faster.
   * Result: -

* Prompt: It is important to stay calm at all times.
   * T5-Base SFT: It is not important to stay calm at all times.
   * T5-Base PPO: It is not important to stay calm at all times.
   * Result: -

* Prompt: Please bring something for dinner.
   * T5-Base SFT: Please don't bring anything for dinner.
   * T5-Base PPO: Please don't bring something for dinner.
   * Result: 1
