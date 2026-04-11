<template>
  <div class="not-found-page">
    <div class="error-content">
      <h1>404</h1>
      <p>页面未找到</p>
      <el-button type="primary" @click="$router.push('/')">
        返回首页
      </el-button>
    </div>
  </div>
</template>

<style scoped lang="scss">
.not-found-page {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  
  .error-content {
    text-align: center;
    
    h1 {
      font-size: 120px;
      font-weight: 700;
      color: #1890ff;
      margin-bottom: 20px;
      line-height: 1;
    }
    
    p {
      font-size: 24px;
      color: #666;
      margin-bottom: 30px;
    }
  }
}
</style>
