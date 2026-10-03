<template>
	<button
		class="app-button"
		:class="[`app-button--${variant}`, { 'app-button--full': full }]"
		:disabled="disabled || busy"
		:aria-busy="busy ? 'true' : 'false'"
		@click="$emit('press')"
	>
		<text v-if="busy" class="app-button__spinner" aria-hidden="true"
			>✎</text
		>
		<text class="app-button__label"><slot /></text>
	</button>
</template>

<script setup lang="ts">
withDefaults(
	defineProps<{
		variant?: "primary" | "secondary" | "ghost" | "danger";
		full?: boolean;
		disabled?: boolean;
		busy?: boolean;
	}>(),
	{
		variant: "secondary",
		full: false,
		disabled: false,
		busy: false,
	},
);

defineEmits<{ press: [] }>();
</script>

<style scoped>
.app-button {
	position: relative;
	min-height: 96rpx;
	padding: 20rpx 30rpx;
	border: 4rpx solid var(--ink);
	border-radius: 24rpx;
	color: var(--ink);
	background: var(--surface);
	box-shadow: 4rpx 4rpx 0 var(--ink);
	font-size: 29rpx;
	font-weight: 900;
	line-height: 1.3;
	cursor: pointer;
	transition:
		transform 180ms ease,
		box-shadow 180ms ease,
		border-color 180ms ease;
}

.app-button::after {
	border: 0;
}
.app-button--full {
	width: 100%;
}
.app-button--primary {
	color: var(--on-primary);
	background: var(--blue);
}
.app-button--ghost {
	border-color: var(--line);
	box-shadow: none;
}
.app-button--danger {
	color: var(--red);
	border-color: var(--red);
	box-shadow: 4rpx 4rpx 0 var(--red);
}
.app-button:active:not([disabled]) {
	transform: translate(4rpx, 4rpx);
	box-shadow: none;
}
.app-button[disabled] {
	cursor: not-allowed;
	opacity: 0.48;
	box-shadow: none;
}

.app-button__spinner {
	position: absolute;
	left: 26rpx;
	animation: pencil-wobble 800ms steps(3) infinite;
}

.app-button__label {
	display: block;
}

@keyframes pencil-wobble {
	50% {
		transform: rotate(9deg);
	}
}
</style>
