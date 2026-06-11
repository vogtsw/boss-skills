# 决策回放评测 Prompt(replay eval)

## 目的

回答一个问题:**这个 skill 像不像老板?** 用可量化的方式。

方法:留出一部分历史决策事件不参与归纳,用蒸馏出的决策模型(rubric + decision_rules + 训练案例)预测老板在这些事件里的选择,和真实决策对比,命中率即保真度。

## 流程

### Step 1: 切分

```bash
python tools/replay_eval.py --action split --slug {slug} --holdout 0.2
```

生成:

- `eval/replay_pack.json` — 留出案例(已删去 decision/rationale/quote/outcome)
- `eval/answer_key.json` — 答案
- `eval/train_ids.json` — 训练集 id

### Step 2: 盲答(关键纪律)

对 `replay_pack.json` 中的每个案例,**只允许使用**:

- `rubric.json`
- `decision_rules.md`
- `train_ids.json` 列出的训练案例
- persona/judgment/management 三份画像

**禁止**查看 `answer_key.json` 和留出案例的原始材料。

以老板身份回答:他会做什么决定?为什么?会先问什么?

### Step 3: 判分

逐案对比预测与 `answer_key.json`:

- `match: true` — 决策方向一致(措辞不同不算错)
- `match: false` — 决策方向相反,或关键理由完全不同

写入 `eval/graded.json`:

```json
[
  {"id": "case-002", "match": true, "note": "预测砍范围,实际砍范围"},
  {"id": "case-007", "match": false, "note": "预测会批,实际被否,因为忽略了合规风险规则"}
]
```

### Step 4: 出分

```bash
python tools/replay_eval.py --action score --slug {slug}
```

输出总体命中率、分场景命中率,并把 miss 列出来。

## 结果使用

- 命中率 < 60%:决策模型不可信,回到 cases 重新归纳 rubric/rules
- miss 的案例是金矿:每个 miss 说明缺一条规则或某条规则条件写错了,修完规则后重新跑
- 每次纠正(correction)或合并新材料后,重跑一次回放,防止保真度回退

## 注意

- 案例少于 10 个时命中率波动很大,只作参考,不下结论
- 这是 README"功能测试"要求的自动化承载:开发完成后跑一次回放即完成对判断功能的验证
