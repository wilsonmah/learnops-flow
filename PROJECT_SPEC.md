# LearnOps Flow

**Learning Operations Automation Platform**

- 正式项目名称：**LearnOps Flow**
- GitHub 仓库建议名称：`learnops-flow`
- 简历项目标题：**LearnOps Flow | Learning Operations Automation Platform**

> 项目规格与开发交接文件 · V1.1 · 2026-10-25
>
> 状态：规划稿，尚未据此开发或验收。本文中的功能、性能、测试与部署均为要求或目标，不代表已经实现；不包含任何已经取得的商业结果。
>
> 使用方式：将本文件放到 GitHub 仓库根目录，命名为 `PROJECT_SPEC.md`，让 Codex 按第 18 节开始实施。

## 1. 项目定位与求职作品集目标

**一句话定位：**为学习与发展团队设计一个轻量的培训运营工具，串联课程排期、报名、出勤与完成记录、规则驱动的沟通以及运营报表，展示从业务流程到可运行软件的落地能力。

本项目是个人作品集中的培训运营原型，不是完整 LMS，也不作为企业生产系统宣传。核心故事是：识别重复工作和数据断点，制定流程与指标，用可验证的软件改善一个具体的运营场景。

### 1.1 信息来源与假设

- 本次需求明确了项目名称、四个 MVP 模块和 Python + Streamlit + SQLite 技术方向，本文据此展开。
- 原会话读取结果中的历史助手回答仅含引用占位符，无法确认原有职位清单或个人履历细节。因此，下表是与本项目匹配的**建议锚定职位**，不声称是原对话逐字确认的职位，也不判断个人录用概率。
- 默认场景：一个虚构组织、一个运营团队、小规模内部培训、单次授课场次；不假定用户具备未提供的工作经历或资历。
- 对外 README、应用主界面和演示建议使用英文；本规格用中文，便于开发沟通。

### 1.2 建议锚定职位及可展示证据

| 定位 | 建议职位名称（招聘名称可能不同） | 项目应提供的证据 |
|---|---|---|
| 核心 | Learning Operations Coordinator / Specialist | 排期、名单管理、提醒、出勤和完成状态闭环 |
| 核心 | Training Coordinator / Training Administrator | 报名规则、容量控制、取消、异常处理与标准流程 |
| 核心 | Learning & Development Coordinator | 学习项目协调、完成情况跟踪、运营汇报 |
| 相邻 | Learning Program Coordinator / Program Operations Coordinator | 场次进度、跨部门汇总、沟通记录与交付纪律 |
| 相邻 | LMS Administrator / Learning Systems Coordinator | 数据模型、记录维护、数据质量与可追溯性；明确未实现商业 LMS 管理经验 |
| 延伸 | Learning Operations Analyst / L&D Reporting Analyst | 指标口径、SQL、图表、可核验的分析结论 |

简历选择 1–2 个最贴合实际经历和招聘要求的定位。该项目本身不证明高级软件工程师、AI 工程师或 L&D 管理者资历。

### 1.3 成功标准

- 招聘方能在 60 秒内理解业务问题，在 3–5 分钟演示中看到完整工作流。
- 仓库能从干净环境按 README 启动，数据可重建，关键规则有测试证据。
- 作者能解释数据模型、指标分母、例外处理、隐私边界，以及为什么 V1 不做更复杂的架构。
- 如展示效率差异，只能来自记录了方法的模拟任务测量；不可将模拟效果写成真实组织成果。

## 2. 业务痛点与设计回应

以下是用于设计的假设场景，并非已完成用户研究的发现。

| 假设痛点 | 业务风险 | V1 回应 |
|---|---|---|
| 排期、报名和出勤散落在多个表格 | 重复登记、名单版本不一致 | 统一课程、场次、报名记录 |
| 逐人整理确认和提醒邮件 | 遗漏、重复沟通、无法追踪 | 模板、规则、待处理队列和模拟投递记录 |
| 报名人数与场次容量靠人工检查 | 超额报名或取消后名额未释放 | 事务内容量检查和状态规则 |
| “报名”“出席”“完成”混用 | 完成率失真、追踪对象错误 | 分开记录状态，公开指标口径 |
| 每次汇报都重新拼数据 | 指标不可复核、耗时 | 可筛选仪表板、明细与 CSV 导出 |

## 3. V1 MVP 范围与非目标

### 3.1 四个必做模块

1. **培训日历及报名**：课程目录；按日期查看培训场次；按课程、部门、状态筛选；创建与发布场次；报名、取消及容量控制。日历可先用按日分组的列表或表格实现，不要求复杂月历组件。
2. **出勤与完成记录**：按场次查看名单；逐人或批量保存出勤；按预先定义的规则记录完成；保留更正理由和变更日志。
3. **自动化沟通**：报名确认、培训前提醒、取消通知、完成后通知、未完成跟进；模板预览、队列、去重、失败重试和模拟投递。
4. **分析报表**：报名人数、出勤率、完成率、未完成情况和容量利用率；按部门、课程、时间筛选；图表、分母和明细可核验；CSV 导出。

### 3.2 V1 非目标

- 不建设视频托管、课件创作、SCORM/xAPI、考试引擎、证书系统或完整 LMS。
- 不接真实 HRIS、商业 LMS、企业邮箱、SSO、支付、Teams 或日历双向同步。
- 不实现真实身份认证、生产级权限、多租户或企业 SLA；角色切换仅为演示。
- 不发送真实邮件或短信，不安排真实员工，不接收真实员工数据。
- 不实现候补名单、周期性课程规则、多次课累计学时、培训预算或供应商管理。
- 不做自动学习推荐、AI 评分或基于学习记录的人员评价。
- 不用 V1 证明学习效果提升、业务绩效提升或合规达标；这些需要独立证据。
- 不为了作品集引入微服务、消息代理或复杂前端工程。

