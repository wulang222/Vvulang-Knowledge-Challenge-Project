import type {
	ApiErrorEnvelope,
	Attempt,
	QuizConfig,
	QuizRun,
	SubmitResponse,
} from "@/types/quiz";

const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim();
export const API_BASE_URL = (
	configuredBaseUrl || "http://127.0.0.1:8000"
).replace(/\/$/, "");

export class QuizApiError extends Error {
	constructor(
		public readonly code: string,
		message: string,
		public readonly retryable: boolean,
		public readonly requestId?: string,
		public readonly statusCode?: number,
	) {
		super(message);
		this.name = "QuizApiError";
	}
}

let activeRequest: ReturnType<typeof uni.request> | null = null;

function asErrorEnvelope(value: unknown): ApiErrorEnvelope {
	return value && typeof value === "object"
		? (value as ApiErrorEnvelope)
		: {};
}

function request<T>(options: {
	path: string;
	method: "GET" | "POST";
	data?: UniApp.RequestOptions["data"];
	timeout?: number;
}): Promise<T> {
	return new Promise<T>((resolve, reject) => {
		const task = uni.request({
			url: `${API_BASE_URL}${options.path}`,
			method: options.method,
			data: options.data,
			timeout: options.timeout ?? 20_000,
			header: { "Content-Type": "application/json" },
			success(response) {
				if (response.statusCode >= 200 && response.statusCode < 300) {
					resolve(response.data as T);
					return;
				}
				const envelope = asErrorEnvelope(response.data);
				reject(
					new QuizApiError(
						envelope.error?.code || "INTERNAL_ERROR",
						envelope.error?.message || "服务暂时不可用，请稍后重试",
						Boolean(envelope.error?.retryable),
						envelope.request_id,
						response.statusCode,
					),
				);
			},
			fail(error) {
				const timedOut = error.errMsg.toLowerCase().includes("timeout");
				reject(
					new QuizApiError(
						timedOut ? "AI_TIMEOUT" : "NETWORK_ERROR",
						timedOut
							? "这次生成等太久了，请重试"
							: "网络连接失败，请检查网络后重试",
						true,
					),
				);
			},
			complete() {
				if (activeRequest === task) activeRequest = null;
			},
		});
		activeRequest = task;
	});
}

export function abortActiveRequest(): void {
	activeRequest?.abort();
	activeRequest = null;
}

export function createQuizRun(
	text: string,
	config: QuizConfig,
): Promise<QuizRun> {
	return request<QuizRun>({
		path: "/api/v1/quiz-runs",
		method: "POST",
		data: {
			learning_input: { text, declared_type: "AUTO" },
			config,
		},
		timeout: 90_000,
	});
}

export function getQuizRun(runId: string): Promise<QuizRun> {
	return request<QuizRun>({
		path: `/api/v1/quiz-runs/${runId}`,
		method: "GET",
	});
}

export function submitQuizRun(
	runId: string,
	attempts: Attempt[],
): Promise<SubmitResponse> {
	return request<SubmitResponse>({
		path: `/api/v1/quiz-runs/${runId}/submit`,
		method: "POST",
		data: { attempts },
		timeout: 90_000,
	});
}
