"""
DeepSeek LLM 服务封装
支持 function calling 和流式响应
"""
import os
import json
import re
import requests
from datetime import datetime

DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
DEEPSEEK_API_BASE = os.environ.get('DEEPSEEK_API_BASE', 'https://api.deepseek.com')

# 模型选择
MODEL_CHAT = "deepseek-chat"        # V3 通用对话
MODEL_REASONER = "deepseek-reasoner"  # R1 推理模型


def chat_completion(messages, stream=False, use_reasoner=False):
    """
    调用 DeepSeek API
    
    Args:
        messages: 消息列表 [{role, content}]
        stream: 是否流式输出
        use_reasoner: 是否使用推理模型
    
    Returns:
        API 响应结果
    """
    if not DEEPSEEK_API_KEY:
        return {
            "error": "DEEPSEEK_API_KEY 未配置，请在环境变量中设置",
            "choices": [{"message": {"content": "AI 服务暂未配置，请联系管理员设置 DeepSeek API Key。"}}]
        }
    
    model = MODEL_REASONER if use_reasoner else MODEL_CHAT
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }
    
    payload = {
        "model": model,
        "messages": messages,
        "stream": stream
    }
    
    try:
        response = requests.post(
            f"{DEEPSEEK_API_BASE}/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            "error": str(e),
            "choices": [{"message": {"content": f"调用 AI 服务失败：{str(e)}"}}]
        }


def build_system_prompt():
    """构建系统提示词，包含工具描述"""
    from app.ai.prompts.system_prompt import SYSTEM_PROMPT
    from app.ai.tools import get_all_tools
    
    tools = get_all_tools()
    
    # 构建工具描述
    tools_desc = []
    for tool in tools:
        func = tool.get("function", {})
        name = func.get("name", "")
        desc = func.get("description", "")
        params = func.get("parameters", {}).get("properties", {})
        
        param_desc = []
        for param_name, param_info in params.items():
            param_type = param_info.get("type", "string")
            param_desc_str = param_info.get("description", "")
            enum_vals = param_info.get("enum", [])
            if enum_vals:
                param_desc.append(f"    - {param_name} ({param_type}): {param_desc_str}，可选值: {', '.join(map(str, enum_vals))}")
            else:
                param_desc.append(f"    - {param_name} ({param_type}): {param_desc_str}")
        
        tool_desc = f"- {name}: {desc}"
        if param_desc:
            tool_desc += "\n  参数:\n" + "\n".join(param_desc)
        tools_desc.append(tool_desc)
    
    tools_description = "\n".join(tools_desc)
    
    return SYSTEM_PROMPT.format(
        current_date=datetime.now().strftime("%Y-%m-%d %H:%M"),
        tools_description=tools_description
    )


# 工具调用正则表达式
TOOL_CALL_PATTERN = re.compile(r'```tool_call\s*\n(.*?)\n```', re.DOTALL)


def parse_tool_calls(content):
    """
    从 AI 回复中解析工具调用
    
    Returns:
        (clean_content, list of tool_calls)
    """
    tool_calls = []
    
    def extract_tool(match):
        try:
            tool_data = json.loads(match.group(1).strip())
            if isinstance(tool_data, dict) and "name" in tool_data:
                tool_calls.append({
                    "name": tool_data["name"],
                    "arguments": tool_data.get("arguments", {})
                })
        except json.JSONDecodeError:
            pass
        return ""  # 替换为空字符串
    
    clean_content = TOOL_CALL_PATTERN.sub(extract_tool, content)
    
    return clean_content.strip(), tool_calls


def process_ai_response(response, user_id=None):
    """
    处理 AI 响应，包括工具调用循环
    
    Returns:
        (final_content, tool_calls_log)
    """
    from app.ai.tools import execute_tool
    
    message = response.get("choices", [{}])[0].get("message", {})
    content = message.get("content", "")
    
    # 解析工具调用
    clean_content, tool_calls = parse_tool_calls(content)
    
    tool_calls_log = []
    
    # 如果有工具调用，执行并继续对话
    if tool_calls:
        for tc in tool_calls:
            tool_name = tc.get("name")
            arguments = tc.get("arguments", {})
            
            # 执行工具
            result = execute_tool(tool_name, arguments, user_id=user_id)
            tool_calls_log.append({
                "name": tool_name,
                "arguments": arguments,
                "result": result
            })
        
        return None, tool_calls_log  # 需要继续对话
    
    return clean_content or content, tool_calls_log