### 3.3 发布优先级

- **P0 / 必须完成**：四模块端到端流程、数据约束、模拟沟通、固定测试数据、关键规则测试、README、本地启动与演示说明。
- **P1 / 有余力再做**：日历视觉优化、额外图表、在线只读演示、短视频。
- P1 不得挤占 P0。公开部署暂未完成时，可用可复现的本地演示交付，但必须如实标记状态。

## 4. 角色、使用场景与用户故事

### 4.1 演示角色

| 角色 | 操作 | 边界 |
|---|---|---|
| Learning Operations Coordinator | 管理课程场次、报名、记录、沟通、导出 | 本地交互演示的主要角色 |
| Learner（合成员工） | 查看可报名场次、报名、取消、查看自己的记录 | 选择虚构身份，不等于登录或鉴权 |
| L&D Manager | 查看汇总、筛选、导出 | V1 只展示读取视图 |

公共只读部署关闭所有写操作、导入、队列执行和重置入口；本地可写演示中所有人物都是虚构人物。角色切换器必须标明 “Demo role — no authentication”。

### 4.2 用户故事与验收行为

| 编号 | 用户故事 | 预期结果 |
|---|---|---|
| US-01 | 作为协调员，我希望建立课程和具体场次 | 草稿可编辑；通过校验后才能发布 |
| US-02 | 作为学员，我希望按时间查找培训并报名 | 仅可报名未来的已发布场次，容量和重复报名检查生效 |
| US-03 | 作为学员，我希望取消报名 | 开课前取消释放名额；旧提醒被取消；可在符合规则时重新报名 |
| US-04 | 作为协调员，我希望课后一次录入整场出勤 | 校验所有行后原子保存；错误不产生部分更新 |
| US-05 | 作为协调员，我希望看到谁出席但还未完成 | 出勤和完成独立显示，可筛选未完成及到期状态 |
| US-06 | 作为协调员，我希望系统整理沟通事项 | 规则生成待处理消息，预览后执行模拟投递，重复执行不重复产生消息 |
| US-07 | 作为经理，我希望核验部门完成率 | 图表显示分子、分母、筛选范围，并能追溯到明细 |
| US-08 | 作为面试官，我希望快速理解作品 | 能按 README 启动，用演示脚本看到一条完整工作流 |

### 4.3 标准演示路径

1. 选择虚构部门与课程，例如 “Customer Support Onboarding”。
2. 创建并发布一个 10 人容量的未来场次。
3. 为虚构学员报名，查看确认消息预览；演示重复报名和满额被拒绝。
4. 使用明确标注的 Demo Clock 推进演示时间，生成培训前提醒并模拟投递。
5. 在场次结束后录入出勤；对需要人工确认的课程，将一名出席学员保留为未完成。
6. 推进到完成期限之后，展示未完成跟进消息。
7. 查看报表分子与分母、导出明细，再展示消息去重和审计记录。

## 5. 功能需求与状态规则

### FR-01 课程与场次

- 课程字段：名称、分类、简介、完成规则、是否启用。
- 场次字段：课程、讲师显示名、形式（online / in_person）、虚构地点或演示链接、开始与结束时间、显示时区、容量、完成期限、状态。
- 场次状态：`draft → scheduled → completed`；`draft/scheduled → cancelled`。
- `completed` 表示场次运营已收尾，不表示所有学员都已完成；只有结束时间到达后才能收尾。
- 容量为正整数；结束晚于开始；完成期限不早于结束；发布时开始时间必须晚于当前业务时钟。
- 草稿可完整编辑；发布后锁定课程、时间、地点、形式、完成规则和期限。V1 改期通过取消原场次并创建新场次实现，不自动迁移报名。
- 发布后可调整容量，但不得低于有效报名数；记录调整日志。
- 只允许删除没有任何报名历史的草稿；其他情况用取消或停用保留历史。

### FR-02 报名

- 同一学员与同一场次只有一条报名记录，通过状态变更实现取消与重新报名。
- 报名状态为 `registered / cancelled`；`registration_cycle` 初始为 1，每次重新报名加 1，用于区分新一轮通知。
- 只有启用的学员和课程、`scheduled` 场次、开课前且有名额时可报名。
- 容量检查和报名写入必须在同一写事务中执行，避免两个请求占用最后一个名额。
- 开课前允许取消并释放名额；开课后不允许追溯取消以改变报表分母，误录按审计更正流程处理并明确记录。
- 取消场次时，所有仍有效的报名转为 cancelled，记录 `session_cancelled` 原因，并撤销尚未处理的相关消息。
- 报名名单只从数据库读取，不依赖界面缓存中的旧计数。

### FR-03 出勤与完成

- 出勤：`unrecorded / present / absent / excused`。
- 完成：`not_completed / completed`。延期状态由期限和当前时钟推导，不另存一份易失真的 `overdue` 布尔值。
- 只允许对未取消场次的有效报名，在场次结束后记录出勤与完成。
- 课程完成规则在发布时复制到场次：`attendance_only` 或 `attendance_plus_confirmation`，后续课程编辑不回溯改变场次规则。
- `attendance_only`：present 自动对应 completed；其他出勤状态对应 not_completed。
- `attendance_plus_confirmation`：先 present，再由协调员确认完成；absent / excused / unrecorded 不得设为 completed。
- 完成时间不得早于场次结束或晚于当前业务时钟；可在到期后补记，作为迟完成展示。
- 更正必须有理由并保留前后值；撤销完成时撤销尚未投递的完成消息，已经模拟投递的记录保留。
- 每次从未完成变为完成，`completion_revision` 加 1，使重新确认的通知与旧通知可区分。
- 批量保存需全部成功或全部回滚，错误信息指向具体行。

