"""Example of repository tracking system in action."""

from datetime import datetime

from curator.tracking import CurationFileManager, ReviewGenerator

# This is a demo showing what the tracking system produces
# Run this to see example CURATION.md and REVIEW.md output


def demo_tracking():
    """Demonstrate the tracking system with example data."""
    print("=" * 60)
    print("GitHub Curator - Repository Tracking Demo")
    print("=" * 60)
    print()

    # Example evaluation data
    theme = "Educational Python Projects"
    overall_score = 8.2
    confidence = 0.85

    dimensions = {
        "Educational Value": {
            "score": 9.0,
            "confidence": 0.90,
            "reasoning": "The repository excels in its educational approach with clear learning objectives, progressive difficulty levels, and well-structured examples. Each concept builds naturally on the previous one, making it ideal for self-paced learning.",
        },
        "Code Quality": {
            "score": 7.5,
            "confidence": 0.80,
            "reasoning": "Code follows Python best practices with consistent formatting and appropriate use of type hints. Some examples could benefit from additional error handling and edge case coverage.",
        },
        "Documentation": {
            "score": 8.0,
            "confidence": 0.85,
            "reasoning": "Comprehensive README with setup instructions, learning path guidance, and concept explanations. Inline comments effectively explain 'why' not just 'what'. Could improve with more architecture diagrams.",
        },
        "Community Engagement": {
            "score": 7.8,
            "confidence": 0.75,
            "reasoning": "Active issue responses and regular updates. Good contribution guidelines, though could benefit from more labeled 'good first issue' tickets for newcomers.",
        },
    }

    evidence = [
        "README has clear learning objectives with skill prerequisites (docs/README.md:1-25)",
        "15 well-commented examples covering beginner to intermediate topics (examples/*.py)",
        "Active maintenance: 23 commits in last month, issues closed within 48 hours average",
        "Interactive Jupyter notebooks for hands-on learning (notebooks/tutorials/*.ipynb)",
        "Comprehensive test suite demonstrates best practices (tests/**/test_*.py)",
    ]

    # Generate CURATION.md entry
    print("📝 CURATION.md Entry (Machine-Readable History)")
    print("   Location: .curator/CURATION.md")
    print("-" * 60)
    curation_entry = CurationFileManager.format_entry(
        theme=theme,
        overall_score=overall_score,
        confidence=confidence,
        dimensions=dimensions,
        evidence=evidence,
        repo_commit="abc123f7d4e5",
    )
    print(curation_entry)
    print()

    # Generate REVIEW.md content with rich LLM-generated content
    print("📄 REVIEW.md Content (Rich LLM-Generated Review)")
    print("   Location: .curator/REVIEW.md")
    print("-" * 60)
    print("ℹ️  NOTE: This example generates actual LLM content.")
    print("   Requires ANTHROPIC_API_KEY to be set.")
    print()

    try:
        review_generator = ReviewGenerator()
        review_content = review_generator.generate_review(
            org="python-edu",
            repo="learn-python-by-example",
            theme=theme,
            overall_score=overall_score,
            confidence=confidence,
            dimensions=dimensions,
            evidence=evidence,
            repo_description="A comprehensive collection of Python examples for learning by doing",
            readme_excerpt="# Learn Python By Example\n\nThis repository provides hands-on Python examples covering topics from basics to advanced concepts. Each example is fully commented and includes explanations.",
            first_reviewed=datetime(2025, 9, 15),
        )
        print(review_content)
    except Exception as e:
        print(f"⚠️  LLM generation failed: {e}")
        print()
        print("Showing fallback template-based review instead:")
        print()
        # Show fallback
        fallback = """# learn-python-by-example

> **Last reviewed**: 2025-10-10 | **Theme**: "Educational Python Projects" | **Score**: 8.2/10 | **Confidence**: 85%

## At a Glance

learn-python-by-example demonstrates strong quality when evaluated against the theme "Educational Python Projects" with an overall score of 8.2/10.

## Key Dimensions

### Educational Value (9.0/10)

The repository excels in its educational approach with clear learning objectives, progressive difficulty levels, and well-structured examples. Each concept builds naturally on the previous one, making it ideal for self-paced learning.

### Documentation (8.0/10)

Comprehensive README with setup instructions, learning path guidance, and concept explanations. Inline comments effectively explain 'why' not just 'what'. Could improve with more architecture diagrams.

### Community Engagement (7.8/10)

Active issue responses and regular updates. Good contribution guidelines, though could benefit from more labeled 'good first issue' tickets for newcomers.

### Code Quality (7.5/10)

Code follows Python best practices with consistent formatting and appropriate use of type hints. Some examples could benefit from additional error handling and edge case coverage.

## Supporting Evidence

- README has clear learning objectives with skill prerequisites (docs/README.md:1-25)
- 15 well-commented examples covering beginner to intermediate topics (examples/*.py)
- Active maintenance: 23 commits in last month, issues closed within 48 hours average
- Interactive Jupyter notebooks for hands-on learning (notebooks/tutorials/*.ipynb)
- Comprehensive test suite demonstrates best practices (tests/**/test_*.py)

## Bottom Line

This repository scored 8.2/10 for the theme "Educational Python Projects". Refer to the dimension evaluations above for detailed assessment.

---

## Review History

- **First reviewed**: 2025-09-15
- **Latest review**: 2025-10-10

---

*Review generated by [GitHub Curator](https://github.com/IntentHub/github-curator) with metacognitive evaluation*
"""
        print(fallback)
    print()

    print("=" * 60)
    print("✅ Demo complete!")
    print()
    print("File structure in tracked repository:")
    print("  tracked-repo/")
    print("  ├── .curator/")
    print("  │   ├── CURATION.md  (append-only history)")
    print("  │   └── REVIEW.md    (latest rich review)")
    print("  ├── .git/")
    print("  └── [original repo files...]")
    print()
    print("Git workflow:")
    print("  - Branch 'curation' holds .curator/ files")
    print("  - Each evaluation = commit + tag")
    print("  - git log shows full curation timeline")
    print()
    print("Commands to try:")
    print("  curator track https://github.com/owner/repo")
    print('  curator curate-tracked owner/repo "Your theme"')
    print("  curator list-tracked")
    print("=" * 60)


if __name__ == "__main__":
    demo_tracking()
