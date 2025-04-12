import pandas as pd
import json
import os
from pathlib import Path

# Define language codes list and JSON folder path
languages = ['en_us', 'zh_cn', 'de_de', 'es_es', 'it_it', 'ru_ru']  # Supported language codes
json_folder = str(Path(__file__).parent / 'json')  # JSON files directory relative to script location

# Create json folder if it doesn't exist
os.makedirs(json_folder, exist_ok=True)

# Create an empty DataFrame for storing merged data
translations_df = pd.DataFrame()

# Read zh_cn.json as baseline
zh_cn_file_path = os.path.join(json_folder, 'zh_cn.json')
zh_cn_keys = []  # Store key order from zh_cn.json
try:
    with open(zh_cn_file_path, 'r', encoding='utf-8') as json_file:
        translations = json.load(json_file)
        translations_df = pd.DataFrame(list(translations.items()), columns=['key', 'zh_cn'])
        zh_cn_keys = translations_df['key'].tolist()  # Store key order from zh_cn.json
except FileNotFoundError:
    print(f"Warning: {zh_cn_file_path} not found, skipping.")
    translations_df = pd.DataFrame()  # Initialize empty DataFrame if file not found
except json.JSONDecodeError as e:
    print(f"Error decoding JSON from {zh_cn_file_path}: {e}")
    translations_df = pd.DataFrame()  # Initialize empty DataFrame if parsing error
except Exception as e:
    print(f"Unexpected error with {zh_cn_file_path}: {e}")

# Create a set to store all keys
all_keys = set(translations_df['key'])

# Read other language JSON files and merge
for lang in languages:
    if lang == 'zh_cn':
        continue  # Skip zh_cn as it's already read as baseline

    json_file_path = os.path.join(json_folder, f'{lang}.json')
    
    # Read JSON file
    try:
        with open(json_file_path, 'r', encoding='utf-8') as json_file:
            translations = json.load(json_file)
            # Convert JSON content to DataFrame and rename columns
            lang_df = pd.DataFrame(list(translations.items()), columns=['key', lang])
            
            # Merge into main DataFrame
            translations_df = translations_df.merge(lang_df, on='key', how='outer')  # Merge using 'key' as join column
            
            # Update all_keys set
            all_keys.update(translations.keys())

    except FileNotFoundError:
        print(f"Warning: {json_file_path} not found, skipping.")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {json_file_path}: {e}")
    except Exception as e:
        print(f"Unexpected error with {json_file_path}: {e}")

# Handle missing keys
missing_keys = []
for key in all_keys:
    if key not in translations_df['key'].values:
        # Get values from other language files and fill in
        row_data = {'key': key, 'zh_cn': None}
        for lang in languages:
            if lang != 'zh_cn':
                # Retrieve translation from respective JSON
                row_data[lang] = translations.get(key) if key in translations else None
        missing_keys.append(row_data)

# Add missing keys to final DataFrame
if missing_keys:
    missing_df = pd.DataFrame(missing_keys)
    translations_df = pd.concat([translations_df, missing_df], ignore_index=True)

# Sort by zh_cn.json order, missing keys at the end
# Create sorting index mapping
translations_df['sort_order'] = translations_df['key'].apply(lambda x: zh_cn_keys.index(x) if x in zh_cn_keys else len(zh_cn_keys))

# Sort by sort_order column
translations_df = translations_df.sort_values(by='sort_order').drop(columns='sort_order')

# Save merged DataFrame to Excel file
output_excel_path = 'translations.xlsx'
translations_df.to_excel(output_excel_path, index=False)

print(f'Merged translations saved to {output_excel_path}')
