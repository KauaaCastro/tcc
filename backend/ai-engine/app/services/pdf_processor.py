from pathlib import Path
from typing import List, Dict, Any
import pdfplumber


class PDFProcessor:
    """
    Serviço responsável por abrir os arquivos PDF das bulas da ANVISA,
    extrair o texto de cada página e particionar em chunks com sobreposição (overlap).
    """
    
    @staticmethod
    def clean_medication_name(pdf_path: Path) -> str:
        """
        Extrai e formata o nome do medicamento a partir do nome do arquivo PDF.
        Exemplo: 'bula_atorvastatina-calcica.pdf' -> 'Atorvastatina Calcica'
        """
        stem = pdf_path.stem
        if stem.lower().startswith("bula_"):
            stem = stem[5:]
            
        clean_name = stem.replace("-", " ").replace("_", " ").strip()
        return clean_name.title()

    @staticmethod
    def extract_text(pdf_path: Path) -> str:
        """
        Abre o PDF e extrai o texto limpo de todas as páginas.
        """
        full_text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    full_text += f"\n--- PÁGINA {i + 1} ---\n" + text
        return full_text

    @staticmethod
    def create_chunks(text: str, chunk_size: int = 800, overlap: int = 100) -> List[str]:
        """
        Divide o texto em blocos (chunks) com sobreposição (overlap)
        para garantir que nenhuma frase clínica seja cortada ao meio.
        """
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk.strip())
            start += chunk_size - overlap
        return chunks

    @classmethod
    def process_single_pdf(cls, pdf_path: Path, chunk_size: int = 800, overlap: int = 100) -> List[Dict[str, Any]]:
        """
        Processa um único PDF e retorna a lista de chunks estruturados com metadados.
        """
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

    @classmethod
    def process_directory(cls, dir_path: Path, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Varre um diretório com arquivos PDF e processa até 'limit' arquivos.
        """
        all_chunks = []
        pdf_files = list(dir_path.glob("*.pdf"))[:limit]

        for pdf_file in pdf_files:
            chunks = cls.process_single_pdf(pdf_file)
            all_chunks.extend(chunks)
            print(f"[OK] Processado '{pdf_file.name}': {len(chunks)} chunks gerados.")

        return all_chunks


# Instância global reutilizável
pdf_processor = PDFProcessor()


# Teste individual do serviço
if __name__ == "__main__":
    # parents[4] sobe de services -> app -> ai-engine -> backend -> raiz do projeto
    BASE_DIR = Path(__file__).resolve().parents[4]
    bulario_dir = BASE_DIR / "Script" / "bulario"

    print(f"[INFO] Processando lote de bulas em: {bulario_dir}\n")
    lote_chunks = PDFProcessor.process_directory(bulario_dir, limit=3)

    print(f"\n[OK] Total geral de chunks acumulados no lote: {len(lote_chunks)}")
    if lote_chunks:
        print("\n--- EXEMPLO DE CHUNK ESTRUTURADO ---")
        print(f"Medicamento: {lote_chunks[0]['med_name']}")
        print(f"Índice: {lote_chunks[0]['chunk_index']} de {lote_chunks[0]['total_chunks']}")
        print(f"Conteúdo:\n{lote_chunks[0]['content'][:250]}...")
        