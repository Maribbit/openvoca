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

- **AC-GEN-003-01**：OpenAI-compatible client 应向「配置的基础地址 + `chat/completions`」发送模型、用户消息和可选 API key，并从 chat completion 中提取文本。
- **AC-GEN-003-02**：当 provider 返回空 choices 时，client 应抛出明确错误。
- **AC-GEN-003-03**：OpenAI-compatible client 必须满足通用 LLMProvider 协议，并能复用连接处理多次调用。
- **AC-GEN-003-04**：client 应支持显式关闭底层 HTTP 连接。
- **AC-GEN-003-05**：流式 completion 应从 SSE delta 中逐块产出文本，并忽略 `[DONE]`。
- **AC-GEN-003-06**：流式解析必须容忍不含 choices 的块（如仅携带用量的尾块），不得因缺少 choice 而中断。
- **AC-GEN-003-07**：流式生成过程中出现未预期异常时，必须产出可区分的错误事件，不得静默截断响应。
- **AC-GEN-003-08**：请求路径必须相对于基础地址拼接，基础地址自带的路径段必须保留；配置值若已包含端点路径，必须归一化为基础地址后再使用，不得产生重复路径。

### 版本段属于提供商，不属于 client

`/v1` 不是 OpenAI 的通用约定，它只是 OpenAI 自己路径里的版本段。各家的版本段名称与有无都不同：
OpenAI 用 `/v1`，Ollama 的兼容 API 也在 `/v1` 下，智谱用 `/api/paas/v4`，
而 DeepSeek 官方文档给出的 `base_url` 是 `https://api.deepseek.com`，其 curl 示例直接请求
`https://api.deepseek.com/chat/completions`，没有版本段。

通用的是「基础地址 + `/chat/completions`」，这也是 OpenAI SDK 的语义：
SDK 的 `base_url` 默认值 `https://api.openai.com/v1` 本身就含版本段，SDK 只往后面拼端点路径。
因此 client 只能拼接端点路径，版本段必须由配置承载。

httpx 是把 `base_url` 与请求路径**直接拼接**而非按 RFC 3986 解析，这使硬编码绝对路径的后果比预期严重：
基础地址 `https://api.openai.com/v1` 配 `"`/v1/chat/completions`"` 会得到 `/v1/v1/chat/completions`，
即用户按 OpenAI 文档填充最自然的值时反而必然 404。

配置值可能来自提供商的 `base_url` 示例，也可能来自其 curl 示例中的完整端点地址，两者常并列出现。
因此一处字段同时接受两种写法：归一化是幂等的——把端点路径拼回去会精确重现传入值，
所以它不会改变一个本来正确的地址。归一化发生在**写入边界**而非 client 内部，
使存储值、运行时 client 与 `GET /api/provider` 回传值三者一致。

## 自定义请求头

部分兼容端点要求额外的请求头才能路由或计费，例如 OpenCode Zen 要求 `x-opencode-session`，
缺失时返回 400 而不是 401，容易被误判为密钥或模型问题。因此 provider 配置需要支持自定义请求头，
而不是让用户改写代码。

自定义请求头与内置头合并后发送，同名时自定义值优先：内置的 `Content-Type` 与 `Authorization` 是默认行为，
显式配置应能覆盖它们，否则用户无法接入使用非 Bearer 鉴权的端点。

请求头名称与取值必须在使用前校验。名称需符合 HTTP token 字符集，取值不得包含换行——
换行会让单个头部跨越多行，等同于允许注入额外头部。校验必须在写入配置时完成，
避免把非法值存进数据库后导致此后所有生成请求持续失败。

- **AC-GEN-004-01**：自定义请求头必须同时应用于非流式与流式生成请求。
- **AC-GEN-004-02**：自定义请求头与内置头合并，同名时自定义值优先。
- **AC-GEN-004-03**：非法请求头名称或取值必须被拒绝，不得写入配置。
