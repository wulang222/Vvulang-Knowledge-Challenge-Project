import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";

const api = vi.hoisted(() => ({
	abortActiveRequest: vi.fn(),
	createQuizRun: vi.fn(),
	getQuizRun: vi.fn(),
	submitQuizRun: vi.fn(),
}));

vi.mock("@/services/api", async (importOriginal) => ({
	...(await importOriginal<typeof import("@/services/api")>()),
	...api,
}));

import { useQuizStore } from "./quiz";
import type { QuizRun, SubmitResponse } from "@/types/quiz";

const values = new Map<string, unknown>();

const run: QuizRun = {
	request_id: "req_1",
	run_id: "run_1",
	status: "READY",
	created_at: "2026-10-03T00:00:00Z",
	expires_at: "2026-10-03T01:00:00Z",
	meta: {
		input_type: "QUESTION",
		source_policy: "OFFICIAL_ALLOWED",
		sources: [
			{
				source_id: "src_1",
				type: "OFFICIAL_WEB",
				title: "官方资料",
				publisher: "官方",
				url: "https://example.com",
				retrieved_at: "2026-10-03T00:00:00Z",
				content_hash: "abc",
				trust_tier: "OFFICIAL_PRIMARY",
			},
		],
		prompt_version: "v1",
		model_version: "qwen",
		generated_at: "2026-10-03T00:00:00Z",
	},
	quiz: {
		title: "RAG",
		knowledge_points: [{ id: "kp_1", name: "定义", importance: 3 }],
		questions: [
			{
				id: "q_1",
				type: "true_false",
				knowledge_point_id: "kp_1",
				stem: "RAG 会先检索资料。",
				options: [
					{ id: "T", text: "正确" },
					{ id: "F", text: "错误" },
				],
				correct_answers: ["T"],
				explanation: "先检索再生成。",
				difficulty: 1,
				source_refs: [
					{
						source_id: "src_1",
						evidence_quote: "先检索",
						location: "正文",
					},
				],
			},
		],
	},
};

const completed: SubmitResponse = {
	request_id: "req_2",
	run_id: "run_1",
	status: "COMPLETED",
	completed_at: "2026-10-03T00:05:00Z",
	result: {
		total: 5,
		correct: 1,
		accuracy: 0.2,
		duration_ms: 1000,
		question_results: [
			{
				question_id: "q_1",
				knowledge_point_id: "kp_1",
				selected_answers: ["T"],
				correct_answers: ["T"],
				is_correct: true,
				duration_ms: 1000,
			},
		],
	},
	report: {
		summary: "本次完成。",
		error_patterns: [],
		next_actions: ["继续练习"],
		mastery: [
			{
				knowledge_point_id: "kp_1",
				status: "strong",
				correct: 1,
				total: 1,
				evidence: "答对 1 题",
			},
		],
		generated_by: "ai",
	},
};

beforeEach(() => {
	values.clear();
	vi.clearAllMocks();
	setActivePinia(createPinia());
	vi.stubGlobal("uni", {
		setStorageSync: (key: string, value: unknown) => values.set(key, value),
		getStorageSync: (key: string) => values.get(key) ?? "",
		removeStorageSync: (key: string) => values.delete(key),
	});
});

