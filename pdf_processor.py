import os
import re
import logging
from pypdf import PdfReader
from datetime import datetime

# --- General Configuration ---
TARGET_DIR = "/data"  # Directory inside the container where PDFs will be mounted
LOG_DIR = "/data"     # Directory where log files will be saved

# --- Prefix Remover Configuration ---
PREFIX_PATTERN = re.compile(r"^(HPE_.*_us_|HPE_.*?_)", re.IGNORECASE)
PREFIX_LOG_FILE = os.path.join(LOG_DIR, "remove_prefix_log.txt")

# --- Date Renamer Configuration ---
DEFAULT_DATE_SUFFIX = "000000"
PAGES_TO_SCAN = 5
RENAME_LOG_FILE = os.path.join(LOG_DIR, "rename_log.txt")

# --- Month Mapping ---
MONTH_MAP = {
    "january": "01", "jan": "01", "february": "02", "feb": "02",
    "march": "03", "mar": "03", "april": "04", "apr": "04", "may": "05",
    "june": "06", "jun": "06", "july": "07", "jul": "07", "august": "08", "aug": "08",
    "september": "09", "sep": "09", "sept": "09", "septemberr": "09",
    "october": "10", "oct": "10", "november": "11", "nov": "11", "december": "12", "dec": "12"
}

# --- Date Regex Patterns ---
published_pattern = re.compile(r"Published:\s*([a-zA-Z]+)\s*(?:\d{1,2}(?:st|nd|rd|th)?(?:,)?)?\s*(\d{4})", re.IGNORECASE)
month_year_pattern = re.compile(r"([a-zA-Z]+)\s+(\d{4})", re.IGNORECASE)
numeric_date_pattern = re.compile(r"(\d{4})[-/](\d{1,2})")
existing_suffix_pattern = re.compile(r"_\d{6}\.pdf$", re.IGNORECASE)
dd_month_year_pattern = re.compile(r"(\d{1,2})[-.\s]+([a-zA-Z]+)[-.\s]+(\d{4})", re.IGNORECASE)
first_edition_pattern = re.compile(r"First edition:\s*([a-zA-Z]+)\s+(\d{4})", re.IGNORECASE)
footer_date_pattern = re.compile(r"([a-zA-Z]+)\s+(\d{1,2}),\s*(\d{4})", re.IGNORECASE)

# --- Logger Setup ---
def setup_logger(name, log_file, level=logging.INFO):
    """Function to setup as many loggers as you want"""
    # 移除已存在的 handler，避免重複記錄
    logger = logging.getLogger(name)
    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # File Handler
    file_handler = logging.FileHandler(log_file, mode='w')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Stream Handler
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    
    logger.setLevel(level)
    return logger

# --- Prefix Remover Functions ---
def remove_prefix_from_pdfs(directory, logger):
    """Traverses a directory and removes specified prefixes from PDF filenames."""
    logger.info(f"Starting prefix removal process in directory: {directory}")
    renamed_count = 0
    skipped_count = 0
    error_count = 0
    skipped_due_to_existence = []

    if not os.path.isdir(directory):
        logger.error(f"Error: Directory '{directory}' does not exist.")
        return

    try:
        all_files = os.listdir(directory)
    except OSError as e:
        logger.error(f"Error reading directory '{directory}': {e}")
        return

    logger.info(f"Found {len(all_files)} items in '{directory}'.")

    for filename in all_files:
        if filename.lower().endswith(".pdf"):
            logger.debug(f"Checking file: {filename}")
            match = PREFIX_PATTERN.match(filename)
            if match:
                prefix_to_remove = match.group(0)
                new_filename = filename[len(prefix_to_remove):]
                logger.info(f"Found prefix '{prefix_to_remove}', preparing to rename to: {new_filename}")

                old_full_path = os.path.join(directory, filename)
                new_full_path = os.path.join(directory, new_filename)

                if os.path.exists(new_full_path):
                    logger.warning(f"Warning: Target filename '{new_filename}' already exists. Skipping rename for '{filename}'")
                    skipped_count += 1
                    skipped_due_to_existence.append(filename)
                    continue

                try:
                    os.rename(old_full_path, new_full_path)
                    logger.info(f"Successfully renamed '{filename}' -> '{new_filename}'")
                    renamed_count += 1
                except OSError as e:
                    logger.error(f"Error renaming file '{filename}' -> '{new_filename}': {e}")
                    error_count += 1
            else:
                logger.debug(f"File '{filename}' does not match prefix pattern, skipping.")
                skipped_count += 1
        else:
            logger.debug(f"Skipping non-PDF file: {filename}")

    logger.info("="*20 + " Prefix Removal Finished " + "="*20)
    logger.info(f"Renamed files: {renamed_count}")
    logger.info(f"Skipped files (no match or exists): {skipped_count}")
    logger.info(f"Errors: {error_count}")
    if skipped_due_to_existence:
        logger.warning("The following files were skipped because the target filename already existed:")
        for skipped_file in skipped_due_to_existence:
            logger.warning(f"- {skipped_file}")
    logger.info(f"Details logged to: {PREFIX_LOG_FILE}")


