# 测试追溯映射

本文件把现有测试逐一对应到中文规格中的验收标准。`status: keep` 表示该测试承载了概念；`status: delete-candidate` 表示测试暂时保留，但它更像实现细节或纯视觉断言，后续可以逐个复查是否删除。

## 后端测试

### backend/tests/test_algorithm.py

- test: backend/tests/test_algorithm.py::test_apply_feedback_decreases_level_for_marked_words
  status: keep
  covers: AC-SRS-001-01
- test: backend/tests/test_algorithm.py::test_apply_feedback_caps_level_at_boundaries
  status: keep
  covers: AC-SRS-001-02
- test: backend/tests/test_algorithm.py::test_graduated_word_relapse_on_mark
  status: keep
  covers: AC-SRS-001-03
- test: backend/tests/test_algorithm.py::test_tick_cooldowns_decrements
  status: keep
  covers: AC-SRS-002-01
- test: backend/tests/test_algorithm.py::test_tick_cooldowns_does_not_go_below_zero
  status: keep
  covers: AC-SRS-002-02
- test: backend/tests/test_algorithm.py::test_cooldown_words_not_picked
  status: keep
  covers: AC-SRS-002-02
- test: backend/tests/test_algorithm.py::test_graduated_words_not_picked
  status: keep
  covers: AC-SRS-002-03
- test: backend/tests/test_algorithm.py::test_pick_target_words_returns_lowest_level
  status: keep
  covers: AC-SRS-002-04
- test: backend/tests/test_algorithm.py::test_full_round_simulation
  status: keep
  covers: AC-SRS-003-01
- test: backend/tests/test_algorithm.py::test_original_targets_advances_unmatched_word
  status: keep
  covers: AC-SRS-004-01
- test: backend/tests/test_algorithm.py::test_original_targets_skipped_when_already_processed
  status: keep
  covers: AC-SRS-004-02
- test: backend/tests/test_algorithm.py::test_original_targets_skipped_when_marked_unknown
  status: keep
  covers: AC-SRS-004-03

### backend/tests/test_dictionary.py

- test: backend/tests/test_dictionary.py::test_lookup_known_word
  status: keep
  covers: AC-DICT-001-01
- test: backend/tests/test_dictionary.py::test_lookup_case_insensitive
  status: keep
  covers: AC-DICT-001-01
- test: backend/tests/test_dictionary.py::test_lookup_unknown_word
  status: keep
  covers: AC-DICT-001-01
- test: backend/tests/test_dictionary.py::test_lookup_custom_found
  status: keep
  covers: AC-DICT-001-02
- test: backend/tests/test_dictionary.py::test_lookup_custom_not_found
  status: keep
  covers: AC-DICT-001-02
- test: backend/tests/test_dictionary.py::test_api_dictionary_found
  status: keep
  covers: AC-DICT-001-03
- test: backend/tests/test_dictionary.py::test_api_dictionary_not_found
  status: keep
  covers: AC-DICT-001-03

### backend/tests/test_main.py

- test: backend/tests/test_main.py::test_health_endpoint
  status: keep
  covers: AC-SHELL-001-01
- test: backend/tests/test_main.py::test_reading_sentence_endpoint_returns_pos_tags
  status: keep
  covers: AC-GEN-002-01, AC-TOK-001-01, AC-TOK-001-02
- test: backend/tests/test_main.py::test_reading_sentence_endpoint_returns_riddle_payload
  status: keep
  covers: AC-LOOP-004-01
- test: backend/tests/test_main.py::test_stream_reading_sentence_endpoint_accepts_fenced_riddle_json
  status: keep
  covers: AC-LOOP-004-01, AC-LOOP-005-01
- test: backend/tests/test_main.py::test_reading_sentence_endpoint_rejects_invalid_riddle_json
  status: keep
  covers: AC-LOOP-004-03
- test: backend/tests/test_main.py::test_target_words_endpoint_picks_from_vocabulary
  status: keep
  covers: AC-LOOP-002-01
