<!-- views/student/StudentList.vue - 学生信息管理页面 -->
<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">学生管理</h2>
      <el-button type="primary" icon="el-icon-plus" @click="openDialog()">新增学生</el-button>
    </div>

    <!-- 搜索栏 -->
    <el-card class="filter-card">
      <el-form inline>
        <el-form-item>
          <el-input
            v-model="filters.keyword"
            placeholder="搜索姓名或学号"
            prefix-icon="el-icon-search"
            clearable
            @keyup.enter.native="loadData"
          />
        </el-form-item>
        <el-form-item label="院系">
          <el-input v-model="filters.department" placeholder="院系名称" clearable />
        </el-form-item>
        <el-form-item label="年级">
          <el-input v-model="filters.grade" placeholder="如：2022" clearable style="width:100px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">搜索</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 学生表格 -->
    <el-card class="table-card">
      <el-table :data="tableData" v-loading="loading" stripe border>
        <el-table-column prop="student_id" label="学号" width="120" />
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column prop="department" label="院系" width="150" />
        <el-table-column prop="grade" label="年级" width="80" align="center" />
        <el-table-column prop="phone" label="手机" width="130" />
        <el-table-column label="状态" width="80" align="center">
          <template slot-scope="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
              {{ row.is_active ? '正常' : '已禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160" />
        <el-table-column label="操作" width="200" fixed="right">
          <template slot-scope="{ row }">
            <el-button size="mini" type="primary" @click="openDialog(row)">编辑</el-button>
            <el-button
              size="mini"
              :type="row.is_active ? 'warning' : 'success'"
              @click="toggleActive(row)"
            >
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
            <el-button
              v-if="isSuperAdmin"
              size="mini" type="danger"
              @click="onDelete(row)"
            >删除</el-button>
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

    <!-- 新增/编辑对话框 -->
    <el-dialog
      :title="editingStudent ? '编辑学生信息' : '新增学生'"
      :visible.sync="dialogVisible"
      width="520px"
    >
      <el-form ref="studentForm" :model="form" :rules="formRules" label-width="90px">
        <el-form-item label="姓名" prop="name">
          <el-input v-model="form.name" placeholder="真实姓名" />
        </el-form-item>
        <el-form-item label="用户名" prop="username" v-if="!editingStudent">
          <el-input v-model="form.username" placeholder="登录用户名（通常为学号）" />
        </el-form-item>
        <el-form-item label="学号" prop="student_id">
          <el-input v-model="form.student_id" placeholder="学生学号" />
        </el-form-item>
        <el-form-item label="院系" prop="department">
          <el-input v-model="form.department" placeholder="所在院系" />
        </el-form-item>
        <el-form-item label="年级">
          <el-input v-model="form.grade" placeholder="如：2022" />
        </el-form-item>
        <el-form-item label="手机">
          <el-input v-model="form.phone" placeholder="手机号码" />
        </el-form-item>
        <el-form-item label="初始密码" v-if="!editingStudent" prop="password">
          <el-input v-model="form.password" type="password" placeholder="初始密码" show-password />
        </el-form-item>
        <el-form-item label="重置密码" v-else>
          <el-input v-model="form.new_password" type="password" placeholder="留空则不修改密码" show-password />
        </el-form-item>
      </el-form>
      <div slot="footer">
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="onSaveStudent">保存</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { studentApi } from '../../api'
import { mapGetters } from 'vuex'

export default {
  name: 'StudentList',
  data() {
    return {
      tableData: [],
      loading: false,
      saving: false,
      dialogVisible: false,
      editingStudent: null,
      filters: { keyword: '', department: '', grade: '' },
      pagination: { page: 1, perPage: 20, total: 0 },
      form: { name: '', username: '', student_id: '', department: '', grade: '', phone: '', password: '', new_password: '' },
      formRules: {
        name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
        username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
        password: [{ required: true, message: '请输入初始密码', trigger: 'blur' }]
      }
    }
  },
  computed: {
    ...mapGetters(['isSuperAdmin'])
  },
  created() {
    this.loadData()
  },
  methods: {
    async loadData() {
      this.loading = true
      try {
        const res = await studentApi.list({
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

    resetFilters() {
      this.filters = { keyword: '', department: '', grade: '' }
      this.loadData()
    },

    openDialog(student = null) {
      this.editingStudent = student
      this.form = student
        ? { ...student, new_password: '' }
        : { name: '', username: '', student_id: '', department: '', grade: '', phone: '', password: '' }
      this.dialogVisible = true
      this.$nextTick(() => this.$refs.studentForm?.clearValidate())
    },

    async toggleActive(row) {
      const action = row.is_active ? '禁用' : '启用'
      await this.$confirm(`确认${action}学生 ${row.name} 的账号？`, '确认', { type: 'warning' })
      await studentApi.update(row.id, { is_active: !row.is_active })
      this.$message.success(`账号已${action}`)
      this.loadData()
    },

    async onDelete(row) {
      await this.$confirm(`确认删除学生 ${row.name}（${row.student_id}）？此操作不可撤销！`, '删除确认', {
        confirmButtonText: '确认删除', cancelButtonText: '取消', type: 'error'
      })
      await studentApi.delete(row.id)
      this.$message.success('学生已删除')
      this.loadData()
    },

    async onSaveStudent() {
      await this.$refs.studentForm.validate()
      this.saving = true
      try {
        if (this.editingStudent) {
          await studentApi.update(this.editingStudent.id, this.form)
          this.$message.success('学生信息已更新')
        } else {
          await studentApi.create(this.form)
          this.$message.success('学生账号已创建')
        }
        this.dialogVisible = false
        this.loadData()
      } finally {
        this.saving = false
      }
    }
  }
}
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-title { font-size: 22px; font-weight: 600; }
.filter-card { margin-bottom: 16px; }
.pagination { margin-top: 16px; text-align: right; }
</style>
