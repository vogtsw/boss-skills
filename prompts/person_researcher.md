# 公开资料人物画像 Prompt(public research mode)

## 任务

当用户想为**导师、PI、老板或其他公开人物**建立画像,但没有(或不够)私有聊天记录时,用免费公开渠道搜集资料,补全 persona / judgment 的证据。

## 工具

运行 `tools/person_research.py`(零 API key,纯免费源):

```bash
python tools/person_research.py --name "姓名" --affiliation "单位提示" \
  --sources all --limit 10 \
  --save-dir bosses/{slug}/knowledge/research
```

| 来源 | 适用对象 | 能拿到什么 |
|------|---------|-----------|
| openalex | 学术导师/PI | 作者档案、研究主题、高被引论文 |
| semanticscholar | 学术导师/PI | h-index、论文摘要 |
| arxiv | AI/理工科导师 | 最新预印本(看他最近在押什么方向) |
| crossref | 所有学术人物 | 出版物元数据 |
| github | 工程背景老板 | 公开仓库、技术栈、bio |
| wikipedia | 公众人物/企业家 | 生平摘要 |

此外,agent 自身具备网页搜索能力时,应补充搜索:访谈、播客、演讲、知乎/博客文章、公司官网介绍,作为管理风格证据。

## 流程

### Step 1: 收集检索线索

向用户确认:真实姓名(学术源需要)、单位/公司、领域、可选的 GitHub ID 或主页。

### Step 2: 运行工具 + 消歧

- 运行 `person_research.py`,结果存入 `knowledge/research/`
- **同名消歧是必做步骤**:如果 openalex/semanticscholar 返回多个候选,用单位和领域过滤;过滤不掉就把候选列表给用户选,不许猜。

### Step 3: 从公开资料推断画像(标注推断链)

公开资料 → 画像的映射规则:

- **研究主题分布** → 他看重什么问题、领域品味(judgment)
- **论文一作/通讯比例、合作网络** → 放权程度、对学生的管理颗粒度(management 参考)
- **近两年 arXiv 方向变化** → 他正在押注什么,提案往这上面靠(management)
- **访谈/演讲原话** → 表达风格、口头禅、价值主张(persona,可直接引用)
- **GitHub 仓库 README 风格、commit 习惯** → 工程品味(judgment)

### Step 4: 写入画像,区分证据等级

所有由公开资料得出的结论,必须标注:

```text
- 他更看重方法的简洁性而不是刷点 (来源: 2024 访谈原话"..." | 证据等级: public-quote)
- 他可能偏好学生先给出完整失败分析 (来源: 论文风格推断 | 证据等级: public-inferred)
```

证据等级:`private`(真实聊天记录) > `public-quote`(公开原话) > `public-inferred`(公开资料推断)。
与真实材料冲突时,private 永远优先。

## 边界与安全

- 只使用公开可得资料,不尝试绕过任何登录或付费墙。
- 产出定位为"公开风格画像",不声称还原私下真实人格。
- 推断必须可溯源;搜不到证据的维度写"(公开资料不足)",不许编。
