<!-- views/questionnaire/QuestionnaireEdit.vue - 问卷创建/编辑页面 -->
<template>
  <div class="page-container">
    <div class="page-header">
      <el-button icon="el-icon-arrow-left" @click="$router.back()">返回</el-button>
      <h2 class="page-title">{{ isEdit ? '编辑问卷' : '创建问卷' }}</h2>
    </div>

    <el-row :gutter="20">
      <!-- 左侧：问卷基本信息 -->
      <el-col :span="10">
        <el-card class="form-card">
          <div slot="header"><b>基本信息</b></div>
          <el-form ref="baseForm" :model="form" :rules="rules" label-width="100px">
            <el-form-item label="问卷标题" prop="title">
              <el-input v-model="form.title" placeholder="如：PHQ-9抑郁量表" />
            </el-form-item>
            <el-form-item label="问卷分类" prop="category">
              <el-select v-model="form.category" placeholder="选择或输入分类" allow-create filterable>
                <el-option label="抑郁筛查" value="抑郁筛查" />
                <el-option label="焦虑筛查" value="焦虑筛查" />
                <el-option label="综合心理健康" value="综合心理健康" />
                <el-option label="压力评估" value="压力评估" />
              </el-select>
            </el-form-item>
            <el-form-item label="问卷说明">
              <el-input v-model="form.description" type="textarea" :rows="3" placeholder="向学生展示的问卷说明文字" />
            </el-form-item>
            <el-form-item label="预计时长">
              <el-input-number v-model="form.estimated_minutes" :min="1" :max="120" />
              <span style="margin-left: 8px; color: #888;">分钟</span>
            </el-form-item>

            <!-- 计分规则 -->
            <el-form-item label="计分规则">
              <div class="scoring-rules">
                <div v-for="(range, level) in form.scoring_rules['总分']" :key="level" class="rule-row">
                  <el-input v-model="scoringLevels[level]" placeholder="等级名" style="width:100px" />
                  <span>：</span>
                  <el-input v-model="form.scoring_rules['总分'][level]" placeholder="如 0-9 或 20+" style="width:120px" />
                  <el-button icon="el-icon-delete" type="text" @click="removeScoringLevel(level)" />
                </div>
                <el-button size="mini" icon="el-icon-plus" @click="addScoringLevel">添加等级</el-button>
              </div>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- 右侧：题目列表 -->
      <el-col :span="14">
        <el-card class="form-card">
          <div slot="header" style="display:flex; justify-content:space-between; align-items:center;">
            <b>题目列表（共 {{ form.questions.length }} 题）</b>
            <el-button type="primary" size="small" icon="el-icon-plus" @click="addQuestion">
              添加题目
            </el-button>
          </div>

          <!-- 题目列表 -->
          <div v-if="form.questions.length === 0" class="empty-tip">
            暂无题目，点击右上角"添加题目"按钮开始创建
          </div>

          <el-collapse v-model="openQuestions">
            <el-collapse-item
              v-for="(q, index) in form.questions"
              :key="index"
              :name="index"
              :title="`第 ${index + 1} 题：${q.content || '（未填写）'}`"
            >
              <el-form label-width="80px">
                <el-form-item label="题目内容">
                  <el-input v-model="q.content" type="textarea" :rows="2" placeholder="输入题目内容" />
                </el-form-item>
                <el-form-item label="题目类型">
                  <el-radio-group v-model="q.question_type">
                    <el-radio label="single_choice">单选题</el-radio>
                    <el-radio label="multiple_choice">多选题</el-radio>
                  </el-radio-group>
                </el-form-item>
                <el-form-item label="所属维度">
                  <el-input v-model="q.dimension" placeholder="可选，如：情绪症状" style="width:200px" />
                </el-form-item>
                <el-form-item label="选项">
                  <div v-for="(opt, oi) in q.options" :key="oi" class="option-row">
                    <el-input v-model="opt.label" placeholder="标签" style="width:60px" />
                    <el-input v-model="opt.text" placeholder="选项文字" style="width:200px; margin: 0 8px;" />
                    <el-input-number v-model="opt.score" placeholder="分值" :min="0" style="width:100px" />
                    <el-button type="text" icon="el-icon-delete" @click="removeOption(q, oi)" />
                  </div>
                  <el-button size="mini" @click="addOption(q)">+ 添加选项</el-button>
                </el-form-item>
                <el-form-item>
                  <el-button type="danger" size="mini" @click="removeQuestion(index)">删除此题</el-button>
                </el-form-item>
              </el-form>
            </el-collapse-item>
          </el-collapse>
        </el-card>
      </el-col>
    </el-row>

    <!-- 底部操作 -->
    <div class="bottom-actions">
      <el-button @click="$router.back()">取消</el-button>
      <el-button type="primary" :loading="saving" @click="onSave">
        {{ isEdit ? '保存修改' : '创建问卷' }}
      </el-button>
    </div>
  </div>
