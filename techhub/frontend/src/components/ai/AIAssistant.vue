<template>
  <div class="ai-assistant">
    <!-- 悬浮按钮 -->
    <div 
      class="ai-float-btn"
      :class="{ 'is-active': isOpen }"
      @click="togglePanel"
    >
      <el-icon v-if="!isOpen"><MagicStick /></el-icon>
      <el-icon v-else><Close /></el-icon>
      <div v-if="unreadCount > 0" class="badge">{{ unreadCount }}</div>
    </div>

    <!-- 对话面板 -->
    <AIChatPanel 
      :is-open="isOpen"
      @close="isOpen = false"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import AIChatPanel from './AIChatPanel.vue'

const isOpen = ref(false)
const unreadCount = ref(0)

function togglePanel() {
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    unreadCount.value = 0
  }
}
</script>

<style scoped lang="scss">
.ai-assistant {
  position: relative;
}

.ai-float-btn {
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  cursor: pointer;
  box-shadow: 0 4px 16px rgba(102, 126, 234, 0.4);
  transition: all 0.3s ease;
  z-index: 2001;

  &:hover {
    transform: scale(1.1);
    box-shadow: 0 6px 24px rgba(102, 126, 234, 0.5);
  }

  &.is-active {
    background: #666;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
  }

  .badge {
    position: absolute;
    top: -2px;
    right: -2px;
    min-width: 18px;
    height: 18px;
    padding: 0 5px;
    border-radius: 9px;
    background: #f56c6c;
    color: #fff;
    font-size: 11px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
}

// 脉冲动画
@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(102, 126, 234, 0.4);
  }
  70% {
    box-shadow: 0 0 0 12px rgba(102, 126, 234, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(102, 126, 234, 0);
  }
}

.ai-float-btn:not(.is-active) {
  animation: pulse 2s infinite;
}
</style>
