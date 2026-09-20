# AI 消息速览

AI 消息速览是一个本地优先的 AI 信息采集、审核、知识卡片、简报和 PPT 更新辅助系统。

当前推荐工作流是：

```text
本地服务器：开发、测试、偏好模型训练、数据分析
云服务器：网页体验、定时抓取验证、人工审核、反馈收集
```

核心页面：

```text
/              工作台，生成今日卡片、查看进度、审核队列、来自媒体
/cards         知识卡片列表、分页、审核、删除
/briefs        生成本日/本周/自定义时间段简报
/ppt           PPT 更新建议、建议审核、讲稿编辑、PPT 报告管理
/sources       消息源管理、Topic 管理、建议新增消息源
/trends        趋势关键词
/preferences   偏好学习数据与特征状态
/login         登录页
```

## 目录结构

```text
config/                         应用配置和消息源配置
data/                           运行数据、反馈、特征、建议源
data/feedback/events.jsonl      人工反馈事件日志
data/features/*.jsonl           偏好学习特征文件
docs/                           部署和使用说明
notes/cards/                    知识卡片 Markdown
notes/inbox/                    候选报告、简报、PPT 建议等输出
notes/trash/                    被删除卡片
ppt/                            PPT 讲稿、结构节点、报告配置
scripts/                        本地/云端部署、定时任务脚本
src/ai_daily_update/            应用源码
tests/                          测试
```

## 本地环境

首次创建环境：

```bash
cd /home/lsh/Documents/AI-daily-update
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
cp config/sources.example.yaml config/sources.yaml
```

日常进入环境：

```bash
cd /home/lsh/Documents/AI-daily-update
. .venv/bin/activate
```

`.env` 至少需要包含：

```env
OPENAI_API_KEY=...
OPENAI_BASE_URL=...
OPENAI_MODEL=...

AI_DAILY_ADMIN_USERNAME=...
AI_DAILY_ADMIN_PASSWORD=...
AI_DAILY_SESSION_SECRET=...
```

注意：

```text
.env 不进入 git，也不会被部署脚本同步到云端。
本地和云服务器应分别维护自己的 .env。
API Key 或登录密码如果泄露，应立即重置。
```

## 本地运行

启动网页服务：

```bash
.venv/bin/ai-daily serve --host 0.0.0.0 --port 8001
```

访问：

```text
本机：http://127.0.0.1:8001/
局域网：http://192.168.5.6:8001/
```

如果只希望本机访问：

```bash
.venv/bin/ai-daily serve --host 127.0.0.1 --port 8001
```

检查服务是否监听：

```bash
ss -ltnp '( sport = :8001 )'
```

## 常用 CLI

健康检查：

```bash
.venv/bin/ai-daily doctor
```

生成今日候选和卡片：

```bash
.venv/bin/ai-daily daily
```

预跑候选，不真正写入最终卡片：

```bash
.venv/bin/ai-daily daily --dry-run
```

重建索引：

```bash
.venv/bin/ai-daily index
```

生成简报：

```bash
.venv/bin/ai-daily brief --from-date 2026-07-01 --to-date 2026-07-08
```

生成自动消息源建议：

```bash
.venv/bin/ai-daily propose-sources
```

抽取偏好学习特征：

```bash
.venv/bin/ai-daily extract-features --surface all
```

也可以按类型抽取：

```bash
.venv/bin/ai-daily extract-features --surface cards
.venv/bin/ai-daily extract-features --surface ppt_suggestions
.venv/bin/ai-daily extract-features --surface source_proposals
```

## 测试

完整测试：

```bash
.venv/bin/python -m pytest
```

常用局部测试：

```bash
.venv/bin/python -m pytest tests/test_web_auth.py
.venv/bin/python -m pytest tests/test_web_ppt.py
.venv/bin/python -m pytest tests/test_preference_features.py
```

当前基线：

```text
198 passed
```

## 工作台流程

工作台是日常入口。

推荐使用方式：

```text
1. 点击“生成今日卡片”
2. 查看“整理进度”
3. 在“审核队列”处理一手信源卡片
4. 在“来自媒体”处理二手信源、自媒体和中文媒体卡片
5. 接受 / 拒绝 / 稍后处理
6. 已接受内容进入后续简报和 PPT 更新流程
```

当前逻辑：

```text
一手信源每日最多入选 20 张
来自媒体每日单独最多入选 5 张
候选超过 1 天未审核时，可进入自动评估/审核流程
```

## 知识卡片

卡片页面：

```text
/cards
```

功能：

```text
分页展示，默认每页 20 条
按状态筛选
按通道筛选
接受 / 拒绝 / 稍后处理
已接受卡片可删除，删除后进入 notes/trash/
```

卡片主要数据位置：

```text
notes/cards/
notes/trash/
```

## 简报

页面：

```text
/briefs
```

支持：

```text
本日简报
本周简报
自定义时间段简报
```

简报生成主要使用已接受卡片。

## PPT 更新

页面：

