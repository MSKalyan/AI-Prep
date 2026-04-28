from ..db.chroma_client import get_vectorstore
def hybrid_retrieve(query, top_k=5, exam_type=None, subject=None):
    vectorstore = get_vectorstore()
    
    search_kwargs = {"k": top_k}
    
    if exam_type or subject:
        filter_dict = {}
        if exam_type:
            filter_dict["exam_type"] = exam_type
        if subject:
            filter_dict["subject"] = subject
        search_kwargs["filter"] = filter_dict
    
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs=search_kwargs
    )
    
    docs = retriever.invoke(query)
    
    results = []
    for doc in docs:
        if hasattr(doc, 'page_content'):
            text = doc.page_content
            metadata = doc.metadata
        else:
            text = str(doc)
            metadata = {}
        results.append({
            "text": text,
            "metadata": metadata,
            "score": 1.0
        })
    return results