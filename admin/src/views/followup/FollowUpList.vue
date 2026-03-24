<!-- views/followup/FollowUpList.vue - 重点学生跟进管理页面 -->
<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">重点学生跟进</h2>
      <div class="header-actions">
        <!-- 跟进状态统计徽章 -->
        <el-tag type="warning">待沟通 {{ summary.pending }}</el-tag>
        <el-tag type="primary" style="margin-left:8px;">跟进中 {{ summary.in_progress }}</el-tag>
        <el-tag type="success" style="margin-left:8px;">已结案 {{ summary.closed }}</el-tag>
      </div>
    </div>

    <!-- 筛选栏 -->
    <el-card class="filter-card">
      <el-form inline>
        <el-form-item label="跟进状态">
          <el-select v-model="filters.status" placeholder="全部状态" clearable @change="loadData">
            <el-option label="待沟通" value="pending" />
            <el-option label="跟进中" value="in_progress" />
            <el-option label="已结案" value="closed" />
          </el-select>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 跟进记录表格 -->
    <el-card class="table-card">
      <el-table :data="tableData" v-loading="loading" stripe border>
        <el-table-column prop="student_name" label="学生姓名" width="100" />
        <el-table-column prop="student_number" label="学号" width="130" />
        <el-table-column prop="department" label="院系" width="150" />
        <el-table-column label="跟进状态" width="110" align="center">
          <template slot-scope="{ row }">
            <el-tag :type="statusTagType(row.follow_status)" size="small">
              {{ statusText(row.follow_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="teacher_name" label="负责老师" width="100">
          <template slot-scope="{ row }">
            {{ row.teacher_name || '未分配' }}
          </template>
        </el-table-column>
        <el-table-column prop="notes" label="跟进备注" min-width="200" show-overflow-tooltip />
        <el-table-column prop="updated_at" label="最后更新" width="160" />
        <el-table-column label="操作" width="180" fixed="right">
          <template slot-scope="{ row }">
            <el-button size="mini" type="primary" @click="openUpdateDialog(row)">更新跟进</el-button>
            <el-button size="mini" @click="viewReport(row)" v-if="row.report_id">查看报告</el-button>
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

    <!-- 更新跟进状态对话框 -->
    <el-dialog
      title="更新跟进记录"
      :visible.sync="updateDialogVisible"
      width="560px"
    >
      <div v-if="currentFollowup" class="student-info-box">
        <el-tag>{{ currentFollowup.student_name }}</el-tag>
        <el-tag type="info" style="margin-left:8px;">{{ currentFollowup.student_number }}</el-tag>
        <el-tag type="warning" style="margin-left:8px;">{{ currentFollowup.department }}</el-tag>
      </div>

      <el-form ref="updateForm" :model="updateForm" label-width="100px" style="margin-top: 20px;">
        <el-form-item label="跟进状态" prop="follow_status">
          <el-radio-group v-model="updateForm.follow_status">
            <el-radio-button label="pending">待沟通</el-radio-button>
            <el-radio-button label="in_progress">跟进中</el-radio-button>
            <el-radio-button label="closed">已结案</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="跟进备注">
          <el-input
            v-model="updateForm.notes"
            type="textarea"
            :rows="4"
            placeholder="记录本次跟进情况（会自动追加时间戳和操作人信息）"
          />
        </el-form-item>

        <el-form-item label="指派老师" v-if="isAdmin">
          <el-select v-model="updateForm.teacher_id" placeholder="选择负责老师" clearable style="width:100%">
            <el-option
              v-for="t in teachers"
              :key="t.id"
              :label="`${t.name}（${t.department || '未设置'}）`"
              :value="t.id"
            />
          </el-select>
        </el-form-item>
      </el-form>

      <div slot="footer">
        <el-button @click="updateDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="onSaveUpdate">保存</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { followupApi, statisticsApi, studentApi } from '../../api'
import { mapGetters } from 'vuex'

export default {
  name: 'FollowUpList',
  data() {
    return {
      tableData: [],
      loading: false,
      saving: false,
      filters: { status: '' },
      pagination: { page: 1, perPage: 20, total: 0 },
      summary: { pending: 0, in_progress: 0, closed: 0 },
      // 更新对话框
      updateDialogVisible: false,
      currentFollowup: null,
      updateForm: { follow_status: '', notes: '', teacher_id: null },
      teachers: []  // 老师列表（用于指派）
    }
  },
  computed: {
    ...mapGetters(['isAdmin'])
  },
  async created() {
    this.loadData()
    this.loadSummary()
    // 加载老师列表
    try {
      const res = await studentApi.listStaff()
      this.teachers = res.data.filter(u => u.role === 'teacher')
    } catch (e) {}
  },
  methods: {
    async loadData() {
      this.loading = true
      try {
        const params = {
          page: this.pagination.page,
          per_page: this.pagination.perPage
        }
        if (this.filters.status) params.status = this.filters.status
        const res = await followupApi.list(params)
        this.tableData = res.data.items
        this.pagination.total = res.data.total
      } finally {
        this.loading = false
      }
    },

    async loadSummary() {
      try {
        const res = await statisticsApi.followupSummary()
        this.summary = res.data
      } catch (e) {}
    },

    onPageChange(page) {
      this.pagination.page = page
      this.loadData()
    },

    openUpdateDialog(row) {
      this.currentFollowup = row
      this.updateForm = {
        follow_status: row.follow_status,
        notes: '',
        teacher_id: row.teacher_id
      }
      this.updateDialogVisible = true
    },

    async onSaveUpdate() {
      if (!this.currentFollowup) return
      this.saving = true
      try {
        await followupApi.update(this.currentFollowup.id, this.updateForm)
        this.$message.success('跟进记录已更新')
        this.updateDialogVisible = false
        this.loadData()
        this.loadSummary()
      } finally {
        this.saving = false
      }
    },

    viewReport(row) {
      this.$router.push(`/report/${row.report_id}`)
    },

    statusText(status) {
      return { pending: '待沟通', in_progress: '跟进中', closed: '已结案' }[status] || status
    },
    statusTagType(status) {
      return { pending: 'warning', in_progress: 'primary', closed: 'success' }[status] || ''
    }
  }
}
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-title { font-size: 22px; font-weight: 600; }
.header-actions { display: flex; align-items: center; }
.filter-card { margin-bottom: 16px; }
.pagination { margin-top: 16px; text-align: right; }
.student-info-box { padding: 12px; background: #F5F7FA; border-radius: 8px; }
</style>
