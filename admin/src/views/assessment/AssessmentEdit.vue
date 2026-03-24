<!-- views/assessment/AssessmentEdit.vue - 发布测评页面 -->
<template>
  <div class="page-container">
    <div class="page-header">
      <el-button icon="el-icon-arrow-left" @click="$router.back()">返回</el-button>
      <h2 class="page-title">发布新测评</h2>
    </div>

    <el-card class="form-card">
      <el-form ref="form" :model="form" :rules="rules" label-width="120px" style="max-width: 680px;">
        <el-form-item label="测评标题" prop="title">
          <el-input v-model="form.title" placeholder="如：2024年春季心理健康普查" />
        </el-form-item>

        <el-form-item label="问卷模板" prop="template_id">
          <el-select v-model="form.template_id" placeholder="选择已发布的问卷模板" style="width:100%">
            <el-option
              v-for="t in templates"
              :key="t.id"
              :label="`${t.title}（${t.category || '无分类'}）`"
              :value="t.id"
            />
          </el-select>
          <div class="field-tip">只能选择状态为"已发布"的问卷</div>
        </el-form-item>

        <el-form-item label="测评对象">
          <el-radio-group v-model="targetType">
            <el-radio label="all">全体学生</el-radio>
            <el-radio label="department">指定院系</el-radio>
          </el-radio-group>
          <el-select
            v-if="targetType === 'department'"
            v-model="form.target_departments"
            multiple
            placeholder="选择院系"
            style="width:100%; margin-top: 8px;"
          >
            <el-option v-for="d in departments" :key="d" :label="d" :value="d" />
          </el-select>
        </el-form-item>

        <el-form-item label="答题时间">
          <el-date-picker
            v-model="timeRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            format="yyyy-MM-dd HH:mm"
            value-format="yyyy-MM-ddTHH:mm:ss"
          />
          <div class="field-tip">不设置则测评发布后立即开始，且无截止时间</div>
        </el-form-item>

        <el-form-item label="答题时限">
          <el-input-number v-model="form.max_duration_minutes" :min="0" placeholder="不限" />
          <span style="margin-left: 8px; color: #888;">分钟（0 = 不限时）</span>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="saving" @click="onSave">创建并保存为草稿</el-button>
          <el-button @click="$router.back()">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script>
import { assessmentApi, questionnaireApi } from '../../api'

export default {
  name: 'AssessmentEdit',
  data() {
    return {
      saving: false,
      templates: [],
      targetType: 'all',
      timeRange: null,
      departments: ['计算机学院', '理学院', '文学院', '工学院', '经济学院', '法学院', '医学院', '艺术学院'],
      form: {
        title: '',
        template_id: null,
        target_departments: [],
        start_time: null,
        end_time: null,
        max_duration_minutes: 0
      },
      rules: {
        title: [{ required: true, message: '请输入测评标题', trigger: 'blur' }],
        template_id: [{ required: true, message: '请选择问卷模板', trigger: 'change' }]
      }
    }
  },
  async created() {
    // 加载已发布的问卷列表
    const res = await questionnaireApi.list({ status: 'published', per_page: 100 })
    this.templates = res.data.items
  },
  methods: {
    async onSave() {
      await this.$refs.form.validate()
      this.saving = true
      try {
        const payload = {
          title: this.form.title,
          template_id: this.form.template_id,
          target_config: this.targetType === 'all'
            ? { type: 'all' }
            : { type: 'department', departments: this.form.target_departments },
          start_time: this.timeRange ? this.timeRange[0] : null,
          end_time: this.timeRange ? this.timeRange[1] : null,
          max_duration_minutes: this.form.max_duration_minutes || null
        }
        await assessmentApi.create(payload)
        this.$message.success('测评创建成功（当前为草稿状态，请在列表中发布）')
        this.$router.push('/assessment')
      } finally {
        this.saving = false
      }
    }
  }
}
</script>

<style scoped>
.page-header { display: flex; align-items: center; gap: 16px; margin-bottom: 20px; }
.page-title { font-size: 20px; font-weight: 600; }
.form-card { padding: 12px; }
.field-tip { font-size: 12px; color: #AAAAAA; margin-top: 4px; }
</style>