- test: backend/tests/test_main.py::test_delete_vocabulary_endpoint
  status: keep
  covers: AC-SRS-006-01
- test: backend/tests/test_main.py::test_reading_sentence_returns_502_on_ollama_failure
  status: keep
  covers: AC-GEN-002-03, AC-LOOP-005-02
- test: backend/tests/test_main.py::test_feedback_via_api
  status: keep
  covers: AC-LOOP-003-02, AC-SRS-001-01
- test: backend/tests/test_main.py::test_vocabulary_endpoint
  status: keep
  covers: AC-SRS-009-01
- test: backend/tests/test_main.py::test_next_endpoint_ticks_cooldowns
  status: keep
  covers: AC-GEN-002-02
- test: backend/tests/test_main.py::test_target_words_endpoint_does_not_tick
  status: keep
  covers: AC-LOOP-002-02, AC-GEN-002-02
- test: backend/tests/test_main.py::test_next_endpoint_accepts_full_prompt
  status: keep
  covers: AC-GEN-001-04, AC-GEN-002-01
- test: backend/tests/test_main.py::test_next_endpoint_works_with_minimal_prompt
  status: keep
  covers: AC-GEN-002-01
- test: backend/tests/test_main.py::test_export_vocabulary_csv
  status: keep
  covers: AC-SRS-008-01
- test: backend/tests/test_main.py::test_export_vocabulary_csv_empty
  status: keep
  covers: AC-SRS-008-01
- test: backend/tests/test_main.py::test_patch_vocabulary_word
  status: keep
  covers: AC-SRS-006-02
- test: backend/tests/test_main.py::test_patch_vocabulary_word_not_found
  status: keep
  covers: AC-SRS-006-03
- test: backend/tests/test_main.py::test_delete_vocabulary_word
  status: keep
  covers: AC-SRS-006-04
- test: backend/tests/test_main.py::test_delete_vocabulary_word_not_found
  status: keep
  covers: AC-SRS-006-04
- test: backend/tests/test_main.py::test_delete_then_patch_stale
  status: keep
  covers: AC-SRS-006-03
- test: backend/tests/test_main.py::test_vocabulary_sort_due
  status: keep
  covers: AC-SRS-009-02
- test: backend/tests/test_main.py::test_vocabulary_sort_familiarity
  status: keep
  covers: AC-SRS-009-02
- test: backend/tests/test_main.py::test_vocabulary_sort_recent
  status: keep
  covers: AC-SRS-009-02
- test: backend/tests/test_main.py::test_vocabulary_sort_invalid
  status: keep
  covers: AC-SRS-009-02
- test: backend/tests/test_main.py::test_vocabulary_includes_last_seen
  status: keep
  covers: AC-SRS-009-01
- test: backend/tests/test_main.py::test_import_vocabulary_endpoint
  status: keep
  covers: AC-SRS-008-02
- test: backend/tests/test_main.py::test_import_vocabulary_endpoint_upserts_existing
  status: keep
  covers: AC-SRS-008-03
- test: backend/tests/test_main.py::test_import_vocabulary_endpoint_skips_invalid_rows
  status: keep
  covers: AC-SRS-008-04
- test: backend/tests/test_main.py::test_import_vocabulary_endpoint_file_too_large
  status: keep
  covers: AC-SRS-008-04
- test: backend/tests/test_main.py::test_import_vocabulary_endpoint_non_utf8
  status: keep
  covers: AC-SRS-008-04
- test: backend/tests/test_main.py::test_export_import_roundtrip
  status: keep
  covers: AC-SRS-008-06
- test: backend/tests/test_main.py::test_import_vocabulary_endpoint_skip_mode
  status: keep
  covers: AC-SRS-008-03
- test: backend/tests/test_main.py::test_import_vocabulary_endpoint_minimal_csv
  status: keep
  covers: AC-SRS-008-02
