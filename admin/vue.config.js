// vue.config.js - Vue CLI配置
module.exports = {
  devServer: {
    port: 8080,
    // 开发环境代理：将/api请求转发到Flask后端
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true
      }
    }
  },
  // 生产环境打包优化
  productionSourceMap: false
}
