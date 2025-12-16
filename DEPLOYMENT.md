# 部署指南

## Launch 平台部署

### 必需配置

1. **Git 仓库**
   - URL: `https://github.com/kai657/po_adjustment.git`
   - 分支: `main`
   - 确保仓库为 Public 或平台有访问权限

2. **Dockerfile**
   - 路径: `/Dockerfile` (根目录)
   - 已配置完成，无需修改

3. **端口配置**
   - 容器端口: `5001`
   - 协议: `HTTP`

4. **环境变量**（可选）
   ```
   PORT=5001
   HOST=0.0.0.0
   WORKERS=2
   PYTHONUNBUFFERED=1
   ```

### 部署步骤

1. 在 launch 平台创建新应用
2. 连接 Git 仓库: `https://github.com/kai657/po_adjustment.git`
3. 选择分支: `main`
4. 设置端口: `5001`
5. 点击部署

### 故障排查

#### NullPointerException 错误

如果遇到 `NullPointerException`，请检查：

1. **Git 配置**
   - ✅ 仓库 URL 是否正确
   - ✅ 分支名称是否为 `main`
   - ✅ 仓库是否为 Public 或已授权

2. **Dockerfile 路径**
   - ✅ 确认路径为根目录: `/Dockerfile` 或 `./Dockerfile`
   - ✅ 文件名大小写正确: `Dockerfile` (不是 dockerfile)

3. **平台配置**
   - ✅ 检查是否需要配置 Deploy Key 或 Access Token
   - ✅ 确认平台支持的 Python 版本 (需要 3.11)
   - ✅ 查看平台文档确认 Dockerfile 格式要求

4. **日志查看**
   - 查看完整构建日志（不只是错误摘要）
   - 检查是否有其他错误信息

## Docker 本地测试

### 使用 Docker Compose（推荐）

```bash
# 构建并启动
docker-compose up --build

# 后台运行
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 使用 Docker 命令

```bash
# 构建镜像
docker build -t po_adjustment .

# 运行容器
docker run -p 5001:5001 \
  -e PORT=5001 \
  -e WORKERS=2 \
  -v $(pwd)/data/output:/app/data/output \
  -v $(pwd)/data/uploads:/app/data/uploads \
  po_adjustment

# 查看日志
docker logs -f <container_id>
```

### 测试访问

访问 http://localhost:5001 确认服务正常运行

## 其他云平台部署

### Railway

1. 安装 Railway CLI: `npm install -g @railway/cli`
2. 登录: `railway login`
3. 初始化: `railway init`
4. 部署: `railway up`

### Render

1. 连接 GitHub 仓库
2. 选择 "Web Service"
3. 设置:
   - Build Command: `(empty)`
   - Start Command: `./start.sh`
   - Docker: 检测到 Dockerfile 会自动使用

### Heroku

创建 `heroku.yml`:
```yaml
build:
  docker:
    web: Dockerfile
run:
  web: ./start.sh
```

部署:
```bash
heroku create po-adjustment
heroku stack:set container
git push heroku main
```

## 生产环境建议

1. **资源配置**
   - CPU: 至少 1 核
   - 内存: 至少 512MB（推荐 1GB）
   - 存储: 至少 1GB

2. **环境变量**
   - 根据负载调整 `WORKERS` 数量
   - 生产环境禁用 Flask DEBUG 模式

3. **监控**
   - 配置健康检查: `GET /`
   - 设置日志收集
   - 配置告警通知

4. **数据持久化**
   - 挂载 `data/output` 和 `data/uploads` 目录
   - 定期备份优化结果

## 常见问题

### Q: 为什么需要 gunicorn？
A: Flask 内置服务器仅用于开发，生产环境需要使用 WSGI 服务器如 gunicorn。

### Q: 如何修改端口？
A: 设置环境变量 `PORT=8000` 或修改 `start.sh`

### Q: 如何增加 workers 数量？
A: 设置环境变量 `WORKERS=4`，建议为 CPU 核心数的 2-4 倍

### Q: 文件上传大小限制？
A: 默认无限制，可在 Flask 应用中配置 `MAX_CONTENT_LENGTH`

## 支持

- GitHub Issues: https://github.com/kai657/po_adjustment/issues
- 文档: /docs/README.md
