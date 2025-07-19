# HPE PDF Renaming Tool

[![Python Version](https://img.shields.io/badge/python-3.9-blue.svg)](https://www.python.org/downloads/release/python-390/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A simple yet powerful Dockerized Python tool to automatically clean up and rename PDF documents from Hewlett Packard Enterprise (HPE).

---

## Features

-   **Prefix Removal**: Automatically removes common filename prefixes like `HPE_*_us_` or `HPE_*_`.
-   **Date-based Suffixing**: Intelligently extracts the publication date from the PDF's text or metadata and appends it to the filename in a clean `_YYYYMM` format.
-   **Fallback Mechanism**: If no date can be found, it appends a default suffix (`_000000`) to ensure all files are processed.
-   **Detailed Logging**: Generates two log files (`remove_prefix_log.txt` and `rename_log.txt`) to provide a transparent and detailed record of all operations.
-   **Dockerized**: Packaged in a lightweight Docker container for easy, cross-platform execution without dependency hassles.

---

## How to Use

You must have [Docker](https://www.docker.com/get-started) installed on your system to use this tool.

### 1. Pull the Docker Image

Open your terminal and pull the latest image from Docker Hub:

```bash
docker pull leonoxo/hpe_pdf-processor:latest
```

### 2. Run the Container

Navigate to the directory containing the PDF files you want to process and run the following command:

```bash
docker run --rm -v "$(pwd)":/data leonoxo/hpe_pdf-processor:latest
```

**Command Breakdown:**

-   `docker run`: The standard command to run a Docker container.
-   `--rm`: This flag automatically removes the container once it finishes its task, keeping your system clean.
-   `-v "$(pwd)":/data`: This is the most crucial part. It mounts your **current working directory** (where your PDFs are) into the `/data` directory inside the container. The script is hardcoded to process all PDF files within this `/data` directory.
-   `leonoxo/hpe_pdf-processor:latest`: The name of the image you want to run.

---

## How It Works

The container executes the `pdf_processor.py` script, which performs the following steps in sequence:

1.  **Prefix Removal**: It scans all PDF files in the `/data` directory and uses regex to find and strip known HPE prefixes from the filenames.
2.  **Date Extraction & Renaming**:
    - For each PDF, it scans the text of the first and last few pages for various date patterns (e.g., "Published: Month Year", "First edition: Month Year", "Month YYYY").
    - If no date is found in the text, it attempts to read the PDF's metadata (`/ModDate` or `/CreationDate`).
    - The extracted date is formatted as `YYYYMM` and appended as a suffix to the filename.
    - If no date can be found through any method, a default suffix is used.

All actions, successes, and errors are logged to `remove_prefix_log.txt` and `rename_log.txt` in your directory.

---

## Contributing

Feel free to open an issue or submit a pull request if you have suggestions for improvements.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.