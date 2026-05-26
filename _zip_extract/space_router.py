"""
HDWS - Space Router
空间路由层：给定查询向量，在层级子空间树里找到最相关的叶子节点

核心逻辑：
1. 从宇宙根节点开始
2. 跟所有子节点的 anchor 算余弦相似度
3. 选最近的，递归往下
4. 直到叶子节点（星球）
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Tuple

from subspace import SubSpace


class SpaceRouter(nn.Module):
  """
  空间路由层

  加在 Attention 层输出之后，FFN 层之前
  根据当前 token 的语义向量，找到对应的子空间
  用该子空间的知识权重做变换，代替原来的全局 FFN
  """

  def __init__(self, root: SubSpace, top_k: int = 2):
    super().__init__()
    self.root = root
    self.top_k = top_k
    self.step = 0

  def route(
    self,
    query: torch.Tensor,
    verbose: bool = False,
  ) -> Tuple[List[SubSpace], List[float]]:
    """
    核心路由函数
    返回：(命中的子空间列表, 对应的相似度分数)
    """
    if query.dim() == 3:
      q = query.mean(dim=[0, 1])
    elif query.dim() == 2:
      q = query.mean(dim=0)
    else:
      q = query

    q = F.normalize(q, dim=-1)

    path = []
    current_node = self.root
    current_node.mark_accessed(self.step)

    if verbose:
      print(f"\n[Router] 开始路由，查询向量 norm={q.norm():.3f}")

    while current_node.has_children():
      children = list(current_node.children_spaces.values())

      anchors = torch.stack([c.get_anchor() for c in children])
      anchors = F.normalize(anchors, dim=-1)
      similarities = anchors @ q

      best_idx = similarities.argmax().item()
      best_child = children[best_idx]
      best_score = similarities[best_idx].item()

      path.append((best_child, best_score))
      best_child.mark_accessed(self.step)

      if verbose:
        print(
          f"  层级 {best_child.level}: '{best_child.name}' "
          f"(相似度={best_score:.3f})"
        )

      current_node = best_child

    self.step += 1

    leaf = path[-1][0] if path else self.root
    scores = [s for _, s in path]

    if verbose:
      print(f"  → 落地子空间: '{leaf.name}'")

    return [leaf], scores

  def forward(
    self,
    x: torch.Tensor,
    verbose: bool = False,
  ) -> torch.Tensor:
    """路由 + 用命中子空间的知识做变换"""
    target_spaces, _scores = self.route(x, verbose=verbose)

    output = x
    for space in target_spaces:
      if space.knowledge_w1 is not None:
        output = space(output)

    return output

  def add_knowledge(
    self,
    path: List[str],
    knowledge_tensor_w1: torch.Tensor,
    knowledge_tensor_w2: torch.Tensor,
  ) -> SubSpace:
    """
    往指定路径加新知识
    path = ["tech", "apple_company"] 表示 宇宙 -> tech -> apple_company
    """
    current = self.root
    for name in path:
      current = current.add_child(name)

    current.knowledge_w1 = nn.Parameter(knowledge_tensor_w1.clone())
    current.knowledge_w2 = nn.Parameter(knowledge_tensor_w2.clone())

    print(f"[Router] 新知识已加入路径: {' -> '.join(['universe'] + path)}")
    return current

  def print_tree(self, node: SubSpace = None, indent: int = 0):
    """打印整棵子空间树"""
    if node is None:
      node = self.root

    prefix = "  " * indent + ("└─ " if indent > 0 else "")
    has_k = "★" if node.knowledge_w1 is not None else "○"
    print(f"{prefix}{has_k} [{node.name}] 访问{node.access_count}次")

    for child in node.children_spaces.values():
      self.print_tree(child, indent + 1)