- test: backend/tests/test_main.py::test_import_vocabulary_legacy_pos_csv
  status: keep
  covers: AC-SRS-008-05
- test: backend/tests/test_main.py::test_import_vocabulary_endpoint_bom_csv
  status: keep
  covers: AC-SRS-008-05

### backend/tests/test_openai_compat.py

- test: backend/tests/test_openai_compat.py::test_openai_compatible_client_returns_sentence
  status: keep
  covers: AC-GEN-003-01
- test: backend/tests/test_openai_compat.py::test_openai_compatible_client_rejects_empty_response
  status: keep
  covers: AC-GEN-003-02
- test: backend/tests/test_openai_compat.py::test_openai_compatible_client_satisfies_provider_protocol
  status: keep
  covers: AC-GEN-003-03
- test: backend/tests/test_openai_compat.py::test_openai_compatible_client_reuses_connection
  status: keep
  covers: AC-GEN-003-03
- test: backend/tests/test_openai_compat.py::test_openai_compatible_client_aclose
  status: keep
  covers: AC-GEN-003-04
- test: backend/tests/test_openai_compat.py::test_openai_compatible_client_streams_chunks
  status: keep
  covers: AC-GEN-003-05

### backend/tests/test_prompt_builder.py

- test: backend/tests/test_prompt_builder.py::test_build_prompt_appends_marking_directive
  status: keep
  covers: AC-GEN-001-01
- test: backend/tests/test_prompt_builder.py::test_build_prompt_no_marking_without_words
  status: keep
  covers: AC-GEN-001-02
- test: backend/tests/test_prompt_builder.py::test_build_prompt_requires_prompt
  status: keep
  covers: AC-GEN-001-03
- test: backend/tests/test_prompt_builder.py::test_build_prompt_strips_whitespace
  status: keep
  covers: AC-GEN-001-03
- test: backend/tests/test_prompt_builder.py::test_build_prompt_ignores_blank_words
  status: keep
  covers: AC-GEN-001-02
- test: backend/tests/test_prompt_builder.py::test_build_prompt_preserves_full_prompt
  status: keep
  covers: AC-GEN-001-04

### backend/tests/test_settings.py

- test: backend/tests/test_settings.py::TestSettingsStore::test_upsert_and_get_single_setting
  status: keep
  covers: AC-SET-001-01
- test: backend/tests/test_settings.py::TestSettingsStore::test_get_missing_setting_returns_none
  status: keep
  covers: AC-SET-001-01
- test: backend/tests/test_settings.py::TestSettingsStore::test_upsert_overwrites_existing
  status: keep
  covers: AC-SET-001-01
- test: backend/tests/test_settings.py::TestSettingsStore::test_get_namespace_returns_all_keys
  status: keep
  covers: AC-SET-001-02
- test: backend/tests/test_settings.py::TestSettingsStore::test_get_namespace_empty
  status: keep
  covers: AC-SET-001-02
- test: backend/tests/test_settings.py::TestSettingsStore::test_get_all_settings_grouped
  status: keep
  covers: AC-SET-001-02
- test: backend/tests/test_settings.py::TestSettingsStore::test_upsert_namespace_batch
  status: keep
  covers: AC-SET-001-02
- test: backend/tests/test_settings.py::TestSettingsStore::test_upsert_namespace_updates_existing
  status: keep
  covers: AC-SET-001-02
- test: backend/tests/test_settings.py::TestSettingsStore::test_delete_namespace
  status: keep
  covers: AC-SET-001-03
- test: backend/tests/test_settings.py::TestSettingsStore::test_delete_empty_namespace
  status: keep
  covers: AC-SET-001-03
- test: backend/tests/test_settings.py::TestSettingsStore::test_clear_all_settings
  status: keep
  covers: AC-SET-001-03
- test: backend/tests/test_settings.py::TestSettingsStore::test_clear_all_settings_empty
  status: keep
  covers: AC-SET-001-03
