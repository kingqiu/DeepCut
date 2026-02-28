"""融合策略：ABC 基类 + 具体策略子类

切片核心思路：
- 有人声视频 → 先按场景/话题切大块，再在大块内找句子边界精切
- 无人声视频 → 按场景切换强制切割，运镜变化辅助

关键概念：
- 强制切分点（scene_change, topic_boundary）：必须在此处切割，不受 min_duration 合并
- 候选切分点（sentence_boundary, motion_*）：仅在需要时使用
"""

from abc import ABC, abstractmethod

from deepcut.models.analysis import AnalysisResult
from deepcut.models.clip import ClipPlan
from deepcut.models.video import VideoInfo

# 默认强制切割的原因类型：这些切分点不会被 min_duration 合并掉
# 各策略可传入不同的 forced_reasons 集合
DEFAULT_FORCED_REASONS = {"topic_boundary", "video_start", "video_end"}

# 视觉优先策略额外将场景切换设为强制切割
VISUAL_FORCED_REASONS = {"scene_change", "topic_boundary", "video_start", "video_end"}

# 硬切原因：这些切分点处不添加 overlap（前后画面完全不同，重叠无意义）
HARD_CUT_REASONS = {"scene_change", "video_start", "video_end"}


class FusionStrategy(ABC):
    """融合策略基类（策略模式）"""

    @abstractmethod
    def fuse(
        self,
        video_info: VideoInfo,
        analysis: AnalysisResult,
        min_duration: float,
        max_duration: float,
        overlap_duration: float,
    ) -> list[ClipPlan]:
        """根据分析结果生成切片计划

        Args:
            video_info: 视频基本信息
            analysis: 综合分析结果
            min_duration: 最小切片时长（参考值）
            max_duration: 最大切片时长（参考值）
            overlap_duration: 重叠过渡时长

        Returns:
            切片计划列表
        """
        ...


def _build_clips(
    cut_points: list[tuple[float, str]],
    min_duration: float,
    max_duration: float,
    overlap_duration: float,
    forced_reasons: set[str] | None = None,
    hard_cut_reasons: set[str] | None = None,
) -> list[ClipPlan]:
    """从候选切分点构建切片计划

    核心规则：
    1. 强制切分点（由 forced_reasons 定义）总是在此切割，不受 min_duration 合并
    2. 候选切分点仅在累积时长 >= min_duration 时才切
    3. 超过 max_duration 时在中间找最近的自然切分点做拆分
    4. 硬切点（由 hard_cut_reasons 定义）处不添加 overlap（前后画面完全不同）
    """
    if forced_reasons is None:
        forced_reasons = DEFAULT_FORCED_REASONS
    if hard_cut_reasons is None:
        hard_cut_reasons = set()

    clips: list[ClipPlan] = []
    current_start = cut_points[0][0]
    clip_index = 0

    for i in range(1, len(cut_points)):
        point_time, point_reason = cut_points[i]
        segment_duration = point_time - current_start

        is_forced = point_reason in forced_reasons
        is_last = (i == len(cut_points) - 1)
        is_hard_cut = point_reason in hard_cut_reasons

        # 太短则跳过（合并到下一段），但强制切分点除外
        if segment_duration < min_duration and not is_last and not is_forced:
            continue

        # 太长则拆分：在中间找一个合适的切分点
        if segment_duration > max_duration:
            mid_point = current_start + max_duration
            best_cut = _find_nearest_cut(
                cut_points, mid_point,
                current_start + min_duration,
                point_time - min_duration,
            )
            if best_cut is not None:
                best_is_hard = best_cut[1] in hard_cut_reasons
                next_overlap = 0.0 if best_is_hard else overlap_duration
                clips.append(
                    ClipPlan(
                        index=clip_index,
                        start=current_start,
                        end=best_cut[0],
                        split_reason=best_cut[1],
                        overlap_prev=overlap_duration if clip_index > 0 else 0.0,
                        overlap_next=next_overlap,
                    )
                )
                clip_index += 1
                current_start = best_cut[0] - next_overlap
                remaining = point_time - current_start
                if remaining < min_duration and not is_last and not is_forced:
                    continue

        # 计算实际时长（可能因上面的拆分而改变）
        segment_duration = point_time - current_start

        # 硬切点不添加 overlap
        next_overlap = 0.0 if is_hard_cut else overlap_duration
        if is_last:
            next_overlap = 0.0

        # 正常切片
        clips.append(
            ClipPlan(
                index=clip_index,
                start=current_start,
                end=point_time,
                split_reason=point_reason,
                overlap_prev=overlap_duration if clip_index > 0 else 0.0,
                overlap_next=next_overlap,
            )
        )
        clip_index += 1
        current_start = point_time - next_overlap

    return clips


