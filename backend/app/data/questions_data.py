"""
S1-2.1 — Sprint 1 technical question library (source of truth).
Each entry: (category, difficulty, prompt, expected_keywords)
expected_keywords are lowercase terms the KeywordEvaluator (S1-5.1) looks for in an answer.
Difficulty: Easy | Medium | Hard
"""

QUESTIONS = [
    # ---------------- Data Structures ----------------
    ("Data Structures", "Easy", "What is the difference between an array and a linked list?",
     ["contiguous", "memory", "node", "pointer", "index", "insertion"]),
    ("Data Structures", "Easy", "What is a stack, and what are its main operations?",
     ["lifo", "push", "pop", "peek", "top"]),
    ("Data Structures", "Medium", "How does a hash table work, and how are collisions handled?",
     ["hash function", "bucket", "key", "collision", "chaining", "open addressing", "o(1)"]),
    ("Data Structures", "Medium", "What is the difference between a queue and a priority queue?",
     ["fifo", "enqueue", "dequeue", "priority", "heap"]),
    ("Data Structures", "Hard", "Explain how a binary search tree works and why it can become unbalanced.",
     ["left", "right", "smaller", "larger", "o(log n)", "o(n)", "balanced", "avl", "red-black"]),

    # ---------------- Algorithms ----------------
    ("Algorithms", "Easy", "Explain how binary search works and its time complexity.",
     ["sorted", "middle", "half", "o(log n)", "left", "right"]),
    ("Algorithms", "Easy", "What is Big-O notation and why is it used?",
     ["time complexity", "space complexity", "worst case", "growth", "input size"]),
    ("Algorithms", "Medium", "Compare merge sort and quick sort.",
     ["divide and conquer", "pivot", "merge", "o(n log n)", "o(n^2)", "stable", "in-place"]),
    ("Algorithms", "Medium", "What is the difference between breadth-first search and depth-first search?",
     ["queue", "stack", "level", "recursion", "shortest path", "graph"]),
    ("Algorithms", "Hard", "What is dynamic programming? Explain with an example.",
     ["subproblem", "overlapping", "memoization", "tabulation", "optimal substructure", "fibonacci"]),

    # ---------------- Object-Oriented Programming ----------------
    ("OOP", "Easy", "What are the four pillars of object-oriented programming?",
     ["encapsulation", "inheritance", "polymorphism", "abstraction"]),
    ("OOP", "Easy", "What is the difference between a class and an object?",
     ["blueprint", "instance", "attribute", "method", "memory"]),
    ("OOP", "Medium", "Explain the difference between method overloading and method overriding.",
     ["compile time", "runtime", "parameters", "subclass", "signature", "polymorphism"]),
    ("OOP", "Medium", "What is the difference between an abstract class and an interface?",
     ["abstract", "interface", "implement", "multiple inheritance", "contract", "method"]),
    ("OOP", "Hard", "Explain the SOLID principles.",
     ["single responsibility", "open closed", "liskov", "interface segregation", "dependency inversion"]),

    # ---------------- Databases & SQL ----------------
    ("Databases", "Easy", "What is the difference between a primary key and a foreign key?",
     ["unique", "identifier", "reference", "relationship", "table", "null"]),
    ("Databases", "Easy", "What is the difference between SQL and NoSQL databases?",
     ["relational", "schema", "table", "document", "scalability", "join"]),
    ("Databases", "Medium", "Explain the different types of SQL joins.",
     ["inner join", "left join", "right join", "full outer join", "matching", "null"]),
    ("Databases", "Medium", "What is database normalization and why is it important?",
     ["redundancy", "1nf", "2nf", "3nf", "dependency", "anomaly"]),
    ("Databases", "Hard", "What are ACID properties and what is an index?",
     ["atomicity", "consistency", "isolation", "durability", "transaction", "index", "b-tree", "lookup"]),

    # ---------------- Web & APIs ----------------
    ("Web & APIs", "Easy", "What is a REST API?",
     ["http", "resource", "stateless", "get", "post", "json", "endpoint"]),
    ("Web & APIs", "Easy", "What is the difference between GET and POST requests?",
     ["retrieve", "send", "body", "url", "idempotent", "query parameter"]),
    ("Web & APIs", "Medium", "What do HTTP status codes 200, 201, 400, 401, 404, and 500 mean?",
     ["ok", "created", "bad request", "unauthorized", "not found", "server error"]),
    ("Web & APIs", "Medium", "What is the difference between authentication and authorization?",
     ["identity", "permission", "login", "role", "token", "access"]),
    ("Web & APIs", "Hard", "What is CORS and why do browsers enforce it?",
     ["cross-origin", "origin", "browser", "header", "preflight", "security"]),

    # ---------------- Operating Systems & Concurrency ----------------
    ("Operating Systems", "Easy", "What is the difference between a process and a thread?",
     ["memory", "shared", "independent", "lightweight", "context switch"]),
    ("Operating Systems", "Easy", "What is virtual memory?",
     ["ram", "disk", "paging", "address", "page table"]),
    ("Operating Systems", "Medium", "What is a deadlock, and what conditions cause it?",
     ["mutual exclusion", "hold and wait", "no preemption", "circular wait", "resource"]),
    ("Operating Systems", "Medium", "What is a race condition and how can you prevent it?",
     ["shared", "concurrent", "lock", "mutex", "synchronization", "atomic"]),
    ("Operating Systems", "Hard", "What is the difference between a mutex and a semaphore?",
     ["lock", "counter", "ownership", "binary", "signal", "wait", "resource"]),

    # ---------------- Networking ----------------
    ("Networking", "Easy", "What is the difference between TCP and UDP?",
     ["connection", "reliable", "ordered", "handshake", "fast", "streaming"]),
    ("Networking", "Easy", "What is DNS and how does it work?",
     ["domain", "ip address", "resolve", "lookup", "server", "cache"]),
    ("Networking", "Medium", "What happens when you type a URL into a browser and press Enter?",
     ["dns", "ip", "tcp", "http", "request", "response", "render"]),
    ("Networking", "Medium", "What is the difference between HTTP and HTTPS?",
     ["encryption", "tls", "ssl", "certificate", "secure", "port 443"]),
    ("Networking", "Hard", "Explain the TCP three-way handshake.",
     ["syn", "syn-ack", "ack", "connection", "sequence number"]),

    # ---------------- Software Engineering & Testing ----------------
    ("Software Engineering", "Easy", "What is version control and why is Git used?",
     ["history", "branch", "commit", "merge", "collaboration", "repository"]),
    ("Software Engineering", "Easy", "What is the difference between unit testing and integration testing?",
     ["individual", "component", "isolation", "together", "interaction", "mock"]),
    ("Software Engineering", "Medium", "What is CI/CD and why is it useful?",
     ["continuous integration", "continuous deployment", "automated", "pipeline", "test", "build"]),
    ("Software Engineering", "Medium", "What is the difference between Agile and Waterfall?",
     ["iterative", "sprint", "sequential", "phase", "feedback", "flexible"]),
    ("Software Engineering", "Hard", "What is test-driven development, and what are its pros and cons?",
     ["test first", "red", "green", "refactor", "coverage", "design", "slower"]),

    # ---------------- Python ----------------
    ("Python", "Easy", "What is the difference between a list and a tuple in Python?",
     ["mutable", "immutable", "brackets", "parentheses", "hashable"]),
    ("Python", "Easy", "What is a Python dictionary and when would you use one?",
     ["key", "value", "hash", "lookup", "o(1)", "unique"]),
    ("Python", "Medium", "What are decorators in Python?",
     ["function", "wrap", "@", "higher-order", "behavior", "closure"]),
    ("Python", "Medium", "What is the difference between a shallow copy and a deep copy?",
     ["reference", "nested", "copy", "deepcopy", "object", "independent"]),
    ("Python", "Hard", "What is the Global Interpreter Lock (GIL) in Python?",
     ["thread", "cpython", "lock", "one thread", "multiprocessing", "cpu-bound", "i/o-bound"]),

    # ---------------- System Design ----------------
    ("System Design", "Easy", "What is caching and why is it used?",
     ["fast", "memory", "redis", "latency", "expiration", "hit", "miss"]),
    ("System Design", "Easy", "What is a load balancer?",
     ["distribute", "traffic", "server", "round robin", "availability", "scalability"]),
    ("System Design", "Medium", "What is the difference between horizontal and vertical scaling?",
     ["more machines", "bigger machine", "cpu", "ram", "distributed", "limit"]),
    ("System Design", "Medium", "How would you design a URL shortener?",
     ["hash", "unique id", "database", "redirect", "cache", "collision", "base62"]),
    ("System Design", "Hard", "Explain the CAP theorem.",
     ["consistency", "availability", "partition tolerance", "trade-off", "distributed"]),
]
