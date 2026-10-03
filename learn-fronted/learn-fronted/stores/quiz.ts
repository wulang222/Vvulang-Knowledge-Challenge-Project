import { defineStore } from "pinia";

import {
	abortActiveRequest,
	createQuizRun,
	getQuizRun,
	submitQuizRun,
} from "@/services/api";
import { toUiFailure, type UiFailure } from "@/services/errors";
import { clearDraft, loadDraft, saveDraft } from "@/services/storage";
import type {
	Attempt,
	Confidence,
	LearningReport,
	QuizConfig,
	QuizResult,
	QuizRun,
} from "@/types/quiz";

interface PersistedQuizState {
	inputText: string;
	config: QuizConfig;
	run: QuizRun | null;
	attempts: Attempt[];
	currentIndex: number;
	result: QuizResult | null;
	report: LearningReport | null;
}

interface QuizState extends PersistedQuizState {
	isGenerating: boolean;
	isSubmitting: boolean;
	restoredAt: number | null;
	error: UiFailure | null;
}

export const DEFAULT_CONFIG: QuizConfig = {
	question_count: 5,
	difficulty: "basic",
	question_types: ["single_choice", "true_false"],
	source_policy: "AUTO",
	language: "zh-CN",
};

function initialState(): QuizState {
	return {
		inputText: "",
		config: {
			...DEFAULT_CONFIG,
			question_types: [...DEFAULT_CONFIG.question_types],
		},
		run: null,
		attempts: [],
		currentIndex: 0,
		result: null,
		report: null,
		isGenerating: false,
		isSubmitting: false,
		restoredAt: null,
		error: null,
	};
}

export const useQuizStore = defineStore("quiz", {
	state: initialState,
	getters: {
		hasRestoredDraft: (state): boolean =>
			state.restoredAt !== null && state.inputText.length > 0,
		currentQuestion: (state) =>
			state.run?.quiz.questions[state.currentIndex] ?? null,
		isRunComplete: (state): boolean =>
			Boolean(
				state.run &&
				state.attempts.length === state.run.quiz.questions.length,
			),
	},
	actions: {
		setInput(text: string) {
			this.inputText = text;
			this.error = null;
		},
		setQuestionCount(count: 5 | 10) {
			this.config.question_count = count;
			this.persistDraft();
		},
		setDifficulty(difficulty: QuizConfig["difficulty"]) {
			this.config.difficulty = difficulty;
			this.persistDraft();
		},
		toggleQuestionType(type: QuizConfig["question_types"][number]) {
			const selected = this.config.question_types.includes(type);
			if (selected && this.config.question_types.length === 1) return;
			this.config.question_types = selected
				? this.config.question_types.filter((item) => item !== type)
				: [...this.config.question_types, type];
			this.persistDraft();
		},
		prepareNewRun(): boolean {
			this.inputText = this.inputText.trim();
			if (!this.inputText) {
				this.error = {
					code: "EMPTY_INPUT",
					title: "先写点想学的内容",
					message: "输入一个问题、主题或学习资料后再开始。",
					icon: "✎",
					retryable: false,
				};
				return false;
			}
			this.run = null;
			this.attempts = [];
			this.currentIndex = 0;
			this.result = null;
			this.report = null;
			this.error = null;
			this.persistDraft();
			return true;
		},
		async generate(): Promise<boolean> {
			if (this.isGenerating) return false;
			this.isGenerating = true;
			this.error = null;
			try {
				this.run = await createQuizRun(this.inputText, this.config);
				this.currentIndex = 0;
				this.attempts = [];
				this.persistDraft();
				return true;
			} catch (error) {
				this.error = toUiFailure(error);
				this.persistDraft();
				return false;
			} finally {
				this.isGenerating = false;
			}
		},
		async refreshRun(): Promise<boolean> {
			if (!this.run?.run_id) return false;
			try {
				this.run = await getQuizRun(this.run.run_id);
				this.persistDraft();
				return true;
			} catch (error) {
				this.error = toUiFailure(error);
				return false;
			}
		},
		recordAttempt(input: {
			questionId: string;
			selectedAnswer: string;
			durationMs: number;
			confidence: Confidence | null;
		}) {
			const attempt: Attempt = {
				question_id: input.questionId,
				selected_answers: [input.selectedAnswer],
				duration_ms: Math.max(
					0,
					Math.min(input.durationMs, 86_400_000),
				),
				confidence: input.confidence,
			};
			const existing = this.attempts.findIndex(
				(item) => item.question_id === input.questionId,
			);
			if (existing >= 0) this.attempts.splice(existing, 1, attempt);
			else this.attempts.push(attempt);
			this.persistDraft();
		},
		moveToNextQuestion(): boolean {
			if (
				!this.run ||
				this.currentIndex >= this.run.quiz.questions.length - 1
			)
				return false;
			this.currentIndex += 1;
			this.persistDraft();
			return true;
		},
		async submit(): Promise<boolean> {
			if (!this.run || this.isSubmitting || !this.isRunComplete)
				return false;
			this.isSubmitting = true;
			this.error = null;
			try {
				const response = await submitQuizRun(
					this.run.run_id,
					this.attempts,
				);
				this.result = response.result;
				this.report = response.report;
				this.run.status = "COMPLETED";
				this.run.result = response.result;
				this.run.report = response.report;
				this.persistDraft();
				return true;
			} catch (error) {
				this.error = toUiFailure(error);
				this.persistDraft();
				return false;
			} finally {
				this.isSubmitting = false;
			}
		},
		cancelActiveRequest() {
			abortActiveRequest();
			this.isGenerating = false;
			this.isSubmitting = false;
		},
		persistDraft() {
			const payload: PersistedQuizState = {
				inputText: this.inputText,
				config: this.config,
				run: this.run,
				attempts: this.attempts,
				currentIndex: this.currentIndex,
				result: this.result,
				report: this.report,
			};
			saveDraft(payload);
		},
		restoreDraft(now = Date.now()): boolean {
			const draft = loadDraft<PersistedQuizState>(now);
			if (!draft) return false;
			this.$patch({
				...draft.payload,
				isGenerating: false,
				isSubmitting: false,
				restoredAt: draft.savedAt,
				error: null,
			});
			return true;
		},
		clearSession() {
			this.cancelActiveRequest();
			clearDraft();
			this.$reset();
		},
		clearRunForRegeneration() {
			this.run = null;
			this.attempts = [];
			this.currentIndex = 0;
			this.result = null;
			this.report = null;
			this.error = null;
			this.persistDraft();
		},
	},
});