# --- Date Renamer Functions ---
def extract_date_from_pdf(pdf_path, logger):
    """Extracts date from PDF text or metadata, returns YYYYMM."""
    try:
        reader = PdfReader(pdf_path)
        num_pages = len(reader.pages)
        text_to_search = ""
        
        # Read start pages
        for i in range(min(num_pages, PAGES_TO_SCAN)):
            try:
                page_text = reader.pages[i].extract_text()
                if page_text:
                    text_to_search += page_text + "\n"
            except Exception as page_error:
                logger.warning(f"Error extracting text from page {i+1} of '{os.path.basename(pdf_path)}': {page_error}")

        # Read end pages
        if num_pages > PAGES_TO_SCAN:
            start_page_for_end = max(PAGES_TO_SCAN, num_pages - PAGES_TO_SCAN)
            for i in range(start_page_for_end, num_pages):
                try:
                    page_text = reader.pages[i].extract_text()
                    if page_text:
                        text_to_search += page_text + "\n"
                except Exception as page_error:
                    logger.warning(f"Error extracting text from page {i+1} of '{os.path.basename(pdf_path)}': {page_error}")

        date_from_text = find_date_in_text(text_to_search.strip(), logger)
        if date_from_text:
            return date_from_text

        # Try metadata if text search fails
        logger.debug(f"No date in text, trying metadata for '{os.path.basename(pdf_path)}'")
        try:
            metadata = reader.metadata
            if metadata:
                date_str = metadata.get('/ModDate') or metadata.get('/CreationDate')
                if date_str and isinstance(date_str, str) and date_str.startswith('D:'):
                    match = re.match(r"D:(\d{4})(\d{2})", date_str)
                    if match:
                        year, month = match.groups()
                        if 1980 <= int(year) <= datetime.now().year + 5:
                            logger.info(f"Extracted date from metadata: {year}{month}")
                            return f"{year}{month}"
        except Exception as meta_error:
            logger.warning(f"Error reading PDF metadata for '{os.path.basename(pdf_path)}': {meta_error}")
        
        return None
    except Exception as e:
        logger.error(f"Error reading PDF '{os.path.basename(pdf_path)}': {e}")
        return None

def find_date_in_text(text, logger):
    """Finds a date pattern in text and returns YYYYMM."""
    if not text:
        return None
    
    patterns = [
        published_pattern, first_edition_pattern, month_year_pattern,
        dd_month_year_pattern, footer_date_pattern, numeric_date_pattern
    ]

    for pattern in patterns:
        try:
            matches = pattern.findall(text)
            if matches:
                logger.debug(f"Pattern {pattern.pattern} found matches: {matches}")
                # Process the last match found
                match = matches[-1]
                year, month_str = "", ""
                if len(match) == 2: # (month, year) or (year, month)
                    if match[0].isdigit() and len(match[0]) == 4: # (year, month)
                        year, month_str = match[0], match[1]
                    else: # (month, year)
                        year, month_str = match[1], match[0]
                elif len(match) == 3: # (day, month, year) or (month, day, year)
                    year = match[2]
                    month_str = match[1] if not match[1].isdigit() else match[0]

                month_num = MONTH_MAP.get(str(month_str).lower())
                if month_num and year.isdigit() and len(year) == 4:
                    if 1980 <= int(year) <= datetime.now().year + 5:
                        logger.debug(f"Valid date found: {year}{month_num}")
                        return f"{year}{month_num}"
        except Exception as e:
            logger.debug(f"Error processing pattern {pattern.pattern}: {e}")
            continue
            
    logger.debug("No valid date pattern found in text.")
    return None

