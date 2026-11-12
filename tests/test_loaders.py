import pytest
import os
import json
from pathlib import Path
import pandas as pd
from app.rag.loaders.registry import registry
from app.rag.loaders.text_loader import TextLoader
from app.rag.loaders.tabular_loader import TabularLoader


def test_text_loader(tmp_path):
    txt_file = tmp_path / "sample.txt"
    txt_file.write_text("CustomBot AI text document content.", encoding="utf-8")

    pages = registry.load_document(txt_file)
    assert len(pages) == 1
    assert "CustomBot AI" in pages[0].content
    assert pages[0].page_number == 1


def test_json_loader(tmp_path):
    json_file = tmp_path / "data.json"
    data = {"company": "Acme", "support_hours": "9-5 EST"}
    json_file.write_text(json.dumps(data), encoding="utf-8")

    pages = registry.load_document(json_file)
    assert len(pages) == 1
    assert "support_hours" in pages[0].content


def test_csv_tabular_loader(tmp_path):
    csv_file = tmp_path / "products.csv"
    df = pd.DataFrame({
        "Product": ["Widget A", "Gadget B"],
        "Price": [19.99, 49.99],
        "InStock": [True, False]
    })
    df.to_csv(csv_file, index=False)

    pages = registry.load_document(csv_file)
    assert len(pages) == 1
    assert "Widget A" in pages[0].content
    assert "Gadget B" in pages[0].content


def test_validation_file_size_and_extension(tmp_path):
    # Valid file
    valid_file = tmp_path / "test.md"
    valid_file.write_text("# Heading", encoding="utf-8")
    registry.validate_file("test.md", 1024)

    # Invalid extension
    with pytest.raises(ValueError) as exc:
        registry.validate_file("malicious.exe", 1024)
    assert "Unsupported file format" in str(exc.value)

    # Oversized file
    with pytest.raises(ValueError) as exc_size:
        registry.validate_file("huge.pdf", 30 * 1024 * 1024)
    assert "exceeds limit" in str(exc_size.value)

