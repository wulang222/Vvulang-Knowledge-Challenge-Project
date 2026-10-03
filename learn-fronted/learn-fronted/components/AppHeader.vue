<template>
	<view class="app-header">
		<view class="app-header__safe" />
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
			<view class="app-header__action"><slot name="action" /></view>
		</view>
	</view>
</template>

<script setup lang="ts">
withDefaults(defineProps<{ title: string; back?: boolean }>(), { back: false });
defineEmits<{ back: [] }>();
</script>

<style scoped>
.app-header {
	background: rgba(255, 248, 231, 0.97);
	border-bottom: 2rpx dashed rgba(36, 32, 27, 0.23);
}

.app-header__safe {
	height: env(safe-area-inset-top);
}

.app-header__bar {
	min-height: 108rpx;
	padding: 10rpx 26rpx 14rpx;
	display: grid;
	grid-template-columns: 84rpx 1fr 84rpx;
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
	width: 84rpx;
	min-height: 84rpx;
	display: grid;
	place-items: center;
}

.app-header__title {
	overflow: hidden;
	font-family: var(--font-display);
	font-size: 36rpx;
	font-weight: 900;
	text-align: center;
	text-overflow: ellipsis;
	white-space: nowrap;
}
</style>