### FR-04 自动化沟通

V1 的“自动化”指**规则生成与批量模拟处理**，不声称已接通真实邮件或有全天运行的后台调度。

| 消息类型 | 生成条件 | 处理时机 | 去重范围 |
|---|---|---|---|
| 报名确认 | 报名成功或重新报名 | 立即进入待处理队列 | 报名 ID + cycle + confirmation |
| 课前提醒 | 有效报名，场次未取消；进入开课前 24 小时窗口 | 规则检查时，且必须仍早于开课 | 报名 ID + cycle + reminder |
| 取消通知 | 学员取消或场次取消 | 立即入队；区别取消原因 | 报名 ID + cycle + cancellation |
| 完成通知 | 从未完成转为完成 | 立即入队 | 报名 ID + cycle + completion_revision + completion |
| 未完成跟进 | 期限已过，仍有效且未完成 | 规则检查时，每报名周期最多一封 | 报名 ID + cycle + followup |

- 开课前不足 24 小时的新报名也可收到一条提醒；开课后不补发已失效的课前提醒。
- 模板至少包含主题、正文、虚构学员名、课程、场次日期与时区；未知变量阻止生成，不保留未替换占位符。
- 消息状态：`pending / simulated_sent / failed / cancelled`。界面使用 “Simulated delivery”，不可写成真实已发送。
- 数据库对 `idempotency_key` 加唯一约束；重复点击、页面重跑和定时任务重复执行均不可产生重复消息。
- 报名、取消、完成变更及其消息写入在同一事务中执行；规则扫描也通过唯一键保证去重。
- 提供预览、Run rules、Process pending（模拟）、Retry failed 和消息日志；failed 总尝试次数上限为 3，超过后显示人工处理提示。
- 每次处理前重新验证业务状态：例如取消报名的提醒、已完成学员的跟进不再处理。迟于开课才执行的课前提醒标为 cancelled，并记原因。
- 使用确定性的 mock provider，可注入失败以验证重试；不包含 SMTP、真实 API 凭据或外部网络投递。
- 提供可重复执行的单次任务命令，供未来外部调度器调用；不能通过 Streamlit 页面重跑启动无限循环或后台调度器。
- Demo Clock 只控制业务测试时间；真实操作日志另记系统时间。公共部署不开放时间修改。

### FR-05 分析与导出

默认统计单位是“报名记录”，同一学员参加两个场次计为两条；另提供 distinct learners，不混用两者。

**统一筛选：**以场次开始时间在所选业务时区的日期为准；用户选择起止日，查询转换为 UTC 的左闭右开区间。课程、部门筛选作用于同一份明细，表格、图表和导出共用查询逻辑。

定义：

- `R`：所选范围内未取消场次的有效报名记录，排除 cancelled 报名。
- `E`：R 中 `end_at <= as_of` 的已结束场次报名，包含尚未手动收尾的 scheduled 场次。
- `P`：E 中出勤为 present 的报名。
- `C`：E 中完成为 completed 的报名。
- `D`：E 中完成期限严格早于 as_of 且仍未完成的报名。

| 指标 | 口径 | 展示要求 |
|---|---|---|
| 有效报名数 | `count(R)` | 同时列出独立学员数；取消数单独显示 |
| 出勤率 | `count(P) / count(E)` | excused 和 unrecorded 仍在分母内，分别显示数量 |
| 完成率 | `count(C) / count(E)` | 不把未来场次放入分母 |
| 到期未完成率 | `count(D) / count(E 中期限已过的报名)` | 分母只含期限已过记录，分母为零显示 N/A |
| 场次容量利用率 | 每场有效报名数 / 该场容量 | 汇总用总报名 / 各场容量之和，不取百分比均值 |
| 记录覆盖率 | E 中非 unrecorded 数量 / count(E) | 提醒读者低覆盖率会影响出勤率解释 |

- 容量利用率只支持日期和课程等场次维度筛选；部门筛选启用时隐藏该指标并说明原因，避免把共享容量误解为部门配额。
- 所有比率分母为零时显示 N/A；不把缺失记录默认解释成明确缺席。
- 提供按部门、课程和月份的统计，至少 2 张图：部门完成率、月度有效报名趋势。
- 表格展示分子/分母、as-of 时间、时区、是否合成数据；图表有文字说明，状态不只靠颜色。
- 导出 UTF-8 CSV，可含 BOM 以方便 Excel；表头稳定。文本单元格若以 `=`, `+`, `-`, `@` 等危险前缀开头，应做公式注入防护。
- V1 报表是按场次日期汇总的**当前状态**，不支持历史时点重建；Demo Clock 不能将当前数据库伪装成过去快照。

## 6. 非功能需求

