import { QuizApiError } from "@/services/api";

export interface UiFailure {
	code: string;
	title: string;
	message: string;
	icon: string;
	retryable: boolean;
	requestId?: string;
}

const ERROR_COPY: Record<
	string,
	Pick<UiFailure, "title" | "message" | "icon">
> = {
	EMPTY_INPUT: {
		title: "先写点想学的内容",
		message: "输入一个问题、主题或学习资料后再开始。",
		icon: "✎",
	},
	SENSITIVE_INFORMATION: {
		title: "检测到可能的敏感信息",
		message: "输入已保留。请删除密钥、密码、身份证号或未授权信息后再试。",
		icon: "!",
	},
	CONTENT_NOT_ALLOWED: {
		title: "这段内容暂时不能用于出题",
		message: "输入已保留。请改成正常的学习问题或学习资料。",
		icon: "!",
	},
	RELIABLE_SOURCE_NOT_FOUND: {
		title: "暂时找不到可核验的资料",
		message:
			"本次不会用模型常识凑题。换个更具体的问法，或粘贴你认可的原文。",
		icon: "⌖",
	},
	SOURCE_FETCH_FAILED: {
		title: "可靠来源暂时读不到",
		message: "你的输入和设置都已保留，可以稍后重试或直接补充原文。",
		icon: "⌁",
	},
	AI_TIMEOUT: {
		title: "这次生成等太久了",
		message: "你的输入和设置都已保留。可以重试，或减少到 5 题。",
		icon: "⌛",
	},
	RATE_LIMITED: {
		title: "现在请求有点多",
		message: "输入已保留，请稍后再试。",
		icon: "…",
	},
	AI_OUTPUT_INVALID: {
		title: "题目没有通过质量检查",
		message: "有题目缺少可靠证据，本次没有放行。请重新生成。",
		icon: "✗",
	},
	RUN_EXPIRED: {
		title: "临时会话已过期",
		message: "旧题目已清除，但本机仍保留输入与设置，可以重新生成。",
		icon: "▤",
	},
	NETWORK_ERROR: {
		title: "网络连接失败",
		message: "输入和作答已保存在本机。检查网络后重试，不需要重新填写。",
		icon: "⌁",
	},
};

export function toUiFailure(error: unknown): UiFailure {
	const apiError = error instanceof QuizApiError ? error : null;
	const code = apiError?.code || "INTERNAL_ERROR";
	const copy = ERROR_COPY[code] || {
		title: "服务暂时不可用",
		message: "数据已保留，请稍后重试。",
		icon: "!",
	};
	return {
		code,
		...copy,
		retryable: apiError?.retryable ?? true,
		requestId: apiError?.requestId,
	};
}
