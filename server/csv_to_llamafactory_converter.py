#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV到LLaMA-Factory格式转换器
生成符合llama-factory要求的Alpaca格式数据
"""

import pandas as pd
import json
from pathlib import Path
import argparse
import random


class LLaMAFactoryConverter:
    """CSV到LLaMA-Factory格式转换器"""
    
    def __init__(self, source_dir: str = "datasets/datasets", output_dir: str = "datasets/llamafactory_output"):
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 预定义的指令模板
        self.instruction_templates = [
            "请分析以下数据并提取关键信息",
            "根据提供的数据，请进行详细分析",
            "请解释以下数据的含义和特征",
            "基于这些数据，请提供专业的分析报告",
            "请对以下数据进行统计分析和总结"
        ]
        
        self.analysis_templates = [
            "数据包含{field_count}个字段，主要特征包括{key_fields}。",
            "这是第{row_num}行数据，显示了{key_info}等重要信息。",
            "数据记录显示{summary}，具有重要的分析价值。",
            "该数据条目反映了{context}，值得深入研究。"
        ]
    
    def read_csv(self, file_path):
        """读取CSV文件"""
        try:
            encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
            for encoding in encodings:
                try:
                    return pd.read_csv(file_path, encoding=encoding)
                except UnicodeDecodeError:
                    continue
            return None
        except Exception as e:
            print(f"读取文件失败 {file_path}: {e}")
            return None
    
    def generate_instruction(self, row_dict, file_name):
        """生成更丰富的指令"""
        # 根据文件名和数据内容生成特定指令
        if 'gpr' in file_name.lower():
            return "请分析以下地缘政治风险数据，提取关键指标和趋势信息"
        elif 'population' in file_name.lower():
            return "请分析以下人口统计数据，识别人口变化趋势和特征"
        elif 'conflict' in file_name.lower() or 'ukraine' in file_name.lower():
            return "请分析以下冲突事件数据，识别关键事件和影响"
        else:
            return random.choice(self.instruction_templates)
    
    def generate_output(self, row_dict, row_idx, file_name):
        """生成更详细的输出"""
        field_count = len(row_dict)
        key_fields = list(row_dict.keys())[:3]
        
        # 根据数据类型生成不同的分析
        if 'date' in str(row_dict).lower() or 'time' in str(row_dict).lower():
            time_info = "时间序列数据"
        else:
            time_info = "结构化数据"
        
        # 生成数据摘要
        non_null_values = [v for v in row_dict.values() if v != "N/A" and str(v).strip()]
        summary = f"包含{len(non_null_values)}个有效数据点"
        
        # 选择分析模板
        template = random.choice(self.analysis_templates)
        analysis = template.format(
            field_count=field_count,
            key_fields="、".join(key_fields),
            row_num=row_idx + 1,
            key_info=time_info,
            summary=summary,
            context=f"{file_name}数据集的重要记录"
        )
        
        # 添加具体的数据洞察
        insights = []
        for key, value in list(row_dict.items())[:3]:
            if value != "N/A":
                insights.append(f"{key}: {value}")
        
        if insights:
            analysis += f" 具体数据包括：{'; '.join(insights)}。"
        
        return analysis
    
    def convert_csv_to_alpaca(self, csv_file):
        """将CSV文件转换为Alpaca格式"""
        try:
            df = self.read_csv(csv_file)
            if df is None:
                return False
            
            # 生成输出文件路径
            relative_path = csv_file.relative_to(self.source_dir)
            new_filename = relative_path.stem + '_alpaca.json'
            output_file = self.output_dir / relative_path.parent / new_filename
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 转换数据为Alpaca格式
            alpaca_data = []
            file_name = csv_file.stem
            
            for idx, row in df.iterrows():
                # 处理NaN值
                row_dict = row.to_dict()
                for key, value in row_dict.items():
                    if pd.isna(value):
                        row_dict[key] = "N/A"
                    else:
                        row_dict[key] = str(value)
                
                # 构建数据描述
                data_str = ", ".join([f"{k}: {v}" for k, v in row_dict.items()])
                
                # 生成指令和输出
                instruction = self.generate_instruction(row_dict, file_name)
                output = self.generate_output(row_dict, idx, file_name)
                
                # 创建Alpaca格式的JSON对象
                alpaca_obj = {
                    "instruction": instruction,
                    "input": f"数据内容：{data_str}",
                    "output": output
                }
                
                alpaca_data.append(alpaca_obj)
            
            # 保存为JSON数组格式（llama-factory要求）
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(alpaca_data, f, ensure_ascii=False, indent=2)
            
            print(f"成功转换: {csv_file} -> {output_file}")
            return output_file
            
        except Exception as e:
            print(f"转换失败 {csv_file}: {e}")
            return None
    
    def create_dataset_info(self, json_files):
        """创建dataset_info.json文件"""
        dataset_info = {}
        
        for json_file in json_files:
            dataset_name = json_file.stem.replace('_alpaca', '')
            dataset_info[dataset_name] = {
                "file_name": json_file.name,
                "columns": {
                    "instruction": "instruction",
                    "input": "input", 
                    "output": "output"
                }
            }
        
        info_file = self.output_dir / "dataset_info.json"
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(dataset_info, f, ensure_ascii=False, indent=2)
        
        print(f"创建数据集信息文件: {info_file}")
        return info_file
    
    def find_csv_files(self):
        """查找所有CSV文件"""
        return list(self.source_dir.rglob("*.csv"))
    
    def process_all_files(self):
        """处理所有CSV文件"""
        csv_files = self.find_csv_files()
        print(f"找到 {len(csv_files)} 个CSV文件")
        
        success_files = []
        for csv_file in csv_files:
            print(f"正在处理: {csv_file}")
            result = self.convert_csv_to_alpaca(csv_file)
            if result:
                success_files.append(result)
        
        # 创建dataset_info.json
        if success_files:
            self.create_dataset_info(success_files)
        
        print(f"\n转换完成! 成功: {len(success_files)}/{len(csv_files)}")
        print(f"输出目录: {self.output_dir}")
        print(f"生成的文件:")
        for file in success_files:
            print(f"  - {file}")
        print(f"  - dataset_info.json")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='CSV到LLaMA-Factory格式转换器')
    parser.add_argument('--source', '-s', default='datasets/datasets', 
                       help='源目录路径 (默认: datasets/datasets)')
    parser.add_argument('--output', '-o', default='datasets/llamafactory_output',
                       help='输出目录路径 (默认: datasets/llamafactory_output)')
    
    args = parser.parse_args()
    
    # 创建转换器
    converter = LLaMAFactoryConverter(args.source, args.output)
    
    # 处理所有文件
    converter.process_all_files()


if __name__ == "__main__":
    main()
