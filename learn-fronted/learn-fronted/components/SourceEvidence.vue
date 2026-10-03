<template>
	<view class="evidence">
		<text class="evidence__quote">“{{ reference.evidence_quote }}”</text>
		<text class="evidence__source">
			{{
				source?.publisher ||
				(source?.type === "USER_TEXT" ? "用户提供" : "公开资料")
			}}
			· {{ source?.title || "来源资料" }} · {{ reference.location }}
		</text>
		<button v-if="source?.url" class="evidence__link" @click="copyUrl">
			复制官方文档链接 ↗
		</button>
	</view>
</template>

<script setup lang="ts">
import type { SourceReference, SourceSummary } from "@/types/quiz";

const props = defineProps<{
	reference: SourceReference;
	source?: SourceSummary;
}>();

function copyUrl() {
	if (!props.source?.url) return;
	uni.setClipboardData({
		data: props.source.url,
		success: () => uni.showToast({ title: "官方链接已复制", icon: "none" }),
	});
}
</script>

<style scoped>
.evidence {
	max-width: 100%;
	box-sizing: border-box;
	margin-top: 24rpx;
	padding: 24rpx;
	border-left: 8rpx solid var(--blue);
	background: var(--surface-blue);
	font-family: var(--font-note);
}

.evidence__quote {
	display: block;
	font-size: 27rpx;
	line-height: 1.7;
	overflow-wrap: anywhere;
}
.evidence__source {
	display: block;
	margin-top: 12rpx;
	color: var(--muted);
	font-family: var(--font-body);
	font-size: 22rpx;
	overflow-wrap: anywhere;
}

.evidence__link {
	min-height: 80rpx;
	margin: 12rpx 0 0;
	padding: 8rpx 0;
	border: 0;
	color: var(--blue-dark);
	background: transparent;
	font-size: 24rpx;
	font-weight: 900;
	text-align: left;
	text-decoration: underline;
}

.evidence__link::after {
	border: 0;
}
</style>
