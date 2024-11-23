from flask import Flask, request, jsonify
from flask_cors import cross_origin
import os
import json
from tqdm import tqdm
from langchain_community.embeddings import ModelScopeEmbeddings
from langchain_community.vectorstores import Chroma

app = Flask(__name__)

# 数据库持久化路径
persist_directory = "chroma_paragraph_db"

# 模型 ID
model_id = "damo/nlp_corom_sentence-embedding_chinese-base"

# 批量大小
BATCH_SIZE = 100


def initialize_database():
    """
    初始化数据库并加载数据到 Chroma。
    """
    if os.path.exists(persist_directory):
        print("数据库已存在，无需初始化。")
        return

    print("数据库不存在，开始初始化...")

    # 数据目录
    data_folder = "全唐诗_简体"  # 替换为实际文件夹路径
    file_list = [f for f in os.listdir(data_folder) if f.endswith(".json")]

    # 初始化嵌入模型
    embeddings = ModelScopeEmbeddings(model_id=model_id)

    # 初始化数据库
    db = Chroma(persist_directory=persist_directory, embedding_function=embeddings)

    # 批量缓存
    batch_texts = []
    batch_metadatas = []

    # 遍历文件夹中的所有 JSON 文件
    for filename in tqdm(file_list, desc="处理文件"):
        file_path = os.path.join(data_folder, filename)
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                for item in tqdm(data, desc=f"处理文件 {filename}", leave=False):
                    for idx, paragraph in enumerate(item["paragraphs"]):
                        metadata = {
                            "author": item.get("author", "未知作者"),
                            "title": item.get("title", "无标题"),
                            "id": item.get("id", "未知ID"),
                            "paragraphs": json.dumps(item.get("paragraphs", [])),
                            "index": idx,
                        }
                        batch_texts.append(paragraph)
                        batch_metadatas.append(metadata)

                        # 达到批量大小，写入数据库
                        if len(batch_texts) >= BATCH_SIZE:
                            db.add_texts(batch_texts, metadatas=batch_metadatas)
                            batch_texts = []
                            batch_metadatas = []

            except Exception as e:
                print(f"文件 {filename} 加载失败: {e}")

    # 处理剩余数据
    if batch_texts:
        db.add_texts(batch_texts, metadatas=batch_metadatas)

    # 持久化到磁盘
    db.persist()
    print("数据库已初始化并保存.")


def query_database(query_text, k=5):
    """
    执行查询并返回结果。
    """
    # 加载嵌入模型
    embeddings = ModelScopeEmbeddings(model_id=model_id)

    # 加载数据库
    db = Chroma(persist_directory=persist_directory, embedding_function=embeddings)

    # 查询
    results = db.similarity_search(query_text, k=k)

    # 处理结果
    result_list = []
    for result in results:
        paragraph_index = result.metadata["index"]
        doc_id = result.metadata["id"]
        author = result.metadata["author"]
        title = result.metadata["title"]
        all_paragraphs = json.loads(result.metadata["paragraphs"])  # 反序列化回列表

        result_list.append({
            "paragraph_index": paragraph_index,
            "content": result.page_content,
            "author": author,
            "title": title,
            "doc_id": doc_id,
            "all_paragraphs": all_paragraphs,
        })

    return result_list


@app.route('/img2poe/<query_text>', methods=['GET'])
@cross_origin()
def img2poe(query_text):
    """
    接收请求并查询数据库，返回相似段落。
    query_text 通过 URL 路径传递
    """
    if not query_text:
        return jsonify({"error": "No query provided"}), 400

    # Execute your query function here
    results = query_database(query_text)

    return jsonify(results)  # Return results as JSON response


if __name__ == "__main__":
    # 初始化数据库（如果尚未存在）
    initialize_database()

    # 运行 Flask 应用
    app.run(host='0.0.0.0', port=8001)
    # query_database("白色背景上有一根黑色和金色的羽毛")