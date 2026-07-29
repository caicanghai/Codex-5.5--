# EIOS 提示词清单（拿去给 KIMI 整合用）

EIOS 全部的 LLM 提示词都集中在 `app/prompts.py` 一个文件里。总共只有三条 + 几句兜底文案。下面是纯文本版，方便你直接复制到 KIMI 或别的助手里。

---

## 1. 对话人设（system prompt）

```
You are EIOS, a concise, friendly personal assistant. Reply briefly.
```

> 中文版可换成：`你是 EIOS，一个简洁、友好的私人助理，回复请简明扼要。`
> 调用参数：`temperature=0.6`，用户消息截断到 4000 字。

---

## 2. 摘要人设（system prompt）

```
You are a concise news summarizer.
```

> 中文版：`你是一个简洁的新闻摘要助手。`
> 调用参数：`temperature=0.3`。

---

## 3. 摘要指令（user prompt 模板）

```
Summarize the following article in at most {N} clear sentences. Be factual and concise.

{文章正文，截断到 8000 字}
```

> `{N}` = 摘要句数（默认 5，配置项 `summary_sentences`）。

---

## 4. 兜底文案（AI 不可用时，不走模型）

| 场景              | 返回的话                                               |
| ----------------- | ------------------------------------------------------ |
| 空消息            | `（空消息）`                                           |
| 有 key 但 AI 报错 | `EIOS online. AI provider is temporarily unavailable.` |
| 没配 AI key       | `EIOS online. 收到：{你发的前 200 字}`                 |

---

## 给 KIMI 整合的建议

- KIMI 是 OpenAI 兼容接口，直接把上面第 1、2 条当 `system` 消息、第 3 条当 `user` 消息发即可。
- 在 EIOS 里改用 KIMI：只需在 `.env` 里设
  - `AI_BASE_URL=https://api.moonshot.cn/v1`
  - `AI_MODEL=moonshot-v1-8k`（或你要的 KIMI 模型名）
  - `OPENAI_API_KEY=你的KIMI key`
- 提示词本身不用改——EIOS 的对话/摘要提示词对任何 OpenAI 兼容模型（含 KIMI、DeepSeek）都通用。
