"""S2-2.4: Hamidat Oloko's tricky-answer fixtures for evaluator tests.

Checkpoint 1 stand-in: the current question library has no rubric statements.
The full sentences below are PROVISIONAL human expectations, not the official
S2-1.4 rubric. Before asserting exact criteria_met equality, replace these texts
with the corresponding official rubric texts and re-review every expected_met.
RUBRICS_FINALIZED must stay False until that review is complete. Do not use this
stand-in for an AI-versus-human agreement report.

There are eight existing technical prompts, each with all five answer kinds.
Add behavioral cases using exact prompts and STAR criteria after S2-3.1 lands;
keep at least eight cases per kind. No evaluator imports, API keys, or AI calls.
Wrong-with-keywords and stuffing cases test the AI path: the basic keyword
fallback is explicitly allowed to over-credit them by the Sprint 2 contract.
"""

RUBRICS_FINALIZED = False

# Proposed criteria are local fixture metadata, never changes to question data.
# Keeping the text in one place makes reconciliation with S2-1.4 straightforward.
PROVISIONAL_CRITERIA = {
    "What is the difference between an array and a linked list?": [
        "Explains that an array stores its elements next to each other in memory.",
        "Explains that a linked list is made of nodes connected by pointers.",
    ],
    "What is a stack, and what are its main operations?": [
        "Explains that a stack removes the most recently added item first.",
        "Explains that push adds to the top, pop removes the top, and peek reads the top without removing it.",
    ],
    "Explain how binary search works and its time complexity.": [
        "Explains that binary search requires sorted data and repeatedly selects the half that could contain the target.",
        "States that binary search takes O(log n) time.",
    ],
    "What is the difference between a primary key and a foreign key?": [
        "Explains that a primary key uniquely identifies a row and cannot be null.",
        "Explains that a foreign key references a key in another or the same table to enforce a relationship.",
    ],
    "What is the difference between authentication and authorization?": [
        "Explains that authentication verifies a user's identity.",
        "Explains that authorization determines which resources or actions a user may access.",
    ],
    "What is the difference between TCP and UDP?": [
        "Explains that TCP provides a connection-oriented, reliable, ordered byte stream.",
        "Explains that UDP sends datagrams without guaranteeing delivery or order.",
    ],
    "What is the difference between unit testing and integration testing?": [
        "Explains that unit testing checks an individual component in isolation.",
        "Explains that integration testing checks interactions between components working together.",
    ],
    "What is the difference between a shallow copy and a deep copy?": [
        "Explains that a shallow copy creates a new outer container but shares references to nested objects.",
        "Explains that a deep copy recursively copies nested mutable objects so they can be changed independently.",
    ],
}


def _case(prompt: str, answer: str, kind: str, met: tuple[int, ...]) -> dict:
    """Build the locked four-field case shape from provisional criteria indices."""
    return {
        "prompt": prompt,
        "answer": answer,
        "kind": kind,
        "expected_met": [PROVISIONAL_CRITERIA[prompt][i] for i in met],
    }


# Each group intentionally uses the same prompt, so wording and correctness
# change while the question stays fixed. Partial cases cover exactly one point.
GRADING_CASES = []

_PROMPT = "What is the difference between an array and a linked list?"
GRADING_CASES.extend([
    _case(_PROMPT,
          "An array stores elements in contiguous memory. A linked list stores "
          "elements in nodes connected by pointers; the nodes need not be adjacent.",
          "correct", (0, 1)),
    _case(_PROMPT,
          "An array keeps its entries side by side in storage. In a linked list, "
          "each item lives in a record that holds a reference to the next record.",
          "reworded", (0, 1)),
    _case(_PROMPT,
          "An array never uses contiguous memory; every array element is a node "
          "connected by a pointer. A linked list requires all its elements to "
          "be contiguous and never uses nodes or pointers.",
          "wrong_with_keywords", ()),
    _case(_PROMPT, "contiguous memory node pointer index insertion",
          "keyword_stuffing", ()),
    _case(_PROMPT, "An array stores its elements next to each other in memory.",
          "partial", (0,)),
])

_PROMPT = "What is a stack, and what are its main operations?"
GRADING_CASES.extend([
    _case(_PROMPT,
          "A stack is LIFO: the last item pushed is the first popped. Push adds "
          "an item to the top, pop removes the top item, and peek returns the "
          "top item without removing it.", "correct", (0, 1)),
    _case(_PROMPT,
          "Think of a pile of plates: the newest plate comes off first. You can "
          "put a plate on top, take the top one away, or inspect the top one "
          "while leaving it in place; those operations are push, pop, and peek.",
          "reworded", (0, 1)),
    _case(_PROMPT,
          "LIFO means the oldest item leaves first. Push removes the bottom, "
          "pop adds an item to the bottom, and peek deletes the top item.",
          "wrong_with_keywords", ()),
    _case(_PROMPT, "lifo push pop peek top", "keyword_stuffing", ()),
    _case(_PROMPT, "A stack removes the most recently added item first.",
          "partial", (0,)),
])

