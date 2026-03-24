<!-- App.vue - 根组件 -->
<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script>
export default {
  name: 'App'
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}
body {
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif;
  background: #F0F2F5;
  color: #333;
}
/* 覆盖Element UI主题色 */
.el-button--primary {
  background-color: #4A90D9;
  border-color: #4A90D9;
}
</style>
