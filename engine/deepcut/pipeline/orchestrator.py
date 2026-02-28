"""Pipeline 编排器：7 步流水线"""

import json
import tempfile
import time
from pathlib import Path

from loguru import logger

from deepcut.ai.llm_client import LLMClient
from deepcut.ai.tag_generator import TagGenerator
from deepcut.ai.topic_segmenter import TopicSegmenter
from deepcut.analyzers.motion_detector import MotionDetector
from deepcut.analyzers.scene_detector import SceneDetector
from deepcut.analyzers.transcriber import Transcriber
from deepcut.analyzers.vad_detector import VADDetector
from deepcut.config import DeepCutConfig
from deepcut.exceptions import PipelineError
from deepcut.fusion.engine import FusionEngine
from deepcut.models.analysis import AnalysisResult, TranscriptResult, VADResult
from deepcut.models.clip import ClipMetadata, ClipPlan, ClipTags, OutputMetadata
from deepcut.models.video import VideoInfo
from deepcut.utils.logging import step_done, step_start
from deepcut.utils.version import create_version_dir
from deepcut.video.cutter import batch_cut
from deepcut.video.extract import extract_audio
from deepcut.video.probe import probe_video

TOTAL_STEPS = 7


class PipelineOrchestrator:
    """7 步切片流水线编排器

    Step 1: 预处理 - 视频探测 + 音频提取
    Step 2: VAD 检测 - 判断有无人声
    Step 3A: 语音分析 - 转录 + 话题分段（有人声时）
    Step 3B: 视觉分析 - 场景检测 + 运镜检测
    Step 4: 融合决策 - 选择策略，生成切片计划
    Step 5: 视频切割 - FFmpeg 批量切割
    Step 6: AI 标签 - 多维度标签生成
    Step 7: 输出 - 保存 metadata.json + transcript.json
    """

    def __init__(
        self,
        config: DeepCutConfig,
        disable_motion: bool = False,
        disable_speech: bool = False,
    ) -> None:
        self.config = config
        self.disable_motion = disable_motion
        self.disable_speech = disable_speech

    def run(
        self,
        input_path: Path,
        output_dir: Path | None = None,
    ) -> Path:
        """执行完整 pipeline

        Args:
            input_path: 输入视频路径
            output_dir: 输出目录（可选）

        Returns:
            版本目录路径

        Raises:
            PipelineError: Pipeline 任意步骤失败
        """
        pipeline_start = time.monotonic()
        logger.info(f"{'=' * 60}")
        logger.info(f"DeepCut Pipeline 开始: {input_path.name}")
        logger.info(f"{'=' * 60}")

        # 创建版本目录
        version_dir = create_version_dir(input_path, output_dir)
        logger.info(f"输出目录: {version_dir}")

        audio_path: Path | None = None

        try:
            # Step 1: 预处理
            video_info, audio_path = self._step1_preprocess(input_path)

            # Step 2: VAD
            vad_result = self._step2_vad(audio_path, video_info)

            # Step 3A/3B: 分析（并行概念，但串行执行）
            analysis = self._step3_analysis(audio_path, input_path, video_info, vad_result)

            # Step 4: 融合决策
            clip_plans = self._step4_fusion(video_info, analysis)

            # Step 5: 视频切割
            clip_paths = self._step5_cut(input_path, clip_plans, version_dir)

            # Step 6: AI 标签
            clip_plans = self._step6_tagging(clip_plans, analysis, video_info, input_path)

            # Step 7: 输出
            self._step7_output(
                version_dir, video_info, clip_plans, clip_paths, analysis
            )

        finally:
            # 清理临时文件
            if audio_path is not None and audio_path.exists():
                try:
                    audio_path.unlink()
                    logger.debug(f"已清理临时音频: {audio_path}")
                except OSError:
                    pass

        elapsed = time.monotonic() - pipeline_start
        logger.info(f"{'=' * 60}")
        logger.success(
            f"Pipeline 完成! 耗时 {elapsed:.1f}s, "
            f"{len(clip_plans)} 个切片 → {version_dir}"
        )
        logger.info(f"{'=' * 60}")

        return version_dir

    # ---- Step 1: 预处理 ----

    def _step1_preprocess(self, input_path: Path) -> tuple[VideoInfo, Path]:
        """Step 1: 视频探测 + 音频提取"""
        step_start(1, TOTAL_STEPS, "预处理")
        t0 = time.monotonic()

        try:
            video_info = probe_video(input_path)
            logger.info(
                f"视频: {video_info.width}x{video_info.height} "
                f"{video_info.codec} {video_info.duration:.1f}s "
                f"{video_info.orientation}"
            )
        except Exception as e:
            raise PipelineError("Step1-预处理", f"视频探测失败: {e}") from e

        # 提取音频
        audio_path: Path | None = None
        if video_info.has_audio:
            try:
                tmp_dir = Path(tempfile.mkdtemp(prefix="deepcut_"))
                audio_path = tmp_dir / "audio.wav"
                extract_audio(input_path, audio_path)
            except Exception as e:
                raise PipelineError("Step1-预处理", f"音频提取失败: {e}") from e
        else:
            logger.warning("视频无音频轨，将跳过语音相关分析")
            # 创建空音频路径占位
            tmp_dir = Path(tempfile.mkdtemp(prefix="deepcut_"))
            audio_path = tmp_dir / "audio.wav"

        step_done(1, TOTAL_STEPS, "预处理", time.monotonic() - t0)
        return video_info, audio_path

    # ---- Step 2: VAD ----

    def _step2_vad(self, audio_path: Path, video_info: VideoInfo) -> VADResult:
        """Step 2: VAD 人声检测"""
        step_start(2, TOTAL_STEPS, "VAD 检测")
        t0 = time.monotonic()

        if self.disable_speech or not video_info.has_audio or not audio_path.exists():
            logger.info("语音分析已禁用或无音频，标记为无人声")
            result = VADResult(has_speech=False, speech_ratio=0.0)
            step_done(2, TOTAL_STEPS, "VAD 检测", time.monotonic() - t0)
            return result

        try:
            detector = VADDetector(
                model_size=self.config.whisper_model,
                device=self.config.whisper_device,
                compute_type=self.config.whisper_compute_type,
            )
            result = detector.detect(audio_path)
        except Exception as e:
            raise PipelineError("Step2-VAD", f"VAD 检测失败: {e}") from e

        step_done(2, TOTAL_STEPS, "VAD 检测", time.monotonic() - t0)
        return result

    # ---- Step 3: 分析 ----

    def _step3_analysis(
        self,
        audio_path: Path,
        video_path: Path,
        video_info: VideoInfo,
        vad_result: VADResult,
    ) -> AnalysisResult:
        """Step 3A + 3B: 语音分析 + 视觉分析"""
        step_start(3, TOTAL_STEPS, "综合分析")
        t0 = time.monotonic()

        transcript: TranscriptResult | None = None
        topics = []
        scenes = []
        motions = []

        # 3A: 语音分析（有人声时）
        if vad_result.has_speech and not self.disable_speech:
            logger.info("3A: 语音分析（有人声）")
            try:
                transcriber = Transcriber(
                    model_size=self.config.whisper_model,
                    device=self.config.whisper_device,
                    compute_type=self.config.whisper_compute_type,
                )
                transcript = transcriber.transcribe(audio_path)
            except Exception as e:
                logger.error(f"语音转录失败，继续执行: {e}")

            # 话题分段（需要 LLM）
            if transcript and transcript.segments and self.config.openai_api_key:
                try:
                    llm_client = LLMClient(
                        api_key=self.config.openai_api_key,
                        base_url=self.config.openai_base_url,
                        model=self.config.openai_model,
                    )
                    segmenter = TopicSegmenter(llm_client)
                    topics = segmenter.segment(transcript)
                except Exception as e:
                    logger.warning(f"话题分段失败，继续执行: {e}")
            elif not self.config.openai_api_key:
                logger.warning("OPENAI_API_KEY 未设置，跳过话题分段")
        else:
            logger.info("3A: 跳过语音分析（无人声或已禁用）")

        # 3B: 视觉分析（始终执行）
        logger.info("3B: 视觉分析")
        try:
            scene_detector = SceneDetector()
            scenes = scene_detector.detect(video_path)
        except Exception as e:
            logger.error(f"场景检测失败，继续执行: {e}")

        if not self.disable_motion:
            try:
                motion_detector = MotionDetector()
                motions = motion_detector.detect(video_path)
            except Exception as e:
                logger.error(f"运镜检测失败，继续执行: {e}")
        else:
            logger.info("运镜检测已禁用")

        analysis = AnalysisResult(
            vad=vad_result,
            scenes=scenes,
            motions=motions,
            transcript=transcript,
            topics=topics,
        )

        step_done(3, TOTAL_STEPS, "综合分析", time.monotonic() - t0)
        return analysis

    # ---- Step 4: 融合决策 ----

    def _step4_fusion(
        self, video_info: VideoInfo, analysis: AnalysisResult
    ) -> list[ClipPlan]:
        """Step 4: 融合决策"""
        step_start(4, TOTAL_STEPS, "融合决策")
        t0 = time.monotonic()

        try:
            engine = FusionEngine()
            clip_plans = engine.decide_and_fuse(
                video_info=video_info,
                analysis=analysis,
                min_duration=self.config.deepcut_default_min_duration,
                max_duration=self.config.deepcut_default_max_duration,
                overlap_duration=self.config.deepcut_overlap_duration,
                force_visual=self.disable_speech,
            )
        except Exception as e:
            raise PipelineError("Step4-融合", f"融合决策失败: {e}") from e

        if not clip_plans:
            raise PipelineError("Step4-融合", "融合结果为空，无法生成切片")

        step_done(4, TOTAL_STEPS, "融合决策", time.monotonic() - t0)
        return clip_plans

    # ---- Step 5: 视频切割 ----

    def _step5_cut(
        self, video_path: Path, clip_plans: list[ClipPlan], version_dir: Path
    ) -> list[Path]:
        """Step 5: FFmpeg 批量切割"""
        step_start(5, TOTAL_STEPS, "视频切割")
        t0 = time.monotonic()

        try:
            clip_paths = batch_cut(
                video_path=video_path,
                clip_plans=clip_plans,
                output_dir=version_dir,
                codec="libx264",
            )
        except Exception as e:
            raise PipelineError("Step5-切割", f"视频切割失败: {e}") from e

        step_done(5, TOTAL_STEPS, "视频切割", time.monotonic() - t0)
        return clip_paths

    # ---- Step 6: AI 标签 ----

    def _step6_tagging(
        self,
        clip_plans: list[ClipPlan],
        analysis: AnalysisResult,
        video_info: VideoInfo,
        video_path: Path,
    ) -> list[ClipPlan]:
        """Step 6: AI 标签生成（多模态 vision 模型 + 关键帧）"""
        step_start(6, TOTAL_STEPS, "AI 标签")
        t0 = time.monotonic()

        if not self.config.openai_api_key:
            logger.warning("OPENAI_API_KEY 未设置，跳过标签生成")
            step_done(6, TOTAL_STEPS, "AI 标签", time.monotonic() - t0)
            return clip_plans

        try:
            llm_client = LLMClient(
                api_key=self.config.openai_api_key,
                base_url=self.config.openai_base_url,
                model=self.config.openai_model,
            )
            tag_gen = TagGenerator(
                llm_client,
                vision_model=self.config.openai_vision_model,
            )

            clips_info: list[dict[str, str | float]] = []
            for plan in clip_plans:
                transcript_text = ""
                if analysis.transcript:
                    transcript_text = " ".join(
                        seg.text
                        for seg in analysis.transcript.segments
                        if seg.start >= plan.start and seg.end <= plan.end
                    )

                motion_types = self._get_motion_types_for_range(
                    analysis.motions, plan.start, plan.end
                )

                clips_info.append({
                    "start": plan.start,
                    "end": plan.end,
                    "split_reason": plan.split_reason,
                    "transcript": transcript_text,
                    "motion_types": motion_types,
                    "orientation": video_info.orientation,
                    "topic": plan.topic,
                    "summary": plan.summary,
                })

            tags_list = tag_gen.generate_batch(clips_info, video_path=video_path)

            # 将标签写回 ClipPlan
            for i, tags in enumerate(tags_list):
                if i < len(clip_plans):
                    clip_plans[i].tags = tags

        except Exception as e:
            logger.warning(f"标签生成失败，继续执行: {e}")

        step_done(6, TOTAL_STEPS, "AI 标签", time.monotonic() - t0)
        return clip_plans

    # ---- Step 7: 输出 ----

    def _step7_output(
        self,
        version_dir: Path,
        video_info: VideoInfo,
        clip_plans: list[ClipPlan],
        clip_paths: list[Path],
        analysis: AnalysisResult,
    ) -> None:
        """Step 7: 保存 metadata.json + transcript.json"""
        step_start(7, TOTAL_STEPS, "输出")
        t0 = time.monotonic()

        # 构建 ClipMetadata 列表
        clips_metadata: list[ClipMetadata] = []
        for i, plan in enumerate(clip_plans):
            file_path = clip_paths[i] if i < len(clip_paths) else None
            file_name = file_path.name if file_path else f"clip_{i:03d}.mp4"

            transcript_text = ""
            if analysis.transcript:
                transcript_text = " ".join(
                    seg.text
                    for seg in analysis.transcript.segments
                    if seg.start >= plan.start and seg.end <= plan.end
                )

            # 计算切片关系
            relationships = []
            if i > 0:
                from deepcut.models.clip import ClipRelationship
                relationships.append(
                    ClipRelationship(
                        related_index=i - 1,
                        relationship_type="sequence",
                    )
                )
                # 检查是否同场景
                if clip_plans[i - 1].scene_group == plan.scene_group:
                    relationships.append(
                        ClipRelationship(
                            related_index=i - 1,
                            relationship_type="same_scene",
                        )
                    )

            clips_metadata.append(
                ClipMetadata(
                    index=plan.index,
                    start=plan.start,
                    end=plan.end,
                    duration=plan.duration,
                    file_name=file_name,
                    file_path=file_path,
                    split_reason=plan.split_reason,
                    scene_group=plan.scene_group,
                    overlap_prev=plan.overlap_prev,
                    overlap_next=plan.overlap_next,
                    orientation=video_info.orientation,
                    tags=plan.tags if plan.tags else ClipTags(),
                    transcript_segment=transcript_text,
                    relationships=relationships,
                    topic=plan.topic,
                    summary=plan.summary,
                )
            )

        # 保存 metadata.json
        output_metadata = OutputMetadata(
            version=version_dir.name,
            source_video=str(video_info.path),
            source_duration=video_info.duration,
            source_orientation=video_info.orientation,
            total_clips=len(clips_metadata),
            config={
                "min_duration": self.config.deepcut_default_min_duration,
                "max_duration": self.config.deepcut_default_max_duration,
                "overlap_duration": self.config.deepcut_overlap_duration,
                "disable_motion": self.disable_motion,
                "disable_speech": self.disable_speech,
                "whisper_model": self.config.whisper_model,
            },
            clips=clips_metadata,
        )

        metadata_path = version_dir / "metadata.json"
        metadata_path.write_text(
            output_metadata.model_dump_json(indent=2, exclude={"clips": {"__all__": {"file_path"}}}),
            encoding="utf-8",
        )
        logger.info(f"metadata.json 已保存: {metadata_path}")

        # 保存 transcript.json（持久化语音转录）
        if analysis.transcript and analysis.transcript.segments:
            transcript_path = version_dir / "transcript.json"
            transcript_path.write_text(
                analysis.transcript.model_dump_json(indent=2),
                encoding="utf-8",
            )
            logger.info(f"transcript.json 已保存: {transcript_path}")

        step_done(7, TOTAL_STEPS, "输出", time.monotonic() - t0)

    # ---- 工具方法 ----

    def _get_motion_types_for_range(
        self, motions: list, start: float, end: float  # type: ignore[type-arg]
    ) -> str:
        """获取指定时间范围内的运镜类型"""
        types = set()
        for m in motions:
            if hasattr(m, "start") and hasattr(m, "end") and hasattr(m, "motion_type"):
                if m.start < end and m.end > start:
                    types.add(m.motion_type)
        return ", ".join(sorted(types)) if types else "未知"
