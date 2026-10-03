<template>
	<view v-if="question && store.run" class="page-shell">
		<AppHeader :title="`第 ${store.currentIndex + 1} 题`">
			<template #action
				><button
					class="exit-button"
					aria-label="退出答题"
					@click="exitDialogOpen = true"
				>
					×
				</button></template
			>
		</AppHeader>
		<view class="page-body">
			<view class="quiz-progress">
				<view
					class="progress"
					role="progressbar"
					:aria-valuenow="store.currentIndex + 1"
					:aria-valuemax="store.run.quiz.questions.length"
					><view class="progress__value" :style="progressStyle"
				/></view>
				<text class="quiz-progress__count"
					>{{ store.currentIndex + 1 }} /
					{{ store.run.quiz.questions.length }}</text
				>
			</view>

			<text class="question-type"
				>{{ question.type === "single_choice" ? "单选" : "判断" }} ·
				{{ knowledgePointName }}</text
			>
			<text class="question">{{ question.stem }}</text>
			<text class="question-source"
				>▣ 依据：{{ sourceLabel }} · 确定答案后可看摘录</text
			>

			<view class="choice-list" role="group" aria-label="答案选项">
				<button
					v-for="option in question.options"
					:key="option.id"
					class="choice"
					:class="choiceClass(option.id)"
					:aria-pressed="selectedAnswer === option.id"
					:disabled="revealed"
					@click="selectAnswer(option.id)"
				>
					<text class="choice__key">{{ option.id }}</text>
					<text class="choice__text">{{ option.text }}</text>
					<text class="choice__mark">{{
						optionMark(option.id)
					}}</text>
				</button>
			</view>

			<view v-if="!revealed" class="confidence">
				<text class="confidence__label">这题你有多确定？（可选）</text>
				<view
					class="confidence__choices"
					role="group"
					aria-label="答题信心"
				>
					<button
						v-for="item in confidenceOptions"
						:key="item.value"
						class="confidence-button"
						:class="{
							'confidence-button--selected':
								confidence === item.value,
						}"
						:aria-pressed="confidence === item.value"
						@click="confidence = item.value"
					>
						{{ item.label }}
					</button>
				</view>
			</view>

			<AppButton
				v-if="!revealed"
				class="mt-16"
				variant="primary"
				full
				:disabled="!selectedAnswer"
				@press="confirmAnswer"
				>确定答案</AppButton
			>

			<view v-else class="answer-feedback">
				<view
					class="result-callout"
					:class="{ 'result-callout--error': !isCorrect }"
				>
					<text class="result-callout__title">{{
						isCorrect ? "答对了，依据也对得上" : "这题需要再看一眼"
					}}</text>
					<text class="result-callout__copy">{{
						question.explanation
					}}</text>
				</view>
				<view class="stamp-wrap"
					><text class="stamp">有依据才放行</text></view
				>
				<SourceEvidence
					v-for="reference in question.source_refs"
					:key="`${reference.source_id}-${reference.location}`"
					:reference="reference"
					:source="sourceById(reference.source_id)"
				/>
				<AppButton
					class="mt-16"
					variant="primary"
					full
					:busy="store.isSubmitting"
					@press="next"
				>
					{{ isLastQuestion ? "查看本次报告 →" : "下一题 →" }}
				</AppButton>
			</view>
		</view>

		<AppDialog
			:open="exitDialogOpen"
			title="先退出本次答题？"
			@close="exitDialogOpen = false"
		>
			<text
				>已确定的答案会在本机保留 24 小时。临时会话 60
				分钟后过期，届时需要重新生成题目。</text
			>
			<template #actions>
				<AppButton
					variant="primary"
					full
					@press="exitDialogOpen = false"
					>继续答题</AppButton
				>
				<AppButton variant="ghost" full @press="exitToInput"
					>保存并退出</AppButton
				>
			</template>
		</AppDialog>
	</view>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import AppButton from "@/components/AppButton.vue";
