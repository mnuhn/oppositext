# Train the reward model.

wd=0.0
epochs=2
lr=0.0001
margin=25.0
# margin25-lr0.0005-wd0.0-ep5-trainallparamsTrue-final

python3 \
  train_reward.py \
  --db=data/mix24.reward.merged_ratings.db \
  --model=./data/mix23.txt.augmented3.t5base.model-final \
  --learning_rate=$lr \
  --weight_decay=$wd \
  --epochs=${epochs} \
  --suffix=fixed \
  --test_frac=0.05 \
  --margin=${margin} \
  --tb_suffix=lr${lr}-wd${wd}-ep${epochs}-final \
  --out_model=data/mix24.t5base.reward-model

#python3 \
#  train_reward.py \
#  --db=data/mix22.extended.txt.model2-final.8antonyms-lenthwiggle.ppo-final.multidecode.db.backup \
#  --model=data/mix22.extended.txt.model2-final \
#  --learning_rate=$lr \
#  --weight_decay=$wd \
#  --epochs=${epochs} \
#  --suffix=fixed \
#  --test_frac=0.05 \
#  --margin=${margin} \
#  --tb_suffix=lr${lr}-wd${wd}-ep${epochs}-final \
#  --out_model=data/mix22.extended.txt.model2-final.lr${lr}-wd${wd}-ep${epochs}-margin${margin}-reward-model-head4

#python3 \
#  train_reward.py \
#  --db=data/mix22.extended.txt.model2-final.8antonyms-lenthwiggle.ppo-final.multidecode.db.backup \
#  --model=data/mix22.extended.txt.model2-final \
#  --learning_rate=$lr \
#  --weight_decay=$wd \
#  --epochs=${epochs} \
#  --train_all_parameters=True \
#  --suffix=fixed \
#  --test_frac=0.05 \
#  --margin=${margin} \
#  --tb_suffix=lr${lr}-wd${wd}-ep${epochs}-final \
#  --out_model=data/mix22.extended.txt.model2-final2.lr${lr}-wd${wd}-ep${epochs}-margin${margin}-reward-model-allparams
