FROM python:3.11-slim

WORKDIR /app

# 仅复制依赖清单，利用层缓存
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# host 网络模式下监听 65279；SSH 凭据等通过 .env 注入
EXPOSE 65279
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "65279"]
