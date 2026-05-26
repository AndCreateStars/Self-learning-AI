"""
HDWS 路由验证脚本

运行: python verify.py
"""

import sys

if hasattr(sys.stdout, "reconfigure"):
  sys.stdout.reconfigure(encoding="utf-8")

import torch
import torch.nn.functional as F

from subspace import SubSpace
from space_router import SpaceRouter


DIM = 64
HIDDEN = DIM * 4


def build_tree() -> SubSpace:
  """构建一棵测试用的子空间树"""
  root = SubSpace(name="universe", level=0, dim=DIM)

  science = root.add_child("science")
  tech = root.add_child("tech")

  apple_fruit = science.add_child("apple_fruit")
  biology = science.add_child("biology")

  apple_company = tech.add_child("apple_company")
  software = tech.add_child("software")

  # 给叶子节点初始化知识权重
  for leaf in [apple_fruit, biology, apple_company, software]:
    leaf.init_knowledge(HIDDEN)

  return root


def set_anchor_toward(node: SubSpace, direction: torch.Tensor):
  """把 anchor 设成某个方向，方便控制路由结果"""
  node.anchor.data = F.normalize(direction.clone(), dim=-1) * 0.02


def main():
  print("=" * 55)
  print("  HDWS 空间路由验证")
  print("=" * 55)

  root = build_tree()
  router = SpaceRouter(root)

  # 手动设定 anchor 方向，模拟"语义分区"
  dir_tech = torch.randn(DIM)
  dir_science = -dir_tech  # 故意设成相反方向

  set_anchor_toward(root.children_spaces["tech"], dir_tech)
  set_anchor_toward(root.children_spaces["science"], dir_science)

  set_anchor_toward(
    root.children_spaces["tech"].children_spaces["apple_company"],
    dir_tech + torch.randn(DIM) * 0.1,
  )
  set_anchor_toward(
    root.children_spaces["tech"].children_spaces["software"],
    -dir_tech,
  )
  set_anchor_toward(
    root.children_spaces["science"].children_spaces["apple_fruit"],
    dir_science + torch.randn(DIM) * 0.1,
  )
  set_anchor_toward(
    root.children_spaces["science"].children_spaces["biology"],
    -dir_science,
  )

  # 测试 1：tech 方向的查询应该路由到 tech 分支
  print("\n【测试 1】查询向量偏向 tech")
  q_tech = F.normalize(dir_tech + torch.randn(DIM) * 0.05, dim=-1)
  x = q_tech.unsqueeze(0).unsqueeze(0).expand(1, 8, DIM)  # [1, 8, dim]
  leaves, scores = router.route(x, verbose=True)
  print(f"  命中: {leaves[0].name}")

  # 测试 2：science 方向的查询
  print("\n【测试 2】查询向量偏向 science")
  q_science = F.normalize(dir_science + torch.randn(DIM) * 0.05, dim=-1)
  x2 = q_science.unsqueeze(0).unsqueeze(0).expand(1, 8, DIM)
  leaves2, _ = router.route(x2, verbose=True)
  print(f"  命中: {leaves2[0].name}")

  # 测试 3：forward 能跑通
  print("\n【测试 3】forward 前向传播")
  out = router(x, verbose=False)
  print(f"  输入 shape: {x.shape}  →  输出 shape: {out.shape}")
  print(f"  输出与输入不同: {not torch.allclose(out, x)}")

  # 打印访问统计
  print("\n【子空间树 + 访问统计】")
  router.print_tree()

  print("\n验证完成 ✓")


if __name__ == "__main__":
  main()
