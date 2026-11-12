from pathlib import Path
from typing import List
import pandas as pd
from app.rag.loaders.base import BaseDocumentLoader, LoadedPage


class TabularLoader(BaseDocumentLoader):
    def load(self, file_path: Path, **kwargs) -> List[LoadedPage]:
        ext = file_path.suffix.lower()
        pages: List[LoadedPage] = []

        if ext == ".csv":
            try:
                df = pd.read_csv(file_path)
            except Exception:
                df = pd.read_csv(file_path, encoding="latin-1")
            
            pages.append(self._process_dataframe(df, sheet_name="CSV_Data", page_num=1))
        elif ext in [".xlsx", ".xls"]:
            excel_file = pd.ExcelFile(file_path)
            for idx, sheet_name in enumerate(excel_file.sheet_names, 1):
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                pages.append(self._process_dataframe(df, sheet_name=sheet_name, page_num=idx))
        else:
            raise ValueError(f"Unsupported tabular extension: {ext}")

        return pages

    def _process_dataframe(self, df: pd.DataFrame, sheet_name: str, page_num: int) -> LoadedPage:
        # Generate summary + row representations
        total_rows, total_cols = df.shape
        columns = list(df.columns)
        
        lines = [
            f"Dataset Sheet: {sheet_name}",
            f"Dimensions: {total_rows} rows x {total_cols} columns",
            f"Columns: {', '.join(str(c) for c in columns)}",
            "\n--- Sample Data & Records ---"
        ]

        # Convert rows into structured key-value representations for high semantic retrieval
        for i, row in df.head(500).iterrows():
            row_repr = ", ".join(f"{col}: {row[col]}" for col in columns if pd.notna(row[col]))
            lines.append(f"Row {i + 1}: {row_repr}")

        if total_rows > 500:
            lines.append(f"... [Truncated {total_rows - 500} additional rows for memory efficiency]")

        content = "\n".join(lines)
        return LoadedPage(
            content=content,
            page_number=page_num,
            metadata={
                "sheet_name": sheet_name,
                "total_rows": total_rows,
                "total_columns": total_cols,
                "format": "Tabular"
            }
        )

