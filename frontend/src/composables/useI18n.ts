import { computed } from "vue";

import { useSettings } from "./useSettings";

export type Locale = "en" | "zh";

export interface LocaleMessages {
  menu: string;
  readingDisplaySettings: string;
  loadingSentence: string;
  loadingRiddle: string;
  connectionError: string;
  goToSettings: string;
  feedbackError: string;
  model: string;
  targetWordCount: string;
  targetWordCountHint: string;
  suggestionPoolSize: string;
  suggestionPoolSizeHint: string;
  language: string;
  fontSize: string;
  spacing: string;
  theme: string;
  themeLight: string;
  themeDark: string;
  colorTheme: string;
  colorTheme_default: string;
  colorTheme_sepia: string;
  colorTheme_sage: string;
  colorTheme_slate: string;
  uiSize: string;
  uiSizeHint: string;
  reviewProgressBtn: string;
  vocabulary: string;
  backToReading: string;
  clearVocabulary: string;
  exportVocabulary: string;
  importVocabulary: string;
  importModeOverwrite: string;
  importedWords: string;
  importedSkipped: string;
  importFailed: string;
  showingWords: string;
  emptyVocabulary: string;
  stats: string;
  settings: string;
  settingsSubtitle: string;
  interfaceSection: string;
  llmProvider: string;
  llmProviderHint: string;
  testConnection: string;
  testingConnection: string;
  runTest: string;
  stopTest: string;
  testConnectionHint: string;
  testStopped: string;
  testUnreachable: string;
  testRequestLabel: string;
  testResponseLabel: string;
  testUsageLabel: string;
  generationDefaults: string;
  dangerZone: string;
  endpoint: string;
  endpointHint: string;
  apiKey: string;
  apiKeyPlaceholder: string;
  apiKeyHint: string;
  apiKeyConfigured: string;
  apiKeySave: string;
  apiKeyClear: string;
  apiKeyClearConfirm: string;
  providerSaveFailed: string;
  advancedHeaders: string;
  advancedHeadersHint: string;
  headerName: string;
  headerValue: string;
  addHeader: string;
  removeHeader: string;
  saveModel: string;
  savingModel: string;
  modelSaved: string;
  modelUnsaved: string;
  discardModel: string;
  leaveWithUnsaved: string;
  bodyFieldsLabel: string;
  bodyFieldsHint: string;
  bodyFieldName: string;
  bodyFieldValue: string;
  addBodyField: string;
  bodyFieldPresets: string;
  bodyFieldPresetsHint: string;
  disableThinking: string;
  lowerThinking: string;
  bodyFieldRejected: string;
  modelPlaceholder: string;
  clearAllVocabulary: string;
  clearAllVocabularyDescription: string;
  clearDatabase: string;
  clearAllSettings: string;
  clearAllSettingsDescription: string;
  clearSettingsButton: string;
  dataSection: string;
  exportSettings: string;
  exportSettingsDescription: string;
  exportSettingsButton: string;
  importSettings: string;
  importSettingsDescription: string;
  importSettingsButton: string;
  importSettingsBadFormat: string;
  exportVocabularySettings: string;
  exportVocabularySettingsDescription: string;
  exportVocabularySettingsButton: string;
  importVocabularySettings: string;
  importVocabularySettingsDescription: string;
  importVocabularySettingsButton: string;
  confirmClearVocabulary: string;
  confirmClearSettings: string;
  composerScenario: string;
  composerScenario_absurd_headlines: string;
  composerScenario_poetry: string;
  composerScenario_fun_facts: string;
  composerScenario_slice_of_life: string;
  composerScenario_none: string;
  composerCustomPlaceholder: string;
  composerCustomPlaceholderSupplement: string;
  composerAddDetails: string;
  composerCustom: string;
  composerNoLimit: string;
  composerCustomDifficultyPlaceholder: string;
  composerCustomLengthPlaceholder: string;
  composerDifficulty: string;
  composerDiffEasy: string;
  composerDiffNormal: string;
  composerDiffChallenge: string;
  composerLength: string;
  composerLenBrief: string;
  composerLenSentence: string;
  composerLenNarrative: string;
  composerGenerate: string;
  composerPreview: string;
  composerTargetWords: string;
  composerRefreshSuggestions: string;
  composerAddWordPlaceholder: string;
  composerModeSentence: string;
  composerModeRiddle: string;
  composerRiddleScenario: string;
  composerRiddleScenario_vocabulary: string;
  composerRiddleScenario_vocabularyDesc: string;
  composerRiddleScenario_business: string;
  composerRiddleScenario_businessDesc: string;
  composerRiddleScenario_culture: string;
  composerRiddleScenario_cultureDesc: string;
  composerRiddleScenario_geography: string;
  composerRiddleScenario_geographyDesc: string;
  composerRiddleScenario_dialogue: string;
  composerRiddleScenario_dialogueDesc: string;
  composerRiddleScenario_none: string;
  composerGenerateRiddle: string;
  revealAnswer: string;
  riddleClue: string;
  riddleAnswer: string;
  statsInterval: string;
  statsIntervalTip: string;
  statsCooldown: string;
  statsLoading: string;
  timeJustNow: string;
  timeMinutesAgo: (m: number) => string;
  timeHoursAgo: (h: number) => string;
  timeDaysAgo: (d: number) => string;
  editRow: string;
  doneEditingRow: string;
  definitionKnow: string;
  definitionDontKnow: string;
  definitionNotFound: string;
  lemmaLabel: string;
  editLemma: string;
  copySentence: string;
  readAloud: string;
  pronounceWord: string;
  dictionarySection: string;
  dictionaryDisplay: string;
  dictionaryDisplayZh: string;
  dictionaryDisplayEn: string;
  dictionaryDisplayBoth: string;
  deleteWord: string;
  sortByDue: string;
  sortByFamiliarity: string;
  sortByRecent: string;
  lastSeenLabel: string;
  lastContextLabel: string;
  firstSeenLabel: string;
  seenCountLabel: string;
  aboutOpenVoca: string;
  aboutTagline: string;
  aboutDescription: string;
  updateAvailable: string;
  updateDownload: string;
  updateDismiss: string;
  wordSingular: string;
  wordPlural: string;

