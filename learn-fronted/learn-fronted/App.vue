<script lang="ts">
import { defineComponent } from "vue";
import { useQuizStore } from "@/stores/quiz";

export default defineComponent({
	onLaunch() {
		useQuizStore().restoreDraft();
	},
});
</script>

<style>
@import "@/styles/theme.css";
</style>