describe("quiz store", () => {
	it("only blocks blank input and preserves long input", () => {
		const store = useQuizStore();
		expect(store.prepareNewRun()).toBe(false);
		expect(store.error?.code).toBe("EMPTY_INPUT");

		store.setInput(`RAG 是什么？${"原文".repeat(30_000)}`);
		expect(store.prepareNewRun()).toBe(true);
		expect(store.inputText.length).toBeGreaterThan(60_000);
	});

	it("never lets the user deselect every question type", () => {
		const store = useQuizStore();
		store.setQuestionCount(10);
		store.setDifficulty("advanced");
		store.toggleQuestionType("single_choice");
		store.toggleQuestionType("true_false");

		expect(store.config.question_types).toEqual(["true_false"]);
		expect(store.config.question_count).toBe(10);
		expect(store.config.difficulty).toBe("advanced");
		store.toggleQuestionType("single_choice");
		expect(store.config.question_types).toContain("single_choice");
	});

	it("generates, locks an attempt, and submits the complete run", async () => {
		api.createQuizRun.mockResolvedValue(run);
		api.submitQuizRun.mockResolvedValue(completed);
		const store = useQuizStore();
		store.setInput("RAG 是什么？");

		await expect(store.generate()).resolves.toBe(true);
		store.recordAttempt({
			questionId: "q_1",
			selectedAnswer: "T",
			durationMs: 1000,
			confidence: "sure",
		});
		expect(store.isRunComplete).toBe(true);
		await expect(store.submit()).resolves.toBe(true);
		expect(store.result?.correct).toBe(1);
		expect(store.report?.mastery[0].status).toBe("strong");
	});

	it("keeps recoverable errors and restores a saved draft", async () => {
		api.createQuizRun.mockRejectedValue(new Error("offline"));
		const store = useQuizStore();
		store.setInput("主题");
		await expect(store.generate()).resolves.toBe(false);
		expect(store.error?.code).toBe("INTERNAL_ERROR");
		store.persistDraft();

		setActivePinia(createPinia());
		const restored = useQuizStore();
		expect(restored.restoreDraft()).toBe(true);
		expect(restored.inputText).toBe("主题");
	});

	it("refreshes a run and maps refresh failures", async () => {
		const store = useQuizStore();
		expect(await store.refreshRun()).toBe(false);
		store.run = structuredClone(run);
		api.getQuizRun.mockResolvedValue({ ...run, status: "COMPLETED" });
		expect(await store.refreshRun()).toBe(true);
		expect(store.run.status).toBe("COMPLETED");

		api.getQuizRun.mockRejectedValue(new Error("offline"));
		expect(await store.refreshRun()).toBe(false);
		expect(store.error?.code).toBe("INTERNAL_ERROR");
	});

	it("replaces repeated answers, clamps duration, and advances within bounds", () => {
		const store = useQuizStore();
		const twoQuestionRun = structuredClone(run);
		twoQuestionRun.quiz.questions.push({
			...structuredClone(run.quiz.questions[0]),
			id: "q_2",
		});
		store.run = twoQuestionRun;
		store.recordAttempt({
			questionId: "q_1",
			selectedAnswer: "F",
			durationMs: -10,
			confidence: null,
		});
		store.recordAttempt({
			questionId: "q_1",
			selectedAnswer: "T",
			durationMs: 100_000_000,
			confidence: "sure",
		});

		expect(store.attempts).toHaveLength(1);
		expect(store.attempts[0].duration_ms).toBe(86_400_000);
		expect(store.moveToNextQuestion()).toBe(true);
		expect(store.moveToNextQuestion()).toBe(false);
	});

	it("guards duplicate work and preserves a failed submission", async () => {
		const store = useQuizStore();
		expect(await store.submit()).toBe(false);
		store.isGenerating = true;
		expect(await store.generate()).toBe(false);
		store.isGenerating = false;
		store.run = structuredClone(run);
		store.recordAttempt({
			questionId: "q_1",
			selectedAnswer: "T",
			durationMs: 10,
			confidence: null,
		});
		api.submitQuizRun.mockRejectedValue(new Error("offline"));

		expect(await store.submit()).toBe(false);
		expect(store.attempts).toHaveLength(1);
		expect(store.error?.code).toBe("INTERNAL_ERROR");
	});

	it("clears or prepares session state without leaving active work", () => {
		const store = useQuizStore();
		expect(store.restoreDraft()).toBe(false);
		store.run = structuredClone(run);
		store.attempts = [
			{
				question_id: "q_1",
				selected_answers: ["T"],
				duration_ms: 10,
				confidence: null,
			},
		];
		store.clearRunForRegeneration();
		expect(store.run).toBeNull();
		expect(store.attempts).toEqual([]);

		store.isGenerating = true;
		store.clearSession();
		expect(api.abortActiveRequest).toHaveBeenCalled();
		expect(store.isGenerating).toBe(false);
		expect(store.inputText).toBe("");
	});
});