- test: backend/tests/test_settings.py::test_api_get_all_settings_empty
  status: keep
  covers: AC-SET-001-04
- test: backend/tests/test_settings.py::test_api_put_and_get_single_setting
  status: keep
  covers: AC-SET-001-04
- test: backend/tests/test_settings.py::test_api_put_namespace_batch
  status: keep
  covers: AC-SET-001-04
- test: backend/tests/test_settings.py::test_api_get_all_settings_grouped
  status: keep
  covers: AC-SET-001-04
- test: backend/tests/test_settings.py::test_api_put_setting_rejects_empty_value
  status: keep
  covers: AC-SET-001-04
- test: backend/tests/test_settings.py::test_api_delete_all_settings
  status: keep
  covers: AC-SET-001-04
- test: backend/tests/test_settings.py::test_api_delete_all_settings_empty
  status: keep
  covers: AC-SET-001-04

### backend/tests/test_static.py

- test: backend/tests/test_static.py::test_spa_fallback_returns_index_html
  status: keep
  covers: AC-SHELL-001-02

### backend/tests/test_tokenizer.py

- test: backend/tests/test_tokenizer.py::test_tokenize_plain_sentence
  status: keep
  covers: AC-TOK-001-01
- test: backend/tests/test_tokenizer.py::test_tokenize_with_target_words
  status: keep
  covers: AC-TOK-001-02
- test: backend/tests/test_tokenizer.py::test_tokenize_mixed_content
  status: keep
  covers: AC-TOK-001-02, AC-TOK-003-02
- test: backend/tests/test_tokenizer.py::test_target_word_bypasses_stopword_filter
  status: keep
  covers: AC-TOK-001-03
- test: backend/tests/test_tokenizer.py::test_tokenize_bold_markdown
  status: keep
  covers: AC-TOK-001-02
- test: backend/tests/test_tokenizer.py::test_tokenize_with_pos_for_all_words
  status: keep
  covers: AC-TOK-001-01
- test: backend/tests/test_tokenizer.py::test_tokenize_distinguishes_leaves_by_context
  status: keep
  covers: AC-TOK-001-01
- test: backend/tests/test_tokenizer.py::test_tokenize_empty_sentence
  status: keep
  covers: AC-TOK-001-04
- test: backend/tests/test_tokenizer.py::test_tokenize_contraction
  status: keep
  covers: AC-TOK-002-01
- test: backend/tests/test_tokenizer.py::test_trailing_space_on_contractions
  status: keep
  covers: AC-TOK-002-01
- test: backend/tests/test_tokenizer.py::test_hyphenated_target_word
  status: keep
  covers: AC-TOK-002-02
- test: backend/tests/test_tokenizer.py::test_hyphenated_non_target_word
  status: keep
  covers: AC-TOK-002-02
- test: backend/tests/test_tokenizer.py::test_hyphenated_chain
  status: keep
  covers: AC-TOK-002-02
- test: backend/tests/test_tokenizer.py::test_well_noun_is_clickable
  status: keep
  covers: AC-TOK-003-01
- test: backend/tests/test_tokenizer.py::test_can_noun_is_clickable
  status: keep
  covers: AC-TOK-003-01
- test: backend/tests/test_tokenizer.py::test_will_noun_is_clickable
  status: keep
  covers: AC-TOK-003-01
- test: backend/tests/test_tokenizer.py::test_auxiliaries_always_filtered
  status: keep
  covers: AC-TOK-003-01
- test: backend/tests/test_tokenizer.py::test_function_pos_always_filtered
  status: keep
  covers: AC-TOK-003-02
- test: backend/tests/test_tokenizer.py::test_tokens_include_lemma
  status: keep
  covers: AC-TOK-004-01
- test: backend/tests/test_tokenizer.py::test_double_s_lemma_preserved
  status: keep
  covers: AC-TOK-004-02

### backend/tests/test_word_store.py

