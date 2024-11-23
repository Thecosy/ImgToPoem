import os
import json
import zhconv

def transform_to_simplified(data):
    """
    递归地将数据中的繁体中文转换为简体中文。
    :param data: 数据对象，可以是字典、列表或字符串
    :return: 转换后的数据
    """
    if isinstance(data, str):
        # 转换字符串
        return zhconv.convert(data, 'zh-hans')
    elif isinstance(data, list):
        # 递归处理列表中的每个元素
        return [transform_to_simplified(item) for item in data]
    elif isinstance(data, dict):
        # 递归处理字典中的每个键值对
        return {key: transform_to_simplified(value) for key, value in data.items()}
    else:
        # 非字符串、列表或字典的类型保持不变
        return data

def convert_folder_to_simplified(folder_path, output_folder=None):
    """
    将文件夹中的所有 JSON 文件中的繁体部分转换为简体中文。
    :param folder_path: 包含 JSON 文件的文件夹路径
    :param output_folder: 转换后的文件输出路径，如果为 None，则覆盖原文件
    """
    if not os.path.exists(folder_path):
        print(f"目录 {folder_path} 不存在。")
        return

    # 创建输出文件夹（如果指定且不存在）
    if output_folder:
        os.makedirs(output_folder, exist_ok=True)

    for filename in os.listdir(folder_path):
        if filename.endswith(".json"):
            file_path = os.path.join(folder_path, filename)

            try:
                # 加载 JSON 数据
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # 转换为简体中文
                simplified_data = transform_to_simplified(data)

                # 确定保存路径
                if output_folder:
                    output_path = os.path.join(output_folder, filename)
                else:
                    output_path = file_path  # 覆盖原文件

                # 保存转换后的数据
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(simplified_data, f, ensure_ascii=False, indent=4)

                print(f"文件 {filename} 转换完成，保存至 {output_path}。")

            except Exception as e:
                print(f"处理文件 {filename} 时出错: {e}")

if __name__ == "__main__":
    # 输入文件夹路径
    data_folder = "全唐诗"  # 替换为实际文件夹路径

    # 输出文件夹路径（如果为 None，则覆盖原文件）
    output_folder = "全唐诗_简体"  # 替换为需要保存的文件夹路径，如果不需要保存新文件夹，可设为 None

    # 转换文件夹中的 JSON 文件
    convert_folder_to_simplified(data_folder, output_folder)