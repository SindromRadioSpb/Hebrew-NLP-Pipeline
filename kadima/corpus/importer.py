# kadima/corpus/importer.py
"""M14: Import TXT, CSV, CoNLL-U, JSON.

Example:
    >>> from kadima.corpus.importer import import_files
    >>> docs = import_files(["tests/data/he_01_*/raw/doc_01.txt"])
    >>> docs[0]["format"]
    'txt'
    >>> len(docs[0]["raw_text"]) > 0
    True
"""

import os
import csv
import json
import logging
from typing import List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

SUPPORTED_FORMATS = {".txt", ".csv", ".conllu", ".json"}


def import_files(file_paths: List[str]) -> List[Dict[str, Any]]:
    """
    Импортировать файлы. Возвращает список документов.

    Returns:
        [{"filename": str, "raw_text": str, "format": str}, ...]
    """
    documents = []
    for path in file_paths:
        ext = Path(path).suffix.lower()
        if ext not in SUPPORTED_FORMATS:
            logger.warning("Unsupported format: %s (skipping %s)", ext, path)
            continue

        try:
            if ext == ".txt":
                documents.extend(_import_txt(path))
            elif ext == ".csv":
                documents.extend(_import_csv(path))
            elif ext == ".conllu":
                documents.extend(_import_conllu(path))
            elif ext == ".json":
                documents.extend(_import_json(path))
        except Exception as e:
            logger.error("Failed to import %s: %s", path, e, exc_info=True)

    logger.info("Imported %d documents from %d files", len(documents), len(file_paths))
    return documents


def import_directory(dir_path: str, recursive: bool = True) -> List[Dict[str, Any]]:
    """Импортировать все поддерживаемые файлы из директории."""
    file_paths = []
    for root, _, files in os.walk(dir_path):
        for fname in sorted(files):
            if Path(fname).suffix.lower() in SUPPORTED_FORMATS:
                file_paths.append(os.path.join(root, fname))
        if not recursive:
            break
    return import_files(file_paths)


def _import_txt(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        text = f.read().strip()
    if not text:
        return []
    return [{"filename": os.path.basename(path), "raw_text": text, "format": "txt"}]


def _import_csv(path: str) -> List[Dict[str, Any]]:
    docs = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            text = row.get("text") or row.get("raw_text") or row.get("content", "")
            if text.strip():
                docs.append({"filename": row.get("filename", os.path.basename(path)), "raw_text": text.strip(), "format": "csv"})
    return docs


def _import_conllu(path: str) -> List[Dict[str, Any]]:
    """Импорт CoNLL-U: собираем предложения в документ."""
    sentences = []
    current = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                if current:
                    sentences.append(" ".join(current))
                    current = []
            elif line.startswith("#"):
                continue
            else:
                parts = line.split("\t")
                if len(parts) >= 2:
                    current.append(parts[1])
    if current:
        sentences.append(" ".join(current))
    text = "\n".join(sentences)
    return [{"filename": os.path.basename(path), "raw_text": text, "format": "conllu"}] if text else []


def _import_json(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, str):
        return [{"filename": os.path.basename(path), "raw_text": data, "format": "json"}]
    if isinstance(data, list):
        docs = []
        for item in data:
            if isinstance(item, str):
                docs.append({"filename": os.path.basename(path), "raw_text": item, "format": "json"})
            elif isinstance(item, dict):
                text = item.get("raw_text") or item.get("text") or json.dumps(item, ensure_ascii=False)
                fname = item.get("filename") or item.get("id") or os.path.basename(path)
                docs.append({"filename": fname, "raw_text": text, "format": "json"})
            else:
                docs.append({"filename": os.path.basename(path), "raw_text": str(item), "format": "json"})
        return docs
    if isinstance(data, dict):
        text = data.get("text") or data.get("raw_text") or json.dumps(data, ensure_ascii=False)
        return [{"filename": os.path.basename(path), "raw_text": text, "format": "json"}]
    return []
