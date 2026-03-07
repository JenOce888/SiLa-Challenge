#!/usr/bin/env python3
"""
JOUR 13 - Moteur de Recherche par Regex et Index
Full-text search engine with inverted index, advanced regex, TF-IDF ranking, and pickle persistence.
Libraries: re, os, pickle, POO (OOP)
"""

import re
import os
import pickle
import math
import argparse
from collections import defaultdict



#  DATA STRUCTURES

class Posting:
    """Represents a single occurrence of a word in a document."""
    def __init__(self, doc_id: str, positions: list[int]):
        self.doc_id = doc_id
        self.positions = positions  # character positions in file

    def __repr__(self):
        return f"Posting(doc={self.doc_id!r}, pos={self.positions})"


class InvertedIndex:
    """
    Inverted index: maps each token → list of Posting objects.
    Also stores document lengths for TF-IDF normalization.
    """

    def __init__(self):
        self.index: dict[str, list[Posting]] = defaultdict(list)
        self.doc_lengths: dict[str, int] = {}       # total tokens per doc
        self.doc_paths: dict[str, str] = {}          # doc_id → file path
        self.total_docs: int = 0

    def add_document(self, doc_id: str, path: str, tokens: list[str]):
        self.doc_paths[doc_id] = path
        self.doc_lengths[doc_id] = len(tokens)
        self.total_docs += 1

        # Build {token: [positions]} for this document
        token_positions: dict[str, list[int]] = defaultdict(list)
        for pos, token in enumerate(tokens):
            token_positions[token].append(pos)

        for token, positions in token_positions.items():
            self.index[token].append(Posting(doc_id, positions))

    def get_postings(self, token: str) -> list[Posting]:
        return self.index.get(token.lower(), [])

    def find_phrase(self, tokens: list[str]) -> dict[str, list[int]]:
        """
        Positional phrase search: returns {doc_id: [start_positions]}
        where all tokens appear consecutively in that exact order.

        Algorithm:
          1. Get postings for each token in the phrase.
          2. Find docs that contain ALL tokens (intersection).
          3. For each candidate doc, check if any position p exists such that
             token[0] is at p, token[1] at p+1, ..., token[n] at p+n.
        """
        if not tokens:
            return {}

        # Step 1 — posting lists per token, keyed by doc_id
        posting_maps: list[dict[str, set[int]]] = []
        for token in tokens:
            pmap: dict[str, set[int]] = {}
            for posting in self.get_postings(token):
                pmap[posting.doc_id] = set(posting.positions)
            posting_maps.append(pmap)

        # Step 2 — candidate docs must appear in ALL posting lists
        candidate_docs: set[str] = set(posting_maps[0].keys())
        for pmap in posting_maps[1:]:
            candidate_docs &= set(pmap.keys())

        # Step 3 — positional check
        results: dict[str, list[int]] = {}
        for doc_id in candidate_docs:
            # Start from positions of the first token
            anchor_positions = posting_maps[0][doc_id]
            matches = []
            for anchor in sorted(anchor_positions):
                # Verify each subsequent token appears at anchor + offset
                if all(
                    (anchor + offset) in posting_maps[offset][doc_id]
                    for offset in range(1, len(tokens))
                ):
                    matches.append(anchor)
            if matches:
                results[doc_id] = matches

        return results

    def vocabulary_size(self) -> int:
        return len(self.index)

    def __repr__(self):
        return (f"InvertedIndex(docs={self.total_docs}, "
                f"vocab={self.vocabulary_size()})")



#  TOKENIZER

def tokenize(text: str) -> list[str]:
    """Lowercase and split on non-alphanumeric characters."""
    return [t for t in re.split(r'\W+', text.lower()) if t]



#  INDEXER

class Indexer:
    """Recursively walks a directory and indexes all .txt files."""

    def __init__(self, index: InvertedIndex):
        self.index = index
        self._doc_counter = 0

    def index_directory(self, root: str):
        """Recursively index all .txt files under root."""
        root = os.path.abspath(root)
        for dirpath, _, filenames in os.walk(root):
            for fname in filenames:
                if fname.endswith('.txt'):
                    fpath = os.path.join(dirpath, fname)
                    self._index_file(fpath)

    def _index_file(self, path: str):
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except OSError as e:
            print(f"  [WARN] Cannot read {path}: {e}")
            return

        doc_id = f"doc_{self._doc_counter}"
        self._doc_counter += 1
        tokens = tokenize(content)
        self.index.add_document(doc_id, path, tokens)
        print(f"  [INDEX] {path}  ({len(tokens)} tokens, id={doc_id})")


#  TF-IDF RANKER


