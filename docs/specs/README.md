# OpenVoca 本地版规格索引

这些文档是本地 OpenVoca 未来开发的需求入口。旧的 `design/` 文档可以保留历史背景，但日常开发、测试维护和 AI 协作应优先从这里开始。

## 使用规则

- 规格用中文描述，便于快速阅读和审查。
- 每条验收标准使用稳定 ID，例如 `AC-LOOP-001-01`。
- 测试映射在 `test-traceability.md` 中维护；每个现有测试必须被映射到验收标准，或标记为 `delete-candidate`。
- `scripts/check_traceability.py` 会检查规格、测试和待删除标记是否同步。

## 文件分组

- `learning-loop.md`：阅读、猜谜、反馈、朗读和前端学习体验。
- `srs-vocabulary.md`：间隔重复算法、词库记录、导入导出和统计数据。
- `dictionary-tokenizer.md`：ECDICT 查询、分词、词性、词元和文本还原。
- `settings-shell.md`：设置、应用壳、更新提示、静态入口和统计页交互。
- `provider-generation.md`：Prompt 构造、LLM provider、OpenAI-compatible client 和生成 API。