- test: backend/tests/test_word_store.py::test_apply_feedback_creates_new_records
  status: keep
  covers: AC-SRS-001-01, AC-SRS-005-01
- test: backend/tests/test_word_store.py::test_apply_feedback_sets_first_seen_once
  status: keep
  covers: AC-SRS-005-01
- test: backend/tests/test_word_store.py::test_apply_feedback_increments_seen_count
  status: keep
  covers: AC-SRS-005-01
- test: backend/tests/test_word_store.py::test_non_target_word_marked_creates_record
  status: keep
  covers: AC-SRS-005-02
- test: backend/tests/test_word_store.py::test_last_context_stored
  status: keep
  covers: AC-SRS-005-01
- test: backend/tests/test_word_store.py::test_clear_all_words_empties_database
  status: keep
  covers: AC-SRS-006-01
- test: backend/tests/test_word_store.py::test_update_word_record_level
  status: keep
  covers: AC-SRS-006-02
- test: backend/tests/test_word_store.py::test_update_word_record_level_clamped
  status: keep
  covers: AC-SRS-006-02
- test: backend/tests/test_word_store.py::test_update_word_record_cooldown
  status: keep
  covers: AC-SRS-006-02
- test: backend/tests/test_word_store.py::test_update_word_record_cooldown_clamped
  status: keep
  covers: AC-SRS-006-02
- test: backend/tests/test_word_store.py::test_update_word_record_not_found
  status: keep
  covers: AC-SRS-006-03
- test: backend/tests/test_word_store.py::test_delete_word_record
  status: keep
  covers: AC-SRS-006-04
- test: backend/tests/test_word_store.py::test_delete_word_record_not_found
  status: keep
  covers: AC-SRS-006-04
- test: backend/tests/test_word_store.py::test_delete_stale_record
  status: keep
  covers: AC-SRS-006-04
- test: backend/tests/test_word_store.py::test_update_stale_record
  status: keep
  covers: AC-SRS-006-03
- test: backend/tests/test_word_store.py::test_make_engine_default_path
  status: keep
  covers: AC-SRS-007-01
- test: backend/tests/test_word_store.py::test_make_engine_respects_data_dir
  status: keep
  covers: AC-SRS-007-01
- test: backend/tests/test_word_store.py::test_import_vocabulary_creates_new_records
  status: keep
  covers: AC-SRS-008-02
- test: backend/tests/test_word_store.py::test_import_vocabulary_overwrite_existing_records
  status: keep
  covers: AC-SRS-008-03
- test: backend/tests/test_word_store.py::test_import_vocabulary_skip_preserves_existing_records
  status: keep
  covers: AC-SRS-008-03
- test: backend/tests/test_word_store.py::test_import_vocabulary_default_mode_is_skip
  status: keep
  covers: AC-SRS-008-03
- test: backend/tests/test_word_store.py::test_import_vocabulary_skips_missing_columns
  status: keep
  covers: AC-SRS-008-04
- test: backend/tests/test_word_store.py::test_import_vocabulary_skips_empty_lemma
  status: keep
  covers: AC-SRS-008-04
- test: backend/tests/test_word_store.py::test_import_vocabulary_skips_non_integer_values
  status: keep
  covers: AC-SRS-008-04
- test: backend/tests/test_word_store.py::test_import_vocabulary_clamps_out_of_range_values
  status: keep
  covers: AC-SRS-008-05
- test: backend/tests/test_word_store.py::test_import_vocabulary_normalizes_case
  status: keep
  covers: AC-SRS-008-05
- test: backend/tests/test_word_store.py::test_import_vocabulary_legacy_pos_column_ignored
  status: keep
  covers: AC-SRS-008-05
- test: backend/tests/test_word_store.py::test_import_vocabulary_empty_rows
  status: keep
  covers: AC-SRS-008-04
- test: backend/tests/test_word_store.py::test_import_vocabulary_too_many_rows
  status: keep
  covers: AC-SRS-008-04
