<!-- views/assessment/AssessmentList.vue - 测评任务列表页 -->
<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">测评管理</h2>
      <el-button type="primary" icon="el-icon-plus" @click="$router.push('/assessment/create')">
        发布测评
      </el-button>
    </div>

    <!-- 状态筛选 -->
    <el-card class="filter-card">
      <el-radio-group v-model="filters.status" @change="loadData">
        <el-radio-button label="">全部</el-radio-button>
        <el-radio-button label="draft">草稿</el-radio-button>
        <el-radio-button label="ongoing">进行中</el-radio-button>
        <el-radio-button label="ended">已结束</el-radio-button>
      </el-radio-group>
    </el-card>

    <el-card class="table-card">
      <el-table :data="tableData" v-loading="loading" stripe border>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="title" label="测评标题" min-width="200" />
        <el-table-column prop="template_title" label="问卷模板" width="180" />
        <el-table-column label="答题时间" width="200">
          <template slot-scope="{ row }">
            <div v-if="row.start_time || row.end_time">
              <div>开始：{{ row.start_time || '不限' }}</div>
              <div>结束：{{ row.end_time || '不限' }}</div>
            </div>
            <span v-else>不限时间</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template slot-scope="{ row }">
            <el-tag :type="assessmentStatusType(row.status)" size="small">
              {{ assessmentStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template slot-scope="{ row }">
            <el-button
              v-if="row.status === 'draft'"
              size="mini" type="success"
              @click="onPublish(row)"
            >发布</el-button>
            <el-button
              v-if="row.status === 'ongoing'"
              size="mini" type="warning"
              @click="onEnd(row)"
            >结束</el-button>
            <el-button
              size="mini"
              @click="onViewStats(row)"
            >查看统计</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        class="pagination"
        :current-page="pagination.page"
        :page-size="pagination.perPage"
        :total="pagination.total"
        layout="total, prev, pager, next"
        @current-change="onPageChange"
      />
    </el-card>
  </div>
</template>

<script>
import { assessmentApi } from '../../api'

export default {
  name: 'AssessmentList',
  data() {
    return {
      tableData: [],
      loading: false,
      filters: { status: '' },
      pagination: { page: 1, perPage: 10, total: 0 }
    }
  },
  created() {
    this.loadData()
  },
  methods: {
    async loadData() {
      this.loading = true
      try {
        const params = { page: this.pagination.page, per_page: this.pagination.perPage }
        if (this.filters.status) params.status = this.filters.status
        const res = await assessmentApi.list(params)
        this.tableData = res.data.items
        this.pagination.total = res.data.total
      } finally {
        this.loading = false
      }
    },

    onPageChange(page) {
      this.pagination.page = page
      this.loadData()
    },

    async onPublish(row) {
      await this.$confirm(`确认发布测评《${row.title}》？发布后学生可以在小程序中看到并参与此测评。`, '发布确认', {
        confirmButtonText: '确认发布', cancelButtonText: '取消', type: 'warning'
      })
      await assessmentApi.updateStatus(row.id, 'ongoing')
      this.$message.success('测评已发布')
      this.loadData()
    },

    async onEnd(row) {
      await this.$confirm(`确认结束测评《${row.title}》？结束后学生将无法继续提交。`, '结束确认', {
        confirmButtonText: '确认结束', cancelButtonText: '取消', type: 'warning'
      })
      await assessmentApi.updateStatus(row.id, 'ended')
      this.$message.success('测评已结束')
      this.loadData()
    },

    onViewStats(row) {
      this.$router.push(`/assessment/${row.id}/statistics`)
    },

    assessmentStatusText(status) {
      return { draft: '草稿', ongoing: '进行中', ended: '已结束', archived: '已归档' }[status] || status
    },
    assessmentStatusType(status) {
      return { draft: 'info', ongoing: 'success', ended: '', archived: 'info' }[status] || ''
    }
  }
}
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.page-title { font-size: 22px; font-weight: 600; }
.filter-card { margin-bottom: 16px; }
.pagination { margin-top: 16px; text-align: right; }
</style>
