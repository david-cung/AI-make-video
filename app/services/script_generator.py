from __future__ import annotations

import os
import textwrap

from app.models.project import ProjectInput


class ScriptGenerator:
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = (api_key if api_key is not None else os.getenv("OPENAI_API_KEY", "")).strip()
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self._client = None

        if self.api_key:
            try:
                from openai import OpenAI
            except ImportError as exc:
                raise RuntimeError(
                    "OPENAI_API_KEY is set, but the openai package is not installed. "
                    "Run `pip install -r requirements.txt`."
                ) from exc

            self._client = OpenAI(api_key=self.api_key)

    @property
    def using_openai(self) -> bool:
        return self._client is not None

    def generate(self, project: ProjectInput) -> str:
        if not self._client:
            return self._generate_mock_script(project)

        prompt = self._build_prompt(project)
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Bạn là copywriter chuyên viết kịch bản video affiliate "
                        "ngắn cho TikTok, Reels và YouTube Shorts bằng tiếng Việt."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.8,
            max_tokens=450,
        )
        script = response.choices[0].message.content or ""
        script = script.strip()
        if not script:
            raise RuntimeError("OpenAI returned an empty script.")
        return script

    def _build_prompt(self, project: ProjectInput) -> str:
        return textwrap.dedent(
            f"""
            Viết một kịch bản voice-over tiếng Việt dài khoảng 20-30 giây cho video affiliate dạng dọc.

            Thông tin sản phẩm:
            - Tên sản phẩm: {project.product_name}
            - Lợi ích chính: {project.product_benefits}
            - Khách hàng mục tiêu: {project.target_audience}
            - Phong cách video: {project.video_style}
            - CTA cuối video: {project.cta_text}

            Yêu cầu:
            - Mở đầu có hook mạnh trong 2 giây đầu.
            - Giọng tự nhiên, dễ nghe, phù hợp TikTok/Reels/Shorts.
            - Không dùng markdown, không đánh số cảnh, không thêm chỉ dẫn sản xuất.
            - Chỉ trả về nội dung lời thoại để đọc voice-over.
            - Kết thúc bằng CTA đã cung cấp hoặc biến thể rất gần.
            """
        ).strip()

    def _generate_mock_script(self, project: ProjectInput) -> str:
        audience = project.target_audience.strip() or "những ai đang cần một lựa chọn tiện lợi hơn"
        benefits = project.product_benefits.strip() or "tiết kiệm thời gian, dễ dùng và tạo cảm giác yên tâm mỗi ngày"
        cta = project.cta_text.strip() or "Nhấn vào link để xem ưu đãi hôm nay."

        return (
            f"Bạn đang tìm một lựa chọn thật sự đáng tiền? {project.product_name} có thể là thứ "
            f"{audience} nên thử. Sản phẩm nổi bật nhờ {benefits}. Điểm mình thích là cách dùng đơn giản, "
            "không mất nhiều thời gian mà vẫn tạo cảm giác hiệu quả trong sinh hoạt hằng ngày. "
            f"Nếu bạn muốn nâng cấp trải nghiệm của mình, {cta}"
        )
