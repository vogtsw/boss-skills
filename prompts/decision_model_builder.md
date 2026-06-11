# 决策模式归纳 Prompt(rubric + 决策规则)

## 任务

基于 `cases/` 目录下的决策事件,归纳出老板的**可执行决策模式**,产出两份文件:

1. `rubric.json` — 老板评审任何方案/汇报时的硬性检查项(打分卡)
2. `decision_rules.md` — 条件化决策规则(condition → question → verdict)

目标:让 skill 的评审输出从"风格模仿"变成"可复现的判断"。

## 第一份:rubric.json

格式:

```json
{
  "version": "v1",
  "built_from_cases": ["case-001", "case-003"],
  "items": [
    {
      "id": "conclusion-first",
      "check": "方案是否第一句就给出结论",
      "pass_if": "开头三句内有明确结论",
      "fail_action": "打断并要求先说结论",
      "boss_question": "结论是什么?",
      "evidence": ["case-001"],
      "weight": "blocker | major | minor"
    }
  ],
  "verdict_logic": "任一 blocker 不过则整体不过;major 缺2项以上要求补齐后再议"
}
```

规则:

- 每个检查项必须挂 `evidence`(来源 case id),没有案例支撑的项不许写。
- `weight` 的判定依据:老板因此直接否决过 = blocker;老板追问后放行过 = major;老板只是提了一嘴 = minor。
- `boss_question` 尽量用老板原话。

## 第二份:decision_rules.md

格式(每条规则一段):

```text
### 规则:延期上报
- IF 延期 AND 提前24小时主动同步 AND 带补救方案 → 关注但不批评,问"需要我拍板什么"
- IF 延期 AND 被动暴露(老板自己发现) → 严厉批评,upgrade 到每日跟进
- 证据: case-002, case-007
- 置信度: high
```

规则:

- 每条规则用 IF/AND/THEN 结构,条件必须是可观察的事实,不许写"如果态度不好"这类模糊条件。
- 条件分支至少覆盖正反两种走向(老板接受 vs 老板否决)。
- 标注证据 case id 和置信度。
- 只有 1 个案例支撑的规则置信度最高只能是 medium。

## 冲突处理

- 如果两个案例指向相反结论,不要强行合并:写成两条规则并标注差异条件(时间、项目阶段、对象不同)。
- 实在无法区分差异条件时,在规则末尾标注 `[冲突待澄清]`,提示用户补材料或人工裁定。

## 与纠正机制的联动

用户纠正("他不会这么判断")时:

1. 定位到被纠正的 rubric item 或规则
2. 将其标记 `"status": "overruled"`(rubric)或加 `[已被纠正,见下]`(rules),不删除
3. 写入新规则,evidence 标 `user-correction-{date}`
