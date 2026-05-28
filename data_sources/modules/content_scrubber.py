"""
Content Scrubber

Removes AI-generated content watermarks and telltale signs including:
- Invisible Unicode characters (zero-width spaces, format-control characters, etc.)
- Em-dashes replaced with contextually appropriate punctuation

This module ensures content appears naturally human-written.
"""

import re
import unicodedata
from typing import Dict, List, Tuple


class ContentScrubber:
    """
    Scrubs AI-generated content to remove watermarks and telltale patterns.
    """

    # Specific Unicode characters to remove
    WATERMARK_CHARS = [
        '\u200B',  # Zero-width space
        '\uFEFF',  # Byte Order Mark (BOM)
        '\u200C',  # Zero-width non-joiner
        '\u200D',  # Zero-width joiner
        '\u2060',  # Word joiner
        '\u00AD',  # Soft hyphen
        '\u202F',  # Narrow no-break space
        '\u2062',  # Invisible times
        '\u2063',  # Invisible separator
        '\u2064',  # Invisible plus
        '\u180E',  # Mongolian vowel separator
        '\u200E',  # Left-to-right mark
        '\u200F',  # Right-to-left mark
        '\u2028',  # Line separator
        '\u2029',  # Paragraph separator
    ]

    # AI-telltale phrases that sound robotic or overly formal
    AI_PHRASE_REPLACEMENTS = [
        # "It's important to note that X" → "X"
        (r"[Ii]t(?:'s| is) (?:important|worth|crucial|essential) to (?:note|mention|highlight|understand|remember|recognize|emphasize) that ", ""),
        # "In today's [fast-paced/digital/modern] landscape/world"
        (r"[Ii]n today'?s (?:(?:fast-paced|digital|modern|ever-changing|rapidly evolving|dynamic|competitive|complex)\s*)+(?:landscape|world|era|age|environment),? ?", ""),
        # "In the ever-evolving world/landscape of"
        (r"[Ii]n the (?:ever-evolving|ever-changing|rapidly evolving|constantly changing) (?:world|landscape|realm|field) of ", ""),
        # "Delve/dive into"
        (r"\b[Dd]elve(?:s|d)? (?:into|deeper)\b", "explore"),
        (r"\b[Dd]ive(?:s|d)? (?:deep )?into\b", "explore"),
        # "Leverage" (overused by AI) → "use"
        (r"\b[Ll]everage(?:s|d)?\b", "use"),
        # "Utilize" → "use"
        (r"\b[Uu]tilize(?:s|d)?\b", "use"),
        # "Harness" → "use"
        (r"\b[Hh]arness(?:es|ed)? (?:the power of |the potential of )?", "use "),
        # "In conclusion," / "To summarize," / "In summary,"
        (r"^[Ii]n conclusion,? ?", ""),
        (r"^[Tt]o summarize,? ?", ""),
        (r"^[Ii]n summary,? ?", ""),
        (r"^[Aa]ll things considered,? ?", ""),
        # "It's worth mentioning" / "It bears mentioning"
        (r"[Ii]t(?:'s| is) worth mentioning (?:that )?", ""),
        (r"[Ii]t bears mentioning (?:that )?", ""),
        # "It should be noted that"
        (r"[Ii]t should be noted (?:that )?", ""),
        # "At the end of the day"
        (r"[Aa]t the end of the day,? ?", ""),
        # "This comprehensive guide"
        (r"[Tt]his comprehensive (?:guide|overview|article|resource)", "this guide"),
        # "Without further ado"
        (r"[Ww]ithout further ado,? ?", ""),
        # "Navigating the complexities of" → remove
        (r"[Nn]avigat(?:e|es|ing) the (?:complexities|intricacies|nuances) of ", ""),
        # "In the realm of" → "in"
        (r"[Ii]n the realm of ", "in "),
        # "It goes without saying" → remove
        (r"[Ii]t goes without saying (?:that )?,? ?", ""),
        # "Needless to say" → remove
        (r"[Nn]eedless to say,? ?", ""),
        # "In essence" → remove
        (r"[Ii]n essence,? ?", ""),
        # "The reality is that" → remove
        (r"[Tt]he reality is (?:that )?,? ?", ""),
        # "As a matter of fact" → remove
        (r"[Aa]s a matter of fact,? ?", ""),
        # "The fact of the matter is" → remove
        (r"[Tt]he fact of the matter is (?:that )?,? ?", ""),
        # "When all is said and done" → remove
        (r"[Ww]hen all is said and done,? ?", ""),
        # "It's no secret that" → remove
        (r"[Ii]t(?:'s| is) no secret (?:that )?", ""),
        # "In order to" → "to"
        (r"\b[Ii]n order to\b", "to"),
        # "Due to the fact that" → "because"
        (r"[Dd]ue to the fact that", "because"),
        # "In light of" → "given"
        (r"[Ii]n light of (?:the fact that )?", "given "),
        # "With regard(s) to" → "about"
        (r"[Ww]ith regards? to", "about"),
        # "At this point in time" → "now"
        (r"[Aa]t this point in time", "now"),
        # "For the purpose of" → "to" or "for"
        (r"[Ff]or the purpose of", "for"),
        # "When it comes to" → "with" or "for"
        (r"[Ww]hen it comes to", "for"),
        # "Unlock the power/potential of" → "find" or "reach"
        (r"[Uu]nlock(?:s|ed|ing)? the (?:full )?(?:power|potential|secrets?) of", "reach the potential of"),
        # "Elevate" → "improve"
        (r"\b[Ee]levate(?:s|d)?\b", "improve"),
        # "Empower" → "help" or "enable"
        (r"\b[Ee]mpower(?:s)?\b", "enable"),
        # "Streamline" → "simplify"
        (r"\b[Ss]treamline(?:s|d)?\b", "simplify"),
        # "Revolutionize" → "transform"
        (r"\b[Rr]evolutionize(?:s|d)?\b", "transform"),
        # "Foster" → "encourage"
        (r"\b[Ff]oster(?:s)?\b", "encourage"),
        # "Seamlessly" → "smoothly"
        (r"\b[Ss]eamlessly\b", "smoothly"),
        # "Cutting-edge" → "modern"
        (r"\b[Cc]utting-edge\b", "modern"),
        # "Robust" → "strong"
        (r"\b[Rr]obust\b", "strong"),
        # "Holistic" → "complete"
        (r"\b[Hh]olistic(?:ally)?\b", "complete"),
        # "Game-changer" / "game-changing" → "breakthrough" / "major"
        (r"\b[Gg]ame-chang(?:er|ing)\b", "breakthrough"),
        # "Embark on" → "start" or "begin"
        (r"\b[Ee]mbark(?:s)? (?:on|upon)\b", "start"),
        # "Spearhead" → "lead"
        (r"\b[Ss]pearhead(?:s)?\b", "lead"),
        # "Pivotal" → "key"
        (r"\b[Pp]ivotal\b", "key"),
        # "Plethora" → "range"
        (r"\b[Pp]lethora\b", "range"),
        # "Myriad" → "many"
        (r"\b[Mm]yriad\b", "many"),
        # "Paramount" → "vital"
        (r"\b[Pp]aramount\b", "vital"),
        # "Tapestry" → "mix"
        (r"\b[Tt]apestry\b", "mix"),
        # "Synergy" / "synergies" → "collaboration"
        (r"\b[Ss]ynerg(?:y|ies)\b", "collaboration"),
        # "Paradigm" → "approach"
        (r"\b[Pp]aradigm\b", "approach"),
        # "Multifaceted" → "varied"
        (r"\b[Mm]ultifaceted\b", "varied"),
        # "Firstly" → "First", "Secondly" → "Second", etc.
        (r"\bFirstly\b", "First"),
        (r"\bSecondly\b", "Second"),
        (r"\bThirdly\b", "Third"),
        (r"\bLastly\b", "Last"),
        # "Let's explore/look at/examine" at start of sentence → remove
        (r"^[Ll]et(?:'s| us) (?:explore|look at|examine|take a (?:look|closer look) at) ", ""),
        # "As we navigate" → remove
        (r"[Aa]s we navigate (?:the (?:world|landscape|complexities|realm) of )?", ""),
    ]

    # Overused AI filler adverbs (sentence-initial usage replaced with simpler connectors)
    AI_FILLER_ADVERBS = {
        'moreover': 'Also',
        'furthermore': 'Also',
        'additionally': 'Also',
        'consequently': 'So',
        'nevertheless': 'Still',
        'nonetheless': 'Still',
        'henceforth': 'From now on',
        'thereby': 'This way',
        'subsequently': 'Then',
        'conversely': 'On the flip side',
        'notwithstanding': 'Despite this',
        'undoubtedly': '',
        'indubitably': '',
        'unquestionably': '',
    }

    def __init__(self):
        self.stats = {
            'unicode_removed': 0,
            'emdashes_replaced': 0,
            'format_control_removed': 0,
            'ai_phrases_replaced': 0,
            'ai_filler_adverbs_replaced': 0,
        }

    def scrub(self, content: str) -> Tuple[str, Dict]:
        """
        Scrub content of all AI watermarks and telltale signs.

        Args:
            content: The text content to scrub

        Returns:
            Tuple of (cleaned_content, statistics_dict)
        """
        # Reset stats
        self.stats = {
            'unicode_removed': 0,
            'emdashes_replaced': 0,
            'format_control_removed': 0,
            'ai_phrases_replaced': 0,
            'ai_filler_adverbs_replaced': 0,
        }

        # Step 1: Remove specific watermark characters
        content = self._remove_watermark_chars(content)

        # Step 2: Remove all Unicode format-control characters (Category Cf)
        content = self._remove_format_control_chars(content)

        # Step 3: Replace em-dashes with contextually appropriate punctuation
        content = self._replace_emdashes(content)

        # Step 4: Replace AI-telltale phrases
        content = self._replace_ai_phrases(content)

        # Step 5: Replace AI filler adverbs at sentence start
        content = self._replace_filler_adverbs(content)

        # Step 6: Clean up any double spaces created by removals
        content = self._clean_whitespace(content)

        return content, self.stats

    def _remove_watermark_chars(self, content: str) -> str:
        """Remove specific invisible Unicode watermark characters."""
        original_len = len(content)

        for char in self.WATERMARK_CHARS:
            # For zero-width space, just remove it completely
            # Don't replace with regular space as it breaks URLs
            content = content.replace(char, '')

        self.stats['unicode_removed'] = original_len - len(content)
        return content

    def _remove_format_control_chars(self, content: str) -> str:
        """Remove all Unicode Category Cf (format-control) characters."""
        cleaned = []
        removed = 0

        for char in content:
            if unicodedata.category(char) == 'Cf':
                removed += 1
                continue
            cleaned.append(char)

        self.stats['format_control_removed'] = removed
        return ''.join(cleaned)

    def _replace_emdashes(self, content: str) -> str:
        """
        Replace em-dashes with contextually appropriate punctuation.

        Analyzes the context around each em-dash to determine the best replacement:
        - Comma: For simple separation, parenthetical phrases, or lists
        - Semicolon: For independent clauses that are closely related
        - Period: For strong breaks or when near sentence end
        - Space: When em-dash is used for attribution or breaking phrases
        """
        # Find all em-dashes with surrounding context
        emdash_pattern = r'([^—]{0,100})—([^—]{0,100})'

        def replace_emdash(match):
            before = match.group(1)
            after = match.group(2)

            replacement = self._determine_emdash_replacement(before, after)
            self.stats['emdashes_replaced'] += 1

            return before + replacement + after

        content = re.sub(emdash_pattern, replace_emdash, content)

        return content

    def _determine_emdash_replacement(self, before: str, after: str) -> str:
        """
        Determine the best punctuation to replace an em-dash.

        Args:
            before: Text before the em-dash
            after: Text after the em-dash

        Returns:
            Replacement punctuation string
        """
        # Get the last 50 chars before and first 50 chars after
        before_context = before[-50:].strip() if before else ""
        after_context = after[:50].strip() if after else ""

        # Check if at the end of a sentence (em-dash before end punctuation)
        if after_context and after_context[0] in '.!?':
            return ''  # Remove em-dash, keep the end punctuation

        # Check if it's an attribution or citation (often at end)
        attribution_patterns = [
            r'\b(said|wrote|noted|according to|via)\s*$',
            r'^[A-Z][a-z]+ [A-Z]',  # Looks like "John Smith" after
        ]
        for pattern in attribution_patterns:
            if re.search(pattern, before_context, re.IGNORECASE) or \
               re.match(pattern, after_context):
                return ', '

        # Check if before text ends with a complete clause
        # Indicators: ends with noun/verb pattern, has subject
        has_verb_before = bool(re.search(r'\b(is|are|was|were|has|have|had|do|does|did|can|could|will|would|should|may|might)\b', before_context[-30:], re.IGNORECASE))
        has_verb_after = bool(re.search(r'\b(is|are|was|were|has|have|had|do|does|did|can|could|will|would|should|may|might)\b', after_context[:30], re.IGNORECASE))

        # If both sides have verbs, they might be independent clauses
        if has_verb_before and has_verb_after:
            # Check if after starts with capital (stronger break)
            if after_context and after_context[0].isupper():
                # Could be a new sentence
                return '. '
            # Check for conjunctive adverbs that suggest semicolon
            conjunctive_adverbs = ['however', 'therefore', 'moreover', 'furthermore',
                                   'nevertheless', 'consequently', 'thus', 'hence']
            after_lower = after_context.lower()
            if any(after_lower.startswith(adv) for adv in conjunctive_adverbs):
                return '; '
            # Otherwise semicolon for independent clauses
            return '; '

        # Check if it's a list or series
        if ',' in before_context[-20:] or ',' in after_context[:20]:
            return ', '

        # Check for parenthetical or explanatory content
        # Usually lowercase after em-dash for parenthetical
        if after_context and after_context[0].islower():
            return ', '

        # Check if after content is short (might be an aside)
        if len(after_context) < 30:
            return ', '

        # Default: Use comma for general separation
        return ', '

    def _replace_ai_phrases(self, content: str) -> str:
        """Replace common AI-telltale phrases with natural alternatives."""
        for pattern, replacement in self.AI_PHRASE_REPLACEMENTS:
            content, count = re.subn(pattern, replacement, content, flags=re.MULTILINE)
            self.stats['ai_phrases_replaced'] += count
        return content

    def _replace_filler_adverbs(self, content: str) -> str:
        """Replace overused AI filler adverbs at the start of sentences."""
        for adverb, replacement in self.AI_FILLER_ADVERBS.items():
            # Match adverb at the start of a sentence (after newline, period, or start)
            # Also capture the first char after the match to capitalize when replacement is empty
            pattern = r'(?:^|(?<=\. )|(?<=\.\n)|(?<=\n))' + re.escape(adverb.capitalize()) + r',? ?'
            new_text = (replacement + ', ') if replacement else ''
            content, count = re.subn(pattern, new_text, content, flags=re.MULTILINE)
            # Also match lowercase after semicolons
            pattern_lower = r'(?<=; )' + re.escape(adverb) + r',? ?'
            content, count2 = re.subn(pattern_lower, new_text.lower() if new_text else '', content)
            self.stats['ai_filler_adverbs_replaced'] += count + count2

        # Capitalize first letter after sentence boundary when adverb removal left it lowercase
        content = re.sub(r'(?:^|(?<=\. )|(?<=\.\n)|(?<=\n))([a-z])', lambda m: m.group(1).upper(), content, flags=re.MULTILINE)
        return content

    def _clean_whitespace(self, content: str) -> str:
        """Clean up multiple spaces and normalize whitespace."""
        # Replace multiple spaces with single space (but not in specific contexts)
        content = re.sub(r'(?<!\.)  +', ' ', content)  # Multiple spaces to single, but not after period
        
        # Remove spaces that appear between filename and extension (e.g., "file. png" -> "file.png")
        content = re.sub(r'(\w)\s+\.\s*(\w+)', r'\1.\2', content)
        
        # Remove space before punctuation
        content = re.sub(r'\s+([,;:!?])', r'\1', content)
        
        # Only add space after sentence-ending punctuation (.!?) when followed by capital letter
        # AND only if preceded by a word character (ensures it's end of sentence, not a domain/file)
        # This avoids breaking URLs, TLDs, and file extensions while fixing sentence spacing
        content = re.sub(r'(\w)([.!?])([A-Z])', r'\1\2 \3', content)

        # Clean up line breaks
        content = re.sub(r'\n{3,}', '\n\n', content)  # Max 2 consecutive newlines

        return content


