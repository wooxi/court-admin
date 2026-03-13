<template>
  <div class="pipeline-bar">
    <div
      v-for="(stage, index) in stages"
      :key="stage.key"
      class="pipeline-stage"
    >
      <div
        class="pipeline-node"
        :class="[stage.status, { active: stage.active }]"
      >
        <div class="pipeline-icon">{{ stage.icon }}</div>
        <div class="pipeline-name">{{ stage.name }}</div>
        <div class="pipeline-action">{{ stage.action }}</div>
        <div v-if="stage.status === 'done'" class="pipeline-tick">✓</div>
      </div>
      <div v-if="index < stages.length - 1" class="pipeline-arrow">›</div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  stages: {
    type: Array,
    required: true,
    default: () => []
  }
})
</script>

<style scoped>
.pipeline-bar {
  display: flex;
  align-items: stretch;
  gap: 0;
  overflow-x: auto;
  padding: 12px;
  background: var(--panel2);
  border-radius: 10px;
  margin-bottom: 16px;
}

.pipeline-stage {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.pipeline-node {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  padding: 8px 12px;
  border-radius: 8px;
  min-width: 70px;
  position: relative;
  transition: all 0.2s;
}

.pipeline-node.done {
  background: #0a2018;
  border: 1px solid #2ecc8a44;
}

.pipeline-node.active {
  background: #0f1838;
  border: 2px solid var(--acc);
  box-shadow: 0 0 12px rgba(106, 158, 255, 0.2);
}

.pipeline-node.pending {
  opacity: 0.3;
  border: 1px dashed var(--line);
}

.pipeline-icon {
  font-size: 18px;
}

.pipeline-name {
  font-size: 11px;
  font-weight: 700;
  margin-top: 2px;
}

.pipeline-node.done .pipeline-name {
  color: var(--ok);
}

.pipeline-node.active .pipeline-name {
  color: var(--acc);
}

.pipeline-node.pending .pipeline-name {
  color: var(--muted);
}

.pipeline-action {
  font-size: 9px;
  color: var(--muted);
  margin-top: 1px;
}

.pipeline-node.active .pipeline-action {
  color: #6a9eff88;
}

.pipeline-tick {
  position: absolute;
  top: -5px;
  right: -5px;
  width: 14px;
  height: 14px;
  background: var(--ok);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 8px;
  color: #000;
  font-weight: 700;
}

.pipeline-arrow {
  color: #1c2236;
  font-size: 16px;
  padding: 0 4px;
  margin-top: -8px;
}
</style>
