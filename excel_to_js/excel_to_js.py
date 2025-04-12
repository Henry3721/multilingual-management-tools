import pandas as pd
import json
import os
import logging
import re
from typing import Dict, List, Any
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LocaleManager:
    def __init__(self, excel_path: str, locales_dir: str):
        """
        Initialize the locale manager
        
        Args:
            excel_path: Path to Excel file
            locales_dir: Directory for locale files
        """
        self.excel_path = excel_path
        self.locales_dir = locales_dir
        self.df = None
        self.load_excel()
        
    def load_excel(self):
        """
        Load Excel file
        """
        try:
            self.df = pd.read_excel(self.excel_path)
            # Ensure required columns exist
            required_cols = ['class', 'key']
            missing_cols = [col for col in required_cols if col not in self.df.columns]
            if missing_cols:
                raise ValueError(f"Excel file missing required columns: {', '.join(missing_cols)}")
            
            logger.info(f"Successfully loaded Excel file: {self.excel_path}")
            logger.info(f"Available languages: {[col for col in self.df.columns if col not in ['class', 'key']]}")
        except Exception as e:
            logger.error(f"Error loading Excel file: {str(e)}")
            raise

    def update_locale(self, class_name: str, key: str, locale: str, value: str):
        """
        Update value for specified locale
        
        Args:
            class_name: Class name (e.g., text, tip)
            key: Key name
            locale: Language code (e.g., zh-cn, en-us)
            value: Translation value
        """
        try:
            if locale not in self.df.columns:
                logger.warning(f"Language {locale} does not exist, adding new column")
                self.df[locale] = None
            
            mask = (self.df['class'] == class_name) & (self.df['key'] == key)
            if not self.df[mask].empty:
                self.df.loc[mask, locale] = value
                logger.info(f"Update successful: {class_name}.{key} -> {locale}: {value}")
            else:
                logger.warning(f"No match found: {class_name}.{key}, adding new row")
                self.add_new_entry(class_name, key, {locale: value})
        except Exception as e:
            logger.error(f"Error updating value: {str(e)}")
            raise

    def add_new_entry(self, class_name: str, key: str, values: Dict[str, str]):
        """
        Add new entry
        
        Args:
            class_name: Class name (e.g., text, tip)
            key: Key name
            values: Values dictionary, format like {'zh-cn': 'value', 'en-us': 'value'}
        """
        try:
            # 检查是否已存在
            mask = (self.df['class'] == class_name) & (self.df['key'] == key)
            if not self.df[mask].empty:
                logger.warning(f"条目已存在: {class_name}.{key}，将更新现有值")
                # 更新现有行
                for locale, value in values.items():
                    if locale not in self.df.columns:
                        self.df[locale] = None
                    self.df.loc[mask, locale] = value
                logger.info(f"更新现有条目成功: {class_name}.{key}")
            else:
                # 添加新行
                new_row = {'class': class_name, 'key': key}
                # 添加语言值
                for locale, value in values.items():
                    if locale not in self.df.columns:
                        self.df[locale] = None
                    new_row[locale] = value
                
                self.df = pd.concat([self.df, pd.DataFrame([new_row])], ignore_index=True)
                logger.info(f"添加新条目成功: {class_name}.{key}")
        except Exception as e:
            logger.error(f"添加新条目时出错: {str(e)}")
            raise
            
    def save_to_excel(self):
        """
        保存更新后的数据到 Excel
        """
        try:
            self.df.to_excel(self.excel_path, index=False)
            logger.info(f"成功保存到 Excel: {self.excel_path}")
        except Exception as e:
            logger.error(f"保存 Excel 时出错: {str(e)}")
            raise
    
    def _escape_string(self, s: Any) -> str:
        """
        处理字符串中的特殊字符
        """
        if not isinstance(s, str):
            return str(s)
        
        # 处理单引号
        s = s.replace("'", "\\'")
        # 处理换行符
        s = s.replace("\n", "\\n")
        # 处理 HTML 中常见的 <br/> 标签
        s = s.replace("<br/>", "\\n")
        
        return s
    
    def _normalize_locale(self, locale: str) -> str:
        """
        标准化语言代码格式，将下划线转换为连字符
        """
        return locale.replace('_', '-').lower()
    
    def _validate_key(self, key: str) -> str:
        """
        验证并修正键名，确保其符合 JavaScript 对象键名规范
        """
        # 如果键名为空或只包含空白字符，使用默认键名
        if not key or key.strip() == '':
            return 'default_key'
        
        # 移除键名中的特殊字符
        key = re.sub(r'[^\w\.]', '_', key)
        
        # 确保键名不以数字开头
        if key[0].isdigit():
            key = 'k_' + key
            
        return key

    def generate_js_files(self):
        try:
            # 获取所有语言列
            locale_columns = [col for col in self.df.columns if col not in ['class', 'key']]
            
            if not locale_columns:
                logger.warning("未找到任何语言列，无法生成 JS 文件")
                return
            
            # 确保目录存在
            os.makedirs(self.locales_dir, exist_ok=True)
            
            for locale in locale_columns:
                normalized_locale = self._normalize_locale(locale)
                locale_dict = {}
                
                for _, row in self.df.iterrows():
                    class_name = row['class']
                    key = row['key']
                    value = row.get(locale)
                    
                    if pd.isna(value):
                        continue
                    
                    # 验证并修正 class_name 和 key
                    class_name = self._validate_key(class_name)
                    key = self._validate_key(key)
                    
                    if class_name not in locale_dict:
                        locale_dict[class_name] = {}
                    
                    # 处理嵌套 key
                    if '.' in key:
                        parts = key.split('.')
                        # 验证每个部分
                        parts = [self._validate_key(part) for part in parts]
                        
                        current_dict = locale_dict[class_name]
                        for i, part in enumerate(parts[:-1]):
                            if part not in current_dict:
                                current_dict[part] = {}
                            # 确保当前节点是字典类型
                            if not isinstance(current_dict[part], dict):
                                # 如果不是字典，将其转换为字典并保留原值
                                original_value = current_dict[part]
                                current_dict[part] = {'_value': original_value}
                            current_dict = current_dict[part]
                        
                        # 设置最终值
                        current_dict[parts[-1]] = self._escape_string(value)
                    else:
                        # 检查是否已存在同名的嵌套对象
                        if key in locale_dict[class_name] and isinstance(locale_dict[class_name][key], dict):
                            # 如果已存在同名的嵌套对象，将值存储在特殊键下
                            locale_dict[class_name][key]['_value'] = self._escape_string(value)
                        else:
                            locale_dict[class_name][key] = self._escape_string(value)
                
                # 修改 JS 内容生成逻辑
                def generate_nested_content(data, indent=0):
                    content = ""
                    indent_str = "  " * indent
                    
                    for key, value in data.items():
                        if isinstance(value, dict):
                            # 检查是否有特殊的 _value 键
                            if '_value' in value:
                                special_value = value.pop('_value')
                                content += f"{indent_str}{key}: '{special_value}',\n"
                                if value:  # 如果还有其他键
                                    content += f"{indent_str}{key}_nested: {{\n"
                                    content += generate_nested_content(value, indent + 1)
                                    content += f"{indent_str}}},\n"
                            else:
                                content += f"{indent_str}{key}: {{\n"
                                content += generate_nested_content(value, indent + 1)
                                content += f"{indent_str}}},\n"
                        else:
                            content += f"{indent_str}{key}: '{value}',\n"
                    return content
                
                # 生成 JS 格式的内容
                js_content = "export default {\n"
                for class_name, class_dict in locale_dict.items():
                    js_content += f"  {class_name}: {{\n"
                    js_content += generate_nested_content(class_dict, 2)
                    js_content += "  },\n"
                js_content += "};"
                
                # 保存 JS 文件
                output_path = os.path.join(self.locales_dir, f"{normalized_locale}.js")
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(js_content)
                logger.info(f"成功生成语言文件: {output_path}")
                
        except Exception as e:
            logger.error(f"生成 JS 文件时出错: {str(e)}")
            raise

    def scan_and_update(self):
        try:
            # 获取所有语言列
            locale_columns = [col for col in self.df.columns if col not in ['class', 'key']]
            
            if not locale_columns:
                logger.warning("未找到任何语言列，无法更新多语言文件")
                return
            
            # 确保目录存在
            os.makedirs(self.locales_dir, exist_ok=True)
            
            # 记录需要更新的内容
            updates = []
            
            for _, row in self.df.iterrows():
                class_name = row['class']
                key = row['key']
                
                for locale in locale_columns:
                    value = row.get(locale)
                    if pd.isna(value):
                        continue
                        
                    # 标准化语言代码
                    normalized_locale = self._normalize_locale(locale)
                    
                    # 检查是否需要更新
                    js_file = os.path.join(self.locales_dir, f"{normalized_locale}.js")
                    if not os.path.exists(js_file):
                        updates.append({
                            'class': class_name,
                            'key': key,
                            'locale': locale,
                            'value': value,
                            'action': 'new'
                        })
                        continue
                    
                    # 读取现有的 JS 文件内容
                    with open(js_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 检查是否需要更新
                    if '.' in key:
                        parts = key.split('.')
                        pattern = rf"{class_name}:\s*{{\s*{parts[0]}:\s*{{\s*{parts[1]}:\s*'[^']*'"
                    else:
                        pattern = rf"{class_name}:\s*{{\s*{key}:\s*'[^']*'"
                    
                    if not re.search(pattern, content):
                        updates.append({
                            'class': class_name,
                            'key': key,
                            'locale': locale,
                            'value': value,
                            'action': 'update'
                        })
            
            # 执行更新
            if updates:
                logger.info(f"发现 {len(updates)} 个需要更新的翻译")
                for update in updates:
                    self.update_locale(
                        update['class'],
                        update['key'],
                        update['locale'],
                        update['value']
                    )
                    logger.info(f"{update['action'].upper()}: {update['class']}.{update['key']} -> {update['locale']}: {update['value']}")
                
                # 保存 Excel
                self.save_to_excel()
                # 重新生成 JS 文件
                self.generate_js_files()
                logger.info("所有更新已完成")
            else:
                logger.info("没有发现需要更新的翻译")
                
        except Exception as e:
            logger.error(f"扫描和更新过程中出错: {str(e)}")
            raise

def main():
    import sys
    import argparse
    
    script_dir = Path(__file__).parent.absolute()
    
    default_excel = script_dir / "h5translation.xlsx"
    default_locales_dir = script_dir
    
    parser = argparse.ArgumentParser(description='Multilingual Excel Management Tool')
    parser.add_argument('--excel', type=str, 
                       help='Excel file path (default: h5translation.xlsx)',
                       default=str(default_excel))
    parser.add_argument('--locales-dir', type=str, help='Locale files directory', default=str(default_locales_dir))
    parser.add_argument('--action', type=str, choices=['update', 'add', 'generate', 'scan'], 
                        help='Action type: update, add, generate(files), scan(and update)', 
                        default='scan')
    
    parser.add_argument('--class', dest='class_name', type=str, help='Class name')
    parser.add_argument('--key', type=str, help='Key name')
    parser.add_argument('--locale', type=str, help='Language code')
    parser.add_argument('--value', type=str, help='Translation value')
    
    args = parser.parse_args()
    
    try:
        if not Path(args.excel).exists():
            print(f"Error: Excel file not found {args.excel}")
            print(f"Please ensure h5translation.xlsx exists in script directory: {script_dir}")
            sys.exit(1)
            
        manager = LocaleManager(args.excel, args.locales_dir)
        
        if args.action == 'update':
            if not all([args.class_name, args.key, args.locale, args.value]):
                print("Update operation requires --class, --key, --locale and --value parameters")
                sys.exit(1)
            manager.update_locale(args.class_name, args.key, args.locale, args.value)
            manager.save_to_excel()
            
        elif args.action == 'add':
            if not all([args.class_name, args.key, args.locale, args.value]):
                print("Add operation requires --class, --key, --locale and --value parameters")
                sys.exit(1)
            manager.add_new_entry(args.class_name, args.key, {args.locale: args.value})
            manager.save_to_excel()
            
        elif args.action == 'generate':
            manager.generate_js_files()
            
        else:  # Default to scan operation
            manager.scan_and_update()
            
        print("Operation completed successfully!")
        
    except Exception as e:
        print(f"Operation failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()