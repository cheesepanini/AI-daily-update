# 云服务器部署工作流

本项目建议采用“本地开发，云端验证”的工作流：

- 本地负责代码开发、测试和偏好模型训练。
- 云服务器负责网页体验、定时任务验证和人工审核。
- `.env` 不同步，本地和云端分别维护。
- 云端产生的反馈和审核状态需要拉回本地，用于后续偏好学习。

## 1. 本地配置 SSH 目标

可以在 `~/.ssh/config` 里配置：

```sshconfig
Host aliyun-ai
  HostName 云服务器公网 IP
  User lsh
  Port 22
```

也可以不配置别名，直接使用 `user@host`。

## 2. 云服务器首次准备

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip rsync git curl
mkdir -p ~/AI-daily-update
cd ~/AI-daily-update
nano .env
```

云端 `.env` 至少需要：

```env
AI_DAILY_ADMIN_USERNAME=admin
AI_DAILY_ADMIN_PASSWORD=change-me
AI_DAILY_SESSION_SECRET=change-me-to-a-long-random-string
```

如果云端需要生成卡片和 PPT 建议，还需要配置模型服务相关变量。

## 3. 从本地部署到云端

```bash
AI_DAILY_REMOTE=aliyun-ai scripts/deploy_cloud.sh
```

如果远端目录不是 `/home/lsh/AI-daily-update`：

```bash
AI_DAILY_REMOTE=aliyun-ai \
AI_DAILY_REMOTE_DIR=/home/your-user/AI-daily-update \
scripts/deploy_cloud.sh
```

部署脚本会：

1. 在本地运行测试。
2. 用 `rsync` 同步代码到云端。
3. 在云端创建虚拟环境（如果不存在）。
4. 在云端执行 `pip install -e .`。
5. 如果远端已经安装 systemd 服务，并且当前 SSH 用户有免密 sudo，则自动重启服务。

默认部署不会覆盖云端运行状态。以下路径默认排除：

- `data/`
- `notes/`
- `ppt/`
- `config/sources.yaml`

这些路径包含卡片、审核状态、回收站、简报、反馈日志、偏好学习特征、PPT 讲稿、PPT 节点、消息源启停和前端维护的 topic 选项。日常代码更新不要同步这些状态，否则可能把云端审核结果改回本地旧版本。

只有首次初始化云端、且确认要用本地状态覆盖云端时，才显式执行：

```bash
AI_DAILY_REMOTE=aliyun-ai \
AI_DAILY_SYNC_STATE=1 \
scripts/deploy_cloud.sh
```

## 4. 安装云端 systemd 服务

首次部署后，可以在本地执行：

```bash
AI_DAILY_REMOTE=aliyun-ai scripts/install_cloud_service.sh
```

如果需要修改远端目录、监听地址或端口：

```bash
AI_DAILY_REMOTE=aliyun-ai \
AI_DAILY_REMOTE_DIR=/home/lsh/AI-daily-update \
AI_DAILY_SERVICE_HOST=0.0.0.0 \
AI_DAILY_SERVICE_PORT=8001 \
scripts/install_cloud_service.sh
```

也可以在云端手动执行：

```bash
sudo cp ~/AI-daily-update/scripts/systemd/ai-daily-web.service /etc/systemd/system/ai-daily.service
sudo systemctl daemon-reload
sudo systemctl enable ai-daily
sudo systemctl start ai-daily
sudo systemctl status ai-daily
```

如果云服务器用户名不是 `lsh`，需要先编辑 service 文件中的路径。

## 5. 阿里云安全组

临时验证可通过 SSH 隧道访问本机端口，无需对公网开放 8001：

```bash
ssh -L 8001:127.0.0.1:8001 aliyun-ai
```

然后在本机访问 `http://127.0.0.1:8001/`。

正式使用建议改成：

```text
TCP 22
TCP 80
TCP 443
```

然后用 Caddy/Nginx 反向代理到 `127.0.0.1:8001`。

## 6. 从云端拉回反馈和状态

```bash
AI_DAILY_REMOTE=aliyun-ai scripts/pull_cloud_state.sh
```

该脚本会尝试拉回：

- `config/sources.yaml`
- `data/feedback/`
- `data/features/`
- `data/manual_urls.txt`
- `data/ppt_source_suggestions.md`
- `data/source_proposals.json`
- `notes/briefs/`
- `notes/cards/`
- `notes/inbox/`
- `notes/trash/`
- `ppt/`

这些数据用于保留云端审核记录，并支持后续偏好模型训练。

## 7. 本地定时拉回偏好学习数据

云端用于体验和审核时，建议把反馈与特征数据定时拉回本地。本项目提供两种模板。

### systemd user timer

先确认本地可以免密 SSH 到云端：

```bash
ssh aliyun-ai
```

安装用户级 timer：

```bash
mkdir -p ~/.config/systemd/user
cp scripts/systemd/ai-daily-pull-cloud-state.service ~/.config/systemd/user/
cp scripts/systemd/ai-daily-pull-cloud-state.timer ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now ai-daily-pull-cloud-state.timer
systemctl --user list-timers | grep ai-daily
```

默认每天 23:30 拉回：

- `data/feedback/`
- `data/features/`
- `notes/cards/`
- `notes/trash/`
- `data/source_proposals.json`

手动执行一次：

```bash
systemctl --user start ai-daily-pull-cloud-state.service
```

查看日志：

```bash
journalctl --user -u ai-daily-pull-cloud-state.service -n 100 --no-pager
```

### cron

也可以把 `scripts/cron/ai-daily-pull-cloud-state.cron` 中的内容加入本地 crontab：

```bash
crontab -e
```

日志会写到：

```text
data/logs/pull-cloud-state.log
```