class TFIDFRanker:
    """Simplified TF-IDF scorer."""

    def __init__(self, index: InvertedIndex):
        self.index = index

    def tf(self, term_count: int, doc_length: int) -> float:
        if doc_length == 0:
            return 0.0
        return term_count / doc_length

    def idf(self, token: str) -> float:
        postings = self.index.get_postings(token)
        df = len(postings)
        if df == 0 or self.index.total_docs == 0:
            return 0.0
        return math.log((self.index.total_docs + 1) / (df + 1)) + 1  # smoothed

    def score(self, tokens: list[str], doc_id: str) -> float:
        total = 0.0
        doc_length = self.index.doc_lengths.get(doc_id, 1)
        for token in tokens:
            postings = self.index.get_postings(token)
            for p in postings:
                if p.doc_id == doc_id:
                    tf_val = self.tf(len(p.positions), doc_length)
                    idf_val = self.idf(token)
                    total += tf_val * idf_val
        return total


#  SEARCH ENGINE


# ANSI colors
RESET  = "\033[0m"
BOLD   = "\033[1m"
YELLOW = "\033[33m"
CYAN   = "\033[36m"
GREEN  = "\033[32m"
RED    = "\033[31m"
DIM    = "\033[2m"


class SearchEngine:
    """
    Full-text search engine combining:
    - Inverted index lookup
    - Advanced PCRE regex (lookahead, named groups)
    - Match highlighting
    - TF-IDF ranking
    - Pickle persistence
    """

    INDEX_FILE = "search_index.pkl"

    def __init__(self):
        self.index = InvertedIndex()
        self.ranker = TFIDFRanker(self.index)

    #  Persistence 

    def save(self, path: str = INDEX_FILE):
        with open(path, 'wb') as f:
            pickle.dump(self.index, f, protocol=pickle.HIGHEST_PROTOCOL)
        print(f"{GREEN}[SAVE]{RESET} Index saved → {path}")

    def load(self, path: str = INDEX_FILE):
        with open(path, 'rb') as f:
            self.index = pickle.load(f)
        self.ranker = TFIDFRanker(self.index)
        print(f"{GREEN}[LOAD]{RESET} Index loaded ← {path}  "
              f"({self.index.total_docs} docs, vocab={self.index.vocabulary_size()})")

    #  Indexing 

    def build_index(self, directory: str):
        print(f"\n{CYAN}{BOLD}Indexing directory:{RESET} {directory}\n")
        indexer = Indexer(self.index)
        indexer.index_directory(directory)
        print(f"\n{GREEN}Done.{RESET} {self.index.total_docs} document(s) indexed, "
              f"vocabulary size: {self.index.vocabulary_size()}\n")

    # Query parser 

    @staticmethod
    def _parse_query(raw: str) -> tuple[str, list[str] | None]:
        """
        Detect query mode:
          - Quoted string  → phrase search  → returns ('phrase', ['tok1','tok2',...])
          - Anything else  → regex search   → returns ('regex', None)
        """
        m = re.fullmatch(r'"([^"]+)"', raw.strip())
        if m:
            phrase_tokens = tokenize(m.group(1))
            return ('phrase', phrase_tokens)
        return ('regex', None)

    #  Phrase search 

    def phrase_search(self, phrase: str, top_k: int = 10) -> list[dict]:
        """
        Find documents where every word in `phrase` appears consecutively,
        using the positional inverted index — NO file I/O needed.
        """
        tokens = tokenize(phrase)
        if not tokens:
            return []

        # Core positional lookup — pure index, no disk reads
        matches_by_doc = self.index.find_phrase(tokens)

        if not matches_by_doc:
            return []

        results = []
        for doc_id, positions in matches_by_doc.items():
            path = self.index.doc_paths[doc_id]

            # Read file only to build snippets
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except OSError:
                continue

            score = self.ranker.score(tokens, doc_id)

            # Convert token positions → character-level snippets
            snippets = []
            for token_pos in positions[:5]:
                snippet = self._snippet_from_token_pos(
                    content, token_pos, tokens, phrase
                )
                snippets.append(snippet)

            results.append({
                "doc_id":       doc_id,
                "path":         path,
                "score":        score,
                "match_count":  len(positions),
                "snippets":     snippets,
                "named_groups": [],
                "mode":         "phrase",
            })

        results.sort(key=lambda r: (r["score"], r["match_count"]), reverse=True)
        return results[:top_k]

    def _snippet_from_token_pos(
        self,
        content: str,
        token_pos: int,
        tokens: list[str],
        original_phrase: str,
        context: int = 60,
    ) -> str:
        """
        Reconstruct character-level snippet from a token-level position.
        We re-tokenize the content to map token index → char offset.
        """
        # Build a list of (char_start, char_end, token) from the content
        char_tokens = list(re.finditer(r'\w+', content))

        if token_pos >= len(char_tokens):
            return f"[token pos {token_pos} out of range]"

        match_start_char = char_tokens[token_pos].start()
        end_token_pos    = token_pos + len(tokens) - 1

        if end_token_pos >= len(char_tokens):
            match_end_char = char_tokens[-1].end()
        else:
            match_end_char = char_tokens[end_token_pos].end()

        # Build snippet around [match_start_char, match_end_char]
        snip_start = max(0, match_start_char - context)
        snip_end   = min(len(content), match_end_char + context)
        snippet    = content[snip_start:snip_end].replace('\n', ' ')

        rel_start  = match_start_char - snip_start
        rel_end    = match_end_char   - snip_start

        highlighted = (
            snippet[:rel_start]
            + YELLOW + BOLD + snippet[rel_start:rel_end] + RESET
            + snippet[rel_end:]
        )
        prefix = "…" if snip_start > 0 else ""
        suffix = "…" if snip_end < len(content) else ""
        return prefix + highlighted + suffix

    #  Search 

    def search(self, pattern: str, top_k: int = 10) -> list[dict]:
        """
        Search using an advanced PCRE-style regex pattern.
        Supports: lookahead (?=...), lookbehind (?<=...), named groups (?P<name>...).
        Returns a ranked list of result dicts.
        """
        # Compile the user pattern (PCRE advanced features via Python re)
        try:
            compiled = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
        except re.error as e:
            print(f"{RED}[ERROR]{RESET} Invalid regex: {e}")
            return []

        # Extract plain tokens from pattern for index pre-filtering
        plain_tokens = re.findall(r'[a-zA-Z0-9]+', pattern)
        plain_tokens = [t.lower() for t in plain_tokens if len(t) > 1]

        # Candidate docs from inverted index
        candidate_ids: set[str] = set()
        if plain_tokens:
            for token in plain_tokens:
                for posting in self.index.get_postings(token):
                    candidate_ids.add(posting.doc_id)
        else:
            # No plain tokens: search all docs (slow but correct)
            candidate_ids = set(self.index.doc_paths.keys())

        results = []
        for doc_id in candidate_ids:
            path = self.index.doc_paths[doc_id]
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except OSError:
                continue

            matches = list(compiled.finditer(content))
            if not matches:
                continue

            score = self.ranker.score(plain_tokens, doc_id)
            snippets = [self._snippet(content, m) for m in matches[:5]]
            named_groups = [m.groupdict() for m in matches if m.groupdict()]

            results.append({
                "doc_id":      doc_id,
                "path":        path,
                "score":       score,
                "match_count": len(matches),
                "snippets":    snippets,
                "named_groups": named_groups,
            })

        # Rank: primary = TF-IDF score, secondary = match count
        results.sort(key=lambda r: (r["score"], r["match_count"]), reverse=True)
        return results[:top_k]

    #  Highlighting 

    def _snippet(self, text: str, match: re.Match, context: int = 60) -> str:
        """Return a context snippet with the match highlighted."""
        start = max(0, match.start() - context)
        end   = min(len(text), match.end() + context)
        snippet = text[start:end].replace('\n', ' ')

        # Highlight the matched portion
        rel_start = match.start() - start
        rel_end   = match.end()   - start
        highlighted = (
            snippet[:rel_start]
            + YELLOW + BOLD + snippet[rel_start:rel_end] + RESET
            + snippet[rel_end:]
        )
        prefix = "…" if start > 0 else ""
        suffix = "…" if end < len(text) else ""
        return prefix + highlighted + suffix

    #,Display 

    def display_results(self, results: list[dict], query: str):
        if not results:
            print(f"\n{RED}No results found for:{RESET} {query!r}\n")
            return

        mode  = results[0].get("mode", "regex")
        label = "phrase" if mode == "phrase" else "regex"
        print(f"\n{CYAN}{BOLD}{'─'*60}{RESET}")
        print(f"{CYAN}{BOLD}  {len(results)} result(s) [{label}] for:{RESET} {query!r}")
        print(f"{CYAN}{BOLD}{'─'*60}{RESET}\n")

        for i, r in enumerate(results, 1):
            fname = os.path.basename(r["path"])
            print(f"{BOLD}{GREEN}#{i}{RESET}  {BOLD}{fname}{RESET}  "
                  f"{DIM}[{r['doc_id']}]{RESET}")
            print(f"    {DIM}Path:{RESET}    {r['path']}")
            print(f"    {DIM}Score:{RESET}   {r['score']:.4f} (TF-IDF)  "
                  f"│  {DIM}Matches:{RESET} {r['match_count']}")

            # Named groups
            for ng in r["named_groups"][:3]:
                if ng:
                    groups_str = "  ".join(f"{CYAN}{k}{RESET}={v!r}"
                                           for k, v in ng.items() if v)
                    print(f"    {DIM}Groups:{RESET}  {groups_str}")

            print(f"    {DIM}Snippets:{RESET}")
            for snippet in r["snippets"]:
                print(f"      {snippet}")
            print()