  progressSummaryTitle: string;
  progressSummaryDesc: string;
  progressRecognized: string;
  progressUnknown: string;
  progressNew: string;
  progressBack: string;
  progressSubmit: string;
  progressEmpty: string;

  onboardingStep1Title: string;
  onboardingStep1Desc: string;
  onboardingStep2Title: string;
  onboardingStep2Desc: string;
  onboardingStep3Title: string;
  onboardingStep3Desc: string;
  howItWorks: string;
}

export const MESSAGES: Record<Locale, LocaleMessages> = {
  en: {
    menu: "MENU",
    readingDisplaySettings: "Reading display settings",
    loadingSentence: "Generating a sentence…",
    loadingRiddle: "Generating a riddle…",
    connectionError: "Unable to reach the model. Check your settings.",
    goToSettings: "Go to Settings →",
    feedbackError: "Failed to save your word feedback.",
    model: "Model",
    targetWordCount: "Auto-selected",
    targetWordCountHint:
      "How many suggestion chips start pre-selected when the Composer opens. Fewer = more natural output.",
    suggestionPoolSize: "Suggestion Pool",
    suggestionPoolSizeHint:
      "How many vocabulary words are offered as toggleable suggestion chips each round.",
    language: "Language",
    fontSize: "Size",
    spacing: "Spacing",
    theme: "Theme",
    themeLight: "Light",
    themeDark: "Dark",
    colorTheme: "Color",
    colorTheme_default: "Ink",
    colorTheme_sepia: "Sepia",
    colorTheme_sage: "Sage",
    colorTheme_slate: "Slate",
    uiSize: "Zoom",
    uiSizeHint:
      "Uses CSS zoom. Requires a modern browser (Chrome 1+, Firefox 126+, Safari 3.1+).",
    reviewProgressBtn: "Review Progress",
    vocabulary: "Your Vocabulary",
    backToReading: "Back to Reading",
    clearVocabulary: "Clear All",
    exportVocabulary: "Export",
    importVocabulary: "Import",
    importModeOverwrite: "Overwrite",
    importedWords: "Imported {0} words",
    importedSkipped: "Imported {0} words, skipped {1}",
    importFailed: "Import failed.",
    showingWords: "words total",
    emptyVocabulary: "No words yet. Start reading to build your vocabulary.",
    stats: "Stats",
    settings: "Settings",
    settingsSubtitle: "Application configuration and preferences.",
    interfaceSection: "Interface",
    llmProvider: "Model",
    llmProviderHint:
      "Uses the OpenAI chat completions format. Compatible with Ollama, OpenRouter, Groq, SiliconFlow, DeepSeek, Z.AI and more.",
    testConnection: "Test Connection",
    testingConnection: "Testing\u2026",
    runTest: "Run Test",
    stopTest: "Stop",
    testConnectionHint:
      "Sends one minimal request using the settings above and prints what was sent and what came back. Nothing is saved, so a configuration can be checked before it replaces one that works.",
    testStopped: "Stopped",
    testUnreachable: "Could not reach the application",
    testRequestLabel: "Request",
    testResponseLabel: "Response",
    testUsageLabel: "Usage",
    generationDefaults: "Word Picking",
    dangerZone: "Danger Zone",
    endpoint: "Endpoint",
    endpointHint:
      "Base URL, including the version prefix your provider uses if it has one. /chat/completions is added automatically, so a full endpoint URL works too. Examples: https://api.openai.com/v1, https://api.deepseek.com, http://localhost:11434/v1",
    apiKey: "API Key",
    apiKeyPlaceholder: "Not required for local models",
    apiKeyHint:
      "Stored locally on your machine. Never transmitted to third parties.",
    apiKeyConfigured: "Configured",
    apiKeySave: "Save Key",
    apiKeyClear: "Clear Key",
    apiKeyClearConfirm:
      "Clear the saved API key? You will need to enter it again.",
    providerSaveFailed: "Failed to save the model configuration.",
    saveModel: "Save",
    savingModel: "Saving\u2026",
    modelSaved: "Saved",
    modelUnsaved: "Unsaved changes",
    discardModel: "Discard",
    leaveWithUnsaved:
      "The model settings have unsaved changes. Leave and discard them?",
    advancedHeaders: "Custom request headers",
    advancedHeadersHint:
      "Some providers require extra request headers, e.g. x-opencode-session.",
    headerName: "Header",
    headerValue: "Value",
    addHeader: "Add Header",
    removeHeader: "Remove",
    bodyFieldsLabel: "Request body fields",
    bodyFieldsHint:
      "Sent as-is in the request body. Providers disagree on how reasoning is turned off, so this is passed through rather than interpreted. A value is read as JSON when it parses, and as text otherwise, so {\"type\": \"disabled\"} and none both work without quoting.",
    bodyFieldName: "Field",
    bodyFieldValue: "Value (JSON or text)",
    addBodyField: "Add Field",
    bodyFieldPresets: "Reasoning presets",
    bodyFieldPresetsHint:
      "Starting points for common providers. Only your provider's own field takes effect, and some models cannot stop thinking at all -- only how hard they think. Check the usage after testing to see which happened.",
    disableThinking: "Disable thinking",
    lowerThinking: "Lower effort",
    bodyFieldRejected:
      "model, messages and stream are set by the application and cannot be configured here.",
    modelPlaceholder: "e.g. deepseek-chat, gpt-4o-mini",
    clearAllVocabulary: "Clear all vocabulary",
    clearAllVocabularyDescription:
      "Permanently delete all word records and learning progress.",
    clearDatabase: "Clear Database",
    clearAllSettings: "Clear all settings",
    clearAllSettingsDescription:
      "Reset all preferences (interface, reading, generation, composer) to defaults.",
    clearSettingsButton: "Clear Settings",
    dataSection: "Data",
    exportSettings: "Export settings",
    exportSettingsDescription:
      "Download every setting as a JSON file for backup or migration, the model configuration included. The API key is never in the file; custom headers are, and a header can carry a credential, so keep it like a password.",
    exportSettingsButton: "Export JSON",
    importSettings: "Import settings",
    importSettingsDescription:
      "Restore settings from a previously exported JSON file, the model configuration included. The API key is not in the file, so if the restored configuration belongs to a different provider, replace the key afterwards.",
    importSettingsButton: "Import JSON",
    importSettingsBadFormat:
      "Invalid settings file. Please select a valid JSON file exported from OpenVoca.",
    exportVocabularySettings: "Export vocabulary",
    exportVocabularySettingsDescription:
      "Download all word records as a CSV file for backup or analysis.",
    exportVocabularySettingsButton: "Export CSV",
    importVocabularySettings: "Import vocabulary",
    importVocabularySettingsDescription:
      "Import words from a CSV file on the Vocabulary page.",
    importVocabularySettingsButton: "Go to Vocabulary →",
    confirmClearVocabulary:
      "Are you sure you want to delete all vocabulary? You can export a backup first using the button above. This cannot be undone.",
    confirmClearSettings:
      "Are you sure you want to reset all settings to defaults? You can export a backup first using the button above. This cannot be undone.",
    composerScenario: "Scenario",
    composerScenario_absurd_headlines: "Fake News",
    composerScenario_poetry: "Poetry",
    composerScenario_fun_facts: "Fun Facts",
    composerScenario_slice_of_life: "Slice of Life",
    composerScenario_none: "Custom",
    composerCustomPlaceholder: "Describe what you want…",
    composerCustomPlaceholderSupplement: "Add details or context…",
    composerAddDetails: "Add details",
    composerCustom: "Custom",
    composerNoLimit: "No limit",
    composerCustomDifficultyPlaceholder: "Describe the difficulty level…",
    composerCustomLengthPlaceholder:
      "Describe the desired length, or leave empty for any…",
    composerDifficulty: "Difficulty",
    composerDiffEasy: "Easy",
    composerDiffNormal: "Normal",
    composerDiffChallenge: "Challenge",
    composerLength: "Length",
    composerLenBrief: "Brief",
    composerLenSentence: "Sentence",
    composerLenNarrative: "Narrative",
    composerGenerate: "Generate next sentence",
    composerPreview: "Preview prompt",
    composerTargetWords: "Target Words",
    composerRefreshSuggestions: "Refresh suggestions",
    composerAddWordPlaceholder: "type & enter",
    composerModeSentence: "Sentence",
    composerModeRiddle: "Riddle",
    composerRiddleScenario: "Scenario",
    composerRiddleScenario_vocabulary: "Vocabulary",
    composerRiddleScenario_vocabularyDesc: "guess a word",
    composerRiddleScenario_business: "Business",
    composerRiddleScenario_businessDesc: "workplace use",
    composerRiddleScenario_culture: "Culture",
    composerRiddleScenario_cultureDesc: "people or events",
    composerRiddleScenario_geography: "Travel",
    composerRiddleScenario_geographyDesc: "places in context",
    composerRiddleScenario_dialogue: "Dialogue",
    composerRiddleScenario_dialogueDesc: "next line",
    composerRiddleScenario_none: "Custom",
    composerGenerateRiddle: "Generate riddle",
    revealAnswer: "Reveal Answer",
    riddleClue: "Clue",
    riddleAnswer: "Answer",
    statsInterval: "Familiarity",
    statsIntervalTip: "Each level doubles the cooldown: 2, 4, 8, 16, 32, 64",
    statsCooldown: "Cooldown",
    statsLoading: "Loading vocabulary...",
    timeJustNow: "just now",
    timeMinutesAgo: (m) => `${m}m ago`,
    timeHoursAgo: (h) => `${h}h ago`,
    timeDaysAgo: (d) => `${d}d ago`,
    editRow: "Edit Row",
    doneEditingRow: "Done Editing",
    definitionKnow: "Know",
    definitionDontKnow: "Don't know",
    definitionNotFound: "No definition found",
    lemmaLabel: "lemma",
    editLemma: "Edit lemma",
    copySentence: "Copy sentence",
    readAloud: "Read aloud",
    pronounceWord: "Pronounce",
    dictionarySection: "Dictionary",
    dictionaryDisplay: "Definition Language",
    dictionaryDisplayZh: "中文",
    dictionaryDisplayEn: "EN",
    dictionaryDisplayBoth: "Both",
    deleteWord: "Delete word",
    sortByDue: "Due for Review",
    sortByFamiliarity: "By Familiarity",
    sortByRecent: "By Recent",
    lastSeenLabel: "Last seen",
    lastContextLabel: "Last context",
    firstSeenLabel: "First seen",
    seenCountLabel: "Seen",
    aboutOpenVoca: "About OpenVoca",
    aboutTagline: "Build Vocabulary Naturally.",
    aboutDescription:
      "A minimalistic, LLM-powered English vocabulary tool — learn new words by reading AI-generated sentences in context.",
    updateAvailable: "New version available: v{0}",
    updateDownload: "Download",
    updateDismiss: "Dismiss",
    wordSingular: "word",
    wordPlural: "words",

    progressSummaryTitle: "Progress Summary",
    progressSummaryDesc: "Here is how your vocabulary will be updated.",
    progressRecognized: "Recognized",
    progressUnknown: "Marked as Unknown",
    progressNew: "First time seen",
    progressBack: "Back to Reading",
    progressSubmit: "Submit",
    progressEmpty: "No vocabulary updates for this sentence.",

    onboardingStep1Title: "Generate a sentence",
    onboardingStep1Desc:
      "Choose a topic and let the AI write a sentence packed with your target words.",
    onboardingStep2Title: "Tap any word",
    onboardingStep2Desc:
      "Tap an unfamiliar word to see its definition and hear it pronounced.",
    onboardingStep3Title: "Know or Don't Know",
    onboardingStep3Desc:
      "Rate each word to schedule spaced-repetition reviews at the right intervals.",
    howItWorks: "How It Works",
  },
  zh: {
    menu: "菜单",
    readingDisplaySettings: "阅读显示设置",
    loadingSentence: "正在生成例句…",
    loadingRiddle: "正在生成谜题…",
    connectionError: "无法连接模型。请检查设置。",
    goToSettings: "前往设置 →",
    feedbackError: "保存词汇反馈失败。",
    model: "模型",
    targetWordCount: "自动选中",
    targetWordCountHint:
      "每次打开编排器时，推荐词中默认选中多少个。越少生成质量越高。",
    suggestionPoolSize: "推荐词数",
    suggestionPoolSizeHint: "每轮从词库抽取多少个词作为推荐词显示。",
    language: "语言",
    fontSize: "字号",
    spacing: "间距",
    theme: "主题",
    themeLight: "明亮",
    themeDark: "暗色",
    colorTheme: "配色",
    colorTheme_default: "墨水",
    colorTheme_sepia: "温柏",
    colorTheme_sage: "鼠尾草",
    colorTheme_slate: "石板",
    uiSize: "缩放",
    uiSizeHint:
      "使用 CSS 缩放。需要现代浏览器（Chrome 1+、Firefox 126+、Safari 3.1+）。",
    reviewProgressBtn: "结算",
    vocabulary: "你的词库",
    backToReading: "返回阅读",
    clearVocabulary: "清空词库",
    exportVocabulary: "导出词库",
    importVocabulary: "导入词库",
    importModeOverwrite: "覆盖",
    importedWords: "已导入 {0} 个单词",
    importedSkipped: "已导入 {0} 个单词，跳过 {1} 个",
    importFailed: "导入失败",
    showingWords: "个单词",
    emptyVocabulary: "暂无单词，开始阅读以积累你的词库。",
    stats: "统计",
    settings: "设置",
    settingsSubtitle: "应用配置与偏好。",
    interfaceSection: "界面",
    llmProvider: "模型配置",
    llmProviderHint:
      "通过 OpenAI chat completions 格式调用。兼容 Ollama、OpenRouter、Groq、硅基流动、DeepSeek、智谱等服务。",
    testConnection: "测试连接",
    testingConnection: "测试中\u2026",
    runTest: "开始测试",
    stopTest: "中断",
    testConnectionHint:
      "用上方配置发送一次最小请求，并打印发送内容与返回内容。不会保存任何设置，因此可以先验证一份配置，再决定是否用它替换现有的。",
    testStopped: "已中断",
    testUnreachable: "无法连接到本应用",
    testRequestLabel: "请求",
    testResponseLabel: "返回",
    testUsageLabel: "用量",
    generationDefaults: "取词策略",
    dangerZone: "危险操作",
    endpoint: "端点",
    endpointHint:
      "基础地址，若你的提供商使用版本前缀则一并填入。/chat/completions 会自动拼接，因此直接填完整端点地址也可以。例如：https://api.openai.com/v1、https://api.deepseek.com、http://localhost:11434/v1",
    apiKey: "API 密钥",
    apiKeyPlaceholder: "本地模型无需填写",
    apiKeyHint: "仅存储在本地，不会传输给第三方。",
    apiKeyConfigured: "已配置",
    apiKeySave: "保存密钥",
    apiKeyClear: "清除密钥",
    apiKeyClearConfirm: "确定要清除已保存的 API 密钥吗？清除后需要重新填写。",
    providerSaveFailed: "保存模型配置失败。",
    saveModel: "保存",
    savingModel: "保存中\u2026",
    modelSaved: "已保存",
    modelUnsaved: "有未保存的更改",
    discardModel: "放弃更改",
    leaveWithUnsaved: "模型配置有未保存的更改，确定离开并放弃吗？",
    advancedHeaders: "自定义请求头",
    advancedHeadersHint: "部分服务商需要额外的请求头，例如 x-opencode-session。",
    headerName: "请求头",
    headerValue: "取值",
    addHeader: "添加请求头",
    removeHeader: "移除",
    bodyFieldsLabel: "请求体字段",
    bodyFieldsHint:
      "原样写入请求体。各家关闭思考的字段并不一致，因此这里只做透传、不做解释。取值能解析为 JSON 时就按 JSON 发送，否则按文本发送，所以 {\"type\": \"disabled\"} 和 none 都可以直接填写、无需加引号。",
    bodyFieldName: "字段",
    bodyFieldValue: "取值（JSON 或文本）",
    addBodyField: "添加字段",
    bodyFieldPresets: "思考控制预设",
    bodyFieldPresetsHint:
      "常见服务商的起始配置。只有你所用服务商的字段会生效；部分模型根本无法关闭思考，只能调整思考强度。测试后请查看用量，以确认实际发生了哪一种。",
    disableThinking: "关闭思考",
    lowerThinking: "降低强度",
    bodyFieldRejected:
      "model、messages 与 stream 由应用设置，不能在此配置。",
    modelPlaceholder: "如 deepseek-chat、gpt-4o-mini",
    clearAllVocabulary: "清空所有词汇",
    clearAllVocabularyDescription: "永久删除所有单词记录和学习进度。",
    clearDatabase: "清空数据库",
    clearAllSettings: "清空所有设置",
    clearAllSettingsDescription:
      "将所有偏好设置（界面、阅读、生成、编排器）恢复为默认值。",
    clearSettingsButton: "清空设置",
    dataSection: "数据",
    exportSettings: "导出设置",
    exportSettingsDescription:
      "将所有设置导出为 JSON 文件，用于备份或迁移，包含模型配置。文件不包含 API 密钥；包含自定义请求头，而请求头可能承载凭据，请像对待密码一样保管。",
    exportSettingsButton: "导出 JSON",
    importSettings: "导入设置",
    importSettingsDescription:
      "从之前导出的 JSON 文件恢复设置，包含模型配置。文件不含 API 密钥；若恢复的配置属于另一个服务商，请之后重新填写密钥。",
    importSettingsButton: "导入 JSON",
    importSettingsBadFormat:
      "无效的设置文件，请选择从 OpenVoca 导出的 JSON 文件。",
    exportVocabularySettings: "导出词库",
    exportVocabularySettingsDescription:
      "将所有单词记录下载为 CSV 文件，用于备份或分析。",
    exportVocabularySettingsButton: "导出 CSV",
    importVocabularySettings: "导入词库",
    importVocabularySettingsDescription: "在词库页面从 CSV 文件导入单词。",
    importVocabularySettingsButton: "前往词库 →",
    confirmClearVocabulary:
      "确定要删除所有词汇吗？建议先通过上方的导出按钮备份。此操作不可撤销。",
    confirmClearSettings:
      "确定要恢复所有设置为默认值吗？建议先通过上方的导出按钮备份。此操作不可撤销。",
    composerScenario: "场景",
    composerScenario_absurd_headlines: "假新闻",
    composerScenario_poetry: "诗歌",
    composerScenario_fun_facts: "冷知识",
    composerScenario_slice_of_life: "日常",
    composerScenario_none: "自定义",
    composerCustomPlaceholder: "描述你想要的内容…",
    composerCustomPlaceholderSupplement: "添加细节或上下文…",
    composerAddDetails: "添加细节",
    composerCustom: "自定义",
    composerNoLimit: "不限",
    composerCustomDifficultyPlaceholder: "描述难度要求…",
    composerCustomLengthPlaceholder: "描述长度要求，留空则不限…",
    composerDifficulty: "难度",
    composerDiffEasy: "简单",
    composerDiffNormal: "普通",
    composerDiffChallenge: "挑战",
    composerLength: "长度",
    composerLenBrief: "短句",
    composerLenSentence: "标准句",
    composerLenNarrative: "长句",
    composerGenerate: "生成下一句",
    composerPreview: "预览提示词",
    composerTargetWords: "目标词",
    composerRefreshSuggestions: "刷新推荐词",
    composerAddWordPlaceholder: "输入并回车",
    composerModeSentence: "例句",
    composerModeRiddle: "猜谜",
    composerRiddleScenario: "场景",
    composerRiddleScenario_vocabulary: "词汇",
    composerRiddleScenario_vocabularyDesc: "猜词短语",
    composerRiddleScenario_business: "商务",
    composerRiddleScenario_businessDesc: "职场表达",
    composerRiddleScenario_culture: "文化",
    composerRiddleScenario_cultureDesc: "人物事件",
    composerRiddleScenario_geography: "旅行",
    composerRiddleScenario_geographyDesc: "地点语境",
    composerRiddleScenario_dialogue: "对话",
    composerRiddleScenario_dialogueDesc: "接下一句",
    composerRiddleScenario_none: "自定义",
    composerGenerateRiddle: "生成谜题",
    revealAnswer: "揭晓答案",
    riddleClue: "提示",
    riddleAnswer: "答案",
    statsInterval: "熟悉度",
    statsIntervalTip: "每升一级，冷却翻倍：2, 4, 8, 16, 32, 64",
    statsCooldown: "冷却剩余",
    statsLoading: "词汇加载中...",
    timeJustNow: "刚刚",
    timeMinutesAgo: (m) => `${m} 分钟前`,
    timeHoursAgo: (h) => `${h} 小时前`,
    timeDaysAgo: (d) => `${d} 天前`,
    editRow: "编辑",
    doneEditingRow: "完成",
    definitionKnow: "认识",
    definitionDontKnow: "不认识",
    definitionNotFound: "未找到释义",
    lemmaLabel: "词元",
    editLemma: "编辑词元",
    copySentence: "复制句子",
    readAloud: "朗读",
    pronounceWord: "发音",
    dictionarySection: "词典",
    dictionaryDisplay: "释义语言",
    dictionaryDisplayZh: "中文",
    dictionaryDisplayEn: "EN",
    dictionaryDisplayBoth: "双语",
    deleteWord: "删除词条",
    sortByDue: "即将复习",
    sortByFamiliarity: "按熟悉度",
    sortByRecent: "按最近复习",
    lastSeenLabel: "上次复习",
    lastContextLabel: "上次例句",
    firstSeenLabel: "首次记录",
    seenCountLabel: "出现次数",
    aboutOpenVoca: "关于 OpenVoca",
    aboutTagline: "在阅读中自然积累词汇。",
    aboutDescription:
      "一个极简的、基于 LLM 的英语词汇工具——通过阅读 AI 生成的上下文例句来学习新单词。",
    updateAvailable: "发现新版本：v{0}",
    updateDownload: "下载",
    updateDismiss: "关闭",
    wordSingular: "词",
    wordPlural: "词",

    progressSummaryTitle: "进度结算",
    progressSummaryDesc: "以下词汇的掌握程度将会更新。",
    progressRecognized: "已认识",
    progressUnknown: "不认识",
    progressNew: "初次遇到",
    progressBack: "返回阅读",
    progressSubmit: "提交",
    progressEmpty: "当前句子没有词汇进度更新。",

    onboardingStep1Title: "生成例句",
    onboardingStep1Desc: "选择主题，让 AI 生成一句包含你目标词汇的英文句子。",
    onboardingStep2Title: "点击生词",
    onboardingStep2Desc: "点击不认识的单词，即可查看释义并听到标准发音。",
    onboardingStep3Title: "认识 / 不认识",
    onboardingStep3Desc: "为每个单词打分，系统将按照遗忘曲线为你安排复习。",
    howItWorks: "使用说明",
  },
};

const SETTINGS_CACHE_KEY = "openvoca.settings.cache";

function normalizeLocale(value: unknown): Locale | null {
  return value === "en" || value === "zh" ? value : null;
}

function detectCachedLocale(): Locale | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(SETTINGS_CACHE_KEY);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as { interface?: { locale?: unknown } };
    return normalizeLocale(parsed.interface?.locale);
  } catch {
    return null;
  }
}

function detectBrowserLocale(): Locale {
  if (typeof window !== "undefined") {
    return window.navigator.language.toLowerCase().startsWith("zh")
      ? "zh"
      : "en";
  }

  return "en";
}

export function useI18n() {
  const { get, set } = useSettings();

  const locale = computed<Locale>(() => {
    return (
      normalizeLocale(get("interface", "locale", "")) ??
      detectCachedLocale() ??
      detectBrowserLocale()
    );
  });

  const messages = computed(() => MESSAGES[locale.value]);

  function setLocale(nextLocale: Locale): void {
    set("interface", { locale: nextLocale });
  }

  return {
    locale,
    messages,
    setLocale,
  };
}
