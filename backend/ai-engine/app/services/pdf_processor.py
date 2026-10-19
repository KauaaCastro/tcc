from pathlib import Path
from typing import List, Dict, Any
import pdfplumber


# Serviço de leitura de bulas em PDF (pdfplumber) e fatiamento em chunks semânticos
class PDFProcessor:

    # Extrai e formata o nome do medicamento a partir do nome do arquivo PDF
    @staticmethod
    def clean_medication_name(pdf_path: Path) -> str:
        stem = pdf_path.stem
        if stem.lower().startswith("bula_"):
            stem = stem[5:]

        clean_name = stem.replace("-", " ").replace("_", " ").strip()
        return clean_name.title()

    # Abre o PDF e extrai o texto limpo de todas as páginas
    @staticmethod
    def extract_text(pdf_path: Path) -> str:
        full_text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    full_text += f"\n--- PÁGINA {i + 1} ---\n" + text
        return full_text

    # Divide o texto em blocos (chunks) respeitando limites de palavra/linha com sobreposição (overlap)
    @staticmethod
    def create_chunks(text: str, chunk_size: int = 1200, overlap: int = 150) -> List[str]:
        clean = (text or "").strip()
        if not clean:
            return []

        chunks: List[str] = []
        start = 0
        text_len = len(clean)
        half_window = max(1, (chunk_size - overlap) // 2)

        while start < text_len:
            end = min(start + chunk_size, text_len)
            if end < text_len:
                nl_pos = clean.rfind("\n", start + half_window, end)
                sp_pos = clean.rfind(" ", start + half_window, end)
                boundary = max(nl_pos, sp_pos)
                if boundary > start:
                    end = boundary

            chunk = clean[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end >= text_len:
                break

            next_start = max(start + 1, end - overlap)
            space_after = clean.find(" ", next_start, min(next_start + 40, text_len))
            if space_after != -1 and space_after < end:
                next_start = space_after + 1
            start = next_start

        return chunks

    # Processa um único PDF e retorna a lista de chunks estruturados com metadados
    @classmethod
    def process_single_pdf(cls, pdf_path: Path, chunk_size: int = 1200, overlap: int = 150) -> List[Dict[str, Any]]:
        med_name = cls.clean_medication_name(pdf_path)
        raw_text = cls.extract_text(pdf_path)
        text_chunks = cls.create_chunks(raw_text, chunk_size, overlap)

        structured_chunks = []
        total = len(text_chunks)
        for index, content in enumerate(text_chunks):
            structured_chunks.append({
                "med_name": med_name,
                "chunk_index": index,
                "content": content,
                "total_chunks": total
            })
        return structured_chunks

    # Varre um diretório com arquivos PDF e processa até 'limit' arquivos
    @classmethod
    def process_directory(cls, dir_path: Path, limit: int = 5) -> List[Dict[str, Any]]:
        all_chunks = []
        pdf_files = list(dir_path.glob("*.pdf"))[:limit]

        for pdf_file in pdf_files:
            chunks = cls.process_single_pdf(pdf_file)
            all_chunks.extend(chunks)
            print(f"[OK] Processado '{pdf_file.name}': {len(chunks)} chunks gerados.")

        return all_chunks


pdf_processor = PDFProcessor()
        