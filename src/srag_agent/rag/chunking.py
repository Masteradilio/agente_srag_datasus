import hashlib

from srag_agent.data.schema import DocumentChunk, DocumentSource


def chunk_document(
    document: DocumentSource,
    max_chars: int = 1200,
    overlap: int = 120,
) -> list[DocumentChunk]:
    sections = _split_sections(document.content)
    chunks: list[DocumentChunk] = []

    for section_index, section in enumerate(sections):
        start = 0
        while start < len(section):
            content = section[start : start + max_chars].strip()
            if content:
                chunk_id = _chunk_id(document.source_path, section_index, start, content)
                chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        source_path=document.source_path,
                        source_type=document.source_type,
                        content=content,
                        metadata={
                            **document.metadata,
                            "section_index": str(section_index),
                        },
                    )
                )
            if start + max_chars >= len(section):
                break
            start += max_chars - overlap

    return chunks


def chunk_documents(
    documents: list[DocumentSource],
    max_chars: int = 1200,
    overlap: int = 120,
) -> list[DocumentChunk]:
    chunks: list[DocumentChunk] = []
    for document in documents:
        chunks.extend(chunk_document(document, max_chars=max_chars, overlap=overlap))
    return chunks


def _split_sections(content: str) -> list[str]:
    sections: list[str] = []
    current: list[str] = []
    for line in content.splitlines():
        if line.startswith("#") and current:
            sections.append("\n".join(current))
            current = [line]
        else:
            current.append(line)
    if current:
        sections.append("\n".join(current))
    return sections


def _chunk_id(source_path: str, section_index: int, start: int, content: str) -> str:
    digest = hashlib.sha256(f"{source_path}:{section_index}:{start}:{content}".encode()).hexdigest()
    return digest[:16]
