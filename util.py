def sanitize_filename(unsafe_filename):
    return "".join([c for c in unsafe_filename if c.isalpha() or c.isdigit() or c==' ']).rstrip()