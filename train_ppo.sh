# Run PPO.

python3 train_ppo.py \
  --prompts_fn=data/ppo_mix.shuffled.txt \
  --model=./data/mix23.txt.augmented3.t5base.model-final \
  --max_ppo_steps=250 \
  --max_len=100 \
  --batch_size=128 \
  --target_kl=10.0 \
  --learning_rate=0.000005 \
  --rule_reward_fac=0.01 \
  --suffix=rewardmodel2b \
  --low_rule_reward_override=True \
  --use_score_scaling=True \
  --reward_model=./data/mix23.txt.augmented3.t5base.model-final
  # ./data/mix22.extended.txt.model2-final.lr0.001-wd0.0-ep5-margin25.0-reward-model-final