def _find_nearest_cut(
    cut_points: list[tuple[float, str]],
    target: float,
    lower_bound: float,
    upper_bound: float,
) -> tuple[float, str] | None:
    """在指定范围内找最近的自然切分点"""
    best: tuple[float, str] | None = None
    best_dist = float("inf")

    for time, reason in cut_points:
        if lower_bound <= time <= upper_bound:
            dist = abs(time - target)
            if dist < best_dist:
                best_dist = dist
                best = (time, reason)

    return best


class SpeechFirstStrategy(FusionStrategy):
    """语义优先策略：有人声视频

    当 LLM 话题分段可用时：
    - 直接用话题段落作为切片边界（一个话题 = 一个切片）
    - 话题过长（超过 max_duration）时，在内部找句子边界拆分
    - 话题间添加 overlap 过渡

    当 LLM 话题不可用时（回退模式）：
    - 用 sentence_boundary + scene_change 按 min/max_duration 规则切分
    """

    def fuse(
        self,
        video_info: VideoInfo,
        analysis: AnalysisResult,
        min_duration: float,
        max_duration: float,
        overlap_duration: float,
    ) -> list[ClipPlan]:
        if analysis.topics:
            return self._fuse_with_topics(
                video_info, analysis, max_duration, overlap_duration,
            )
        return self._fuse_fallback(
            video_info, analysis, min_duration, max_duration, overlap_duration,
        )

    def _fuse_with_topics(
        self,
        video_info: VideoInfo,
        analysis: AnalysisResult,
        max_duration: float,
        overlap_duration: float,
    ) -> list[ClipPlan]:
        """LLM 话题驱动切分：话题段落直接作为切片"""
        from loguru import logger

        clips: list[ClipPlan] = []
        duration = video_info.duration

        # LLM 话题已经做了时长控制（prompt 限制 120s 上限），
        # 这里只在话题真正过长时才拆分，用 120s 作为硬上限
        topic_max_duration = max(max_duration, 120.0)

        # 收集句子边界，用于过长话题的内部拆分
        sentence_ends: list[float] = []
        if analysis.transcript:
            sentence_ends = sorted({seg.end for seg in analysis.transcript.segments})

        for i, topic in enumerate(analysis.topics):
            topic_start = topic.start
            topic_end = topic.end

            # 保证不超出视频边界
            topic_start = max(0.0, topic_start)
            topic_end = min(duration, topic_end)

            topic_dur = topic_end - topic_start
            if topic_dur <= 0:
                continue

            # 话题过长：在内部找句子边界拆分
            if topic_dur > topic_max_duration:
                sub_clips = self._split_long_topic(
                    topic_start, topic_end, topic.topic, topic.summary,
                    sentence_ends, max_duration, overlap_duration,
                    start_index=len(clips),
                )
                clips.extend(sub_clips)
            else:
                # 正常：一个话题 = 一个切片
                prev_overlap = overlap_duration if clips else 0.0
                is_last = (i == len(analysis.topics) - 1)
                next_overlap = 0.0 if is_last else overlap_duration

                clips.append(
                    ClipPlan(
                        index=len(clips),
                        start=topic_start - prev_overlap if prev_overlap and topic_start > prev_overlap else topic_start,
                        end=topic_end,
                        split_reason="topic_boundary",
                        overlap_prev=prev_overlap,
                        overlap_next=next_overlap,
                        topic=topic.topic,
                        summary=topic.summary,
                    )
                )

        logger.info(
            f"SpeechFirst (LLM 话题驱动): {len(analysis.topics)} 个话题 → {len(clips)} 个切片"
        )
        return clips

    def _split_long_topic(
        self,
        start: float,
        end: float,
        topic: str,
        summary: str,
        sentence_ends: list[float],
        max_duration: float,
        overlap_duration: float,
        start_index: int,
    ) -> list[ClipPlan]:
        """将过长的话题在句子边界处拆分"""
        clips: list[ClipPlan] = []
        current_start = start

        while current_start < end - 1.0:
            target_end = current_start + max_duration

            if target_end >= end:
                # 剩余部分不超过 max_duration，直接作为最后一片
                clips.append(
                    ClipPlan(
                        index=start_index + len(clips),
                        start=current_start,
                        end=end,
                        split_reason="topic_boundary",
                        overlap_prev=overlap_duration if clips else 0.0,
                        overlap_next=0.0,
                        topic=topic,
                        summary=summary,
                    )
                )
                break

            # 在 target_end 附近找最近的句子边界
            best_cut = None
            best_dist = float("inf")
            for se in sentence_ends:
                if current_start + 15.0 <= se <= end - 5.0:
                    dist = abs(se - target_end)
                    if dist < best_dist:
                        best_dist = dist
                        best_cut = se

            cut_point = best_cut if best_cut else target_end

            clips.append(
                ClipPlan(
                    index=start_index + len(clips),
                    start=current_start,
                    end=cut_point,
                    split_reason="topic_split",
                    overlap_prev=overlap_duration if clips else 0.0,
                    overlap_next=overlap_duration,
                    topic=topic,
                    summary=summary,
                )
            )
            current_start = cut_point - overlap_duration

        return clips

    def _fuse_fallback(
        self,
        video_info: VideoInfo,
        analysis: AnalysisResult,
        min_duration: float,
        max_duration: float,
        overlap_duration: float,
    ) -> list[ClipPlan]:
        """回退模式：无 LLM 话题时，用规则切分"""
        cut_points: list[tuple[float, str]] = []

        # 场景切换（候选切分点，不强制 — 对话完整性优先于画面切换）
        for scene in analysis.scenes:
            cut_points.append((scene.timestamp, "scene_change"))

        # 转录句界（候选切分点）
        if analysis.transcript:
            for seg in analysis.transcript.segments:
                cut_points.append((seg.end, "sentence_boundary"))

        # 运镜突变（候选切分点）
        for motion in analysis.motions:
            if motion.motion_type == "transition":
                cut_points.append((motion.start, "motion_transition"))

        # 去重、排序
        cut_points = list(set(cut_points))
        cut_points.sort(key=lambda x: x[0])

        # 添加视频首尾
        duration = video_info.duration
        if not cut_points or cut_points[0][0] > 0.1:
            cut_points.insert(0, (0.0, "video_start"))
        if not cut_points or cut_points[-1][0] < duration - 0.1:
            cut_points.append((duration, "video_end"))

        return _build_clips(
            cut_points, min_duration, max_duration, overlap_duration,
            forced_reasons=DEFAULT_FORCED_REASONS,
        )


