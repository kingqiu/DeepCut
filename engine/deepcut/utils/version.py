"""版本目录管理：每次切片独立版本目录"""

import re
from datetime import datetime
from pathlib import Path


def get_next_version_tag(output_base: Path) -> str:
    """生成下一个版本标签，格式：v{N}_{timestamp}"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    existing = sorted(output_base.glob("v*_*")) if output_base.exists() else []
    max_n = 0
    for d in existing:
        match = re.match(r"v(\d+)_", d.name)
        if match:
            max_n = max(max_n, int(match.group(1)))

    return f"v{max_n + 1}_{timestamp}"


def create_version_dir(
    video_path: Path,
    output_dir: Path | None = None,
    project_id: str | None = None,
) -> Path:
    """创建版本目录，返回路径

    优先级：
    1. output_dir + project_id → {output_dir}/{project_id}/
    2. output_dir 无 project_id → {output_dir}/deepcut_output/v{N}/
    3. 无 output_dir → {video_parent}/deepcut_output/v{N}/

    目录结构：
        {base}/
        ├── clips/
        ├── thumbnails/
        ├── metadata.json
        └── transcript.json
    """
    if project_id is not None and output_dir is not None:
        # Web 模式：统一存储目录，以 project_id 为子目录名
        version_dir = output_dir / project_id
    else:
        # CLI 模式：保留版本号目录
        if output_dir is not None:
            output_base = output_dir / "deepcut_output"
        else:
            output_base = video_path.parent / "deepcut_output"

        output_base.mkdir(parents=True, exist_ok=True)
        version_tag = get_next_version_tag(output_base)
        version_dir = output_base / version_tag

    version_dir.mkdir(parents=True, exist_ok=True)
    (version_dir / "clips").mkdir(exist_ok=True)
    (version_dir / "thumbnails").mkdir(exist_ok=True)

    return version_dir