def scrub_content(content: str, verbose: bool = False) -> str:
    """
    Convenience function to scrub content.

    Args:
        content: The text to scrub
        verbose: If True, print statistics

    Returns:
        Cleaned content
    """
    scrubber = ContentScrubber()
    cleaned_content, stats = scrubber.scrub(content)

    if verbose:
        print(f"Content Scrubbing Complete:")
        print(f"  - Unicode watermarks removed: {stats['unicode_removed']}")
        print(f"  - Format-control chars removed: {stats['format_control_removed']}")
        print(f"  - Em-dashes replaced: {stats['emdashes_replaced']}")
        print(f"  - AI phrases replaced: {stats['ai_phrases_replaced']}")
        print(f"  - AI filler adverbs replaced: {stats['ai_filler_adverbs_replaced']}")

    return cleaned_content


def scrub_file(file_path: str, output_path: str = None, verbose: bool = False) -> None:
    """
    Scrub a file and optionally save to a new location.

    Args:
        file_path: Path to file to scrub
        output_path: Path to save cleaned content (if None, overwrites original)
        verbose: If True, print statistics
    """
    # Read file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Scrub content
    cleaned_content = scrub_content(content, verbose=verbose)

    # Write file
    output = output_path or file_path
    with open(output, 'w', encoding='utf-8') as f:
        f.write(cleaned_content)

    if verbose:
        print(f"Scrubbed content saved to: {output}")


if __name__ == '__main__':
    # Test the scrubber
    test_content = """
    This is a test\u200Bcontent with invisible\uFEFF characters.

    Here's a sentence with an em-dash—it should be replaced appropriately.

    And another one—this time with\u200C more context—to test the logic.

    Final test: some content\u2060 with word\u00AD joiners and soft\u202F hyphens.
    """

    print("Original content (with invisible chars):")
    print(repr(test_content))
    print("\n" + "="*60 + "\n")

    cleaned = scrub_content(test_content, verbose=True)

    print("\n" + "="*60 + "\n")
    print("Cleaned content:")
    print(cleaned)
