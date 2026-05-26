"""
HDWS - SubSpace Container
把权重从死的矩阵变成带标签的活容器

每个 SubSpace 就是一个"星系"
- 有自己的权重参数
- 有自己的标签/名字
- 可以装子 SubSpace
- 有精度等级（LOD）
"""

import torch
import torch.nn as nn
from typing import Optional


PRECISION_MAP = {
    "FP32": torch.float32,
    "FP16": torch.float16,
    "INT8": torch.float32,
    "INT4": torch.float32,
}


class SubSpace(nn.Module):
  """
  一个子空间容器 = 一个星系

  结构：
      SubSpace("universe")
          ├── SubSpace("science")
          │       ├── SubSpace("apple_fruit")
          │       └── SubSpace("biology")
          └── SubSpace("tech")
                  ├── SubSpace("apple_company")
                  └── SubSpace("software")
  """

  def __init__(self, name: str, level: int, dim: int = 768):
    super().__init__()
    self.name = name
    self.level = level
    self.dim = dim

    self.anchor = nn.Parameter(torch.randn(dim) * 0.02)

    self.knowledge_w1: Optional[nn.Parameter] = None
    self.knowledge_w2: Optional[nn.Parameter] = None

    self.children_spaces = nn.ModuleDict()

    self.precision = "FP32"
    self.access_count = 0
    self.last_access = 0

  def init_knowledge(self, hidden_dim: Optional[int] = None):
    """初始化这个子空间的知识权重"""
    if hidden_dim is None:
      hidden_dim = self.dim * 4

    self.knowledge_w1 = nn.Parameter(
      torch.randn(self.dim, hidden_dim) * 0.02
    )
    self.knowledge_w2 = nn.Parameter(
      torch.randn(hidden_dim, self.dim) * 0.02
    )
    return self

  def add_child(self, name: str, dim: Optional[int] = None) -> "SubSpace":
    """加新知识 = 加新子容器，旧的子容器完全不动"""
    if name in self.children_spaces:
      return self.children_spaces[name]

    child = SubSpace(
      name=name,
      level=self.level + 1,
      dim=dim or self.dim,
    )
    self.children_spaces[name] = child
    return child

  def has_children(self) -> bool:
    return len(self.children_spaces) > 0

  def forward(self, x: torch.Tensor) -> torch.Tensor:
    """用这个子空间的知识权重做变换"""
    if self.knowledge_w1 is None:
      return x

    h = torch.relu(x @ self.knowledge_w1)
    return x + h @ self.knowledge_w2

  def get_anchor(self) -> torch.Tensor:
    return self.anchor

  def mark_accessed(self, step: int):
    self.access_count += 1
    self.last_access = step

  def __repr__(self):
    children_names = list(self.children_spaces.keys())
    has_knowledge = self.knowledge_w1 is not None
    return (
      f"SubSpace(name='{self.name}', level={self.level}, "
      f"knowledge={has_knowledge}, children={children_names})"
    )
