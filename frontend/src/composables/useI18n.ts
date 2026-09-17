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
      "Uses the OpenAI API format (/v1/chat/completions). Compatible with Ollama, OpenRouter, Groq, SiliconFlow, and more.",
    testConnection: "Test Connection",
    testingConnection: "Testing\u2026",
    generationDefaults: "Word Picking",
    dangerZone: "Danger Zone",
    endpoint: "Endpoint",
    endpointHint:
      "Enter the base URL only (e.g. http://localhost:11434). The /v1/chat/completions path is added automatically.",
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
    advancedHeaders: "Advanced: Custom Headers",
    advancedHeadersHint:
      "Some providers require extra request headers, e.g. x-opencode-session.",
    headerName: "Header",
    headerValue: "Value",
    addHeader: "Add Header",
    removeHeader: "Remove",
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
      "Download all settings as a JSON file for backup or migration.",
    exportSettingsButton: "Export JSON",
    importSettings: "Import settings",
    importSettingsDescription:
      "Restore settings from a previously exported JSON file. API key is not imported for security.",
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
      "通过 OpenAI API 格式（/v1/chat/completions）调用。兼容 Ollama、OpenRouter、Groq、硅基流动等服务。",
    testConnection: "测试连接",
    testingConnection: "测试中\u2026",
    generationDefaults: "取词策略",
    dangerZone: "危险操作",
    endpoint: "端点",
    endpointHint:
      "只填基础地址（如 http://localhost:11434），/v1/chat/completions 路径会自动拼接。",
    apiKey: "API 密钥",
    apiKeyPlaceholder: "本地模型无需填写",
    apiKeyHint: "仅存储在本地，不会传输给第三方。",
    apiKeyConfigured: "已配置",
    apiKeySave: "保存密钥",
    apiKeyClear: "清除密钥",
    apiKeyClearConfirm: "确定要清除已保存的 API 密钥吗？清除后需要重新填写。",
    providerSaveFailed: "保存模型配置失败。",
    advancedHeaders: "高级：自定义请求头",
    advancedHeadersHint:
      "部分服务商需要额外的请求头，例如 x-opencode-session。",
    headerName: "请求头",
    headerValue: "取值",
    addHeader: "添加请求头",
    removeHeader: "移除",
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
    exportSettingsDescription: "将所有设置下载为 JSON 文件，用于备份或迁移。",
    exportSettingsButton: "导出 JSON",
    importSettings: "导入设置",
    importSettingsDescription:
      "从之前导出的 JSON 文件恢复设置。为安全起见，API 密钥不会被导入。",
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