class VisualFirstStrategy(FusionStrategy):
    """视觉优先策略：无人声视频

    场景切换是强制切割点，每个场景变成独立切片。
    运镜变化作为辅助切分点。
    """

    def fuse(
        self,
        video_info: VideoInfo,
        analysis: AnalysisResult,
        min_duration: float,
        max_duration: float,
        overlap_duration: float,
    ) -> list[ClipPlan]:
        cut_points: list[tuple[float, str]] = []

        # 1. 场景切换（强制切割）
        for scene in analysis.scenes:
            cut_points.append((scene.timestamp, "scene_change"))

        # 2. 运镜变化（辅助切分）
        for motion in analysis.motions:
            if motion.motion_type == "transition":
                cut_points.append((motion.start, "motion_transition"))
            elif motion.motion_type != "static":
                cut_points.append((motion.start, f"motion_{motion.motion_type}_start"))
                cut_points.append((motion.end, f"motion_{motion.motion_type}_end"))

        # 去重、排序
        cut_points = list(set(cut_points))
        cut_points.sort(key=lambda x: x[0])

        duration = video_info.duration
        if not cut_points or cut_points[0][0] > 0.1:
            cut_points.insert(0, (0.0, "video_start"))
        if not cut_points or cut_points[-1][0] < duration - 0.1:
            cut_points.append((duration, "video_end"))

        # 如果切分点太少（场景太少），补充固定间隔切分
        if len(cut_points) < 3 and duration > max_duration * 2:
            interval = (min_duration + max_duration) / 2
            t = interval
            while t < duration - min_duration:
                cut_points.append((t, "fixed_interval"))
                t += interval
            cut_points = list(set(cut_points))
            cut_points.sort(key=lambda x: x[0])

        # VisualFirst: scene_change 是强制切割点 + 硬切（不加 overlap）
        return _build_clips(
            cut_points, min_duration, max_duration, overlap_duration,
            forced_reasons=VISUAL_FORCED_REASONS,
            hard_cut_reasons=HARD_CUT_REASONS,
        )
