from __future__ import annotations

import os
import textwrap
from pathlib import Path

from app.models.project import ProjectInput
from app.services.templates import (
    BEFORE_AFTER,
    HONEST_REVIEW,
    PROBLEM_SOLUTION,
    TIKTOK_HOOK_TEST,
    TOP_3_BENEFITS,
    get_template,
)


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

    def generate_from_fields(
        self,
        product_name: str,
        product_benefits: str,
        target_audience: str,
        video_style: str,
        cta_text: str,
        video_template: str,
    ) -> str:
        project = ProjectInput(
            product_name=product_name,
            product_benefits=product_benefits,
            target_audience=target_audience,
            video_style=video_style,
            cta_text=cta_text,
            background_video_path=Path(),
            output_folder=Path(),
            video_template=video_template,
        )
        return self.generate(project)

    def _build_prompt(self, project: ProjectInput) -> str:
        template = get_template(project.video_template)
        return textwrap.dedent(
            f"""
            Viết một kịch bản voice-over tiếng Việt dài khoảng 20-30 giây cho video affiliate dạng dọc.

            Thông tin sản phẩm:
            - Tên sản phẩm: {project.product_name}
            - Lợi ích chính: {project.product_benefits}
            - Khách hàng mục tiêu: {project.target_audience}
            - Phong cách video: {project.video_style}
            - CTA cuối video: {project.cta_text}
            - Video template: {template.name}
            - Cấu trúc template: {template.structure_text}

            Hướng dẫn template:
            {template.prompt_guidance}

            Yêu cầu:
            - Mở đầu có hook mạnh trong 2 giây đầu.
            - Giọng tự nhiên, dễ nghe, phù hợp TikTok/Reels/Shorts.
            - Tiếng Việt là ngôn ngữ mặc định.
            - Ngắn, tự nhiên, không phóng đại, không spam.
            - Tránh tuyên bố y tế, tài chính, hoặc cam kết kết quả chắc chắn.
            - Không dùng markdown, không đánh số cảnh, không thêm chỉ dẫn sản xuất.
            - Chỉ trả về nội dung lời thoại để đọc voice-over.
            - Kết thúc bằng CTA đã cung cấp hoặc biến thể rất gần.
            """
        ).strip()

    def _generate_mock_script(self, project: ProjectInput) -> str:
        template_name = get_template(project.video_template).name
        name = project.product_name.strip() or "sản phẩm này"
        audience = project.target_audience.strip() or "những ai đang cần một lựa chọn tiện lợi hơn"
        benefits = project.product_benefits.strip() or "tiết kiệm thời gian, dễ dùng và tạo cảm giác yên tâm mỗi ngày"
        cta = project.cta_text.strip() or "Nhấn vào link để xem thêm thông tin."
        benefit_items = self._benefit_items(benefits)

        if template_name == TOP_3_BENEFITS:
            return (
                f"3 lý do khiến {name} đáng để {audience} cân nhắc. "
                f"Thứ nhất, {benefit_items[0]}. "
                f"Thứ hai, {benefit_items[1]}. "
                f"Thứ ba, {benefit_items[2]}. "
                f"Nếu bạn đang tìm một lựa chọn đơn giản và thực tế hơn, {cta}"
            )

        if template_name == BEFORE_AFTER:
            return (
                f"Trước đây, nhiều người mất khá nhiều thời gian vì {benefit_items[0]}. "
                f"Sau khi có {name}, mọi thứ trở nên gọn hơn và dễ bắt đầu hơn. "
                f"Sản phẩm này phù hợp với {audience} vì {benefit_items[1]}. "
                f"Nếu bạn muốn xem nó có hợp với mình không, {cta}"
            )

        if template_name == HONEST_REVIEW:
            return (
                f"Mình đã thử {name} và đây là cảm nhận thật. "
                f"Về cơ bản, đây là một lựa chọn dành cho {audience}. "
                f"Điểm mình thích là {benefit_items[0]} và {benefit_items[1]}. "
                "Điểm có thể cân nhắc là bạn vẫn nên xem kỹ nhu cầu của mình trước khi mua. "
                f"Nếu thấy phù hợp, {cta}"
            )

        if template_name == TIKTOK_HOOK_TEST:
            return (
                f"Đừng mua {name} trước khi xem điều này. "
                f"Nếu bạn là {audience}, sản phẩm này đáng chú ý vì {benefit_items[0]}. "
                f"Nó không hứa hẹn điều quá đà, nhưng có thể giúp trải nghiệm hằng ngày gọn hơn nhờ {benefit_items[1]}. "
                f"Muốn kiểm tra có hợp với mình không thì {cta}"
            )

        if template_name == PROBLEM_SOLUTION:
            return (
                f"Bạn có đang thấy phiền vì {benefit_items[0]}? "
                f"Vấn đề là những việc nhỏ này thường làm mất thời gian mỗi ngày. "
                f"{name} là một lựa chọn có thể giúp {audience} xử lý mọi thứ gọn hơn. "
                f"Điểm đáng chú ý là {benefit_items[1]} và cách dùng khá đơn giản. "
                f"Nếu muốn xem chi tiết, {cta}"
            )

        return (
            f"Bạn đang tìm một lựa chọn thật sự đáng tiền? {name} có thể là thứ "
            f"{audience} nên thử. Sản phẩm nổi bật nhờ {benefits}. Điểm mình thích là cách dùng đơn giản, "
            "không mất nhiều thời gian mà vẫn tạo cảm giác hiệu quả trong sinh hoạt hằng ngày. "
            f"Nếu bạn muốn nâng cấp trải nghiệm của mình, {cta}"
        )

    def _benefit_items(self, benefits: str) -> list[str]:
        raw_items = [
            item.strip(" .;-")
            for item in benefits.replace("\n", ",").split(",")
            if item.strip(" .;-")
        ]
        if not raw_items:
            raw_items = ["dễ dùng", "tiết kiệm thời gian", "phù hợp với nhu cầu hằng ngày"]

        while len(raw_items) < 3:
            if len(raw_items) == 1:
                raw_items.append("dễ áp dụng trong sinh hoạt hằng ngày")
            else:
                raw_items.append("giúp trải nghiệm trở nên gọn gàng hơn")

        return raw_items[:3]
