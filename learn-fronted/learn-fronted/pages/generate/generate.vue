<template>
	<view class="page-shell">
		<AppHeader title="出题中" back @back="cancel" />
		<view class="page-body">
			<view class="loader" aria-hidden="true">✎</view>
			<view class="center"
				><text class="generate-title">正在把问题变成关卡</text
				><text class="generate-copy"
					>后端正在检查内容、整理来源并逐题质检。</text
				></view
			>
			<view class="stage-list" role="status" aria-live="polite">
				<view class="stage stage--done"
					><text class="stage__dot">✓</text
					><view
						><text class="stage__title">输入和设置已保存</text
						><text class="stage__meta"
							>离开页面也不会丢失</text
						></view
					></view
				>
				<view class="stage stage--current"
					><text class="stage__dot">2</text
					><view
						><text class="stage__title">生成与质量检查进行中</text
						><text class="stage__meta"
							>服务完成后才显示题目，不伪造百分比</text
						></view
					></view
				>
				<view class="stage"
					><text class="stage__dot">3</text
					><view
						><text class="stage__title">准备第一题</text
						><text class="stage__meta"
							>等待可靠来源和证据全部通过</text
						></view
					></view
				>
			</view>
			<view class="paper-note"
				>慢一点，是因为正在逐题核对答案、来源和证据。没有可靠依据的题不会放行。</view
			>
			<AppButton class="mt-16" variant="ghost" full @press="cancel"
				>取消生成并返回</AppButton
			>
		</view>
	</view>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue";
import AppButton from "@/components/AppButton.vue";
import AppHeader from "@/components/AppHeader.vue";
import { useQuizStore } from "@/stores/quiz";

const store = useQuizStore();
const cancelled = ref(false);

onMounted(async () => {
	const success = await store.generate();
	if (!cancelled.value)
		uni.redirectTo({
			url: success ? "/pages/quiz/quiz" : "/pages/error/error",
		});
});
onBeforeUnmount(() => {
	if (cancelled.value) store.cancelActiveRequest();
});
function cancel() {
	cancelled.value = true;
	store.cancelActiveRequest();
	uni.navigateBack();
}
</script>

<style scoped>
.loader {
	box-sizing: border-box;
	width: 156rpx;
	height: 156rpx;
	margin: 48rpx auto 34rpx;
	display: grid;
	place-items: center;
	border: 6rpx dashed var(--blue);
	border-radius: 47% 53% 44% 56%;
	background: var(--surface);
	animation: loader-wobble 1s steps(3) infinite;
	font-size: 62rpx;
}
.generate-title {
	display: block;
	font-family: var(--font-display);
	font-size: 39rpx;
	font-weight: 900;
}
.generate-copy {
	display: block;
	margin-top: 10rpx;
	color: var(--muted);
	font-size: 25rpx;
	overflow-wrap: anywhere;
}
.stage-list {
	margin: 42rpx 0;
}
.stage {
	position: relative;
	min-height: 118rpx;
	padding: 8rpx 0 22rpx 100rpx;
	display: flex;
	align-items: flex-start;
}
.stage:not(:last-child)::before {
	content: "";
	position: absolute;
	left: 38rpx;
	top: 76rpx;
	bottom: -6rpx;
	border-left: 4rpx dashed var(--line);
}
.stage__dot {
	position: absolute;
	left: 2rpx;
	top: 0;
	width: 76rpx;
	height: 76rpx;
	display: grid;
	place-items: center;
	border: 4rpx solid var(--line);
	border-radius: 50%;
	background: var(--surface);
	font-weight: 900;
}
.stage--done .stage__dot {
	color: white;
	border-color: var(--green);
	background: var(--green);
}
.stage--current .stage__dot {
	color: white;
	border-color: var(--blue);
	background: var(--blue);
	animation: pulse-ink 1.2s steps(2) infinite;
}
.stage__title {
	display: block;
	font-weight: 900;
	overflow-wrap: anywhere;
}
.stage__meta {
	display: block;
	margin-top: 5rpx;
	color: var(--muted);
	font-size: 23rpx;
	overflow-wrap: anywhere;
}
@keyframes loader-wobble {
	50% {
		transform: rotate(6deg);
	}
}
@keyframes pulse-ink {
	50% {
		transform: rotate(5deg) scale(1.06);
	}
}
</style>
