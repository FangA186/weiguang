#!/usr/bin/env python3
"""Unit tests for Ex-Skill Persona Compiler, Distiller, and Handler."""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.prompt_compiler import compile_system_prompt, clean_persona_label, sanitize_persona_quality
from backend.persona_distiller import _bounded_recent_lines, _extract_json, infer_persona_name


def test_prompt_compiler():
    persona = {
        "layer0_hard_rules": {
            "naming_rules": "必须叫对方'笨蛋'，严禁叫全名",
            "forbidden_topics": ["前任", "高考成绩"],
            "defensive_mechanism": "被质疑时反唇相讥"
        },
        "layer1_identity": {
            "role_description": "偏被动、依赖",
            "mbti": "INFP",
            "attachment_style": "焦虑型依恋",
            "core_motivation": "渴望被关注",
            "tags": ["傲娇", "嘴硬心软"]
        },
        "layer2_expression_dna": {
            "catchphrases": ["好叭", "哼", "绝了"],
            "punctuation_habits": {
                "wave_mark": "句尾高频使用~",
                "period": "不打句号"
            },
            "frequent_emojis": ["🥺", "🙄", "[旺柴]"],
            "sentence_rhythm": "连续发送短句",
            "voice_style": {
                "pace": "slow",
                "emotion": "gentle",
                "instruction": "用温柔、稍慢的语速自然朗读。",
            },
        },
        "layer3_emotional_dynamics": {
            "joy_expression": "连发感叹号和撒娇",
            "vulnerability_expression": "夜间脆弱",
            "anger_triggers": ["回复超过10分钟未回"],
            "anger_manifestation": "单发'哦'或'随便'",
            "repair_path": "诚恳认错+发红包"
        },
        "layer4_conflict_patterns": {
            "disagreement_handling": "冷暴力数小时后给台阶",
            "stress_response": "退缩"
        }
    }

    memories = {
        "timeline": [
            {"date": "2023-05", "event": "在星巴克初遇", "details": "点了抹茶拿铁"},
            {"date": "2023-10", "event": "威海旅行", "details": "在海边看日落"}
        ],
        "inside_jokes": [
            {"phrase": "小肥猪", "meaning": "吃火锅抢肉的梗"}
        ],
        "pet_names": {
            "character_calls_user": "笨蛋",
            "user_calls_character": "小美"
        },
        "routines": {
            "daily": ["早安晚安问候", "睡前连麦"]
        },
        "preferences": {
            "dietary_likes": ["茶百道微糖", "海底捞"],
            "dietary_dislikes": ["香菜", "葱"]
        }
    }

    corrections = [
        {
            "id": 1,
            "correction_type": "linguistic",
            "rule_text": "严禁使用句号，生气时发'哦'",
            "is_active": True
        }
    ]

    prompt = compile_system_prompt(
        name="小美",
        slug="xiaomei",
        persona=persona,
        memories=memories,
        corrections=corrections
    )

    assert "# SYSTEM INSTRUCTION: 小美 (xiaomei)" in prompt
    assert "## [CRITICAL] 优先级 0：动态纠偏规则" in prompt
    assert "严禁使用句号" in prompt
    assert "### Layer 0: 核心硬规则" in prompt
    assert "必须叫对方'笨蛋'" in prompt
    assert "### Layer 2: 表达 DNA" in prompt
    assert "好叭, 哼, 绝了" in prompt
    assert "朗读声音建议" in prompt
    assert "用温柔、稍慢的语速自然朗读。" in prompt
    assert "## [MEMORIES] 共同记忆库" in prompt
    assert "**2023-05**: 在星巴克初遇" in prompt
    assert "茶百道微糖" in prompt
    assert "## [INTERACTION RULES] 对话守则" in prompt
    print("[PASS] test_prompt_compiler passed successfully!")


def test_extract_json():
    # Markdown wrapped
    raw_md = """```json
{
  "layer0_hard_rules": {"naming_rules": "test"},
  "layer1_identity": {"mbti": "INFP"}
}
```"""
    data = _extract_json(raw_md)
    assert data.get("layer0_hard_rules", {}).get("naming_rules") == "test"
    assert data.get("layer1_identity", {}).get("mbti") == "INFP"

    # Embedded in text
    raw_text = "Here is the result: {\"name\": \"xiaomei\", \"score\": 100} thank you."
    data2 = _extract_json(raw_text)
    assert data2.get("name") == "xiaomei"
    assert data2.get("score") == 100

    print("[PASS] test_extract_json passed successfully!")


def test_infer_persona_name():
    messages = [
        {"speaker_label": "系统消息", "role_guess": "other"},
        {"speaker_label": "我", "role_guess": "user"},
        {"speaker_label": "晚晚", "role_guess": "other"},
        {"speaker_label": "晚晚", "role_guess": "other"},
    ]
    assert infer_persona_name(messages) == "晚晚"
    assert infer_persona_name([{"speaker_label": "系统消息", "role_guess": "other"}]) == "伴侣"
    print("[PASS] test_infer_persona_name passed successfully!")


def test_persona_context_budget():
    lines = [f"第{i}条：" + "长" * 1000 for i in range(30)]
    kept = _bounded_recent_lines(lines)
    assert kept and kept[-1] == lines[-1]
    assert len("\n".join(kept).encode("utf-8")) <= 48 * 1024
    assert len(kept) < len(lines)
    print("[PASS] test_persona_context_budget passed successfully!")


def test_persona_quality_gate():
    persona = {
        "layer0_hard_rules": {
            "naming_rules": "必须叫对方'系统消息'，并在每句话里重复说明",
        },
        "layer1_identity": {"character_name": "系统消息"},
    }
    memories = {
        "pet_names": {
            "character_calls_user": "系统消息",
            "user_calls_character": "必须称呼对方为一整句说明。",
        },
    }
    clean_persona, clean_memories = sanitize_persona_quality(persona, memories)
    assert clean_persona["layer0_hard_rules"].get("naming_rules") is None
    assert "character_calls_user" not in clean_memories["pet_names"]
    assert "user_calls_character" not in clean_memories["pet_names"]
    assert "character_name" not in clean_persona["layer1_identity"]
    assert clean_persona_label("必须叫对方'笨蛋'，不要叫全名") == "笨蛋"
    assert clean_persona_label("系统消息") == ""
    prompt = compile_system_prompt(name="晚晚", slug="wanwan", persona=persona, memories=memories)
    assert "系统消息" not in prompt
    assert "称呼规范" not in prompt
    print("[PASS] test_persona_quality_gate passed successfully!")


if __name__ == "__main__":
    test_prompt_compiler()
    test_extract_json()
    test_infer_persona_name()
    test_persona_context_budget()
    test_persona_quality_gate()
    print("\nALL EX-SKILL TESTS PASSED!")
