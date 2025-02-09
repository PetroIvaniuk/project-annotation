import re


def highlight_changes(text1, text2):
    # Tokenize the texts into words
    words1 = re.findall(r'\w+|[^\w\s]', text1)
    words2 = re.findall(r'\w+|[^\w\s]', text2)

    # Initialize a SequenceMatcher object
    matcher = SequenceMatcher(None, words1, words2)

    # Get the differences
    diff = matcher.get_opcodes()
    highlighted_text = []

    for op, start1, end1, start2, end2 in diff:
        if op == 'equal':
            # No change, just append the words as is
            highlighted_text.extend(words1[start1:end1])
        elif op == 'delete':
            # Word(s) removed, highlight with red
            for word in words1[start1:end1]:
                word = '\u0336'.join(word) + '\u0336'
                # highlighted_text.append('\033[91m\033[1m' + word + '\033[0m')
                highlighted_text.append(':red[' + word + ']')
        elif op == 'insert':
            # Word(s) added, highlight with green
            for word in words2[start2:end2]:
#                 highlighted_text.append('\033[92m\033[1m' + word + '\033[0m')
                highlighted_text.append(':green[' + word + ']')
        elif op == 'replace':
            # Word(s) replaced, highlight with yellow
            for word in words2[start2:end2]:
#                 highlighted_text.append('\033[93m\033[1m' + word + '\033[0m')
                highlighted_text.append(':violet[' + word + ']')

    return ' '.join(highlighted_text)

def generate_original_corrected_texts(original_text, corrected_text):
    original_words = original_text.split()
    corrected_words = corrected_text.split()

    marked_original_text = []
    marked_corrected_text = []

    removed_words = set(original_words) - set(corrected_words)
    added_words = set(corrected_words) - set(original_words)

    for word in original_words:
        if word in removed_words:
#             marked_original_text.append('\033[91m\033[1m' + word + '\033[0m')
            marked_original_text.append(':red[' + word + ']')

        else:
            marked_original_text.append(word)

    for word in corrected_words:
        if word in added_words:
#             marked_corrected_text.append('\033[92m\033[1m' + word + '\033[0m')
            marked_corrected_text.append(':green[' + word + ']')
        else:
            marked_corrected_text.append(word)

    return (' '.join(marked_original_text), ' '.join(marked_corrected_text))