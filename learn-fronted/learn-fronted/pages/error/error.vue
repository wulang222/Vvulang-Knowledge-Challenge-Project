<template>
	<view class="page-shell">
		<AppHeader title="出题暂停" back @back="editInput" />
		<view class="page-body">
			<view class="empty-state">
				<text class="empty-state__icon" aria-hidden="true">{{
					failure.icon
				}}</text>
				<text class="error-code">{{ failure.code }}</text>
				<text class="empty-state__title">{{ failure.title }}</text>
				<text class="empty-state__copy">{{ failure.message }}</text>
			</view>

			<view class="card card--blue">
				<text class="card-title">你的内容没有丢</text>
				<text class="recovery-copy"
					>✓ 问题、主题或原始学习文本<br />✓ 题量、难度和题型设置<br />✓
					已完成的本地作答</text
				>
			</view>
			<view
				v-if="failure.code === 'RELIABLE_SOURCE_NOT_FOUND'"
				class="card card--yellow mt-12"
			>
				<text class="card-title">下一步</text
				><text class="recovery-copy"
					>换一个更具体的问法，或粘贴你认可的原文；原文会优先作为依据。</text
				>
			</view>

			<AppButton
				v-if="failure.retryable || failure.code === 'RUN_EXPIRED'"
				class="mt-16"
				variant="primary"
				full
				:busy="retrying"
				@press="retry"
				>{{ retryLabel }}</AppButton
			>
			<AppButton
				v-if="
					store.config.question_count === 10 &&
					failure.code === 'AI_TIMEOUT'
				"
				class="mt-12"
				variant="ghost"
				full
				@press="retryWithFive"
				>减少到 5 题后重试</AppButton
			>
			<AppButton class="mt-12" variant="ghost" full @press="editInput"
				>返回修改输入</AppButton
			>
			<view v-if="failure.requestId" class="request-id"
				>request_id: {{ failure.requestId
				}}<br />反馈问题时请带上这串编号</view
			>
		</view>
	</view>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import AppButton from "@/components/AppButton.vue";
import AppHeader from "@/components/AppHeader.vue";
import { useQuizStore } from "@/stores/quiz";
import type { UiFailure } from "@/services/errors";

const store = useQuizStore();
const retrying = ref(false);
const fallback: UiFailure = {
	code: "INTERNAL_ERROR",
	title: "服务暂时不可用",
	message: "数据已保留，请稍后重试。",
	icon: "!",
	retryable: true,
};
const failure = computed(() => store.error || fallback);
const retryLabel = computed(() =>
	failure.value.code === "RUN_EXPIRED"
		? "用原设置重新生成 →"
		: store.isRunComplete
			? "重新提交作答"
			: "重试生成",
);

async function retry() {
	if (retrying.value) return;
	retrying.value = true;
	if (
		store.run &&
		store.isRunComplete &&
		failure.value.code !== "RUN_EXPIRED"
	) {
		const success = await store.submit();
		retrying.value = false;
		if (success) uni.redirectTo({ url: "/pages/report/report" });
		return;
	}
	store.clearRunForRegeneration();
	retrying.value = false;
	uni.redirectTo({ url: "/pages/generate/generate" });
}
function retryWithFive() {
	store.setQuestionCount(5);
	store.clearRunForRegeneration();
	uni.redirectTo({ url: "/pages/generate/generate" });
}
function editInput() {
	store.error = null;
	store.persistDraft();
	uni.reLaunch({ url: "/pages/index/index" });
}
</script>

<style scoped>
.empty-state {
	padding: 60rpx 24rpx;
	text-align: center;
}
.empty-state__icon {
	display: block;
	margin-bottom: 16rpx;
	font-size: 94rpx;
}
.empty-state__title {
	display: block;
	margin: 12rpx 0 10rpx;
	font-family: var(--font-display);
	font-size: 42rpx;
	font-weight: 900;
	line-height: 1.3;
}
.empty-state__copy {
	display: block;
	color: var(--muted);
	font-size: 26rpx;
}
.recovery-copy {
	color: var(--muted);
	font-size: 25rpx;
	line-height: 1.8;
}
.request-id {
	margin-top: 24rpx;
	padding: 18rpx;
	border: 2rpx dashed var(--line);
	color: var(--muted);
	background: var(--surface-code);
	font-family: ui-monospace, monospace;
	font-size: 20rpx;
	overflow-wrap: anywhere;
}
</style>
