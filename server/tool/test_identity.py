#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试AI身份认知功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from identity_config import (
    get_available_identities, 
    get_identity_info, 
    get_identity_system_prompt,
    get_identity_name,
    is_military_analyst
)
from llm_utils import llm

def test_identity_config():
    """测试身份配置功能"""
    print("=== AI身份认知功能测试 ===\n")
    
    # 1. 测试获取可用身份
    print("1. 可用身份列表:")
    identities = get_available_identities()
    for identity_id in identities:
        name = get_identity_name(identity_id)
        print(f"   - {identity_id}: {name}")
    
    # 2. 测试军事分析专家身份
    print(f"\n2. 军事分析专家身份测试:")
    military_info = get_identity_info("military_analyst")
    print(f"   身份名称: {military_info['name']}")
    print(f"   身份描述: {military_info['description']}")
    print(f"   关键词: {military_info['keywords']}")
    print(f"   是否为军事分析专家: {is_military_analyst('military_analyst')}")
    
    # 3. 测试系统提示词
    print(f"\n3. 系统提示词测试:")
    military_prompt = get_identity_system_prompt("military_analyst")
    print(f"   军事分析专家提示词长度: {len(military_prompt)} 字符")
    print(f"   提示词前200字符:")
    print(f"   {military_prompt[:200]}...")
    
    # 4. 测试默认身份
    print(f"\n4. 默认身份测试:")
    default_prompt = get_identity_system_prompt()
    print(f"   默认身份名称: {get_identity_name()}")
    print(f"   默认提示词长度: {len(default_prompt)} 字符")

def test_military_analyst_llm():
    """测试军事分析专家LLM功能"""
    print("\n=== 军事分析专家LLM测试 ===\n")
    
    test_questions = [
        "请分析当前中东地区的安全形势",
        "俄乌冲突对全球地缘政治格局有什么影响？",
        "如何评估台海局势的发展趋势？"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"测试问题 {i}: {question}")
        try:
            # 使用军事分析专家身份
            response = llm(question, identity_id="military_analyst")
            print(f"AI回复: {response[:200]}...")
            print("-" * 50)
        except Exception as e:
            print(f"LLM调用失败: {e}")
            print("-" * 50)

if __name__ == "__main__":
    # 测试身份配置
    test_identity_config()
    
    # 测试LLM功能（需要确保环境变量配置正确）
    print("\n" + "="*60)
    print("注意：以下LLM测试需要确保环境变量LOCAL_MODEL_URL和LOCAL_MODEL_NAME已正确配置")
    print("="*60)
    
    try:
        test_military_analyst_llm()
    except Exception as e:
        print(f"LLM测试跳过: {e}")
        print("请检查环境变量配置")



