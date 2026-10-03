import { beforeEach, describe, expect, it, vi } from "vitest";

import {
	abortActiveRequest,
	createQuizRun,
	getQuizRun,
	QuizApiError,
	submitQuizRun,
} from "./api";
import type { QuizConfig } from "@/types/quiz";

const config: QuizConfig = {
	question_count: 5,
	difficulty: "basic",
	question_types: ["single_choice", "true_false"],
	source_policy: "AUTO",
	language: "zh-CN",
};

beforeEach(() => vi.unstubAllGlobals());

function installRequestMock(
	callback: (options: UniApp.RequestOptions) => void,
) {
	const task = { abort: vi.fn() };
	const request = vi.fn((options: UniApp.RequestOptions) => {
		queueMicrotask(() => callback(options));
		return task;
	});
	vi.stubGlobal("uni", { request });
	return { request, task };
}

describe("quiz API", () => {
	it("posts the untruncated input and frozen config", async () => {
		const { request } = installRequestMock((options) => {
			options.success?.({
				statusCode: 201,
				data: { run_id: "run_1" },
				header: {},
				cookies: [],
			});
			options.complete?.({ errMsg: "request:ok" });
		});
		const text = "资料".repeat(20_000);

		await expect(createQuizRun(text, config)).resolves.toMatchObject({
			run_id: "run_1",
		});
		expect(request).toHaveBeenCalledWith(
			expect.objectContaining({
				method: "POST",
				data: expect.objectContaining({
					learning_input: { text, declared_type: "AUTO" },
				}),
			}),
		);
	});

	it("preserves the backend error code and request id", async () => {
		installRequestMock((options) => {
			options.success?.({
				statusCode: 422,
				data: {
					request_id: "req_9",
					error: {
						code: "RELIABLE_SOURCE_NOT_FOUND",
						message: "没有来源",
						retryable: false,
					},
				},
				header: {},
				cookies: [],
			});
		});

		const error = await createQuizRun("主题", config).catch(
			(value: unknown) => value,
		);
		expect(error).toBeInstanceOf(QuizApiError);
		expect(error).toMatchObject({
			code: "RELIABLE_SOURCE_NOT_FOUND",
			requestId: "req_9",
		});
	});

	it("distinguishes timeout and supports cancellation", async () => {
		const { task } = installRequestMock((options) => {
			options.fail?.({ errMsg: "request:fail timeout" });
		});
		const pending = createQuizRun("主题", config);
		abortActiveRequest();

		expect(task.abort).toHaveBeenCalledOnce();
		await expect(pending).rejects.toMatchObject({
			code: "AI_TIMEOUT",
			retryable: true,
		});
	});

	it("gets a run and submits attempts through their contract paths", async () => {
		const { request } = installRequestMock((options) => {
			options.success?.({
				statusCode: 200,
				data: { run_id: "run_1" },
				header: {},
				cookies: [],
			});
		});

		await getQuizRun("run_1");
		await submitQuizRun("run_1", [
			{
				question_id: "q_1",
				selected_answers: ["A"],
				duration_ms: 30,
				confidence: null,
			},
		]);

		expect(request.mock.calls[0][0].url).toContain(
			"/api/v1/quiz-runs/run_1",
		);
		expect(request.mock.calls[1][0]).toEqual(
			expect.objectContaining({
				method: "POST",
				data: { attempts: expect.any(Array) },
			}),
		);
	});

	it("maps ordinary network failures separately from timeouts", async () => {
		installRequestMock((options) =>
			options.fail?.({ errMsg: "request:fail disconnected" }),
		);

		await expect(getQuizRun("run_1")).rejects.toMatchObject({
			code: "NETWORK_ERROR",
			retryable: true,
		});
	});
});
