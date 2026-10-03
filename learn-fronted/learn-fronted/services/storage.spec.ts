import { beforeEach, describe, expect, it, vi } from "vitest";

import {
	clearDraft,
	DRAFT_TTL_MS,
	isDraftFresh,
	loadDraft,
	saveDraft,
} from "./storage";

const values = new Map<string, unknown>();

beforeEach(() => {
	values.clear();
	vi.stubGlobal("uni", {
		setStorageSync: (key: string, value: unknown) => values.set(key, value),
		getStorageSync: (key: string) => values.get(key) ?? "",
		removeStorageSync: (key: string) => values.delete(key),
	});
});

describe("draft storage", () => {
	it("keeps arbitrary-length input for 24 hours", () => {
		const text = "学习资料".repeat(50_000);
		saveDraft({ text }, 1_000);

		expect(
			loadDraft<{ text: string }>(1_000 + DRAFT_TTL_MS - 1)?.payload.text,
		).toBe(text);
	});

	it("removes an expired draft", () => {
		saveDraft({ text: "RAG 是什么？" }, 1_000);

		expect(loadDraft(1_000 + DRAFT_TTL_MS)).toBeNull();
		expect(values.size).toBe(0);
	});

	it("handles malformed and unavailable storage", () => {
		values.set("ai-quiz:mvp-draft:v1", { savedAt: Number.NaN });
		expect(loadDraft()).toBeNull();
		expect(isDraftFresh(0)).toBe(false);

		vi.stubGlobal("uni", {
			getStorageSync: () => {
				throw new Error("blocked");
			},
			removeStorageSync: () => {
				throw new Error("blocked");
			},
		});
		expect(loadDraft()).toBeNull();
		expect(() => clearDraft()).not.toThrow();
	});
});
