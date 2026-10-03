const DRAFT_KEY = "ai-quiz:mvp-draft:v1";
export const DRAFT_TTL_MS = 24 * 60 * 60 * 1000;

export interface StoredDraft<T> {
	savedAt: number;
	payload: T;
}

export function isDraftFresh(savedAt: number, now = Date.now()): boolean {
	return (
		Number.isFinite(savedAt) && savedAt > 0 && now - savedAt < DRAFT_TTL_MS
	);
}

export function saveDraft<T>(payload: T, now = Date.now()): number {
	const draft: StoredDraft<T> = { savedAt: now, payload };
	uni.setStorageSync(DRAFT_KEY, draft);
	return now;
}

export function loadDraft<T>(now = Date.now()): StoredDraft<T> | null {
	try {
		const value = uni.getStorageSync(DRAFT_KEY) as StoredDraft<T> | "";
		if (
			!value ||
			typeof value !== "object" ||
			!isDraftFresh(value.savedAt, now)
		) {
			uni.removeStorageSync(DRAFT_KEY);
			return null;
		}
		return value;
	} catch {
		return null;
	}
}

export function clearDraft(): void {
	try {
		uni.removeStorageSync(DRAFT_KEY);
	} catch {
		// Storage can be unavailable in private/restricted environments.
	}
}
