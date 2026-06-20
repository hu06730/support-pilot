"""文档加载 & 分块测试。"""


from app.rag.loader import load_document, split_documents, load_and_split


class TestLoadDocument:
    def test_load_txt(self, sample_text_file):
        docs = load_document(sample_text_file)
        assert len(docs) > 0
        assert "数据库" in docs[0].page_content

    def test_unsupported_format(self, tmp_path):
        bad_file = tmp_path / "test.xyz"
        bad_file.write_text("content")
        try:
            load_document(bad_file)
            assert False, "应该抛出 ValueError"
        except ValueError as e:
            assert "不支持" in str(e)


class TestSplitDocuments:
    def test_split_produces_chunks(self, sample_text_file):
        docs = load_document(sample_text_file)
        chunks = split_documents(docs, chunk_size=100, chunk_overlap=20)
        assert len(chunks) >= 1
        for chunk in chunks:
            assert "chunk_index" in chunk.metadata

    def test_chunk_size_respected(self, sample_text_file):
        docs = load_document(sample_text_file)
        chunks = split_documents(docs, chunk_size=50, chunk_overlap=10)
        for chunk in chunks:
            assert len(chunk.page_content) <= 80  # 允许一定超出


class TestLoadAndSplit:
    def test_end_to_end(self, sample_text_file):
        chunks = load_and_split(sample_text_file)
        assert len(chunks) > 0
        assert all(c.page_content for c in chunks)
