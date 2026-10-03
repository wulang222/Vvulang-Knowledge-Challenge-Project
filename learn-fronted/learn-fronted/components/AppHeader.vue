<template>
	<view class="app-header">
		<view class="app-header__safe" :style="safeAreaStyle" />
		<view class="app-header__bar">
			<button
				v-if="back"
				class="app-header__icon"
				aria-label="返回"
				@click="$emit('back')"
			>
				‹
			</button>
			<view v-else class="app-header__placeholder" />
			<text class="app-header__title">{{ title }}</text>
			<view class="app-header__action" :style="actionStyle"
				><slot name="action"
			/></view>
		</view>
	</view>
</template>

<script setup lang="ts">
import { ref } from "vue";

withDefaults(defineProps<{ title: string; back?: boolean }>(), { back: false });
defineEmits<{ back: [] }>();

const safeAreaStyle = ref<Record<string, string>>({});
const actionStyle = ref<Record<string, string>>({});

// 微信胶囊同时占用顶部导航区：状态栏高度不能依赖 CSS env，右侧动作也要让开胶囊。
// #ifdef MP-WEIXIN
try {
	const windowInfo = uni.getWindowInfo();
	const menuButton = uni.getMenuButtonBoundingClientRect();
	const statusBarHeight = windowInfo.statusBarHeight || 0;
	const actionOffset = Math.max(
		0,
		windowInfo.windowWidth - menuButton.left + 8,
	);
	safeAreaStyle.value = { height: `${statusBarHeight + 6}px` };
	actionStyle.value = { transform: `translateX(-${actionOffset}px)` };
} catch {
	// 旧版基础库继续使用下方 CSS 变量兜底。
}
// #endif
</script>

<style scoped>
.app-header {
	background: rgba(255, 248, 231, 0.97);
	border-bottom: 2rpx dashed rgba(36, 32, 27, 0.23);
}

.app-header__safe {
	height: calc(var(--status-bar-height) + 12rpx);
}

/* #ifdef H5 */
.app-header__safe {
	height: env(safe-area-inset-top);
}
/* #endif */

.app-header__bar {
	box-sizing: border-box;
	min-height: 108rpx;
	padding: 10rpx 26rpx 14rpx;
	display: grid;
	grid-template-columns: 84rpx minmax(0, 1fr) 84rpx;
	align-items: center;
}

.app-header__icon {
	width: 84rpx;
	min-height: 84rpx;
	padding: 0;
	border: 0;
	border-radius: 50%;
	color: var(--ink);
	background: transparent;
	font-size: 44rpx;
	cursor: pointer;
}

.app-header__icon::after {
	border: 0;
}
.app-header__icon:active {
	background: rgba(77, 120, 184, 0.12);
}
.app-header__placeholder {
	width: 84rpx;
}
.app-header__action {
	min-width: 0;
	width: 84rpx;
	min-height: 84rpx;
	display: grid;
	place-items: center;
}

.app-header__title {
	min-width: 0;
	overflow: hidden;
	font-family: var(--font-display);
	font-size: 36rpx;
	font-weight: 900;
	text-align: center;
	text-overflow: ellipsis;
	white-space: nowrap;
}
</style>
