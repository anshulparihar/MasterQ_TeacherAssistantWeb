from langchain_text_splitters import RecursiveCharacterTextSplitter

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[dict]:
    # Initialize the text splitter
    # We use RecursiveCharacterTextSplitter to preserve paragraph boundaries 
    # where possible before splitting by sentences or words
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    
    chunks = text_splitter.split_text(text)
    
    result = []
    for i, chunk in enumerate(chunks):
        result.append({
            "content": chunk,
            "metadata": {
                "chunk_index": i,
                # Simple heuristic for approximate page based on 2000 chars per page
                "approximate_page": (i * (chunk_size - overlap)) // 2000 + 1 
            }
        })
        
    return result
