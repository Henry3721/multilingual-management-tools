import pandas as pd
import json
import os

# 读取 Excel 文件
def read_excel(file_path):
    return pd.read_excel(file_path)

# 更新多语言 JSON 文件
def update_language_files(data_frame, output_directory):
    updated_count = 0  # 计数器以跟踪更新的内容

    # 确保输出目录存在
    os.makedirs(output_directory, exist_ok=True)

    # 读取现有的语言文件内容
    language_files = {}
    for lang in data_frame.columns[1:]:  # 从第二列开始，假设第一列为 key
        lang_file_path = os.path.join(output_directory, f"{lang}.json")
        
        try:
            if os.path.getsize(lang_file_path) > 0:  # 检查文件是否为空
                with open(lang_file_path, 'r', encoding='utf-8') as file:
                    language_files[lang] = json.load(file)
            else:
                language_files[lang] = {}  # 如果文件为空，初始化为空字典
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error reading {lang_file_path}: {e}")
            language_files[lang] = {}  # 如果文件不存在或格式错误，初始化为空字典

    # 读取每一行的数据，更新语言文件中的内容
    for _, row in data_frame.iterrows():
        key = row['key']
        print(f"Processing key: {key}")  # 打印当前处理的 key
        
        # 遍历每一列语言的翻译
        for lang in row.index[1:]:  # 从下一列开始，假设第一列为 key
            if lang in row and pd.notna(row[lang]):
                # 更新或新增该语言的翻译内容
                previous_value = language_files[lang].get(key, None)
                language_files[lang][key] = row[lang]
                
                # 只在内容实际改变时增加更新计数
                if previous_value != language_files[lang][key]:
                    updated_count += 1
                    print(f"Updated {lang} - {key}: {row[lang]}")
                else:
                    print(f"No change for {lang} - {key}: {row[lang]} (remains the same)")

    # 写入到每个语言对应的 JSON 文件
    for lang, translations in language_files.items():
        json_file = os.path.join(output_directory, f"{lang}.json")
        with open(json_file, 'w', encoding='utf-8') as file:
            json.dump(translations, file, ensure_ascii=False, indent=4)
        print(f"Wrote translations to {json_file}")

    # 打印更新的内容
    print(f"Total updated entries: {updated_count}")

# 主程序
if __name__ == "__main__":
    excel_file = 'translations.xlsx'  # Excel 文件路径
    output_directory = 'translations'   # 输出 JSON 文件的目录
    data = read_excel(excel_file)      # 读取 Excel 文件
    update_language_files(data, output_directory)  # 更新语言 JSON 文件
