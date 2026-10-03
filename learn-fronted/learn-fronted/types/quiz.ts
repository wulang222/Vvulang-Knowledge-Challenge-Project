export type Difficulty = "basic" | "advanced";
export type QuestionType = "single_choice" | "true_false";
export type SourcePolicy = "AUTO" | "USER_ONLY" | "OFFICIAL_ALLOWED";
export type InputType = "QUESTION" | "USER_SOURCE" | "HYBRID";
export type RunStatus = "READY" | "COMPLETED";
export type Confidence = "sure" | "unsure" | "guessed";
export type MasteryStatus = "strong" | "developing" | "needs_review";

export interface QuizConfig {
	question_count: 5 | 10;
	difficulty: Difficulty;
	question_types: QuestionType[];
	source_policy: SourcePolicy;
	language: "zh-CN";
}

export interface SourceSummary {
	source_id: string;
	type: "USER_TEXT" | "OFFICIAL_WEB";
	title: string;
	publisher: string | null;
	url: string | null;
	retrieved_at: string | null;
	content_hash: string;
	trust_tier:
		"USER_PROVIDED" | "OFFICIAL_PRIMARY" | "AUTHORITATIVE_SECONDARY";
}

export interface KnowledgePoint {
	id: string;
	name: string;
	importance: number;
}

export interface QuestionOption {
	id: string;
	text: string;
}

export interface SourceReference {
	source_id: string;
	evidence_quote: string;
	location: string;
}

export interface Question {
	id: string;
	type: QuestionType;
	knowledge_point_id: string;
	stem: string;
	options: QuestionOption[];
	correct_answers: string[];
	explanation: string;
	difficulty: 1 | 2;
	source_refs: SourceReference[];
}

export interface Quiz {
	title: string;
	knowledge_points: KnowledgePoint[];
	questions: Question[];
}

export interface GenerationMeta {
	input_type: InputType;
	source_policy: Exclude<SourcePolicy, "AUTO">;
	sources: SourceSummary[];
	prompt_version: string;
	model_version: string;
	generated_at: string;
}

export interface QuizRun {
	request_id: string;
	run_id: string;
	status: RunStatus;
	quiz: Quiz;
	meta: GenerationMeta;
	created_at: string;
	expires_at: string;
	result?: QuizResult | null;
	report?: LearningReport | null;
}

export interface Attempt {
	question_id: string;
	selected_answers: string[];
	duration_ms: number;
	confidence: Confidence | null;
}

export interface QuestionResult {
	question_id: string;
	knowledge_point_id: string;
	selected_answers: string[];
	correct_answers: string[];
	is_correct: boolean;
	duration_ms: number;
}

export interface QuizResult {
	total: 5 | 10;
	correct: number;
	accuracy: number;
	duration_ms: number;
	question_results: QuestionResult[];
}

export interface MasteryItem {
	knowledge_point_id: string;
	status: MasteryStatus;
	correct: number;
	total: number;
	evidence: string;
}

export interface LearningReport {
	summary: string;
	error_patterns: string[];
	next_actions: string[];
	mastery: MasteryItem[];
	generated_by: "ai" | "deterministic_fallback";
}

export interface SubmitResponse {
	request_id: string;
	run_id: string;
	status: "COMPLETED";
	result: QuizResult;
	report: LearningReport;
	completed_at: string;
}

export interface ApiErrorEnvelope {
	request_id?: string;
	error?: {
		code?: string;
		message?: string;
		retryable?: boolean;
		details?: Record<string, unknown> | null;
	};
}