#  CLI


def banner():
    print(f"""
{CYAN}{BOLD}╔══════════════════════════════════════════════╗
║   🔍  MOTEUR DE RECHERCHE     
║   Regex · Index Inversé · TF-IDF · Pickle   
╚══════════════════════════════════════════════╝{RESET}
""")


def repl(engine: SearchEngine):
    """Interactive REPL for searching."""
    banner()
    print(f"  Type a regex pattern to search.  {DIM}Commands: :help :quit :stats{RESET}\n")

    while True:
        try:
            raw = input(f"{GREEN}search>{RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not raw:
            continue

        if raw == ":quit":
            print("Bye!")
            break
        elif raw == ":stats":
            print(f"  Docs:  {engine.index.total_docs}")
            print(f"  Vocab: {engine.index.vocabulary_size()}\n")
        elif raw == ":help":
            print(f"""
  {CYAN}Commands:{RESET}
    :stats          — show index statistics
    :quit           — exit
    "phrase here"   — {YELLOW}phrase search{RESET} (exact consecutive words, uses positional index)
    <regex>         — regex search (PCRE-style)

  {CYAN}Phrase search examples:{RESET}
    "binary search"               exact two-word phrase
    "import os"                   consecutive tokens
    "def binary search"           three-word phrase

  {CYAN}Regex examples:{RESET}
    hello                         simple word
    (?i)python                    case-insensitive
    (?P<word>\\bdata\\w*)           named group
    (?<=def )\\w+                  lookbehind (function names)
    import (?=os|sys|re)          lookahead
    \\b\\w{{4,6}}\\b                  words of 4-6 chars
""")
        else:
            mode, phrase_tokens = SearchEngine._parse_query(raw)
            if mode == 'phrase':
                phrase_text = raw.strip('"')
                results = engine.phrase_search(phrase_text)
            else:
                results = engine.search(raw)
            engine.display_results(results, raw)


def main():
    parser = argparse.ArgumentParser(
        description="Full-text search engine — Jour 13",
        formatter_class=argparse.RawTextHelpFormatter
    )
    sub = parser.add_subparsers(dest="command")

    # index command
    idx_p = sub.add_parser("index", help="Build index from a directory")
    idx_p.add_argument("directory", help="Root directory to index")
    idx_p.add_argument("--save", default="search_index.pkl",
                       help="Output pickle file (default: search_index.pkl)")

    # search command
    srch_p = sub.add_parser("search", help="Search the index")
    srch_p.add_argument("pattern", nargs="?", default=None,
                        help="Regex pattern (omit for interactive REPL)")
    srch_p.add_argument("--load", default="search_index.pkl",
                        help="Index pickle file (default: search_index.pkl)")
    srch_p.add_argument("--top", type=int, default=10,
                        help="Max results to show (default: 10)")
    srch_p.add_argument("--phrase", action="store_true",
                        help='Force phrase search mode (same as wrapping in quotes)')

    # interactive command
    sub.add_parser("repl", help="Interactive search REPL (loads existing index)")

    args = parser.parse_args()
    engine = SearchEngine()

    if args.command == "index":
        engine.build_index(args.directory)
        engine.save(args.save)

    elif args.command == "search":
        if not os.path.exists(args.load):
            print(f"{RED}[ERROR]{RESET} Index file not found: {args.load}")
            print("  Run:  python search_engine.py index <directory>  first.")
            return
        engine.load(args.load)
        if args.pattern:
            mode, _ = SearchEngine._parse_query(args.pattern)
            if args.phrase or mode == 'phrase':
                phrase_text = args.pattern.strip('"')
                results = engine.phrase_search(phrase_text, top_k=args.top)
            else:
                results = engine.search(args.pattern, top_k=args.top)
            engine.display_results(results, args.pattern)
        else:
            repl(engine)

    elif args.command == "repl":
        if os.path.exists(SearchEngine.INDEX_FILE):
            engine.load(SearchEngine.INDEX_FILE)
        else:
            print(f"{YELLOW}[WARN]{RESET} No index loaded. Use 'index' command first.\n")
        repl(engine)

    else:
        banner()
        parser.print_help()


if __name__ == "__main__":
    main()