<template>
	<view
		v-if="open"
		class="dialog-layer"
		role="presentation"
		@touchmove.stop.prevent
	>
		<button
			class="dialog-layer__backdrop"
			aria-label="关闭弹窗"
			@click="$emit('close')"
		/>
		<view
			class="dialog"
			role="dialog"
			aria-modal="true"
			:aria-label="title"
		>
			<text class="dialog__title">{{ title }}</text>
			<view class="dialog__body"><slot /></view>
			<view class="dialog__actions"><slot name="actions" /></view>
		</view>
	</view>
</template>

<script setup lang="ts">
defineProps<{ open: boolean; title: string }>();
defineEmits<{ close: [] }>();
</script>

<style scoped>
.dialog-layer {
	position: fixed;
	inset: 0;
	z-index: 100;
	display: grid;
	place-items: center;
	padding: 40rpx 34rpx calc(40rpx + env(safe-area-inset-bottom));
}

.dialog-layer__backdrop {
	position: absolute;
	inset: 0;
	width: 100%;
	height: 100%;
	border: 0;
	border-radius: 0;
	background: rgba(36, 32, 27, 0.64);
}

.dialog-layer__backdrop::after {
	border: 0;
}

.dialog {
	position: relative;
	width: min(100%, 660rpx);
	max-height: 82vh;
	padding: 36rpx;
	overflow-y: auto;
	border: 6rpx solid var(--ink);
	border-radius: 32rpx;
	background: var(--paper);
	box-shadow: 12rpx 14rpx 0 var(--ink);
}

.dialog__title {
	display: block;
	font-family: var(--font-display);
	font-size: 41rpx;
	font-weight: 900;
	line-height: 1.25;
}

.dialog__body {
	margin-top: 18rpx;
	color: var(--muted);
	font-size: 27rpx;
}
.dialog__actions {
	margin-top: 28rpx;
	display: grid;
	gap: 18rpx;
}
</style>