import AppDialog from "@/components/AppDialog.vue";
import AppHeader from "@/components/AppHeader.vue";
import SourceEvidence from "@/components/SourceEvidence.vue";
import { useQuizStore } from "@/stores/quiz";
import type { Confidence, SourceSummary } from "@/types/quiz";

const store = useQuizStore();
const selectedAnswer = ref("");
const confidence = ref<Confidence | null>(null);
const revealed = ref(false);
const questionStartedAt = ref(Date.now());
const exitDialogOpen = ref(false);
const confidenceOptions: { label: string; value: Confidence }[] = [
	{ label: "确定", value: "sure" },
	{ label: "犹豫", value: "unsure" },
	{ label: "猜的", value: "guessed" },
];

const question = computed(() => store.currentQuestion);
const isLastQuestion = computed(() =>
	Boolean(
		store.run && store.currentIndex === store.run.quiz.questions.length - 1,
	),
);
const isCorrect = computed(
	() =>
		question.value?.correct_answers.includes(selectedAnswer.value) ?? false,
);
const knowledgePointName = computed(
	() =>
		store.run?.quiz.knowledge_points.find(
			(item) => item.id === question.value?.knowledge_point_id,
		)?.name || "知识点",
);
const sourceLabel = computed(() => {
	const first = question.value?.source_refs[0];
	const source = first ? sourceById(first.source_id) : undefined;
	return source?.type === "USER_TEXT"
		? "用户原文"
		: source?.publisher || source?.title || "可靠资料";
});
const progressStyle = computed(() => ({
	width: `${((store.currentIndex + 1) / (store.run?.quiz.questions.length || 1)) * 100}%`,
}));

onMounted(() => {
	if (!store.run) {
		uni.reLaunch({ url: "/pages/index/index" });
		return;
	}
	hydrateCurrentAttempt();
});
watch(() => store.currentIndex, hydrateCurrentAttempt);

function hydrateCurrentAttempt() {
	const current = question.value;
	const attempt = current
		? store.attempts.find((item) => item.question_id === current.id)
		: undefined;
	selectedAnswer.value = attempt?.selected_answers[0] || "";
	confidence.value = attempt?.confidence || null;
	revealed.value = Boolean(attempt);
	questionStartedAt.value = Date.now();
}
function sourceById(sourceId: string): SourceSummary | undefined {
	return store.run?.meta.sources.find((item) => item.source_id === sourceId);
}
function selectAnswer(optionId: string) {
	if (!revealed.value) selectedAnswer.value = optionId;
}
function confirmAnswer() {
	if (!question.value || !selectedAnswer.value || revealed.value) return;
	store.recordAttempt({
		questionId: question.value.id,
		selectedAnswer: selectedAnswer.value,
		durationMs: Date.now() - questionStartedAt.value,
		confidence: confidence.value,
	});
	revealed.value = true;
}
function choiceClass(optionId: string): Record<string, boolean> {
	return {
		"choice--selected":
			selectedAnswer.value === optionId && !revealed.value,
		"choice--correct":
			revealed.value &&
			question.value?.correct_answers.includes(optionId) === true,
		"choice--wrong":
			revealed.value &&
			selectedAnswer.value === optionId &&
			!question.value?.correct_answers.includes(optionId),
	};
}
function optionMark(optionId: string): string {
	if (!revealed.value) return selectedAnswer.value === optionId ? "●" : "";
	if (question.value?.correct_answers.includes(optionId)) return "✓";
	return selectedAnswer.value === optionId ? "×" : "";
}
async function next() {
	if (!isLastQuestion.value) {
		store.moveToNextQuestion();
		uni.pageScrollTo({ scrollTop: 0, duration: 0 });
		return;
	}
	const success = await store.submit();
	uni.redirectTo({
		url: success ? "/pages/report/report" : "/pages/error/error",
	});
}
function exitToInput() {
	store.persistDraft();
	uni.reLaunch({ url: "/pages/index/index" });
}
</script>

