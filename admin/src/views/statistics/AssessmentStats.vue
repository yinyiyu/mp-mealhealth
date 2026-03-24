<!-- views/statistics/AssessmentStats.vue - 单个测评统计详情页（从测评管理跳转） -->
<template>
  <div class="page-container">
    <div class="page-header">
      <el-button icon="el-icon-arrow-left" @click="$router.back()">返回</el-button>
      <h2 class="page-title">{{ stats ? stats.assessment_title : '测评统计' }}</h2>
    </div>

    <div v-if="loading" v-loading="true" style="height: 200px;"></div>

    <template v-else-if="stats">
      <el-row :gutter="16" style="margin-bottom: 16px;">
        <el-col :span="6" v-for="item in metricItems" :key="item.label">
          <div class="metric-card" :style="{ borderLeftColor: item.color }">
            <div class="metric-value" :style="{ color: item.color }">{{ item.value }}</div>
            <div class="metric-label">{{ item.label }}</div>
          </div>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-card>
            <div slot="header"><b>风险等级分布</b></div>
            <div ref="riskChart" style="height: 260px;"></div>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card>
            <div slot="header"><b>院系完成情况</b></div>
            <div ref="deptChart" style="height: 260px;"></div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 高风险学生列表入口 -->
      <el-card style="margin-top: 16px;">
        <div slot="header" style="display:flex; justify-content:space-between;">
          <b>高风险学生名单（{{ stats.risk_distribution.high_risk }} 人）</b>
          <el-button size="mini" type="danger" @click="goHighRisk">查看完整名单</el-button>
        </div>
        <p style="color:#888; font-size:14px;">
          共有 <b style="color:#FF4D4F;">{{ stats.risk_distribution.high_risk }}</b> 名学生测评结果为高风险，
          系统已自动创建跟进记录，请及时安排心理老师跟进。
        </p>
      </el-card>
    </template>
  </div>
</template>

<script>
import * as echarts from 'echarts'
import { statisticsApi } from '../../api'

export default {
  name: 'AssessmentStats',
  data() {
    return { stats: null, loading: true }
  },
  computed: {
    metricItems() {
      if (!this.stats) return []
      return [
        { label: '完成率', value: `${this.stats.completion_rate}%`, color: '#4A90D9' },
        { label: '已完成', value: this.stats.submitted_count, color: '#52C41A' },
        { label: '平均分', value: this.stats.score_stats.avg, color: '#FA8C16' },
        { label: '高风险', value: this.stats.risk_distribution.high_risk, color: '#FF4D4F' }
      ]
    }
  },
  async created() {
    const id = this.$route.params.id
    try {
      const res = await statisticsApi.assessment(id)
      this.stats = res.data
    } finally {
      this.loading = false
    }
    this.$nextTick(() => this.initCharts())
  },
  methods: {
    initCharts() {
      if (!this.stats) return
      const d = this.stats.risk_distribution
      echarts.init(this.$refs.riskChart).setOption({
        tooltip: { trigger: 'item' },
        legend: { bottom: 0 },
        series: [{
          type: 'pie', radius: ['35%', '65%'],
          data: [
            { value: d.normal, name: '正常', itemStyle: { color: '#52C41A' } },
            { value: d.low_risk, name: '低风险', itemStyle: { color: '#1890FF' } },
            { value: d.medium_risk, name: '中风险', itemStyle: { color: '#FA8C16' } },
            { value: d.high_risk, name: '高风险', itemStyle: { color: '#FF4D4F' } }
          ]
        }]
      })
      const deptData = this.stats.department_stats
      echarts.init(this.$refs.deptChart).setOption({
        tooltip: {},
        grid: { left: 80, right: 20, bottom: 30, top: 20 },
        xAxis: { type: 'value' },
        yAxis: { type: 'category', data: deptData.map(d => d.department) },
        series: [{ type: 'bar', data: deptData.map(d => d.completed), itemStyle: { color: '#4A90D9', borderRadius: 4 } }]
      })
    },
    goHighRisk() {
      this.$router.push(`/followup?assessment_id=${this.$route.params.id}`)
    }
  }
}
</script>

<style scoped>
.page-header { display: flex; align-items: center; gap: 16px; margin-bottom: 20px; }
.page-title { font-size: 20px; font-weight: 600; }
.metric-card {
  background: #FFFFFF; border-radius: 12px; padding: 20px;
  text-align: center; border-left: 4px solid; box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}
.metric-value { font-size: 36px; font-weight: 700; }
.metric-label { font-size: 13px; color: #888; margin-top: 6px; }
</style>
