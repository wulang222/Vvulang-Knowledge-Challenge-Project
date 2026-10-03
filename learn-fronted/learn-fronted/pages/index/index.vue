<template>
	<view class="page-shell">
		<AppHeader title="准备闯关">
			<template #action>
				<button
					class="header-action-button header-info"
					aria-label="查看隐私说明"
					@click="privacyOpen = true"
				>
					ⓘ
				</button>
			</template>
		</AppHeader>

		<view class="page-body">
			<view
				v-if="store.hasRestoredDraft"
				class="restore-card"
				role="status"
			>
				<view>
					<text class="restore-card__title"
						>本机有一份未过期草稿</text
					>
					<text class="restore-card__meta"
						>输入、设置和已完成作答会保留 24 小时。</text
					>
				</view>
				<view class="restore-card__actions">
					<button
						v-if="store.run"
						class="text-action"
						@click="continueDraft"
					>
						继续
					</button>
					<button
						class="text-action text-action--danger"
						@click="discardDraft"
					>
						清除
					</button>
				</view>
			</view>

			<view class="hero-copy">
				<text class="hero-copy__kicker">把“想知道”变成“答得出”</text>
				<text class="hero-copy__title">今天想弄懂什么？</text>
				<text class="hero-copy__body"
					>输入一句问题、一个主题，或粘贴学习资料。每道题都会写明依据。</text
				>
			</view>

			<view class="mascot-row">
				<view class="mascot" aria-hidden="true"><text>•‿•</text></view>
				<text class="speech"
					>一句“RAG
					是什么？”也能开始；没有原文时，会查找可靠资料。</text
				>
			</view>

			<view class="field">
				<view class="field__label">
					<text>问题、主题或学习资料</text>
					<text class="status-pill status-pill--success"
						>不限字数</text
					>
				</view>
				<view
					class="textarea-wrap"
					:class="{ 'textarea-wrap--error': inputError }"
				>
					<textarea
						class="learning-input resize-none"
						v-model="store.inputText"
						:maxlength="-1"
						:aria-invalid="inputError ? 'true' : 'false'"
						aria-label="问题、主题或学习资料"
						aria-describedby="learning-input-help"
						placeholder="例如：RAG 是什么？也可以直接粘贴长资料"
						@input="store.error = null"
						@blur="store.persistDraft()"
					/>
					<button
						v-if="store.inputText"
						class="clear-input"
						aria-label="清空输入"
						@click="clearInput"
					>
						清空
					</button>
				</view>
				<text
					id="learning-input-help"
					class="field__help"
					:class="{ 'field__help--error': inputError }"
				>
					{{
						inputError ||
						"一句话也可以。后端判断问题或原文，不要求凑字数。"
					}}
				</text>
			</view>

			<button class="example-button" @click="useExample">
				用“RAG 是什么？”试一关 →
			</button>

			<view class="section-title"
				><text>这次做几题？</text
				><text class="section-caption">约 3–8 分钟</text></view
			>
			<view class="segmented" role="group" aria-label="题目数量">
				<button
					v-for="count in [5, 10] as const"
					:key="count"
					class="segment"
					:class="{
						'segment--selected':
							store.config.question_count === count,
					}"
					:aria-pressed="store.config.question_count === count"
					@click="store.setQuestionCount(count)"
				>
					{{ count }} 题 · {{ count === 5 ? "快速" : "完整" }}
				</button>
			</view>

			<view class="section-title"><text>难度</text></view>
			<view class="segmented" role="group" aria-label="难度">
				<button
					class="segment"
					:class="{
						'segment--selected':
							store.config.difficulty === 'basic',
					}"
					:aria-pressed="store.config.difficulty === 'basic'"
					@click="store.setDifficulty('basic')"
				>
					基础
				</button>
				<button
					class="segment"
					:class="{
						'segment--selected':
							store.config.difficulty === 'advanced',
					}"
					:aria-pressed="store.config.difficulty === 'advanced'"
					@click="store.setDifficulty('advanced')"
				>
					进阶
				</button>
			</view>

			<view class="section-title"
				><text>题型</text
				><text class="section-caption">至少保留一种</text></view
			>
			<view class="chip-row" role="group" aria-label="题型">
				<button
					class="chip"
					:class="{ 'chip--selected': hasType('single_choice') }"
					:aria-pressed="hasType('single_choice')"
					@click="store.toggleQuestionType('single_choice')"
				>
					{{ hasType("single_choice") ? "✓ " : "" }}单选题
				</button>
				<button
					class="chip"
					:class="{ 'chip--selected': hasType('true_false') }"
					:aria-pressed="hasType('true_false')"
					@click="store.toggleQuestionType('true_false')"
				>
					{{ hasType("true_false") ? "✓ " : "" }}判断题
				</button>
			</view>

			<view class="card card--blue mt-16">
				<text class="card-title">来源策略 · 自动</text>
				<text class="source-copy"
					>只有问题时检索可靠资料；粘贴原文时优先依据原文，外部补充会单独标记。</text
				>
			</view>

			<AppButton
				class="mt-16"
				variant="primary"
				full
				@press="startGeneration"
				>生成有依据的题目 →</AppButton
			>
			<text class="privacy-note"
				>🔒 默认不公开输入；API Key 只保存在后端。</text
			>
		</view>

		<AppDialog
			:open="privacyOpen"
			title="输入和检索怎么处理？"
			@close="privacyOpen = false"
		>
			<text class="dialog-copy"
				>内容会发送到后端和大模型服务；没有原文时，问题会用于检索公开资料。</text
			>
			<text class="dialog-copy"
				>后端会检查身份证、密码、密钥等敏感信息，发现风险会暂停生成并请你修改。</text
			>
			<template #actions
				><AppButton variant="primary" full @press="privacyOpen = false"
					>知道了</AppButton
				></template
			>
		</AppDialog>
	</view>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import AppButton from "@/components/AppButton.vue";
