---
name: testing-content-scrubber
description: Test the content scrubber module end-to-end. Use when verifying AI phrase detection, stats tracking, or em-dash replacement changes.
---

# Testing the Content Scrubber

## Overview

The content scrubber (`data_sources/modules/content_scrubber.py`) removes AI watermarks and telltale phrases from generated content. It's a pure Python module with no external dependencies beyond stdlib.

## How to Run

```bash
# Self-test (built into module)
python3 data_sources/modules/content_scrubber.py

# Import and test programmatically
python3 -c "
from data_sources.modules.content_scrubber import ContentScrubber, scrub_content
scrubber = ContentScrubber()
cleaned, stats = scrubber.scrub('your test text here')
print(cleaned)
print(stats)
"

# Verbose convenience function
python3 -c "
from data_sources.modules.content_scrubber import scrub_content
scrub_content('Moreover, leverage data.', verbose=True)
"
```

## Key Stats Dict Keys

After calling `scrubber.scrub(text)`, the stats dict should contain:
- `unicode_removed` — invisible watermark chars stripped
- `format_control_removed` — Unicode Cf category chars stripped
- `emdashes_replaced` — em-dashes converted to commas/semicolons/periods
- `ai_phrases_replaced` — AI-telltale phrases matched and replaced
- `ai_filler_adverbs_replaced` — sentence-initial filler adverbs replaced

## Testing Patterns

### 1. Phrase Replacement Accuracy
Feed text with known AI phrases and assert the exact replacement appears:
- "In order to X" → "to X"
- "streamline" → "simplify"
- "robust" → "strong"

### 2. Stats Tracking
Verify `stats['ai_phrases_replaced']` matches the count of patterns triggered. A common bug: the stats reset dict in `scrub()` might not include new keys.

### 3. Sentence-Initial Adverb Precision
Test that filler adverbs are only replaced at sentence start, not mid-sentence:
- "Moreover, X" → "Also, X" (replaced)
- "Y is moreover Z" → unchanged (not replaced)

### 4. Compound Patterns
The "In today's..." pattern should handle multiple adjectives:
- "In today's fast-paced digital landscape" → removed

### 5. Idempotency
Scrubbing already-clean output should produce identical text with all stats at 0.

### 6. Verbose Output
Use `scrub_content(text, verbose=True)` and capture stdout to verify all stat lines are printed.

## No External Dependencies

No credentials, APIs, or services needed. All testing is shell-based Python execution.

## Devin Secrets Needed

None — this module uses only Python stdlib.
