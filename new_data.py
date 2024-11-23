import os
import json
from tqdm import tqdm
from langchain_community.embeddings import ModelScopeEmbeddings
from langchain_community.vectorstores import Chroma

# 配置参数
persist_directory = "chroma_paragraph_db"  # 数据库持久化路径
model_id = "damo/nlp_corom_sentence-embedding_chinese-base"  # 嵌入模型 ID
BATCH_SIZE = 100  # 批量大小

def add_vectors_to_chroma(new_data_folder):
    """
    向 Chroma 数据库新增向量。
    :param new_data_folder: 包含新增 JSON 数据的文件夹路径
    """
    # 检查数据库是否存在
    if not os.path.exists(persist_directory):
        print(f"数据库目录 {persist_directory} 不存在，请先初始化数据库。")
        return

    # 初始化嵌入模型
    embeddings = ModelScopeEmbeddings(model_id=model_id)

    # 加载现有数据库
    db = Chroma(persist_directory=persist_directory, embedding_function=embeddings)

    # 新增数据批量缓存
    batch_texts = []
    batch_metadatas = []

    # 遍历新数据文件夹中的所有 JSON 文件
    file_list = [f for f in os.listdir(new_data_folder) if f.endswith(".json")]

    for filename in tqdm(file_list, desc="处理新增文件"):
        file_path = os.path.join(new_data_folder, filename)
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

                        # 达到批量大小时写入数据库
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
    print(f"新增数据已写入数据库并持久化。")


if __name__ == "__main__":
    # 输入新增数据文件夹路径
    new_data_folder = "新增数据"  # 替换为实际文件夹路径

    # 向 Chroma 数据库新增向量
    add_vectors_to_chroma(new_data_folder)