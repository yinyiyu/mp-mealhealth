<!-- views/Dashboard.vue - 数据看板首页 -->
<template>
  <div class="dashboard">
    <h2 class="page-title">数据看板</h2>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stat-cards">
      <el-col :span="6" v-for="card in statCards" :key="card.key">
        <div class="stat-card" :style="{ borderLeftColor: card.color }">
          <div class="stat-icon" :style="{ background: card.color + '20', color: card.color }">
            <i :class="card.icon"></i>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ overview[card.key] || 0 }}</div>
            <div class="stat-label">{{ card.label }}</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <!-- 风险趋势折线图 -->
      <el-col :span="14">
        <el-card class="chart-card">
          <div slot="header">
            <span>风险趋势（近6个月）</span>
          </div>
          <div ref="trendChart" class="chart-container"></div>
        </el-card>
      </el-col>

      <!-- 跟进状态饼图 -->
      <el-col :span="10">
        <el-card class="chart-card">
          <div slot="header">
            <span>跟进状态分布</span>
          </div>
          <div ref="followupChart" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import * as echarts from 'echarts'
import { statisticsApi } from '../api'

export default {
  name: 'Dashboard',
  data() {
    return {
      overview: {},
      trendData: [],
      followupData: {},
      statCards: [
        { key: 'total_students', label: '在校学生总数', icon: 'el-icon-user', color: '#4A90D9' },
        { key: 'total_submissions', label: '累计测评完成', icon: 'el-icon-s-check', color: '#52C41A' },
        { key: 'high_risk_count', label: '高风险学生', icon: 'el-icon-warning', color: '#FF4D4F' },
        { key: 'pending_followups', label: '待跟进学生', icon: 'el-icon-bell', color: '#FA8C16' }
      ]
    }
  },
  async mounted() {
    await this.loadData()
    this.initCharts()
  },
  methods: {
    async loadData() {
      try {
        const [overviewRes, trendRes, followupRes] = await Promise.all([
          statisticsApi.overview(),
          statisticsApi.riskTrend(6),
          statisticsApi.followupSummary()
        ])
        this.overview = overviewRes.data
        this.trendData = trendRes.data
        this.followupData = followupRes.data
      } catch (e) {
        console.error('加载统计数据失败', e)
      }
    },

    initCharts() {
      this.$nextTick(() => {
        this.initTrendChart()
        this.initFollowupChart()
      })
    },

    /** 风险趋势折线图 */
    initTrendChart() {
      const chart = echarts.init(this.$refs.trendChart)
      const months = this.trendData.map(d => d.month)
      chart.setOption({
        tooltip: { trigger: 'axis' },
        legend: { data: ['高风险', '中风险'] },
        grid: { left: 40, right: 20, bottom: 30, top: 40 },
        xAxis: { type: 'category', data: months },
        yAxis: { type: 'value', minInterval: 1 },
        series: [
          {
            name: '高风险',
            type: 'line',
            data: this.trendData.map(d => d.high_risk),
            lineStyle: { color: '#FF4D4F' },
            itemStyle: { color: '#FF4D4F' },
            smooth: true,
            areaStyle: { color: 'rgba(255,77,79,0.1)' }
          },
          {
            name: '中风险',
            type: 'line',
            data: this.trendData.map(d => d.medium_risk),
            lineStyle: { color: '#FA8C16' },
            itemStyle: { color: '#FA8C16' },
            smooth: true,
            areaStyle: { color: 'rgba(250,140,22,0.1)' }
          }
        ]
      })
    },

    /** 跟进状态饼图 */
    initFollowupChart() {
      const chart = echarts.init(this.$refs.followupChart)
      const d = this.followupData
      chart.setOption({
        tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
        legend: { bottom: 0 },
        series: [{
          type: 'pie',
          radius: ['40%', '70%'],
          center: ['50%', '45%'],
          data: [
            { value: d.pending || 0, name: '待沟通', itemStyle: { color: '#FA8C16' } },
            { value: d.in_progress || 0, name: '跟进中', itemStyle: { color: '#4A90D9' } },
            { value: d.closed || 0, name: '已结案', itemStyle: { color: '#52C41A' } }
          ],
          emphasis: { itemStyle: { shadowBlur: 10 } }
        }]
      })
    }
  }
}
</script>

<style scoped>
.page-title {
  font-size: 22px;
  font-weight: 600;
  color: #1A1A1A;
  margin-bottom: 20px;
}

/* 统计卡片 */
.stat-card {
  background: #FFFFFF;
  border-radius: 12px;
  padding: 24px 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  border-left: 4px solid transparent;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}

.stat-icon {
  width: 52px;
  height: 52px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #1A1A1A;
  line-height: 1;
}

.stat-label {
  font-size: 13px;
  color: #888888;
  margin-top: 6px;
}

/* 图表卡片 */
.chart-card {
  border-radius: 12px;
}

.chart-container {
  height: 300px;
}
</style>
