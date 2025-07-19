# HPE PDF 重命名工具

[![Python Version](https://img.shields.io/badge/python-3.9-blue.svg)](https://www.python.org/downloads/release/python-390/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

一個簡單而強大的 Docker 化 Python 工具，可自動清理和重命名來自 Hewlett Packard Enterprise (HPE) 的 PDF 文件。

---

## 功能特性

-   **移除前綴**：自動移除檔名中常見的 `HPE_*_us_` 或 `HPE_*_` 前綴。
-   **日期後綴**：從 PDF 的內容或元數據中智能提取發布日期，並將其以 `_YYYYMM` 的格式附加到檔名末尾。
-   **備用機制**：如果找不到日期，腳本會附加一個預設後綴 (`_000000`)，以確保所有檔案都得到處理。
-   **詳細日誌**：產生兩個日誌檔案 (`remove_prefix_log.txt` 和 `rename_log.txt`)，提供所有操作的透明且詳細的記錄。
-   **Docker化**：封裝在一個輕量級的 Docker 容器中，方便在不同平台執行，無需處理繁瑣的相依性問題。

---

## 如何使用

您必須先在系統上安裝 [Docker](https://www.docker.com/get-started) 才能使用此工具。

### 1. 拉取 Docker 映像

開啟您的終端機，並使用以下指令從 Docker Hub 拉取最新的映像：

```bash
docker pull leonoxo/hpe_pdf-processor:latest
```

### 2. 執行容器

請切換到包含您想處理的 PDF 檔案的目錄，然後執行以下指令：

```bash
docker run --rm -v "$(pwd)":/data leonoxo/hpe_pdf-processor:latest
```

**指令說明：**

-   `docker run`: 執行 Docker 容器的標準指令。
-   `--rm`: 此旗標會在容器完成任務後自動將其刪除，以保持系統整潔。
-   `-v "$(pwd)":/data`: 這是最關鍵的部分。它會將您**當前的工作目錄**（也就是您存放 PDF 的地方）掛載到容器內的 `/data` 目錄。腳本被設定為處理此 `/data` 目錄中的所有 PDF 檔案。
-   `leonoxo/hpe_pdf-processor:latest`: 指定您想要執行的映像名稱。

---

## 運作原理

容器會執行 `pdf_processor.py` 腳本，該腳本依序執行以下步驟：

1.  **移除前綴**：掃描 `/data` 目錄中的所有 PDF 檔案，並使用正規表示式尋找並移除已知的 HPE 檔名前綴。
2.  **提取日期並重命名**：
    -   對於每個 PDF，腳本會掃描文件前幾頁和後幾頁的內文，以尋找各種日期格式（例如 "Published: Month Year"、"First edition: Month Year"、"Month YYYY"）。
    -   如果在內文中找不到日期，它會嘗試讀取 PDF 的元數據（`/ModDate` 或 `/CreationDate`）。
    -   提取出的日期會被格式化為 `YYYYMM`，並作為後綴附加到檔名上。
    -   如果透過任何方法都找不到日期，則會使用預設後綴。

所有操作、成功和錯誤的資訊都會被記錄到您目錄中的 `remove_prefix_log.txt` 和 `rename_log.txt` 檔案中。

---

## 貢獻

如果您有任何改進建議，歡迎提出 Issue 或提交 Pull Request。