</template>

<script>
import { questionnaireApi } from '../../api'

export default {
  name: 'QuestionnaireEdit',
  data() {
    return {
      isEdit: false,
      saving: false,
      openQuestions: [],
      form: {
        title: '',
        description: '',
        category: '',
        estimated_minutes: 10,
        scoring_rules: { '总分': { '正常': '0-4', '轻度': '5-9', '中度': '10-19', '重度': '20+' } },
        questions: []
      },
      scoringLevels: {},
      rules: {
        title: [{ required: true, message: '请输入问卷标题', trigger: 'blur' }]
      }
    }
  },
  async created() {
    if (this.$route.params.id) {
      this.isEdit = true
      await this.loadTemplate(this.$route.params.id)
    }
  },
  methods: {
    async loadTemplate(id) {
      const res = await questionnaireApi.get(id)
      const t = res.data
      this.form = {
        title: t.title,
        description: t.description || '',
        category: t.category || '',
        estimated_minutes: t.estimated_minutes || 10,
        scoring_rules: t.scoring_rules || { '总分': {} },
        questions: t.questions || []
      }
    },

    addQuestion() {
      const q = {
        content: '',
        question_type: 'single_choice',
        dimension: '',
        order_num: this.form.questions.length + 1,
        options: [
          { label: 'A', text: '', score: 0 },
          { label: 'B', text: '', score: 1 },
          { label: 'C', text: '', score: 2 },
          { label: 'D', text: '', score: 3 }
        ]
      }
      this.form.questions.push(q)
      this.openQuestions = [this.form.questions.length - 1]
    },

    removeQuestion(index) {
      this.form.questions.splice(index, 1)
    },

    addOption(q) {
      const labels = ['A', 'B', 'C', 'D', 'E', 'F']
      q.options.push({ label: labels[q.options.length] || String(q.options.length + 1), text: '', score: 0 })
    },

    removeOption(q, index) {
      q.options.splice(index, 1)
    },

    addScoringLevel() {
      this.$set(this.form.scoring_rules['总分'], `等级${Object.keys(this.form.scoring_rules['总分']).length + 1}`, '')
    },

    removeScoringLevel(level) {
      this.$delete(this.form.scoring_rules['总分'], level)
    },

    async onSave() {
      await this.$refs.baseForm.validate()
      this.saving = true
      try {
        if (this.isEdit) {
          await questionnaireApi.update(this.$route.params.id, this.form)
          this.$message.success('问卷已更新')
        } else {
          await questionnaireApi.create(this.form)
          this.$message.success('问卷创建成功')
        }
        this.$router.push('/questionnaire')
      } finally {
        this.saving = false
      }
    }
  }
}
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}
.page-title { font-size: 20px; font-weight: 600; }
.form-card { margin-bottom: 20px; }
.empty-tip { text-align: center; color: #AAAAAA; padding: 40px 0; }
.option-row { display: flex; align-items: center; margin-bottom: 8px; }
.scoring-rules { }
.rule-row { display: flex; align-items: center; margin-bottom: 8px; gap: 4px; }
.bottom-actions {
  background: #FFFFFF;
  padding: 16px 20px;
  border-radius: 8px;
  text-align: right;
  margin-top: 8px;
  box-shadow: 0 -2px 8px rgba(0,0,0,0.06);
}
</style>