- test: backend/tests/test_word_store.py::test_import_result_is_dataclass
  status: delete-candidate
  reason: 只验证 ImportResult 的 dataclass 默认值，概念价值低，导入结果语义已由导入测试覆盖。
- test: backend/tests/test_word_store.py::test_import_vocabulary_minimal_columns
  status: keep
  covers: AC-SRS-008-02
- test: backend/tests/test_word_store.py::test_import_vocabulary_with_last_seen_and_context
  status: keep
  covers: AC-SRS-008-05
- test: backend/tests/test_word_store.py::test_import_vocabulary_bad_last_seen_skips_row
  status: keep
  covers: AC-SRS-008-04
- test: backend/tests/test_word_store.py::test_draft_feedback
  status: keep
  covers: AC-SRS-010-01, AC-LOOP-003-01

## 前端测试

### frontend/tests/App.spec.ts

- test: frontend/tests/App.spec.ts::shows banner when update is available
  status: keep
  covers: AC-SHELL-002-01
- test: frontend/tests/App.spec.ts::hides banner when dismissed
  status: keep
  covers: AC-SHELL-002-02
- test: frontend/tests/App.spec.ts::does not show banner when no update is available
  status: keep
  covers: AC-SHELL-002-01
- test: frontend/tests/App.spec.ts::keeps the reading sentence when visiting another route
  status: keep
  covers: AC-LOOP-001-03
- test: frontend/tests/App.spec.ts::updates cached reading copy when language changes in settings
  status: keep
  covers: AC-SET-002-03

### frontend/tests/DefinitionToast.spec.ts

- test: frontend/tests/DefinitionToast.spec.ts::renders the speak-word button
  status: delete-candidate
  reason: 单独验证按钮存在，播放、回退和未找到词朗读测试已经覆盖同一入口的实际行为。
- test: frontend/tests/DefinitionToast.spec.ts::plays word audio via /api/tts when speak button is clicked
  status: keep
  covers: AC-LOOP-006-02
- test: frontend/tests/DefinitionToast.spec.ts::falls back to browser SpeechSynthesis on audio error
  status: keep
  covers: AC-LOOP-006-02
- test: frontend/tests/DefinitionToast.spec.ts::stops playback when clicked while speaking
  status: keep
  covers: AC-LOOP-006-02
- test: frontend/tests/DefinitionToast.spec.ts::uses notFoundWord when entry is null
  status: keep
  covers: AC-LOOP-006-02, AC-LOOP-006-03
- test: frontend/tests/DefinitionToast.spec.ts::emits normalized lemma edits
  status: keep
  covers: AC-LOOP-006-03, AC-TOK-005-01
- test: frontend/tests/DefinitionToast.spec.ts::does not repeat the lemma label when it matches the lookup word
  status: keep
  covers: AC-LOOP-006-03

### frontend/tests/HomeView.spec.ts

- test: frontend/tests/HomeView.spec.ts::renders the generated reading sentence
  status: keep
  covers: AC-LOOP-001-01, AC-LOOP-001-02, AC-LOOP-006-01
- test: frontend/tests/HomeView.spec.ts::reveals riddle answers before progress review
  status: keep
  covers: AC-LOOP-004-01
- test: frontend/tests/HomeView.spec.ts::builds concise English riddle prompts from a scene and custom details
  status: keep
  covers: AC-LOOP-004-02
- test: frontend/tests/HomeView.spec.ts::shows stream generation error details in the composer
  status: keep
  covers: AC-LOOP-004-03, AC-LOOP-005-02
- test: frontend/tests/HomeView.spec.ts::opens progress summary on continue and advances on submit
  status: keep
  covers: AC-LOOP-003-01, AC-LOOP-003-02
- test: frontend/tests/HomeView.spec.ts::switches UI language to Chinese and persists locale
  status: keep
  covers: AC-SET-002-03
