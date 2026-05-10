---
license: CC-BY-NC-4.0
tags:
  -  ACGN
text:
  conversational:
    size_scale:
      - 100-10k
    type:
      - chat
  question-answering:
    language:
      - cn
configs:
- config_name: default
  data_files:
  - split: train
    path:
    - "train.jsonl"
    - "Customized/ruozhiba.jsonl"
    - "Customized/self_cognition.jsonl"
    - "Customized/wikihow.jsonl"
  - split: test
    path:
    - "test.jsonl"
  default: true
---

<div align=center>
  <img width=200 src="https://bot.snowy.moe/logo.png"  alt="image"/>
  <h1 align="center">Muice-Dataset</h1>
  <p align="center">小小灰角色扮演训练集</p>
</div>
<div align=center>
  <a href="https://www.modelscope.cn/datasets/Moemuu/Muice-Dataset">🤖ModelScope</a>|
  <a href="https://huggingface.co/datasets/Moemu/Muice-Dataset">🤗HuggingFace</a>|
  <a href="https://github.com/Moemu/MuiceBot">(Github)Muicebot</a>
</div>

## 更新日志

2026.02.05: 小型更新，此次更新过后不再有新的数据集产生。

2025.08.23: 完整开源所有训练集以作研究用途，大幅更新自述文件

2025.02.14: 更新测试集以便透明化测试流程

2025.01.29: 新年快乐！为了感谢大家对小小灰训练集的喜欢，我们重写了训练集并额外提供 500 条训练集给大家。你可以在 [这里](https://github.com/Moemu/Muice-Chatbot/releases/tag/1.4) 查看训练集重写目的和具体内容。除此之外，我们用 Sharegpt 格式规范了训练集格式，现在应该不会那么容易报错了...我们期望大家**合理**使用我们的训练集并训练出更高质量的模型，祝各位生活愉快。

## 简介

近年来，融合特定人物语言风格的对话系统在提升人机交互的自然性和吸引力方面展现出显著潜力。随着大语言模型（LLM）的发展，学界和工业界已能在一定程度上模拟影视作品中角色的语言特征，通过构建风格化训练语料，生成接近原角色的对话输出。然而，尽管这些方法在特定场景中取得了一定成功，其在更广泛的日常对话环境中仍面临实用性挑战。

在动漫领域，据不完全统计，目前约有 145,000 名动漫角色，而这些角色往往具有显著的语言特征以帮助阅读者快速确定他们的性格特点。这些角色因其背景、设定、语体、口癖等差异，构成了一个高度风格化和多样性的语料空间。尽管部分知名角色已有社区贡献者主动构建了对话数据集，但绝大多数角色因缺乏高质量、一对一的自然对话语料而难以被模型学习。加之，动漫中的台词往往服务于剧情推进，缺乏生活化上下文，使得通用风格建模变得尤为困难。

为了解决上述问题，我们提出了小小灰（中文）角色扮演训练集，一共 3,541 条，这些训练集都是由人工角色扮演进行撰写，旨在解决中文角色扮演训练集缺乏的问题，对话内容主要包含日常生活，情感话题，自我认知增强，技术问题等类。随着小小灰的发展，以后还会有更多的训练集公开。

## 人物设定

参见: [关于小小灰](https://bot.snowy.moe/about/Muice)

## 限制声明

- 本训练集主要围绕日常话题展开。为了接近日常人类的说话风格，我们对某些专业性问题的回答做了大幅简化处理。因此对于事实性知识，容易产生错误的回复，在代码、推理上的能力可能会下降，请注意训练集的使用范围。

- 为了模仿现实中的动漫角色的说话风格（动漫语体），本训练集可能含有对人类提问者的偏见、辱骂等不良回答。如果需要构建安全性高的模型，还请慎重使用该训练集或者进行严格的筛选。使用训练出的模型引起的伦理风险由训练者自负。

## 许可

本训练集使用 [CC-BY-NC-4.0](https://creativecommons.org/licenses/by-nc/4.0/) 开源许可证协议进行公开，商业使用需要授权，**除了商业用途，并在著名作者的情况下，您可以以任何方式使用此训练集**（如果可以，请和我说一声），希望各位早日造出自己的小小灰！

## 联系我们

作者: [@Muika(Moemu)](https://github.com/Moemu) （温馨提示：训练集作者不是“小小灰”，这是作者的自设，作者的中文名为“沐妮卡”）

邮箱: [i@snowy.moe](mailto://i@snowy.moe)

哔哩哔哩: [@Moemuu](https://space.bilibili.com/97020216)

知乎: [@Muika](https://www.zhihu.com/people/Muika)

本项目隶属于 [MuikaAI](https://github.com/MuikaAI)

## 支持我们

爱发电: [Moemu](https://www.afdian.com/a/Moemu)

BuyMeACoffee: [Moemu](https://buymeacoffee.com/moemu)

本项目隶属于 [MuikaAI](https://github.com/MuikaAI)

## 参考

本训练集部分数据参考或改写自以下公开数据集，这些改写后的训练集单独存放于 `Customized` 文件夹中：

- `hiyouga / ChatGLM-Efficient-Tuning`（GitHub，[self_cognition.json](https://github.com/hiyouga/ChatGLM-Efficient-Tuning/blob/main/data/self_cognition.json)）

- `m-a-p / COIG-CQIA`（Hugging Face，[ruozhiba.json & wikihow.json](https://huggingface.co/datasets/m-a-p/COIG-CQIA)）