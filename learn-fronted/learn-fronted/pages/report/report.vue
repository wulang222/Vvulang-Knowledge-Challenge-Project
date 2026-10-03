<template>
	<view v-if="store.result && store.report && store.run" class="page-shell">
		<AppHeader title="本次通关报告" />
		<view class="page-body">
			<view class="score-hero"
				><text class="score-hero__number"
					>{{ store.result.correct
					}}<text class="score-hero__total"
						>/{{ store.result.total }}</text
					></text
				><text class="score-hero__label">{{
					store.report.summary
				}}</text></view
			>
			<view class="score-stats">
				<view class="stat"
					><text class="stat__value"
						>{{ Math.round(store.result.accuracy * 100) }}%</text
					><text class="stat__label">正确率</text></view
				>
				<view class="stat"
					><text class="stat__value">{{
						formatDuration(store.result.duration_ms)
					}}</text
					><text class="stat__label">总用时</text></view
				>
				<view class="stat"
					><text class="stat__value">{{ weakCount }}</text
					><text class="stat__label">待复习</text></view
				>
			</view>

			<view class="section-title"><text>知识点表现</text></view>
			<view
				v-for="item in store.report.mastery"
				:key="item.knowledge_point_id"
				class="card mastery-card"
				:class="masteryCardClass(item.status)"
			>
				<view class="mastery-card__top"
					><text class="mastery-card__name">{{
						knowledgePointName(item.knowledge_point_id)
					}}</text
					><text
						class="status-pill"
						:class="masteryPillClass(item.status)"
						>{{ masteryLabel(item.status) }}</text
					></view
				>
				<view class="mastery-progress"
					><view
						class="mastery-progress__value"
						:style="{
							width: `${(item.correct / item.total) * 100}%`,
						}"
				/></view>
				<text class="mastery-card__evidence">{{ item.evidence }}</text>
			</view>

			<view
				v-if="store.report.error_patterns.length"
				class="section-title"
				><text>这次容易卡在</text></view
			>
			<view v-if="store.report.error_patterns.length" class="chip-list"
				><text
					v-for="pattern in store.report.error_patterns"
					:key="pattern"
					class="report-chip"
					>{{ pattern }}</text
				></view
			>

			<view class="section-title"><text>下一步复习单</text></view>
			<view class="timeline"
				><view
					v-for="(action, index) in store.report.next_actions"
					:key="action"
					class="timeline__item"
					><text class="timeline__dot">{{ index + 1 }}</text
					><text class="timeline__copy">{{ action }}</text></view
				></view
			>

			<view
				v-if="store.report.generated_by === 'deterministic_fallback'"
				class="paper-note mt-16"
				>AI
				反馈暂时不可用；分数和统计仍由程序按作答记录计算，结果可信。</view
			>
			<AppButton class="mt-16" variant="primary" full @press="regenerate"
				>按原设置再出一组 →</AppButton
			>
			<AppButton class="mt-12" variant="ghost" full @press="backToInput"
				>修改输入</AppButton
			>
			<text class="footnote"
				>“掌握”只描述本次表现，不代表长期记忆已经形成。</text
			>
		</view>
	</view>
</template>

<script setup lang="ts">
import { computed, onMounted } from "vue";
import AppButton from "@/components/AppButton.vue";
import AppHeader from "@/components/AppHeader.vue";
import { useQuizStore } from "@/stores/quiz";
import type { MasteryStatus } from "@/types/quiz";

