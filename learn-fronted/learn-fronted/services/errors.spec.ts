import { describe, expect, it } from "vitest";

import { QuizApiError } from "./api";
import { toUiFailure } from "./errors";

describe("error copy", () => {
	it.each([
		"EMPTY_INPUT",
		"SENSITIVE_INFORMATION",
		"CONTENT_NOT_ALLOWED",
		"RELIABLE_SOURCE_NOT_FOUND",
		"SOURCE_FETCH_FAILED",
		"AI_TIMEOUT",
		"RATE_LIMITED",
		"AI_OUTPUT_INVALID",
		"RUN_EXPIRED",
		"NETWORK_ERROR",
	])("maps %s to actionable Chinese copy", (code) => {
		const failure = toUiFailure(
			new QuizApiError(code, "raw backend text", true, "req_1"),
		);

		expect(failure.code).toBe(code);
		expect(failure.title.length).toBeGreaterThan(3);
		expect(failure.message).not.toContain("raw backend text");
		expect(failure.requestId).toBe("req_1");
	});

	it("sanitizes unknown exceptions", () => {
		expect(toUiFailure(new Error("secret stack"))).toMatchObject({
			code: "INTERNAL_ERROR",
			retryable: true,
		});
	});
});
