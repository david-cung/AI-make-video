from __future__ import annotations

from dataclasses import dataclass


PROBLEM_SOLUTION = "Problem Solution"
TOP_3_BENEFITS = "Top 3 Benefits"
BEFORE_AFTER = "Before After"
HONEST_REVIEW = "Honest Review"
TIKTOK_HOOK_TEST = "TikTok Hook Test"
DEFAULT_TEMPLATE = PROBLEM_SOLUTION


@dataclass(frozen=True)
class VideoTemplate:
    name: str
    structure: tuple[str, ...]
    prompt_guidance: str

    @property
    def structure_text(self) -> str:
        return " -> ".join(self.structure)


TEMPLATES: tuple[VideoTemplate, ...] = (
    VideoTemplate(
        name=PROBLEM_SOLUTION,
        structure=("Hook", "Problem", "Solution", "Benefit", "CTA"),
        prompt_guidance=(
            "Dùng cấu trúc Problem Solution: mở đầu bằng một nỗi đau phổ biến, "
            "nói ngắn gọn vấn đề, giới thiệu sản phẩm như một lựa chọn hỗ trợ, "
            "giải thích lợi ích thực tế, rồi kết bằng CTA tự nhiên."
        ),
    ),
    VideoTemplate(
        name=TOP_3_BENEFITS,
        structure=("Hook: 3 reasons why", "Benefit 1", "Benefit 2", "Benefit 3", "CTA"),
        prompt_guidance=(
            "Dùng cấu trúc Top 3 Benefits: mở đầu theo kiểu '3 lý do vì sao...', "
            "sau đó trình bày 3 lợi ích rõ ràng, mỗi lợi ích một ý ngắn, rồi CTA nhẹ nhàng."
        ),
    ),
    VideoTemplate(
        name=BEFORE_AFTER,
        structure=("Hook", "Before", "After", "CTA"),
        prompt_guidance=(
            "Dùng cấu trúc Before After: mở đầu bằng sự tương phản trước/sau, "
            "mô tả tình huống cũ còn bất tiện, mô tả trải nghiệm tốt hơn sau khi dùng sản phẩm, "
            "rồi kết bằng CTA. Không hứa hẹn kết quả chắc chắn."
        ),
    ),
    VideoTemplate(
        name=HONEST_REVIEW,
        structure=("Hook: I tried this", "What it is", "What I liked", "What could be better", "Who it is for", "CTA"),
        prompt_guidance=(
            "Dùng cấu trúc Honest Review: mở đầu bằng trải nghiệm thử sản phẩm, "
            "nói sản phẩm là gì, điểm thích, một điểm có thể chưa hoàn hảo, "
            "ai phù hợp, rồi CTA tự nhiên. Giọng chân thật, không quá bán hàng."
        ),
    ),
    VideoTemplate(
        name=TIKTOK_HOOK_TEST,
        structure=("Generate 3 hooks", "Pick strongest hook", "Full script with chosen hook", "CTA"),
        prompt_guidance=(
            "Dùng cấu trúc TikTok Hook Test: nghĩ ra 3 hook ngắn khác nhau, chọn hook mạnh nhất, "
            "nhưng chỉ trả về kịch bản voice-over hoàn chỉnh bắt đầu bằng hook đã chọn. "
            "Không liệt kê các hook phụ trong kết quả cuối cùng."
        ),
    ),
)


def template_names() -> list[str]:
    return [template.name for template in TEMPLATES]


def get_template(name: str | None) -> VideoTemplate:
    normalized = (name or "").strip().casefold()
    for template in TEMPLATES:
        if template.name.casefold() == normalized:
            return template
    return TEMPLATES[0]
