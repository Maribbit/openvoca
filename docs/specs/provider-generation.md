# 生成与 Provider 规格

本文件描述 prompt 构造、生成 API 与 OpenAI-compatible provider 的边界。它不规定具体模型质量，只规定 OpenVoca 与模型交互的协议。

## Prompt 构造

- **AC-GEN-001-01**：有目标词时，生成 prompt 必须保留用户原始指令，并追加要求模型用单星号标记目标词的指令。
- **AC-GEN-001-02**：没有有效目标词时，不应追加目标词标记指令。
- **AC-GEN-001-03**：空 prompt 应被拒绝；非空 prompt 的首尾空白应被裁剪。
- **AC-GEN-001-04**：前端已经组装好的场景、难度、长度等完整 prompt 不能在后端构造时丢失。

## 生成 API

- **AC-GEN-002-01**：`/api/reading-sentence/next` 应接受完整 prompt 或最小 prompt，并返回句子、目标词和已分词 token。
- **AC-GEN-002-02**：生成过程中后端应推进学习轮次 cooldown；刷新目标词接口不能推进 cooldown。
- **AC-GEN-002-03**：LLM 不可达时，生成 API 应返回 502。

## OpenAI-compatible provider

- **AC-GEN-003-01**：OpenAI-compatible client 应向 `/v1/chat/completions` 发送模型、用户消息和可选 API key，并从 chat completion 中提取文本。
- **AC-GEN-003-02**：当 provider 返回空 choices 时，client 应抛出明确错误。
- **AC-GEN-003-03**：OpenAI-compatible client 必须满足通用 LLMProvider 协议，并能复用连接处理多次调用。
- **AC-GEN-003-04**：client 应支持显式关闭底层 HTTP 连接。
- **AC-GEN-003-05**：流式 completion 应从 SSE delta 中逐块产出文本，并忽略 `[DONE]`。
