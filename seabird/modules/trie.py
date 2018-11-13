from typing import Dict, List


class UnknownLetterError(Exception):
    pass


class TrieNode:
    def __init__(self, letter: str) -> None:
        self.letter = letter
        self.is_word = False
        self.children: Dict[str, "TrieNode"] = {}

    def __hash__(self) -> int:
        return hash(self.letter)

    def __lt__(self, other: "TrieNode") -> bool:
        return self.letter < other.letter

    def __str__(self) -> str:
        return 'TrieNode("{}", [{}])'.format(
            self.letter,
            ", ".join([str(self.children[c]) for c in sorted(self.children)]),
        )

    def child(self, letter: str, create: bool = False) -> "TrieNode":
        node = self.children.get(letter)
        if node is not None:
            return node

        if create:
            node = self.__class__(letter)
            self.children[letter] = node
            return node

        raise UnknownLetterError()


class Trie:
    def __init__(self):
        self.root = TrieNode("")

    def __str__(self) -> str:
        return str(self.root)

    def add_word(self, word: str) -> None:
        node = self.root
        for letter in word:
            node = node.child(letter, create=True)
        node.is_word = True

    def words_for_prefix(self, prefix: str) -> List[str]:
        node = self.root
        for letter in prefix:
            try:
                node = node.child(letter)
            except UnknownLetterError:
                return []

        words = []
        to_check = []
        for child in node.children.values():
            to_check.append((prefix, child))

        while to_check:
            node_prefix, node = to_check[0]
            to_check = to_check[1:]
            new_prefix = node_prefix + node.letter

            if node.is_word:
                words.append(new_prefix)

            for child in node.children.values():
                to_check.append((new_prefix, child))

        return words