```text
/ppt
```

功能：

```text
生成 PPT 更新建议
显示生成进度
审核建议：采纳建议 / 标记已写入 PPT / 暂不更新
按标题层级编辑讲稿
上传或创建新的 PPT 报告
查看结构节点和最近 PPT 更新建议
```

PPT 数据位置：

```text
ppt/decks.yaml
ppt/decks/<deck_id>/manuscript.md
ppt/decks/<deck_id>/nodes.yaml
ppt/decks/<deck_id>/structured.csv
ppt/backups/
```

生成 PPT 建议时应注意：

```text
建议要具体可操作，例如“第 XX 页某句话改为某句话”
同一证据卡片匹配多个相近位置时，应尽量合并建议
二级标题下没有三级标题时，三级标题应为空，而不是重复二级标题
```

## 消息源管理

页面：

```text
/sources
```

功能：

```text
查看消息源
启用 / 停用消息源
按主题、关键词、通道筛选
新增 Topic
为每个消息源设置主 topic 和副 topic
查看自动/手工建议新增消息源
```

配置文件：

```text
config/sources.yaml
```

自动建议源输出：

```text
data/source_proposals.json
```

## 趋势关键词

页面：

```text
/trends
```

趋势关键词需要考虑中英文和同义合并，例如：

```text
推理 / reasoning
智能体 / agent
具身智能 / embodied AI
人形机器人 / humanoid robot
自动驾驶 / autonomous driving
```

## 偏好学习

页面：

```text
/preferences
```

当前实现：

```text
记录人工反馈事件
抽取 SVM 可用特征 v1
暂不直接训练和使用 SVM
预留后续模型训练/加载接口
```

反馈事件：

```text
data/feedback/events.jsonl
```

特征文件：

```text
data/features/cards.jsonl
data/features/ppt_suggestions.jsonl
data/features/source_proposals.jsonl
```

手动抽取：

```bash
.venv/bin/ai-daily extract-features --surface all
```

推荐训练策略：

```text
云端负责收集反馈
本地定时拉回反馈和特征
本地训练 SVM / LogisticRegression / LinearSVC
训练好的模型再同步到云端做推理
```

后续模型文件建议位置：

```text
data/models/card_preference.joblib
data/models/ppt_suggestion_preference.joblib
data/models/source_proposal_preference.joblib
```

## 本地到云端部署

项目推荐：

```text
本地开发
本地测试
同步代码到云端
云端验证和体验
云端反馈拉回本地
本地继续开发和训练
```

云端部署说明详见：

```text
docs/cloud-deploy.md
```

公开 JSON API 说明详见：

```text
docs/api.md
```

首次部署前，建议本地配置 SSH alias：

```sshconfig
Host aliyun-ai
  HostName 47.116.30.84
  User lsh
  Port 22
```

部署：

```bash
AI_DAILY_REMOTE=aliyun-ai scripts/deploy_cloud.sh
```

默认部署只同步代码和非运行态配置，不会覆盖云端运行数据。以下内容默认保留云端版本：

```text
data/
notes/
ppt/
config/sources.yaml
```

这些目录/文件包含卡片、审核状态、已拒绝/删除记录、反馈日志、偏好学习特征、PPT 讲稿、简报、消息源启停和 topic 管理等运营状态。首次初始化云端、且确认要用本地状态覆盖云端时，才使用：

```bash
AI_DAILY_REMOTE=aliyun-ai \
AI_DAILY_SYNC_STATE=1 \
scripts/deploy_cloud.sh
```

如果远端目录不是默认值：

```bash
AI_DAILY_REMOTE=aliyun-ai \
AI_DAILY_REMOTE_DIR=/home/lsh/AI-daily-update \
scripts/deploy_cloud.sh
```

安装云端 systemd 服务：

```bash
AI_DAILY_REMOTE=aliyun-ai scripts/install_cloud_service.sh
```

云端服务状态：

```bash
ssh aliyun-ai
sudo systemctl status ai-daily
journalctl -u ai-daily -n 100 --no-pager
```

云端临时访问：

```text
http://47.116.30.84:8001/
```

正式公网访问建议：

```text
https://ai.cheesepanini.fun/
```

正式部署推荐结构：

```text
Caddy/Nginx: 80/443
ai-daily: 127.0.0.1:8001
公网不开放 8001
```

## 云端状态拉回本地

手动拉回：

```bash
AI_DAILY_REMOTE=aliyun-ai scripts/pull_cloud_state.sh
```

拉回内容：

```text
config/sources.yaml
data/feedback/
data/features/
data/manual_urls.txt
data/ppt_source_suggestions.md
data/source_proposals.json
notes/briefs/
notes/cards/
notes/inbox/
notes/trash/
ppt/
```

这些数据用于：

```text
保留云端审核记录
同步云端卡片状态
积累偏好学习训练数据
```

## 定时拉回偏好学习数据

推荐使用 systemd user timer。

前提：本地到云端需要 SSH 免密登录。

测试：

