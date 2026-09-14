=================================
  OpenVoca {version}
=================================

快速开始
--------
双击 "openvoca.bat" 启动 OpenVoca。

程序将自动在默认浏览器中打开，后台运行本地服务。
关闭控制台窗口（或按 Ctrl+C）即可停止服务。


初次设置
--------
前往 菜单 -> 设置 -> 模型，填写 LLM 服务配置：

  端点      例如  http://localhost:11434      （Ollama，本地）
                  https://api.openai.com       （OpenAI）
                  https://openrouter.ai/api    （OpenRouter）
                  https://api.siliconflow.cn   （硅基流动）
  API 密钥  你的 API 密钥（本地模型如 Ollama 可留空）
  模型      例如  deepseek-chat / gpt-4o-mini / llama3.2

填写后点击「测试连接」，确认无误再开始使用。


使用方法
--------
1. 打开编排器，选择主题，点击「生成下一句」。
2. 点击句子中任意不认识的单词，查看释义并听发音。
3. 标记「认识」或「不认识」，开始间隔重复复习。

OpenVoca 会在你的记忆消退前重新呈现不熟悉的单词，
让词汇在真实语境中牢固扎根，无需死记硬背。


你的数据
--------
所有词汇和设置都保存在本目录下的 "data" 文件夹中。
更新版本时请先备份该文件夹，以保留学习记录。


支持与更新
----------
GitHub:   https://github.com/Maribbit/openvoca
发布页：  https://github.com/Maribbit/openvoca/releases