<style scoped>
.exit-button {
	font-size: 42rpx !important;
}
.quiz-progress {
	display: flex;
	align-items: center;
	gap: 20rpx;
	margin-bottom: 28rpx;
}
.progress {
	flex: 1;
	height: 20rpx;
	overflow: hidden;
	border: 3rpx solid var(--ink);
	border-radius: 999px;
	background: white;
}
.progress__value {
	height: 100%;
	background: var(--blue);
	transition: width 180ms ease;
}
.quiz-progress__count {
	flex: none;
	font-size: 25rpx;
	font-weight: 900;
}
.question-type {
	display: inline-flex;
	padding: 7rpx 16rpx;
	border: 3rpx solid var(--blue);
	border-radius: 999px;
	color: var(--blue-dark);
	background: var(--surface-blue);
	font-size: 22rpx;
	font-weight: 900;
}
.question {
	display: block;
	margin: 24rpx 0 28rpx;
	font-family: var(--font-display);
	font-size: 40rpx;
	font-weight: 900;
	line-height: 1.5;
}
.question-source {
	display: block;
	margin-bottom: 24rpx;
	color: var(--muted);
	font-size: 22rpx;
}
.choice-list {
	display: grid;
	gap: 20rpx;
}
.choice {
	width: 100%;
	min-height: 128rpx;
	padding: 20rpx 24rpx;
	display: grid;
	grid-template-columns: 68rpx 1fr 40rpx;
	align-items: center;
	gap: 20rpx;
	border: 4rpx solid var(--line);
	border-radius: 26rpx;
	color: var(--ink);
	background: var(--surface);
	text-align: left;
}
.choice::after {
	border: 0;
}
.choice--selected {
	border-color: var(--blue);
	background: var(--surface-choice);
	box-shadow: 4rpx 4rpx 0 var(--ink);
}
.choice--correct {
	border-color: var(--green);
	background: var(--surface-green);
}
.choice--wrong {
	border-color: var(--red);
	background: var(--surface-red);
}
.choice[disabled] {
	opacity: 1;
}
.choice__key {
	width: 64rpx;
	height: 64rpx;
	display: grid;
	place-items: center;
	border: 3rpx solid currentColor;
	border-radius: 50%;
	font-weight: 900;
}
.choice__text {
	font-size: 28rpx;
	line-height: 1.5;
}
.choice__mark {
	font-size: 30rpx;
	font-weight: 900;
}
.confidence {
	margin-top: 28rpx;
	padding-top: 24rpx;
	border-top: 2rpx dashed var(--line);
}
.confidence__label {
	display: block;
	margin-bottom: 14rpx;
	color: var(--muted);
	font-size: 24rpx;
}
.confidence__choices {
	display: grid;
	grid-template-columns: repeat(3, 1fr);
	gap: 14rpx;
}
.confidence-button {
	min-height: 80rpx;
	border: 3rpx solid var(--line);
	border-radius: 20rpx;
	color: var(--ink);
	background: var(--surface);
	font-size: 24rpx;
	font-weight: 800;
}
.confidence-button::after {
	border: 0;
}
.confidence-button--selected {
	border-color: var(--blue);
	color: var(--blue-dark);
	background: var(--surface-blue);
}
.answer-feedback {
	margin-top: 28rpx;
}
.stamp-wrap {
	margin: 30rpx 0 10rpx;
	text-align: center;
}
.stamp {
	display: inline-grid;
	min-width: 216rpx;
	min-height: 88rpx;
	padding: 12rpx 24rpx;
	place-items: center;
	transform: rotate(-4deg);
	border: 6rpx double var(--red);
	border-radius: 50%;
	color: var(--red);
	font-family: var(--font-note);
	font-size: 28rpx;
	font-weight: 900;
}
</style>
