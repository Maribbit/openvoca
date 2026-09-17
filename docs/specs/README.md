# OpenVoca 本地版规格索引

这些文档是本地 OpenVoca 未来开发的需求入口。旧的 `design/` 文档可以保留历史背景，但日常开发、测试维护和 AI 协作应优先从这里开始。

## 使用规则

- 规格用中文描述，便于快速阅读和审查。
- 每条验收标准使用稳定 ID，例如 `AC-LOOP-001-01`。
- 测试映射写在测试文件中，通过验收标准 ID 的内联注释（`# Covers: AC-XXX` / `// Covers: AC-XXX`）建立关联。
- `scripts/check_traceability.py` 检查规格与测试是否同步：缺少测试引用的标准会报错。
- 已定义但尚未实现的验收标准列在 `deferred.txt` 中。门禁据此区分「已规划未实现」与「已实现但测试缺失」；
  某条标准一旦有测试，必须从该列表移除，否则门禁报错，列表不会失效。

## 文件分组

- `learning-loop.md`：阅读、猜谜、反馈、朗读和前端学习体验。
- `srs-vocabulary.md`：间隔重复算法、词库记录、导入导出和统计数据。
- `dictionary-tokenizer.md`：ECDICT 查询、分词、词性、词元和文本还原。
- `settings-shell.md`：设置、密钥存储与交互、应用壳、更新提示、静态入口和统计页交互。
- `provider-generation.md`：Prompt 构造、LLM provider、OpenAI-compatible client 和生成 API。
- `private-deployment.md`：**当前生效的部署规格**。自有机器 + 私有网络，代码与数据分离、启动期模式自检、部署原子性、进程监督、更新请求与执行分离。
- `deployment.md`：公网 VPS 方案，**已搁置**。保留其中的分发一致性不变量，以及将来若需公网暴露时的访问控制条款。
- `release-process.md`：版本号一致性、发布说明提取与修复工具。