| 编号 | 要求 | 验收方式 |
|---|---|---|
| NFR-01 可复现 | 锁定依赖，数据库可从脚本创建，固定 seed 可重建数据 | 干净目录按 README 完成启动 |
| NFR-02 正确性 | 外键、唯一键、状态检查、事务覆盖关键规则 | 数据层测试验证约束，不只测试按钮 |
| NFR-03 幂等性 | 页面重跑、重试、重复点击不重复报名或通知 | 相同动作执行两次，记录数量符合规则 |
| NFR-04 可维护 | UI、业务逻辑、查询和持久化分层 | 业务服务可脱离 Streamlit 测试 |
| NFR-05 可解释 | 指标显示口径，错误描述具体，审计记录可查看 | 按演示脚本人工核对 |
| NFR-06 性能目标 | 200 学员、24 场次、约 400 报名下，暖启动后主要查询争取在 2 秒内 | 在记录配置的机器上各测 10 次并报告中位数与最大值；不声称云端 SLA |
| NFR-07 可访问性 | 文本标签、键盘可达、足够对比、状态文字说明 | 手动检查主要路径，不宣称认证合规 |
| NFR-08 时间一致性 | 数据库保存 UTC；输入输出用明确 IANA 时区 | 夏令时歧义时间要求明确选择，不存在的时间拒绝 |
| NFR-09 安全边界 | 参数化查询；服务层执行公共只读限制；日志无密钥 | 直接调用写服务也被公共模式阻止 |
| NFR-10 部署边界 | 单实例轻量演示；公共数据可重建 | 文档声明无真实认证、无真实消息、无持久化保证 |