const store = useQuizStore();
const weakCount = computed(
	() =>
		store.report?.mastery.filter((item) => item.status !== "strong")
			.length || 0,
);
onMounted(() => {
	if (!store.result || !store.report)
		uni.reLaunch({ url: "/pages/index/index" });
});
function formatDuration(milliseconds: number): string {
	const total = Math.floor(milliseconds / 1000);
	return `${String(Math.floor(total / 60)).padStart(2, "0")}:${String(total % 60).padStart(2, "0")}`;
}
function knowledgePointName(id: string): string {
	return (
		store.run?.quiz.knowledge_points.find((item) => item.id === id)?.name ||
		id
	);
}
function masteryLabel(status: MasteryStatus): string {
	return {
		strong: "本次稳住",
		developing: "继续巩固",
		needs_review: "需要复习",
	}[status];
}
function masteryCardClass(status: MasteryStatus): string {
	return status === "strong"
		? "card--green"
		: status === "developing"
			? "card--yellow"
			: "card--red";
}
function masteryPillClass(status: MasteryStatus): string {
	return status === "strong"
		? "status-pill--success"
		: status === "developing"
			? "status-pill--warning"
			: "status-pill--danger";
}
function regenerate() {
	store.clearRunForRegeneration();
	uni.redirectTo({ url: "/pages/generate/generate" });
}
function backToInput() {
	store.clearRunForRegeneration();
	uni.reLaunch({ url: "/pages/index/index" });
}
</script>

<style scoped>
.score-hero {
	padding: 36rpx;
	border: 4rpx solid var(--ink);
	border-radius: 36rpx;
	background: var(--yellow);
	box-shadow: 8rpx 8rpx 0 var(--ink);
	text-align: center;
}
.score-hero__number {
	display: block;
	font-family: var(--font-display);
	font-size: 116rpx;
	font-weight: 900;
	line-height: 1;
}
.score-hero__total {
	font-size: 48rpx;
}
.score-hero__label {
	display: block;
	margin-top: 16rpx;
	font-size: 26rpx;
	font-weight: 800;
}
.score-stats {
	display: grid;
	grid-template-columns: repeat(3, minmax(0, 1fr));
	gap: 16rpx;
	margin-top: 28rpx;
}
.stat {
	min-width: 0;
	box-sizing: border-box;
	padding: 20rpx 10rpx;
	border: 3rpx solid var(--line);
	border-radius: 20rpx;
	background: var(--surface);
	text-align: center;
}
.stat__value {
	display: block;
	font-family: var(--font-display);
	font-size: 38rpx;
	font-weight: 900;
	overflow-wrap: anywhere;
}
.stat__label {
	color: var(--muted);
	font-size: 20rpx;
}
.mastery-card {
	margin-top: 18rpx;
}
.mastery-card__top {
	margin-bottom: 14rpx;
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 16rpx;
}
.mastery-card__name {
	min-width: 0;
	font-weight: 900;
	overflow-wrap: anywhere;
}
.mastery-progress {
	height: 18rpx;
	overflow: hidden;
	border: 3rpx solid var(--ink);
	border-radius: 999px;
	background: var(--on-primary);
}
.mastery-progress__value {
	height: 100%;
	background: var(--blue);
}
.mastery-card__evidence {
	display: block;
	margin-top: 12rpx;
	color: var(--muted);
	font-size: 23rpx;
}
.chip-list {
	display: flex;
	flex-wrap: wrap;
	gap: 12rpx;
}
.report-chip {
	padding: 10rpx 18rpx;
	border: 3rpx solid var(--red);
	border-radius: 999px;
	color: var(--red-dark);
	background: var(--surface-red);
	font-size: 23rpx;
	font-weight: 800;
}
.timeline__item {
	position: relative;
	min-height: 88rpx;
	padding: 6rpx 0 22rpx 72rpx;
}
.timeline__item:not(:last-child)::after {
	content: "";
	position: absolute;
	left: 28rpx;
	top: 58rpx;
	bottom: -6rpx;
	border-left: 3rpx dashed var(--line);
}
.timeline__dot {
	position: absolute;
	left: 0;
	top: 0;
	width: 58rpx;
	height: 58rpx;
	display: grid;
	place-items: center;
	border: 3rpx solid var(--ink);
	border-radius: 50%;
	background: var(--yellow);
	font-weight: 900;
}
.timeline__copy {
	display: block;
	min-width: 0;
	font-weight: 800;
	overflow-wrap: anywhere;
}
.footnote {
	display: block;
	margin-top: 20rpx;
	color: var(--muted);
	font-size: 21rpx;
	text-align: center;
}
</style>
