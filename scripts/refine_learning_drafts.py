"""Apply one-time, source-checked wording fixes to learning microtopic drafts."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WIKI = ROOT / "AI-introduction" / "AI-introduction" / "wiki" / "microtopics"

# A None leaves the existing field unchanged. The answer is rebuilt from both fields.
FIXES = {
    "3.2.1-2-支持向量机": ("支持向量机在两类样本之间寻找分类边界，并通过最大化边界到最近训练样本的间隔来确定超平面。", None),
    "3.2.2-3-模型评估": ("模型评估需按任务选指标；类别不均衡时，单看准确率可能掩盖少数类识别失败。", None),
    "3.3.1-2-从浅层模型到多层非线性变换结构": ("深度网络把多层变换与非线性激活组合起来，逐级形成更抽象的特征表示；浅层模型的表示过程较短。", None),
    "3.3.2-4-MLP的局限性": ("多层感知机虽能表示复杂函数，但直接处理高维图像时缺少针对局部空间结构的先验，参数、数据和训练成本可能较高。", None),
    "3.4.1-1-价值函数和最优策略": (None, "走迷宫时，一条路马上得到小奖励，另一条路稍后到达终点；比较动作价值要把后续回报算进去。"),
    "3.4.1-2-贝尔曼最优方程和简单问题的策略求解": (None, "在迷宫的一个格子比较两种移动：当前奖励与下一格的最优价值共同决定选择。"),
    "3.4.3-2-多智能体强化学习求解范式": ("多智能体强化学习可按训练和执行时的信息共享方式，比较完全中心化、完全去中心化以及中心化训练与去中心化执行等范式。", None),
    "4.2.1-1-概念与原理": ("自监督学习利用原始数据自身构造训练目标，在缺少人工标签时学习有用表示；目标仍需按任务设计。", "遮住句子中的一部分词元，再用原句未遮住的上下文预测它们。"),
    "4.2.2-3-跨模态知识迁移": ("跨模态迁移尝试把一种模态学到的知识用于另一模态，但不同模态的表示需要对齐，并用目标任务数据验证效果。", None),
    "4.2.2-1-模型复用": (None, "在月球地貌分割任务中复用已训练的视觉模型，再用目标图像检查分割效果。"),
    "4.2.3-2-模型剪枝": (None, "删除对输出影响较小的部分权重或结构后，重新测量模型质量、实际延迟和内存占用。"),
    "4.3.1-1-图像增广": (None, "对一张猫的照片适度裁剪或调亮后仍标为“猫”，再检查变换是否保留主体。"),
    "4.4.2-4-可视化工具": ("TensorBoard 和 Weights & Biases 等工具可展示训练指标、计算图或特征分布，帮助比较实验并定位异常。", None),
    "5.4.3-1-提示工程": ("提示工程通过明确任务、可用材料、输出格式和约束条件，帮助模型给出更可核查的回答。", "要求模型只根据指定教材页概述某概念，并在找不到依据时说明资料不足。"),
    "5.3.1-3-文本生成语音": (None, "输入一段播报文字，分别指定语速和音调，检查合成语音是否清楚自然。"),
    "5.3.2-2-图像生成图像": (None, "把一张灰度照片转成彩色图，再核对主体结构是否保持。"),
    "5.4.1-2-主流架构的演进与分化": (None, "让编码器—解码器模型生成一段文档摘要，并核对摘要是否保留原文要点。"),
    "5.5.1-1-基础对齐与融合架构": (None, "把图片编码为视觉特征，经适配模块映射后交给语言模型回答“图中有什么”。"),
    "5.5.1-3-混合专家架构": (None, "一个词元进入模型时，由路由器选择少数专家处理，而不是每次让所有专家都计算。"),
    "6.2.1-1-智能体的概念界定": ("智能体通过感知获取环境信息，并通过行动影响环境；任务完成还需依据反馈判断结果。", "扫地机器人读取传感器判断障碍位置，调整行进路线并继续观察环境。"),
    "6.4.3-2-通信载体": (None, "一个智能体发送“资料已核实”的即时消息，并把证据与进度写入团队共享工作区。"),
    "6.4.3-3-协调机制": ("多智能体协调需明确任务调度、先后依赖和冲突处理；同一外部状态的写入还要安排责任与顺序。", None),
    "6.5.3-1-基本概念": (None, "个人助理读取用户授权的日程，整理空闲时段并把候选安排反馈给用户。"),
    "7.2.1-2-数据准备与处理": ("本案例先清洗犯罪记录中的异常与缺失，再处理时间、地点等特征，并确保训练和验证过程没有信息泄漏。", None),
    "7.2.1-4-算法评估": ("本案例用分层交叉验证比较模型，并结合准确率、多分类对数损失及折间波动判断效果。", None),
    "7.2.2-2-建模流程概述": ("多步时序预测可直接输出未来一段序列，也可逐步递推；两者的输出设计和误差传播方式不同。", None),
    "7.2.4-2-提示词工程与模型有效对话的艺术": (None, "写智能手表介绍时，在提示中说明目标读者、核心功能、篇幅和语气，再核对输出是否满足要求。"),
    "7.2.4-3-常见问题与解决方案": (None, "问模型一个可能超出教材证据范围的获奖信息时，要求它说明来源；无法核实时不编造获奖者。"),
    "7.1.1-2-算力训练推理资源和加速方法": (None, "同一模型分别在 CPU 与 GPU 上运行，比较实际延迟、显存或内存占用和部署成本。"),
    "7.1.2-1-Python与包管理": (None, "把训练项目的 Python 依赖版本写入环境文件，在另一台机器按文件重新创建环境。"),
    "7.2.1-3-算法实现": (None, "用同一套犯罪记录特征训练逻辑回归、随机森林与梯度提升模型，再按统一指标比较。"),
    "7.2.5-5-常见问题与解决方案": (None, "生成视频里人物动作僵硬时，调整动作描述与镜头约束，再检查连续帧是否自然。"),
    "7.3.2-1-Kaggle算法竞赛平台实践": (None, "在 Kaggle 竞赛中按给定指标验证模型并提交预测文件，同时保留独立验证集防止追逐公开榜。"),
    "8.2.2-2-无人集群协同感知与决策": ("无人集群把多个设备的感知信息结合起来，并依任务目标分配区域与行动；通信延迟和信息冲突会影响协同效果。", None),
    "8.2.2-1-无人集群的概念": (None, "多台机器人分工搬运同一件大件物资，通过通信同步位置和动作。"),
    "8.2.3-2-虚拟到现实迁移": (None, "机器人在仿真中学会抓杯子后，真机仍要面对不同的光照、材质和摩擦条件。"),
    "8.3.1-2-脑机接口": ("脑机接口采集并解码脑活动信号，将估计出的操作意图转为设备指令；解码结果存在误差。", "佩戴脑电采集设备后，系统识别一类预设意图并尝试移动虚拟光标，再检查误判率。"),
    "8.3.1-3-数字孪生": ("数字孪生用数据把物理对象或过程与虚拟模型关联起来，并随真实状态变化更新；仅有静态三维外观还不够。", "为工厂设备建立虚拟模型，接入传感器数据后同步显示温度和运行状态。"),
    "8.5.2-1-安全多方计算": ("安全多方计算让多方在约定的安全假设下共同计算函数，同时限制各方获知他人的原始输入；输出本身仍可能透露信息。", None),
    "8.5.2-4-联邦学习": ("联邦学习让参与方保留本地原始数据并交换模型更新，以协同训练；模型更新仍需额外保护和泄露评估。", None),
    "8.3.2-3-虚拟办公": (None, "团队在虚拟会议室用白板讨论方案并共享屏幕，事后仍核对决议和任务责任人。"),
    "8.4.1-2-AI推动科研设施的升级": (None, "科研装置用模型建议参数设置，实验人员再核对测量结果、校准记录和安全边界。"),
    "8.4.2-4-气候与环境科学": (None, "用 GraphCast 生成天气预报后，按地区和时段与观测及其他预报方法对比。"),
    "8.6.1-1-AI伦理的主要挑战": ("人工智能伦理挑战涉及隐私与数据使用、偏见与公平、知识产权、透明度及责任归属等方面，需结合具体场景评估。", "教材以 COMPAS 为例讨论算法偏见；评估这类系统还要核对数据、指标和具体使用情境。"),
    "8.6.2-1-AI全球治理的核心维度": ("教材把人工智能全球治理分为国际公约、标准规范、法规政策和行业规范等维度；各维度的制定主体与约束力不同。", None),
    "8.6.2-3-AI治理面临的主要问题与挑战": (None, "面对新的生成式 AI 应用，治理规则需持续更新，并检查已有规范能否覆盖新的传播和责任问题。"),
}


def main() -> None:
    changes = []
    for stem, (new_explanation, new_example) in FIXES.items():
        path = WIKI / f"{stem}.md"
        text = path.read_text(encoding="utf-8")
        before, divider, section = text.partition("## 学习说明与参考答案")
        if not divider:
            raise ValueError(stem)
        old = {}
        for key in ("explanation", "example", "answer"):
            match = re.search(rf"(?m)^{key}: (.*)$", before)
            if not match:
                raise ValueError((stem, key))
            old[key] = json.loads(match.group(1))
        explanation = new_explanation or old["explanation"]
        example = new_example or old["example"]
        answer = f"要点：{explanation} 示例：{example}"
        for key, value in (("explanation", explanation), ("example", example), ("answer", answer)):
            before, count = re.subn(
                rf"(?m)^{key}: .*?$",
                lambda _: f"{key}: {json.dumps(value, ensure_ascii=False)}",
                before,
            )
            if count != 1:
                raise ValueError((stem, key, count))
        for label, value in (("解释", explanation), ("示例", example), ("参考答案", answer)):
            section, count = re.subn(rf"(?m)^{label}：.*?$", lambda _: f"{label}：{value}", section)
            if count != 1:
                raise ValueError((stem, label, count))
        changes.append((path, before + divider + section, stem, bool(new_explanation), bool(new_example)))
    for path, text, *_ in changes:
        path.write_text(text, encoding="utf-8")
    audit = ROOT / "docs" / "learning-writing-audit.json"
    rows = json.loads(audit.read_text(encoding="utf-8"))
    by_stem = {stem: (changed_explanation, changed_example) for _, _, stem, changed_explanation, changed_example in changes}
    for row in rows:
        stem = Path(row["path"]).stem
        if stem in by_stem:
            changed_explanation, changed_example = by_stem[stem]
            if changed_explanation:
                row["explanation_origin"] = "reviewed_edit"
            if changed_example:
                row["example_origin"] = "reviewed_edit"
    audit.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"quality_edits": len(changes), "explanations": sum(row[3] for row in changes), "examples": sum(row[4] for row in changes)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