Streamlit 的脚本可能因交互重跑，Session State 用于会话交互状态，不替代数据库中的业务事实。参见 [Streamlit Session State 官方文档](https://docs.streamlit.io/develop/concepts/architecture/session-state)。

SQLite 适合此处的轻量本地数据存储；多写入者和扩展需求增加时评估客户端/服务端数据库。本项目选择来自使用规模假设，不构成容量承诺。参见 [SQLite 适用场景](https://www.sqlite.org/whentouse.html)。

## 7. 数据模型

### 7.1 关系

```text
departments 1 ── N learners
courses     1 ── N sessions
learners    1 ── N enrollments N ── 1 sessions
enrollments 1 ── N communication_jobs N ── 1 message_templates
audit_events ── 记录上述实体的变更
schema_migrations ── 记录数据库结构版本
```

出勤和完成直接存于 enrollments，适用于 V1 单次场次；多次课出勤明细留待 V2。

### 7.2 表与关键字段

| 表 | 关键字段 |
|---|---|
| `departments` | `id` PK，`name` UNIQUE |
| `learners` | `id` PK，`synthetic_employee_code` UNIQUE，`display_name`，`email` UNIQUE，`department_id` FK，`active`，`created_at` |
| `courses` | `id` PK，`title`，`category`，`description`，`completion_rule`，`active`，`created_at` |
| `sessions` | `id` PK，`course_id` FK，`facilitator_name`，`delivery_mode`，`location`，`starts_at_utc`，`ends_at_utc`，`timezone`，`capacity`，`completion_due_at_utc`，`completion_rule_snapshot`，`status`，`created_at`，`updated_at` |
| `enrollments` | `id` PK，`learner_id` FK，`session_id` FK，`department_id_at_registration` FK，`status`，`registration_cycle`，`registered_at`，`cancelled_at`，`cancellation_reason`，`attendance_status`，`completion_status`，`completed_at`，`completion_revision`，`updated_at` |
| `message_templates` | `id` PK，`message_type`，`version`，`subject_template`，`body_template`，`active`；UNIQUE(type, version) |
| `communication_jobs` | `id` PK，`enrollment_id` FK，`registration_cycle`，`message_type`，`template_id` FK，`idempotency_key` UNIQUE，`recipient_snapshot`，`subject_rendered`，`body_rendered`，`due_at_utc`，`status`，`attempt_count`，`last_error`，`created_at`，`processed_at`，`cancellation_reason` |
| `audit_events` | `id` PK，`actor_demo_role`，`entity_type`，`entity_id`，`action`，`before_json`，`after_json`，`reason`，`occurred_at_utc`（真实操作时间），`business_as_of_utc` |
| `schema_migrations` | `version` PK，`applied_at_utc` |

### 7.3 约束与持久化规则

- SQLite 每个连接启用外键；使用 CHECK 限定枚举、正容量和非负尝试次数，时间顺序和跨表规则也由服务层校验。
- enrollments 对 `(learner_id, session_id)` 建唯一约束；同一报名重新激活前必须重新检查容量、时间和状态。
- 首次报名保存部门快照，部门报表使用该快照；重新报名更新为当时部门，并保留审计历史。
- 对 `sessions.starts_at_utc`、`enrollments.session_id/status`、`communication_jobs.status/due_at_utc` 建索引。
- 数据库时间统一使用固定 UTC 格式，例如 `2026-10-25T14:00:00Z`；不混存本地时间文本。
- 更新报名、出勤、完成或消息状态时，同事务写入审计事件；角色标签用于演示追踪，不视为已验证身份。
- 消息保存模板和收件人的渲染快照，模板修改不改写已有历史。
- 报名写事务使用适当写锁，例如 `BEGIN IMMEDIATE`，配合短事务和有限等待；锁冲突返回可理解的重试信息。
- 不跨请求共享未经管理的数据库连接；不将数据库路径放入静态可下载目录。
- 重置数据只允许通过显式本地命令，目标仅为配置中的演示数据库；不在应用启动时覆写已有数据库。

## 8. 推荐技术栈与架构

| 层 | V1 选择 | 原因与边界 |
|---|---|---|
| 语言 | Python，建议以 3.12 为初始兼容基线 | 以实际环境和依赖验证为准，不声称是最新版本 |
| 界面 | Streamlit | 适合快速表达表单、表格和分析流程 |
| 数据库 | SQLite + Python `sqlite3` | 部署简单、方便理解 SQL 与事务 |
| 分析 | pandas + Streamlit 原生图表 | 优先减少依赖；确有需要再增加图表库 |
| 时间 | `datetime`、`zoneinfo`，必要时 `tzdata` | UTC 存储、显式时区与可注入时钟 |
| 模板 | 标准库严格变量替换 | 固定模板、拒绝未知变量，不执行用户模板代码 |
| 测试 | pytest；Streamlit AppTest 用于关键 UI 路径 | 以业务规则测试为主，少量界面冒烟测试 |
| 质量 | Ruff、GitHub Actions | 格式/静态检查与自动测试 |
| 依赖 | `pyproject.toml` + 固定版本 requirements 文件 | 实现时验证兼容组合，记录实际版本 |

```text
Streamlit pages
      ↓
Services（规则、只读边界、时钟、事务）
      ↓
Repositories / parameterized SQL
      ↓
SQLite

Rules runner → communication_jobs → Mock delivery provider
Reporting   → shared query functions → table / charts / CSV
```

不要把业务写入放在页面顶层、图表渲染函数或缓存函数中。Session State 可存筛选条件和 Demo Clock；数据库保存业务事实。数据写入后刷新有关查询，避免过期缓存掩盖结果。

## 9. 建议项目目录

```text
learnops-flow/
├── PROJECT_SPEC.md
├── README.md
├── app.py
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── .gitignore
├── .env.example
├── .streamlit/
│   └── config.toml
├── pages/
│   ├── 01_Overview.py
│   ├── 02_Training_Calendar.py
│   ├── 03_Enrollments.py
│   ├── 04_Attendance_Completion.py
│   ├── 05_Communications.py
│   └── 06_Reports.py
├── src/learning_ops/
│   ├── __init__.py
│   ├── config.py
│   ├── clock.py
│   ├── db.py
│   ├── repositories/
│   ├── services/
│   │   ├── scheduling.py
│   │   ├── enrollment.py
│   │   ├── completion.py
│   │   └── communications.py
│   ├── reporting/
│   │   ├── queries.py
│   │   └── exports.py
│   └── ui/
├── migrations/
│   └── 001_initial.sql
├── scripts/
│   ├── __init__.py
│   ├── init_db.py
│   ├── seed_demo.py
│   ├── run_communications.py
│   └── reset_demo.py
├── data/
│   └── .gitkeep
├── tests/
│   ├── conftest.py
│   ├── test_enrollment.py
│   ├── test_completion.py
│   ├── test_communications.py
│   ├── test_reporting.py
│   ├── test_read_only.py
│   └── test_app_smoke.py
├── docs/
│   ├── architecture.md
│   ├── metric_definitions.md
│   ├── demo_script.md
│   ├── decisions.md
│   ├── validation.md
│   └── screenshots/
└── .github/workflows/ci.yml
```

这是目标结构，不代表文件已存在。若为保持简单调整结构，记录原因；必须保留 UI 与业务逻辑的边界。忽略 `.venv/`、缓存、数据库及其 WAL/SHM 文件、`.env`、真实 secrets 和日志。

## 10. 合成数据与隐私约束

- 默认演示数据目标：200 名虚构学员、6 个虚构部门、8 门课程、24 个场次、约 400 条报名；生成器须尊重容量和状态规则，不以凑数破坏约束。
- 使用固定随机 seed，例如 42，并把 `base_date` 作为显式参数；相同参数产生相同逻辑数据。测试使用固定日期，普通演示可用当前日期重建新库。
- 覆盖过去与未来场次、已取消场次、不同完成规则、缺席、请假、未记录、迟完成、满额、消息失败与重试。
- 邮箱仅用明确虚构地址，如 `learner001@example.com`；不从公司通讯录、LinkedIn、客户资料或真实员工表复制数据。
- 不包含真实姓名、手机号、地址、员工编号、健康信息、薪资、绩效或其他个人敏感数据。
- 应用、README、导出说明和截图标注 “Synthetic data / Portfolio demo”。
- V1 不提供任意 CSV 上传入口；导出只来自合成数据集。未来加入上传前需另做访问、校验、保留与删除设计。
- 不把密钥写入 Git、截图或日志；V1 mock 沟通不需要 API 密钥。
- 数据库默认不提交；提交生成脚本与小型确定性测试夹具。公共演示使用可重建只读数据，不承诺保存访问者操作。
- 不宣称满足 GDPR、PIPEDA、SOC 2 等法规或认证要求。

## 11. 测试与验收标准

本节是待执行的验收清单，不是测试结果。实现后在 `docs/validation.md` 记录日期、环境、提交版本、命令、结果、限制及失败项。

### 11.1 必测业务用例

| 编号 | 场景 | 通过条件 |
|---|---|---|
| AC-01 | 正常报名、重复报名 | 一条有效报名、一条该周期确认消息；重复动作无额外记录 |
| AC-02 | 容量为 1，两个独立连接竞争报名 | 至多一人成功；无超额；失败有可理解提示 |
| AC-03 | 取消后重新报名 | 释放名额；旧提醒失效；cycle 递增且有新确认消息 |
| AC-04 | 未发布、已取消、已开课场次报名 | 全部拒绝且数据库不变 |
| AC-05 | 取消场次 | 有效报名取消、旧提醒撤销、每个相关周期仅一条取消通知 |
| AC-06 | 两种完成规则 | 出勤和完成映射正确；缺席不能完成；期限前后状态正确 |
| AC-07 | 批量出勤含一条非法数据 | 整批回滚，合法行也不被提前保存 |
| AC-08 | 同一时间重复执行沟通规则与处理 | 消息数量稳定；已模拟投递消息不重复处理 |
| AC-09 | mock 投递失败与重试 | 失败可见；成功后不再重试；总尝试上限 3 |
| AC-10 | 提醒生成后报名取消或开课 | 处理前复查并取消失效消息 |
| AC-11 | 完成撤销与重新确认 | 审计保留；待发旧通知撤销；新 revision 区分新通知 |
| AC-12 | 报表含未来、取消、未记录、请假、空集 | 使用固定夹具得到已知分子/分母，零分母显示 N/A |
| AC-13 | 日期边界与时区 | 日期筛选包含起点、排除下一日终点；夏令时歧义与不存在时间有明确处理 |
| AC-14 | CSV 与界面筛选一致 | 导出行集合与界面一致；危险公式前缀得到防护 |
| AC-15 | 重启与重跑 | 本地数据库记录保留；页面重跑不产生额外写入 |
| AC-16 | 公共只读模式 | UI 无写入口，直接调用写服务也拒绝，现有数据不变 |
| AC-17 | 审计与事务失败 | 成功变更有前后值；事务失败不留下孤立通知或日志 |
| AC-18 | 干净环境启动 | 安装、初始化、种子、测试、启动路径均按文档可执行 |

### 11.2 指标固定夹具

创建一组独立于随机种子的报表测试数据：

- 2 个已结束且期限已过的场次，容量各为 5，共 8 条有效报名。
- 其中 6 条 present、1 条 absent、1 条 unrecorded；6 条 present 中 5 条 completed。
- 预期：出勤率 6/8 = 75%；完成率 5/8 = 62.5%；到期未完成率 3/8 = 37.5%；记录覆盖率 7/8 = 87.5%；容量利用率 8/10 = 80%。
- 再添加一条取消报名、一场取消的培训，以及一个有 2 条报名、容量为 4 的未来场次。结束场次三项出勤/完成/到期指标仍按上述数值计算；全部日期范围的有效报名变为 10，容量利用率变为 10/14。
- 对其中一条 present 改为 excused，同时撤销其完成状态（若原已完成），验证分母保持 8，分子按新状态变化。

### 11.3 质量门槛

- 全部 P0 验收用例通过；关键业务服务有自动化测试，UI 至少有启动和主路径冒烟检查。
- CI 执行依赖安装、静态检查与测试，不连接外部邮箱或真实服务。
- 无硬编码密钥、无真实个人数据、无伪造测试徽章或完成状态。
- README 中命令与实际实现一致；截图必须来自运行后的真实界面，不用设计图冒充产品。
- 不以覆盖率百分比替代关键规则正确性；任何未执行或未通过的检查必须明确列出。

## 12. 14 天分期计划

这是个人项目的建议时间盒，不是工期承诺；按每日约 2–3 小时规划，可依据熟悉程度调整。时间不足时先移除 P1，不能用跳过关键测试来赶进度。

| 天 | 重点 | 当日可检查产物 |
|---|---|---|
| 1 | 明确业务流程、角色、P0 与指标 | 流程草图、README 骨架、假设清单 |
| 2 | 搭建项目和依赖 | 可启动空应用、配置、CI 骨架 |
| 3 | 数据库、迁移、时钟、种子 | 可重建数据库、外键和约束测试 |
| 4 | 课程、场次与日历 | 创建、发布、筛选、非法时间校验 |
| 5 | 报名、容量与取消 | 正常/重复/满额/竞争报名测试 |
| 6 | 名单、出勤与完成 | 批量更新、两类完成规则、审计 |
| 7 | 第一条完整业务流程 | 从创建场次到完成的可重复本地演示；修复集成问题 |
| 8 | 模板、沟通队列与规则 | 确认、提醒、取消、完成和跟进生成 |
| 9 | mock 处理、去重与重试 | 重复执行、过期消息、失败注入测试 |
| 10 | 报表查询和指标夹具 | 已知分子分母验证、筛选与明细一致 |
| 11 | 图表、CSV 与界面整理 | 至少两图、导出防护、空状态和错误提示 |
| 12 | 完整验收与性能测量 | validation 文档、核心测试和 UI 冒烟结果 |
| 13 | README、部署配置与演示素材 | 本地重现说明、只读配置；有余力部署公开演示 |
| 14 | 干净环境复核、演示与简历整理 | 3–5 分钟脚本、真实截图、证据支持的项目描述 |

阶段闸门：第 7 天核心数据流程未稳定，不扩展图表；第 12 天关键验收未通过，不标记 V1 完成；第 14 天只记录实际交付和待办。

## 13. README 要求

README 优先英文，面向招聘方，也要能让开发者启动项目。至少包含：

1. 名称、一句话问题定义、项目状态与合成数据声明。
2. 使用者、业务痛点，以及四个模块如何连接。
3. 真实界面截图或 GIF，附 3–5 分钟演示入口（如已有）。
4. 已实现功能与 Roadmap 分开列示；未实现的项目不能勾选完成。
5. 架构图、技术选择理由、数据库关系图。
6. 安装、配置、初始化、种子、运行和重置步骤。
7. 演示角色、Demo Clock、mock 消息和公共只读边界。
8. 指标定义及一个可手算的例子，说明不是学习效果评估。
9. 测试命令、真实验证记录链接、已知问题。
10. 部署限制、隐私说明、V2 路线。
11. 作者贡献与 AI 辅助开发说明：如实说明使用工具及本人完成的需求、设计、核验工作；不夸大独立编码比例。
12. 许可状态：公开前由仓库所有者确定；未选择时不要擅自声称开源许可。

### 13.1 预期本地命令接口

以下是**要求实现并验证的接口**，当前不代表这些命令已有对应程序。默认目标数据库为 `data/demo.sqlite3`。

```bash
python -m venv .venv
# 激活环境：Windows PowerShell 使用 .venv\Scripts\Activate.ps1
# macOS/Linux 使用 source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pip install -e . --no-deps
python -m scripts.init_db
python -m scripts.seed_demo --seed 42 --base-date 2026-10-25
python -m pytest
python -m ruff check .
python -m streamlit run app.py
```

单次沟通演示接口：

```bash
python -m scripts.run_communications --as-of 2026-10-25T14:00:00Z --mode mock
```

约定 `requirements-dev.txt` 引用运行依赖；运行依赖文件同时保证项目包可导入。种子脚本遇到已有数据应拒绝重复初始化并说明重置方法，不能静默清库。

建议配置项：`APP_MODE=local_demo|public_readonly`、`DATABASE_PATH`、`DISPLAY_TIMEZONE=America/Toronto`、`MESSAGE_PROVIDER=mock`。代码默认使用安全的公共只读模式，本地写入需显式设置 `APP_MODE=local_demo`；`.env.example` 不含秘密值。

## 14. 部署与演示要求

### 14.1 本地可写演示（P0）

- 单用户、合成数据、mock provider；允许完整交互与 Demo Clock。
- 关闭应用再启动，数据保留；恢复初始演示用显式重置命令。
- 提供故障排查：缺少依赖、数据库未初始化、数据库被锁定、端口占用、时间筛选为空。
- 演示记录应能够在没有外部 API、账号或网络投递的情况下完成。

### 14.2 公共只读演示（P1）

- 可评估 Streamlit Community Cloud，仓库须有入口文件和依赖配置；实际步骤参考 [官方部署文档](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app)。
- 公共演示只读取启动时生成的合成数据；初始化在只读应用开放前完成，不能给访问者提供初始化或重置按钮。
- 不把云端本地 SQLite 当成持久存储承诺。设计为实例重建时可恢复种子数据，不保存用户输入。
- 展示固定且明确的演示 as-of 时间，避免种子数据逐渐过期导致截图和指标无法复核。
- 所有写服务执行模式检查；隐藏按钮本身不算完成只读限制。
- 不在公共实例里运行常驻调度器；沟通页展示预生成的合成日志。
- 发布前核对平台当时支持的 Python 和依赖，不把云服务可用性写成保证。
- 未获得实际链接前用 “Deployment planned”，不放伪造 Demo 链接。

### 14.3 3–5 分钟讲解结构

- 0:00–0:40：谁遇到什么运营问题，为什么要把数据集中。
- 0:40–1:40：场次、报名与容量规则。
- 1:40–2:40：出勤、完成、模拟沟通及一个失败/重复执行例子。
- 2:40–3:40：报表分母、明细和导出。
- 3:40–5:00：架构选择、测试证据、限制和下一阶段。

提前准备本地演示和真实截图作为网络不稳定时的替代材料；截图应标明版本与数据来源。

## 15. 简历、GitHub 与面试呈现规范

### 15.1 事实边界

- 项目未完成：使用 “Designing / Building”，标注 “In progress”。
- 完成某项功能并验证后：才可使用 “Built / Implemented / Tested”。
- 沟通只接 mock 时必须写 “simulated notifications” 或 “mock delivery”，不能写已向员工自动发送邮件。
- 合成数据规模写 “synthetic learners / simulated enrollments”，不能暗示真实使用人数。
- 只有实际部署后才写 “Deployed”；只有实际通过测试才陈述通过情况。
- 不写 “reduced administrative work by 60%”“improved completion by 30%”“served 500 employees”等无证据成果。
- 若量化操作效率，需记录同一个模拟任务的人工基线、工具流程、样本次数、机器/环境及测量范围，并标注 “in a controlled synthetic-data demo”。不得外推至真实团队。

### 15.2 项目条目模板（按实际状态修改）

**未完成时可用：**

> LearnOps Flow — Learning Operations Automation Platform | Personal portfolio project (in progress)  
> Designing a Python, Streamlit, and SQLite prototype for training scheduling, enrollment tracking, completion records, and rule-based communication workflows using synthetic data.

**完成相应功能并验证后才可使用：**

> Built a learning operations prototype using Python, Streamlit, and SQLite to manage training schedules, enrollment, attendance, and completion records with synthetic data.  
> Implemented rule-based notification queues with duplicate prevention, retry handling, and simulated delivery.  
> Developed department and course reporting with documented metric definitions, filterable dashboards, and CSV exports.

从上述完成后模板中选取与目标职位最相关的 2–3 条，并删除尚未实现部分。不自动添加量化收益或商业背景。

### 15.3 面试应能解释的问题

- 为什么报名、出勤和完成必须分开？未来场次为什么不进入完成率分母？
- 同一学员取消再报名，为什么需要区分报名周期？
- 两人争抢最后一个名额，数据库如何保证不超额？
- 为什么演示角色切换不等于真正权限控制？
- 为什么 Streamlit 重跑不会重复发送提醒？实际消息平台为什么更复杂？
- 哪些地方使用了 AI 辅助，作者如何理解、修改并验证结果？
- 哪些是已实现事实，哪些只是计划，哪些需要真实业务验证？

## 16. V2 扩展路线

按真实需求逐步扩展，不以同时引入所有技术为目标。

| 阶段 | 触发条件 | 建议改动 | 进入下一阶段前的证据 |
|---|---|---|---|
| V2.1 API | 出现第二个前端或外部集成需求 | 把已有服务层接入 FastAPI；定义版本化接口、输入校验、错误与幂等规则；补充真实身份认证与权限 | API 合同测试、身份/权限测试；UI 不直接绕过 API 写入 |
| V2.2 PostgreSQL | 多用户写入、共享持久存储或多实例需求出现 | 迁移到 PostgreSQL；采用适合的 ORM/迁移工具；增加连接管理、事务隔离、备份恢复 | 数据迁移核对、并发测试、备份恢复演练 |
| V2.3 真实沟通与集成 | 有明确场景、可用账户及授权 | 外部调度/worker、事务 outbox、邮件服务、回执、错误分类、退避重试；再评估 LMS/日历 API | 测试环境端到端验证、凭据管理、数据权限与投递状态说明 |
| V2.4 AI 辅助 | 核心流程稳定，存在可评价的文本任务 | 生成提醒文案草稿、把聚合报表转为摘要、解释指标异常 | 人工审核、固定评测集、成本/延迟/事实一致性记录 |

AI 边界：

- 不自动更改出勤或完成状态，不对员工绩效进行排名或做雇佣决策。
- 初期只使用合成或聚合数据；不把真实个人学习记录直接提交给外部模型。
- 摘要需引用对应指标和时间范围，不得虚构原因、收益或趋势。
- AI 输出先作为草稿，审核后才可被正式采用；未来真实发送另需可靠的权限与发布流程。
- 不将未经执行的 AI 路线写成 “AI-powered platform”。

## 17. 决策记录与待验证假设

| 决策 | 当前选择 | 何时重审 |
|---|---|---|
| 产品范围 | 培训运营闭环 | 有明确内容交付或多课次需求时 |
| 完成机制 | 单次出勤 / 出勤加人工确认 | 有外部考试或 LMS 结果来源时 |
| 数据库 | 本地 SQLite | 需要多实例、共享持久存储或更多并发写入时 |
| 消息 | 规则队列 + mock | 有真实投递场景和授权后 |
| 权限 | 本地演示角色 + 公共只读 | 要使用真实组织数据之前 |
| 统计 | 当前状态、场次日期归属 | 需要历史时点、报名事件趋势或纵向效果评估时 |
| 求职定位 | 本文件列出的建议职位 | 获得原职位清单或具体招聘描述后 |

每次改变核心规则，在 `docs/decisions.md` 写明原因、影响和需要更新的验收用例。新需求先判断是否属于 V1，再实现。

## 18. 给 Codex 的实施指令

将以下内容作为实施约定；本文件本身不授权发送真实消息、处理真实员工数据、付费或发布到外部服务。

```text
请按仓库根目录 PROJECT_SPEC.md 实现 LearnOps Flow（Learning Operations Automation Platform）V1。

目标：交付可复现、可解释、可演示的培训运营作品集原型，完成 P0 四模块闭环。

开始前：
1. 阅读仓库现有文件及适用的仓库说明，保留已有工作，不盲目重建。
2. 检查 Python 和依赖环境，记录兼容版本，不假设任何功能已存在。
3. 将规格拆分成可验证的小阶段，明确每阶段的输入、产物和验收用例。
4. 无需为一般实现细节逐项提问；采用符合规格的简单选择并记录。
   只有缺失信息实质影响范围、真实数据、外部发布或不可逆操作时才提出问题。

实现顺序：
A. 配置、可注入时钟、数据库迁移、合成种子及基本约束。
B. 场次、报名、容量事务、取消与审计；先验证一条完整数据路径。
C. 出勤、完成规则、批量原子更新和更正记录。
D. 模板、队列、规则扫描、mock provider、去重和重试。
E. 共用报表查询、固定指标夹具、图表和安全 CSV 导出。
F. 公共只读边界、错误提示、README、演示脚本和验收文档。

实现约束：
- 使用 Python + Streamlit + SQLite，UI 与业务逻辑分层。
- 只使用合成数据；真实通知、真实认证、API、PostgreSQL 和 AI 不属于 V1。
- 业务状态存数据库；防止 Streamlit 页面重跑造成重复写入。
- 外键、唯一键、事务、参数化 SQL、时间规则和幂等约束必须落地。
- 公共只读限制必须在服务层生效，不能只隐藏按钮。
- 不偷偷降低验收标准，不创建只验证实现表象的测试来充数。
- 不把大批无关功能加入 MVP；有价值的新想法放入 Roadmap。

验证与交付：
- 每阶段运行相关检查；完成前执行全部 P0 验收和一次干净环境重现。
- 出现错误先查明原因并修复，保留实际失败或未执行检查的记录。
- docs/validation.md 记录环境、提交版本、命令、结果、性能测量和限制。
- 只用真实运行界面生成截图；所有数据和模拟沟通清楚标记。
- 更新 README 的完成状态，让功能列表、测试记录和演示内容与代码一致。
- 最后报告已完成内容、启动方法、验证结果、已知问题和下一步。
- 不声称未发生的开发、测试、部署、实际使用人数或商业效果。
```

## 19. V1 完成定义（Definition of Done）

- [ ] 四个 P0 模块实现，并能按标准路径连续演示。
- [ ] 报名容量、重复记录、取消、完成、通知去重和重试规则通过验收。
- [ ] 指标固定夹具得到预期结果，图表和 CSV 使用一致数据范围。
- [ ] 所有数据均为合成，mock 投递标识清晰，公共模式只读限制生效。
- [ ] 干净环境可安装、初始化、生成数据、运行测试和启动应用。
- [ ] README、架构、指标口径、决策、演示与验证文档齐全且与实际一致。
- [ ] 简历条目仅包含实际实现并验证的内容。
- [ ] 未完成项、已知限制与 V2 路线明确列出。

以上复选框初始全部未勾选。只有对应实现及证据已经存在时才能更新。

## 20. 文档更新与 GitHub 同步约定

- 每次完成本地文件更新后，向用户提供可查看或下载的新版文件，并询问是否同步到 GitHub。
- 未获得针对本次更新的同步授权前，不自动提交或推送；用户已经明确授权的特定 GitHub 修改可直接执行。
- 同步时说明目标仓库、文件和实际结果；未成功同步时不得声称 GitHub 已更新。
- 2026-10-25：规格版本更新为 V1.1，正式命名为 LearnOps Flow；更新标题、目录示例、简历标题和 Codex 实施指令。产品范围未变。
