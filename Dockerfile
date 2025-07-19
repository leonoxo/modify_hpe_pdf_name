# 使用官方的 Python 3.9 slim 版本作為基礎映像
FROM python:3.9-slim

# 設定工作目錄
WORKDIR /app

# 複製相依性檔案到工作目錄
COPY requirements.txt .

# 安裝所需的套件
RUN pip install --no-cache-dir -r requirements.txt

# 複製主腳本到工作目錄
COPY pdf_processor.py .

# 建立一個掛載點，用於存放要處理的 PDF 檔案
VOLUME /data

# 設定容器啟動時要執行的命令
CMD ["python", "pdf_processor.py"]