_PROMPT = "Explain how binary search works and its time complexity."
GRADING_CASES.extend([
    _case(_PROMPT,
          "Binary search requires sorted data. Compare the target with the "
          "middle item, then keep only the left or right half where it could "
          "be. Repeat until found or the range is empty. Time is O(log n).",
          "correct", (0, 1)),
    _case(_PROMPT,
          "With entries in ascending order, check the midpoint and discard the "
          "half that cannot contain the value. Keep halving the remaining "
          "range. The number of checks grows logarithmically, O(log n).",
          "reworded", (0, 1)),
    _case(_PROMPT,
          "Binary search does not need sorted data. After checking the middle, "
          "search both the left and right half completely. Its time is O(n); "
          "O(log n) is never its search complexity.",
          "wrong_with_keywords", ()),
    _case(_PROMPT, "sorted middle half o(log n) left right",
          "keyword_stuffing", ()),
    _case(_PROMPT, "Binary search has O(log n) time complexity.",
          "partial", (1,)),
])

_PROMPT = "What is the difference between a primary key and a foreign key?"
GRADING_CASES.extend([
    _case(_PROMPT,
          "A primary key is a unique identifier for each row and cannot be "
          "null. A foreign key references a key in another table, or the same "
          "table, to enforce the relationship between rows.",
          "correct", (0, 1)),
    _case(_PROMPT,
          "The main row identifier must be distinct for every record and always "
          "present. A reference column points to an existing keyed record, "
          "linking related records and preventing invalid references.",
          "reworded", (0, 1)),
    _case(_PROMPT,
          "A primary key identifier may be null and duplicate, so it is not "
          "unique. A foreign key never references any table or enforces a "
          "relationship; reference checks are forbidden.",
          "wrong_with_keywords", ()),
    _case(_PROMPT, "unique identifier reference relationship table null",
          "keyword_stuffing", ()),
    _case(_PROMPT,
          "A primary key uniquely identifies each row and cannot be null.",
          "partial", (0,)),
])

_PROMPT = "What is the difference between authentication and authorization?"
GRADING_CASES.extend([
    _case(_PROMPT,
          "Authentication verifies identity, such as checking a password at "
          "login. Authorization checks permissions to decide whether that "
          "user can access a resource or perform an action.",
          "correct", (0, 1)),
    _case(_PROMPT,
          "First you prove who you are. Separately, the system decides what "
          "you are allowed to do, such as view a report or edit a record.",
          "reworded", (0, 1)),
    _case(_PROMPT,
          "Authentication never checks identity at login; it only grants "
          "permission based on role. Authorization only validates an identity "
          "token and never decides access permissions.",
          "wrong_with_keywords", ()),
    _case(_PROMPT, "identity permission login role token access",
          "keyword_stuffing", ()),
    _case(_PROMPT,
          "Authorization checks which actions and resources a user is allowed "
          "to access.", "partial", (1,)),
])

_PROMPT = "What is the difference between TCP and UDP?"
GRADING_CASES.extend([
    _case(_PROMPT,
          "TCP establishes a connection and provides a reliable, ordered byte "
          "stream, retransmitting lost data. UDP sends datagrams without "
          "guaranteeing arrival or order; applications handle those needs.",
          "correct", (0, 1)),
    _case(_PROMPT,
          "TCP opens a conversation, resends missing bytes and presents them "
          "in sequence. UDP sends separate messages with no promise that "
          "they reach the destination or keep their original sequence.",
          "reworded", (0, 1)),
    _case(_PROMPT,
          "TCP has no connection or handshake and never provides reliable or "
          "ordered delivery. UDP always uses a handshake and guarantees a "
          "reliable, ordered stream, making streaming loss impossible.",
          "wrong_with_keywords", ()),
    _case(_PROMPT, "connection reliable ordered handshake fast streaming",
          "keyword_stuffing", ()),
    _case(_PROMPT,
          "UDP sends datagrams without guaranteeing delivery or their order.",
          "partial", (1,)),
])

_PROMPT = "What is the difference between unit testing and integration testing?"
GRADING_CASES.extend([
    _case(_PROMPT,
          "Unit testing checks an individual component in isolation, often "
          "using a mock for dependencies. Integration testing runs components "
          "together to check that their interactions work correctly.",
          "correct", (0, 1)),
    _case(_PROMPT,
          "One approach tests a single small piece while substituting its "
          "collaborators. The other connects several pieces and verifies "
          "that they communicate and work with each other as intended.",
          "reworded", (0, 1)),
    _case(_PROMPT,
          "Unit testing always runs every component together and never checks "
          "an individual component in isolation. Integration testing only "
          "tests one isolated function with a mock and never tests interaction.",
          "wrong_with_keywords", ()),
    _case(_PROMPT, "individual component isolation together interaction mock",
          "keyword_stuffing", ()),
    _case(_PROMPT,
          "Integration testing checks the interactions between components "
          "that run together.", "partial", (1,)),
])

_PROMPT = "What is the difference between a shallow copy and a deep copy?"
GRADING_CASES.extend([
    _case(_PROMPT,
          "A shallow copy creates a new outer container but keeps references "
          "to the same nested objects. A deep copy recursively copies nested "
          "mutable objects so changing a copied nested list does not change "
          "the original nested list.", "correct", (0, 1)),
    _case(_PROMPT,
          "For a list of lists, the shallow version makes a new outer list "
          "while its inner lists are still shared. The deep version duplicates "
          "the inner lists too, letting either version be edited independently.",
          "reworded", (0, 1)),
    _case(_PROMPT,
          "A shallow copy recursively makes every nested object independent. "
          "A deep copy made with deepcopy never copies nested objects and "
          "always keeps the original nested reference shared.",
          "wrong_with_keywords", ()),
    _case(_PROMPT, "reference nested copy deepcopy object independent",
          "keyword_stuffing", ()),
    _case(_PROMPT,
          "A shallow copy makes a new outer container while retaining "
          "references to the same nested objects.", "partial", (0,)),
])