import AppDialog from "@/components/AppDialog.vue";
import AppHeader from "@/components/AppHeader.vue";
import { useQuizStore } from "@/stores/quiz";
import type { QuestionType } from "@/types/quiz";

const store = useQuizStore();
const privacyOpen = ref(false);
const inputError = computed(() =>
	store.error?.code === "EMPTY_INPUT" ? store.error.message : "",
);

function clearInput() {
	store.setInput("");
	store.persistDraft();
}
function useExample() {
	store.setInput("RAG 是什么？");
	store.persistDraft();
}
function hasType(type: QuestionType): boolean {
	return store.config.question_types.includes(type);
}
function startGeneration() {
	if (store.prepareNewRun())
		uni.navigateTo({ url: "/pages/generate/generate" });
}
function continueDraft() {
	uni.navigateTo({
		url: store.report ? "/pages/report/report" : "/pages/quiz/quiz",
	});
}
function discardDraft() {
	store.clearSession();
}
</script>

<style scoped>
.header-info {
	font-size: 35rpx !important;
}
.restore-card {
	margin-bottom: 26rpx;
	padding: 22rpx;
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 18rpx;
	border: 3rpx solid var(--blue);
	border-radius: 22rpx;
	background: var(--surface-blue);
}
.restore-card__title {
	display: block;
	font-weight: 900;
}
.restore-card__meta {
	display: block;
	margin-top: 4rpx;
	color: var(--muted);
	font-size: 22rpx;
}
.restore-card__actions {
	display: flex;
	flex: none;
	gap: 8rpx;
}
.text-action {
	min-height: 72rpx;
	padding: 8rpx 12rpx;
	border: 0;
	color: var(--blue-dark);
	background: transparent;
	font-size: 24rpx;
	font-weight: 900;
}
.text-action::after {
	border: 0;
}
.text-action--danger {
	color: var(--red);
}
.hero-copy__kicker {
	display: block;
	color: var(--red);
	font-family: var(--font-note);
	font-size: 27rpx;
	font-weight: 800;
}
.hero-copy__title {
	display: block;
	margin: 12rpx 0 8rpx;
	font-family: var(--font-display);
	font-size: 58rpx;
	font-weight: 900;
	line-height: 1.15;
}
.hero-copy__body {
	display: block;
	color: var(--muted);
	font-size: 27rpx;
}
.mascot-row {
	display: flex;
	align-items: center;
	gap: 24rpx;
	margin: 24rpx 0 30rpx;
}
.mascot {
	flex: none;
	width: 112rpx;
	height: 102rpx;
	display: grid;
	place-items: center;
	transform: rotate(-2deg);
	border: 5rpx solid var(--ink);
	border-radius: 45% 52% 46% 50%;
	background: var(--skin);
	box-shadow: 4rpx 4rpx 0 var(--ink);
	font-size: 34rpx;
	font-weight: 900;
	letter-spacing: 8rpx;
}
.speech {
	flex: 1;
	padding: 20rpx 24rpx;
	border: 4rpx solid var(--ink);
	border-radius: 26rpx;
	background: var(--surface);
	font-family: var(--font-note);
	font-size: 25rpx;
	font-weight: 700;
}
.field {
	margin-top: 24rpx;
}
.field__label {
	margin-bottom: 12rpx;
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 16rpx;
	font-size: 27rpx;
	font-weight: 900;
}
.textarea-wrap {
	position: relative;
	border: 4rpx solid var(--ink);
	border-radius: 22rpx;
	background: var(--surface);
}
.textarea-wrap--error {
	border-color: var(--red);
}
.learning-input {
	width: 100%;
	height: 340rpx;
	padding: 24rpx;
	box-sizing: border-box;
	line-height: 1.65;
	resize: none;
}
.clear-input {
	position: absolute;
	right: 12rpx;
	bottom: 12rpx;
	min-width: 84rpx;
	min-height: 64rpx;
	padding: 8rpx 12rpx;
	border: 0;
	border-radius: 14rpx;
	color: var(--blue-dark);
	background: var(--surface-blue);
	font-size: 22rpx;
	font-weight: 900;
}
.clear-input::after {
	border: 0;
}
.field__help {
	display: block;
	min-height: 36rpx;
	margin-top: 10rpx;
	color: var(--muted);
	font-size: 22rpx;
}
.field__help--error {
	color: var(--red);
}
.example-button {
	width: 100%;
	min-height: 88rpx;
	margin-top: 18rpx;
	border: 3rpx solid var(--line);
	border-radius: 22rpx;
	color: var(--blue-dark);
	background: var(--surface);
	font-size: 25rpx;
	font-weight: 900;
}
.example-button::after,
.segment::after,
.chip::after {
	border: 0;
}
.section-caption {
	color: var(--muted);
	font-family: var(--font-body);
	font-size: 22rpx;
	font-weight: 400;
}
.segmented {
	display: grid;
	grid-template-columns: 1fr 1fr;
	gap: 16rpx;
}
.segment {
	min-height: 88rpx;
	padding: 16rpx;
	border: 3rpx solid var(--line);
	border-radius: 20rpx;
	color: var(--ink);
	background: var(--surface);
	font-size: 26rpx;
	font-weight: 800;
}
.segment--selected,
.chip--selected {
	border-color: var(--blue);
	color: var(--blue-dark);
	background: var(--surface-selected);
	box-shadow: inset 0 -6rpx 0 var(--blue-shadow);
}
.chip-row {
	display: flex;
	flex-wrap: wrap;
	gap: 14rpx;
}
.chip {
	min-height: 72rpx;
	padding: 10rpx 22rpx;
	border: 3rpx solid var(--line);
	border-radius: 999px;
	color: var(--ink);
	background: var(--surface);
	font-size: 25rpx;
	font-weight: 800;
}
.source-copy {
	color: var(--muted);
	font-size: 24rpx;
}
.privacy-note {
	display: block;
	margin-top: 22rpx;
	color: var(--muted);
	font-size: 22rpx;
	text-align: center;
}
.dialog-copy {
	display: block;
	margin-bottom: 18rpx;
}
</style>
