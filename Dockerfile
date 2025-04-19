# VocabMaster Dockerfile
# 提供容器化部署选项

FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY . /app/

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 暴露端口（如果应用需要）
# EXPOSE 8080

# 启动应用
CMD ["python", "app.py"]

# 注意：此Dockerfile提供基本的容器化支持
# 对于GUI应用，需要额外配置X11转发或使用VNC/noVNC
# 在实际部署时可能需要根据具体需求修改