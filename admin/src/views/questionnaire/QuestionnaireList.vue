<!-- views/questionnaire/QuestionnaireList.vue - 问卷模板列表页 -->
<template>
  <div class="page-container">
    <!-- 页面标题和操作 -->
    <div class="page-header">
      <h2 class="page-title">问卷管理</h2>
      <el-button type="primary" icon="el-icon-plus" @click="$router.push('/questionnaire/create')">
        创建问卷
      </el-button>
    </div>

    <!-- 筛选栏 -->
    <el-card class="filter-card">
      <el-form inline>
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部状态" clearable @change="loadData">
            <el-option label="草稿" value="draft" />
            <el-option label="已发布" value="published" />
            <el-option label="已下架" value="archived" />
          </el-select>
        </el-form-item>
        <el-form-item label="分类">
          <el-input v-model="filters.category" placeholder="问卷分类" clearable @change="loadData" />
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 问卷表格 -->
    <el-card class="table-card">
      <el-table :data="tableData" v-loading="loading" stripe border>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="title" label="问卷标题" min-width="200" />
        <el-table-column prop="category" label="分类" width="120" />
        <el-table-column prop="question_count" label="题目数" width="80" align="center" />
        <el-table-column prop="estimated_minutes" label="预计时长" width="90" align="center">
          <template slot-scope="{ row }">{{ row.estimated_minutes }}分钟</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template slot-scope="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small">
              {{ statusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160" />
        <el-table-column label="操作" width="260" fixed="right">
          <template slot-scope="{ row }">
            <el-button size="mini" @click="onView(row)">查看</el-button>
            <el-button size="mini" type="primary" @click="onEdit(row)" :disabled="row.status !== 'draft'">
              编辑
            </el-button>
            <!-- 上架/下架按钮 -->
            <el-button
              v-if="row.status === 'draft'"
              size="mini" type="success"
              @click="onPublish(row)"
            >上架</el-button>
            <el-button
              v-if="row.status === 'published'"
              size="mini" type="warning"
              @click="onArchive(row)"
            >下架</el-button>
            <el-button
              v-if="row.status === 'draft'"
              size="mini" type="danger"
              @click="onDelete(row)"
            >删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
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
import { questionnaireApi } from '../../api'

export default {
  name: 'QuestionnaireList',
  data() {
    return {
      tableData: [],
      loading: false,
      filters: { status: '', category: '' },
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
        const res = await questionnaireApi.list({
          page: this.pagination.page,
          per_page: this.pagination.perPage,
          ...this.filters
        })
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

    onView(row) {
      this.$router.push(`/questionnaire/edit/${row.id}`)
    },

    onEdit(row) {
      this.$router.push(`/questionnaire/edit/${row.id}`)
    },

    async onPublish(row) {
      await this.$confirm(`确认将问卷《${row.title}》上架发布？上架后学生可在测评中使用。`, '上架确认', {
        confirmButtonText: '确认上架', cancelButtonText: '取消', type: 'warning'
      })
      await questionnaireApi.updateStatus(row.id, 'published')
      this.$message.success('问卷已上架')
      this.loadData()
    },

    async onArchive(row) {
      await this.$confirm(`确认将问卷《${row.title}》下架？下架后无法新建测评使用此问卷。`, '下架确认', {
        confirmButtonText: '确认下架', cancelButtonText: '取消', type: 'warning'
      })
      await questionnaireApi.updateStatus(row.id, 'archived')
      this.$message.success('问卷已下架')
      this.loadData()
    },

    async onDelete(row) {
      await this.$confirm(`确认删除问卷《${row.title}》？此操作不可撤销！`, '删除确认', {
        confirmButtonText: '确认删除', cancelButtonText: '取消', type: 'error'
      })
      await questionnaireApi.delete(row.id)
      this.$message.success('问卷已删除')
      this.loadData()
    },

    statusText(status) {
      return { draft: '草稿', published: '已发布', archived: '已下架' }[status] || status
    },
    statusTagType(status) {
      return { draft: 'info', published: 'success', archived: 'warning' }[status] || ''
    }
  }
}
</script>

<style scoped>
.page-container { padding: 0; }
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.page-title { font-size: 22px; font-weight: 600; }
.filter-card { margin-bottom: 16px; }
.table-card { border-radius: 12px; }
.pagination { margin-top: 16px; text-align: right; }
</style>