def rename_pdf_files(directory, logger):
    """Renames PDF files by appending a date suffix."""
    logger.info(f"Starting date-based renaming process in directory: {directory}")
    renamed_count = 0
    error_count = 0
    processed_with_new_suffix = 0
    processed_with_default_suffix = 0
    no_rename_needed_count = 0
    base_name_suffix_pattern = re.compile(r"_\d{6}$")

    if not os.path.isdir(directory):
        logger.error(f"Error: Directory '{directory}' does not exist.")
        return

    pdf_files = [f for f in os.listdir(directory) if f.lower().endswith(".pdf")]
    logger.info(f"Found {len(pdf_files)} PDF files to process for date renaming.")

    for filename in pdf_files:
        original_full_path = os.path.join(directory, filename)
        base_name_original, ext = os.path.splitext(filename)
        base_name_cleaned = base_name_suffix_pattern.sub("", base_name_original)

        logger.info(f"Processing file: {filename} (Cleaned base name: {base_name_cleaned})")
        date_suffix = extract_date_from_pdf(original_full_path, logger)

        if date_suffix:
            new_base_name = f"{base_name_cleaned}_{date_suffix}"
            processed_with_new_suffix += 1
            logger.info(f"Found date {date_suffix}, new base name: {new_base_name}")
        else:
            new_base_name = f"{base_name_cleaned}_{DEFAULT_DATE_SUFFIX}"
            processed_with_default_suffix += 1
            logger.warning(f"No date found, using default {DEFAULT_DATE_SUFFIX}. New base name: {new_base_name}")

        new_filename = f"{new_base_name}{ext}"
        new_full_path = os.path.join(directory, new_filename)

        if filename == new_filename:
            logger.info(f"Filename '{filename}' is already correct. No rename needed.")
            no_rename_needed_count += 1
            continue

        if os.path.exists(new_full_path) and not os.path.samefile(original_full_path, new_full_path):
            logger.error(f"Error: Target file '{new_filename}' already exists. Skipping rename for '{filename}'")
            error_count += 1
            continue

        try:
            os.rename(original_full_path, new_full_path)
            logger.info(f"Successfully renamed '{filename}' -> '{new_filename}'")
            renamed_count += 1
        except OSError as e:
            logger.error(f"Error renaming file '{filename}' -> '{new_filename}': {e}")
            error_count += 1

    logger.info("-" * 20 + " Date Renaming Finished " + "-" * 20)
    logger.info(f"Successfully renamed: {renamed_count}")
    logger.info(f"No rename needed (already correct): {no_rename_needed_count}")
    logger.info(f"Processed with extracted date: {processed_with_new_suffix}")
    logger.info(f"Processed with default date: {processed_with_default_suffix}")
    logger.info(f"Errors: {error_count}")
    logger.info(f"Details logged to: {RENAME_LOG_FILE}")


# --- Main Execution ---
if __name__ == "__main__":
    # Setup loggers
    prefix_logger = setup_logger('prefix_remover', PREFIX_LOG_FILE, level=logging.INFO)
    rename_logger = setup_logger('date_renamer', RENAME_LOG_FILE, level=logging.INFO)

    # --- Step 1: Remove Prefixes ---
    prefix_logger.info("### Starting Step 1: Remove Prefixes ###")
    remove_prefix_from_pdfs(TARGET_DIR, prefix_logger)
    prefix_logger.info("### Finished Step 1 ###\n")

    # --- Step 2: Rename by Date ---
    rename_logger.info("### Starting Step 2: Rename by Date ###")
    rename_pdf_files(TARGET_DIR, rename_logger)
    rename_logger.info("### Finished Step 2 ###")