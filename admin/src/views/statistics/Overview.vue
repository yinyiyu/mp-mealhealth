<!-- views/statistics/Overview.vue - 数据统计总览页 -->
<template>
  <div class="page-container">
    <h2 class="page-title">数据统计</h2>

    <!-- 选择测评 -->
    <el-card class="filter-card">
      <el-form inline>
        <el-form-item label="选择测评">
          <el-select
            v-model="selectedAssessmentId"
            placeholder="请选择要统计的测评"
            style="width: 340px;"
            @change="loadAssessmentStats"
          >
            <el-option
              v-for="a in assessments"
              :key="a.id"
              :label="a.title"
              :value="a.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 未选择测评时的提示 -->
    <el-empty v-if="!selectedAssessmentId" description="请先选择一个测评以查看统计数据" />

    <!-- 统计数据展示 -->
    <template v-else-if="stats">
      <!-- 关键指标 -->
      <el-row :gutter="16" class="stats-row">
        <el-col :span="6">
          <div class="metric-card">
            <div class="metric-value">{{ stats.expected_count }}</div>
            <div class="metric-label">应参与人数</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="metric-card">
            <div class="metric-value" style="color: #52C41A;">{{ stats.submitted_count }}</div>
            <div class="metric-label">已完成人数</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="metric-card">
            <div class="metric-value" style="color: #4A90D9;">{{ stats.completion_rate }}%</div>
            <div class="metric-label">完成率</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="metric-card">
            <div class="metric-value" style="color: #FF4D4F;">
              {{ stats.risk_distribution.high_risk }}
            </div>
            <div class="metric-label">高风险人数</div>
          </div>
        </el-col>
      </el-row>

      <!-- 完成率进度条 -->
      <el-card class="chart-card">
        <div slot="header"><b>完成率</b></div>
        <el-progress
          :percentage="stats.completion_rate"
          :color="progressColor(stats.completion_rate)"
          :stroke-width="20"
          style="margin: 16px 0;"
        />
        <p style="text-align:center; color:#888;">
          {{ stats.submitted_count }} / {{ stats.expected_count }} 人已完成
        </p>
      </el-card>

      <el-row :gutter="20" style="margin-top: 16px;">
        <!-- 风险等级分布 -->
        <el-col :span="12">
          <el-card class="chart-card">
            <div slot="header"><b>风险等级分布</b></div>
            <div ref="riskChart" class="chart-box"></div>
          </el-card>
        </el-col>

        <!-- 院系完成情况 -->
        <el-col :span="12">
          <el-card class="chart-card">
            <div slot="header"><b>各院系完成人数</b></div>
            <div ref="deptChart" class="chart-box"></div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 得分统计 -->
      <el-card class="chart-card" style="margin-top: 16px;">
        <div slot="header"><b>得分统计</b></div>
        <el-row :gutter="24">
          <el-col :span="8">
            <div class="score-stat">
              <div class="score-val">{{ stats.score_stats.avg }}</div>
              <div class="score-lbl">平均分</div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="score-stat">
              <div class="score-val">{{ stats.score_stats.min }}</div>
              <div class="score-lbl">最低分</div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="score-stat">
              <div class="score-val">{{ stats.score_stats.max }}</div>
              <div class="score-lbl">最高分</div>
            </div>
          </el-col>
        </el-row>
      </el-card>
    </template>
  </div>
</template>

<script>
import * as echarts from 'echarts'
import { assessmentApi, statisticsApi } from '../../api'

export default {
  name: 'Overview',
  data() {
    return {
      assessments: [],
      selectedAssessmentId: null,
      stats: null
    }
  },
  async created() {
    const res = await assessmentApi.list({ per_page: 100 })
    this.assessments = res.data.items
  },
  methods: {
    async loadAssessmentStats(id) {
      if (!id) return
      const res = await statisticsApi.assessment(id)
      this.stats = res.data
      this.$nextTick(() => {
        this.initRiskChart()
        this.initDeptChart()
      })
    },

    initRiskChart() {
      const chart = echarts.init(this.$refs.riskChart)
      const d = this.stats.risk_distribution
      chart.setOption({
        tooltip: { trigger: 'item', formatter: '{b}: {c}人 ({d}%)' },
        legend: { bottom: 0 },
        series: [{
          type: 'pie',
          radius: ['35%', '65%'],
          data: [
            { value: d.normal, name: '正常', itemStyle: { color: '#52C41A' } },
            { value: d.low_risk, name: '低风险', itemStyle: { color: '#1890FF' } },
            { value: d.medium_risk, name: '中风险', itemStyle: { color: '#FA8C16' } },
            { value: d.high_risk, name: '高风险', itemStyle: { color: '#FF4D4F' } }
          ]
        }]
      })
    },

    initDeptChart() {
      const chart = echarts.init(this.$refs.deptChart)
      const data = this.stats.department_stats
      chart.setOption({
        tooltip: {},
        grid: { left: 80, right: 20, bottom: 30, top: 20 },
        xAxis: { type: 'value' },
        yAxis: {
          type: 'category',
          data: data.map(d => d.department)
        },
        series: [{
          type: 'bar',
          data: data.map(d => d.completed),
          itemStyle: { color: '#4A90D9', borderRadius: 4 }
        }]
      })
    },

    progressColor(percentage) {
      if (percentage >= 80) return '#52C41A'
      if (percentage >= 50) return '#FA8C16'
      return '#FF4D4F'
    }
  }
}
</script>

<style scoped>
.page-title { font-size: 22px; font-weight: 600; margin-bottom: 16px; }
.filter-card { margin-bottom: 16px; }

.stats-row { margin-bottom: 16px; }
.metric-card {
  background: #FFFFFF;
  border-radius: 12px;
  padding: 24px;
  text-align: center;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}
.metric-value { font-size: 40px; font-weight: 700; color: #1A1A1A; }
.metric-label { font-size: 14px; color: #888888; margin-top: 8px; }

.chart-card { border-radius: 12px; }
.chart-box { height: 280px; }

.score-stat { text-align: center; padding: 20px; }
.score-val { font-size: 36px; font-weight: 700; color: #4A90D9; }
.score-lbl { font-size: 14px; color: #888888; margin-top: 8px; }
</style>