```bash
ssh aliyun-ai
```

如果仍然要求密码，先配置：

```bash
ssh-copy-id aliyun-ai
```

安装 timer：

```bash
mkdir -p ~/.config/systemd/user
cp scripts/systemd/ai-daily-pull-cloud-state.service ~/.config/systemd/user/
cp scripts/systemd/ai-daily-pull-cloud-state.timer ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now ai-daily-pull-cloud-state.timer
systemctl --user list-timers | grep ai-daily
```

手动执行一次：

```bash
systemctl --user start ai-daily-pull-cloud-state.service
```

查看日志：

```bash
journalctl --user -u ai-daily-pull-cloud-state.service -n 100 --no-pager
```

cron 模板：

```text
scripts/cron/ai-daily-pull-cloud-state.cron
```

## 本地定时任务

注意：网页服务（`ai-daily serve` / systemd `ai-daily-web.service`）内置了一个调度线程，会按 `config/app.yaml` 里 `daily.schedule` 配置的时间点自动触发生成。如果你同时按下文安装了 systemd timer 或 cron，两套机制会在同一时间点各自触发一次 `daily` 任务——虽然文件锁保证不会互相破坏数据，但会导致同一时段被触发两次（浪费一次采集/LLM 调用）。二者选一即可：

- 只用网页服务：保持 `daily.schedule.enabled: true`，不要再安装下面的 systemd timer / cron。
- 只用系统定时任务：把 `config/app.yaml` 里的 `daily.schedule.enabled` 改成 `false`，再安装 systemd timer 或 cron。

本地 daily 脚本：

```text
scripts/ai-daily-update.sh
scripts/ai-daily-dry-run.sh
```

systemd 示例：

```text
scripts/systemd/ai-daily-update.service
scripts/systemd/ai-daily-update.timer
```

cron 示例：

```text
scripts/cron/ai-daily-update.cron
```

安装 systemd user timer：

```bash
mkdir -p ~/.config/systemd/user
cp scripts/systemd/ai-daily-update.service ~/.config/systemd/user/
cp scripts/systemd/ai-daily-update.timer ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now ai-daily-update.timer
systemctl --user list-timers | grep ai-daily
```

## Git 与同步边界

当前原则：

```text
代码以本地为准
.env 永不同步
.venv 永不同步
云端反馈和审核状态要拉回本地
偏好模型训练在本地完成
训练好的模型后续再同步到云端
```

已忽略：

```text
.env
.venv/
__pycache__/
.pytest_cache/
data/kb.sqlite
data/logs/
data/raw/
data/cache/
ppt/backups/
```

查看 git 状态：

```bash
git status --short --ignored
```

## 常用排障

### 登录页打不开

检查服务：

```bash
sudo systemctl status ai-daily
ss -ltnp | grep 8001
curl -I http://127.0.0.1:8001/
```

### 云端公网打不开

检查：

```text
阿里云安全组是否放行端口
服务器 UFW 是否放行端口
服务是否监听 0.0.0.0 或是否有 Caddy 反向代理
```

UFW：

```bash
sudo ufw status numbered
```

临时开放 8001：

```bash
sudo ufw allow 8001/tcp
```

正式 HTTPS 后关闭 8001：

```bash
sudo ufw delete allow 8001/tcp
```

### pip 在云端下载超时

部署脚本默认使用阿里云 PyPI 镜像：

```text
https://mirrors.aliyun.com/pypi/simple/
```

也可临时改用清华源：

```bash
AI_DAILY_REMOTE=aliyun-ai \
AI_DAILY_PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple \
scripts/deploy_cloud.sh
```

### SSH 定时任务失败

定时任务不能交互输入密码，需要 SSH key：

```bash
ssh-copy-id aliyun-ai
ssh aliyun-ai
```

确认不再提示密码后，再启用 timer 或 cron。

## 日常推荐节奏

```text
1. 本地修改代码
2. 本地运行 pytest
3. 部署到云端：scripts/deploy_cloud.sh
4. 云端网页体验和审核
5. 拉回云端反馈：scripts/pull_cloud_state.sh
6. 本地抽取偏好特征：ai-daily extract-features --surface all
7. 后续本地训练偏好模型
8. 再进入下一轮开发
```

## 协作与调试样例

仓库提供 [固定调试样例](examples/demo-data/README.md)，可在独立目录重建索引，复现卡片浏览、审核、关联检索和反馈处理。请按样例说明启动，避免覆盖现有运行数据。

完整 data/、notes/、ppt/ 及 .env 保留在各自运行环境，不随代码提交。PPT 讲稿、配置和备份不上传；PPT 功能源代码继续维护。实验性的 nettest/ 和根目录课程大纲原件仅保留本地。Android 客户端见 [mobile-app/README.md](mobile-app/README.md)。

提交前运行 `python -m pytest`，并检查 `git diff --cached --stat`，确认不包含本机凭据或构建产物。现有部署文档包含原环境的路径和地址，使用时请替换为自己的配置。