- test: frontend/tests/HomeView.spec.ts::applies and persists dark reading theme from inline settings
  status: keep
  covers: AC-SET-003-01
- test: frontend/tests/HomeView.spec.ts::closes inline settings when clicking the blank overlay
  status: keep
  covers: AC-SET-003-02
- test: frontend/tests/HomeView.spec.ts::shows streaming word count progress during generation
  status: keep
  covers: AC-LOOP-005-01
- test: frontend/tests/HomeView.spec.ts::plays TTS audio from backend when read aloud is clicked
  status: keep
  covers: AC-LOOP-006-02
- test: frontend/tests/HomeView.spec.ts::uses corrected lemmas for draft and submit
  status: keep
  covers: AC-LOOP-003-03, AC-TOK-005-02

### frontend/tests/ProgressSummaryModal.spec.ts

- test: frontend/tests/ProgressSummaryModal.spec.ts::uses theme-aware level delta badges
  status: delete-candidate
  reason: 主要断言 Tailwind class，缺少独立概念；进度弹窗的学习语义由 draft feedback 和提交流程测试覆盖。
- test: frontend/tests/ProgressSummaryModal.spec.ts::emits normalized lemma edits
  status: keep
  covers: AC-LOOP-003-03, AC-TOK-005-01

### frontend/tests/reading.spec.ts

- test: frontend/tests/reading.spec.ts::joins tokens with spaces based on trailingSpace
  status: keep
  covers: AC-TOK-002-03
- test: frontend/tests/reading.spec.ts::handles contractions without extra spaces
  status: keep
  covers: AC-TOK-002-03
- test: frontend/tests/reading.spec.ts::handles hyphenated compound words
  status: keep
  covers: AC-TOK-002-03
- test: frontend/tests/reading.spec.ts::returns empty string for empty token list
  status: keep
  covers: AC-TOK-002-03
- test: frontend/tests/reading.spec.ts::defaults trailingSpace to true when undefined
  status: keep
  covers: AC-TOK-002-03
- test: frontend/tests/reading.spec.ts::handles punctuation attached to words
  status: keep
  covers: AC-TOK-002-03

### frontend/tests/StatsView.spec.ts

- test: frontend/tests/StatsView.spec.ts::moves delete out of the row edit action
  status: keep
  covers: AC-STATS-001-01
- test: frontend/tests/StatsView.spec.ts::uses centered text inputs for numeric editing
  status: delete-candidate
  reason: 只检查输入框排版 class，缺少独立产品概念；编辑能力由后端 patch 与统计行交互测试间接覆盖。

### frontend/tests/useLemmaOverrides.spec.ts

- test: frontend/tests/useLemmaOverrides.spec.ts::normalizes and validates lemma input
  status: keep
  covers: AC-TOK-005-01
- test: frontend/tests/useLemmaOverrides.spec.ts::resolves current-sentence overrides without persistence
  status: keep
  covers: AC-TOK-005-02
- test: frontend/tests/useLemmaOverrides.spec.ts::supports chained row edits from the progress modal
  status: keep
  covers: AC-TOK-005-02, AC-LOOP-003-03

### frontend/tests/useSettings.spec.ts

- test: frontend/tests/useSettings.spec.ts::exportAll excludes provider.apiKey
  status: keep
  covers: AC-SET-002-01
- test: frontend/tests/useSettings.spec.ts::exportAll omits namespace when only apiKey present
  status: keep
  covers: AC-SET-002-01
- test: frontend/tests/useSettings.spec.ts::importAll merges settings and skips apiKey
  status: keep
  covers: AC-SET-002-02
- test: frontend/tests/useSettings.spec.ts::importAll skips non-string values
  status: keep
  covers: AC-SET-002-02
- test: frontend/tests/useSettings.spec.ts::importAll skips non-object namespaces
  status: keep
  covers: AC-SET-002-02
- test: frontend/tests/useSettings.spec.ts::importAll handles empty object without error
  status: keep
  covers: AC-SET-002-02
