=================================
  OpenVoca {version}
=================================

快速开始
--------
在本目录下打开终端，运行：

    bash run.sh

程序将自动在默认浏览器中打开，后台运行本地服务。
在终端中按 Ctrl+C 即可停止服务。

macOS 注意：启动脚本会自动清除下载文件的隔离属性，
  无需手动处理 Gatekeeper 安全警告。

Linux 注意：如需要，请先赋予执行权限：
  chmod +x run.sh


初次设置
--------
前往 菜单 -> 设置 -> 模型，填写 LLM 服务配置：

  端点      基础地址，带上你的提供商使用的版本前缀：
              http://localhost:11434/v1      （Ollama，本地）
              https://api.openai.com/v1      （OpenAI）
              https://openrouter.ai/api/v1   （OpenRouter）
              https://api.siliconflow.cn/v1  （硅基流动）
              https://api.deepseek.com       （DeepSeek，无版本段）
            /chat/completions 由程序自动拼接。
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
