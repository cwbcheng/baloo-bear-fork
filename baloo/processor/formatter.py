"""Format review comments and summaries as Markdown."""

from typing import Any

from baloo.github.models import GeneralFinding, ReviewComment


class CommentFormatter:
    """Format review comments and summaries for GitHub."""

    SEVERITY_EMOJIS = {
        "CRITICAL": "🔴",
        "HIGH": "🟠",
        "MEDIUM": "🟡",
        "LOW": "🔵",
    }

    @staticmethod
    def format_summary(
        comments: list[ReviewComment],
        metadata: dict[str, Any] | None = None,
        general_findings: list[GeneralFinding] | None = None,
    ) -> str:
        """
        Format a review summary markdown.

        Args:
            comments: List of review comments
            metadata: Optional agent metadata (costs, tokens)

        Returns:
            Formatted Markdown summary
        """
        general_findings = general_findings or []
        severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for finding in list(comments) + list(general_findings):
            sev = finding.severity.value if hasattr(finding.severity, "value") else finding.severity
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        critical = severity_counts["CRITICAL"]
        high = severity_counts["HIGH"]
        medium = severity_counts["MEDIUM"]
        low = severity_counts["LOW"]
        total = len(comments) + len(general_findings)

        summary_parts = []
        summary_parts.append("## 🐻 Baloo 审查摘要\n")

        if not comments and not general_findings:
            summary_parts.append("✅ **未发现问题！** 代码看起来没问题。")
        else:
            stats = []
            if critical > 0:
                stats.append(f"🔴 **{critical}** 严重")
            if high > 0:
                stats.append(f"🟠 **{high}** 高")
            if medium > 0:
                stats.append(f"🟡 **{medium}** 中")
            if low > 0:
                stats.append(f"🔵 **{low}** 低")

            summary_parts.append(" | ".join(stats))
            summary_parts.append(f"\n**共发现**: {total} 个问题")

            if critical > 0 or high > 0:
                summary_parts.append("\n⚠️ **合并前请先处理严重/高等级问题**")
            else:
                summary_parts.append(
                    "\n✅ **无阻塞问题 - 可以合并**（建议关注中/低等级项）"
                )

        if general_findings:
            summary_parts.append("\n---\n\n**💬 一般性观察**\n")
            for gf in general_findings:
                sev = gf.severity.value if hasattr(gf.severity, "value") else gf.severity
                emoji = CommentFormatter.SEVERITY_EMOJIS.get(sev, "")
                summary_parts.append(f"{emoji} {gf.body}\n")

        if metadata:
            summary_parts.append(CommentFormatter.format_metadata_section(metadata))

        return "\n".join(summary_parts)

    @staticmethod
    def format_metadata_section(metadata: dict[str, Any]) -> str:
        """
        Format agent metadata as a collapsible HTML details section.

        Args:
            metadata: Metadata dictionary

        Returns:
            HTML Markdown string
        """
        if not metadata:
            return ""

        model = metadata.get("model", "unknown")
        in_tok = metadata.get("input_tokens", 0)
        out_tok = metadata.get("output_tokens", 0)
        cache_read_tok = metadata.get("cache_read_tokens", 0)
        cache_write_tok = metadata.get("cache_write_tokens", 0)
        think_tok = metadata.get("thinking_tokens", 0)
        cost = metadata.get("cost_usd", 0)
        turns = metadata.get("num_turns", 0)
        duration = metadata.get("duration_seconds", 0)

        thinking_info = ""
        if think_tok > 0:
            thinking_info = f"<li>**Thinking Tokens:** {think_tok:,}</li>"

        cache_info = ""
        if cache_read_tok > 0 or cache_write_tok > 0:
            cache_info = f"<li>**Cache:** {cache_write_tok:,} write / {cache_read_tok:,} read</li>"

        return f"""
<details>
<summary>📊 审查元数据</summary>

<ul>
  <li>**模型:** `{model}`</li>
  <li>**Token:** {in_tok:,} (输入) / {out_tok:,} (输出)</li>
  {cache_info}
  {thinking_info}
  <li>**费用:** ${cost:.4f}</li>
  <li>**轮次:** {turns}</li>
  <li>**耗时:** {duration:.1f} 秒</li>
</ul>

</details>
"""
