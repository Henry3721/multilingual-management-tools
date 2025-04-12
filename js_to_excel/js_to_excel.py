import pandas as pd
import json
import os
import logging
import re
from typing import Dict, List, Tuple
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_js_file(file_path: str) -> Dict:
    """
    Parse JS file and return a dictionary
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # 移除 export default 和分号
            content = content.replace('export default', '')
            
            # 处理注释 (单行注释)
            content = re.sub(r'//.*?\n', '\n', content)
            
            # 移除末尾的分号
            content = content.strip()
            if content.endswith(';'):
                content = content[:-1]
            
            # 创建最终结果字典
            result = {}
            
            # 基本方法：手动提取嵌套对象
            # 匹配顶级对象，如 text: {...}, tip: {...} 等
            top_level_pattern = r'(\w+)\s*:\s*{([^{}]|(?R))*}'
            
            # 获取所有顶级匹配
            current_pos = 0
            while current_pos < len(content):
                # 查找下一个顶级键名
                match = re.search(r'(\w+)\s*:', content[current_pos:])
                if not match:
                    break
                    
                key = match.group(1)
                start_pos = current_pos + match.end()
                
                # 跳过冒号和空白
                while start_pos < len(content) and content[start_pos] != '{':
                    start_pos += 1
                    
                if start_pos >= len(content):
                    break
                    
                # 找到对应的闭合大括号
                bracket_count = 1
                end_pos = start_pos + 1
                
                while end_pos < len(content) and bracket_count > 0:
                    if content[end_pos] == '{':
                        bracket_count += 1
                    elif content[end_pos] == '}':
                        bracket_count -= 1
                    end_pos += 1
                
                if bracket_count != 0:
                    raise ValueError(f"Cannot find closing bracket for class {key}")
                
                # 提取类内容 (不包括外层的大括号)
                class_content = content[start_pos+1:end_pos-1].strip()
                
                # 解析类内容
                class_dict = {}
                
                # 解析类中的所有键值对
                item_pattern = r'([^,{}]+?)\s*:\s*[\'"]([^\'"]*)[\'"],?'
                items = re.finditer(item_pattern, class_content)
                
                for item in items:
                    item_key = item.group(1).strip()
                    item_value = item.group(2)
                    class_dict[item_key] = item_value
                
                result[key] = class_dict
                current_pos = end_pos
            
            logger.info(f"Successfully parsed file: {file_path}, found {len(result)} top-level categories")
            return result
                
    except Exception as e:
        logger.error(f"Error parsing file {file_path}: {str(e)}")
        raise

def flatten_dict(d: Dict, parent_key: str = '', sep: str = '.') -> List[Tuple[str, str, str, int]]:
    """
    Flatten nested dictionary into a list while maintaining original order
    """
    items = []
    # 移除特殊键 __order__
    order_keys = d.pop('__order__', list(d.keys()))
    
    # 按照原始顺序遍历
    for idx, k in enumerate(order_keys):
        if k not in d:
            continue
        v = d[k]
        class_name = k
        if isinstance(v, dict):
            # 记录子键的顺序
            sub_keys = list(v.keys())
            for sub_idx, sub_k in enumerate(sub_keys):
                sub_v = v[sub_k]
                if isinstance(sub_v, dict):
                    # 如果还有更深层次的嵌套，继续展平
                    subsub_keys = list(sub_v.keys())
                    for subsub_idx, subsub_k in enumerate(subsub_keys):
                        subsub_v = sub_v[subsub_k]
                        items.append((class_name, f"{sub_k}.{subsub_k}", subsub_v, idx*10000 + sub_idx*100 + subsub_idx))
                else:
                    items.append((class_name, sub_k, sub_v, idx*10000 + sub_idx))
        else:
            items.append((parent_key, k, v, idx))
    return items

def js_to_excel(js_files: Dict[str, str], output_excel_path: str):
    """
    Convert multiple JS language files to Excel spreadsheet
    """
    try:
        # Create base DataFrame
        all_data = {}
        order_info = {}
        
        # Process first file to get baseline order
        first_lang = next(iter(js_files))
        first_file = js_files[first_lang]
        first_data = parse_js_file(first_file)
        
        if not first_data:
            logger.warning(f"{first_lang} parsing result is empty, please check file format")
            raise ValueError("Base file parsing resulted in empty data")
            
        # 展平字典，保留顺序信息
        first_flattened = flatten_dict(first_data)
        
        if not first_flattened:
            logger.warning(f"{first_lang} flattened data is empty, please check parsing result")
            raise ValueError("Base file flattening resulted in empty data")
        
        # 创建基准 DataFrame，包含顺序列
        base_df = pd.DataFrame(first_flattened, columns=['class', 'key', first_lang, 'order'])
        
        # 记录每个 class 和 key 的顺序
        for _, row in base_df.iterrows():
            class_name = row['class']
            key = row['key']
            order = row['order']
            order_info[(class_name, key)] = order
        
        # 处理其他语言文件
        for lang, file_path in list(js_files.items())[1:]:
            data = parse_js_file(file_path)
            
            if not data:
                logger.warning(f"{lang} 解析结果为空，请检查文件格式")
                continue
                
            flattened_data = flatten_dict(data)
            
            if not flattened_data:
                logger.warning(f"{lang} 展平后的数据为空，请检查解析结果")
                continue
            
            # 创建当前语言的 DataFrame
            current_df = pd.DataFrame(flattened_data, columns=['class', 'key', lang, 'order'])
            
            # 合并数据
            base_df = pd.merge(base_df, current_df[['class', 'key', lang]], 
                             on=['class', 'key'], how='left')
        
        # 按照原始顺序排序
        base_df = base_df.sort_values('order')
        
        # 删除顺序列
        base_df = base_df.drop('order', axis=1)
            
        # 保存到 Excel
        base_df.to_excel(output_excel_path, index=False)
        logger.info(f"Successfully exported data to {output_excel_path}, total {len(base_df)} records")
        return base_df
        
    except Exception as e:
        logger.error(f"Error during processing: {str(e)}")
        raise

if __name__ == "__main__":
    # Get script directory
    script_dir = Path(__file__).parent.absolute()
    
    # 按照指定顺序设置语言文件映射
    language_files = {
        'en_us': str(script_dir / "en-us.js"),
        'zh_cn': str(script_dir / "zh-cn.js"),
        'de_de': str(script_dir / "de-de.js"),
        'es_es': str(script_dir / "es-es.js"),
        'it_it': str(script_dir / "it-it.js"),
        'ru_ru': str(script_dir / "ru-ru.js")
    }
    
    output_excel_path = script_dir / "output.xlsx"
    
    try:
        # 检查所有语言文件是否存在
        missing_files = []
        for lang, file_path in language_files.items():
            if not Path(file_path).exists():
                missing_files.append(f"{lang}: {file_path}")
        
        if missing_files:
            print("Error: The following language files are missing:")
            for file in missing_files:
                print(file)
            sys.exit(1)
            
        import sys
        
        df = js_to_excel(language_files, str(output_excel_path))
        print(f"Processing complete! Exported {len(df)} records to {output_excel_path}")
    except Exception as e:
        print(f"Processing failed: {str(e)}")
        sys.exit(1)