## 2024-05-24 - Pre-compile regex for performance
**Learning:** Instantiating and compiling regular expressions inside tight loops or frequently called functions adds significant, unnecessary CPU overhead.
**Action:** When a static set of string patterns is used repeatedly (like locale keywords in NLP), compile them to `re.Pattern` objects during class initialization or at the module level.
