# scoring_utils.py
from typing import Dict, Any
import random

def normalize_score(raw: float) -> int:
    """Convert raw 0–1 score to a 0–10 integer."""
    return max(0, min(10, int(round(raw * 10))))


def mock_evaluate_answer(question: str, answer: str) -> Dict[str, Any]:
    """Mock evaluator for Java / Python / DSA answers."""
    
    if not answer or len(answer.strip()) < 5:
        return {
            "score": 0,
            "feedback": "Answer too short.",
            "suggestions": ["Provide more detail in your explanation."]
        }

    answer_lower = answer.lower()

    # ------------------------------------------------------------
    # DOMAIN SPECIFIC KEYWORDS (Java, Python, DSA)
    # ------------------------------------------------------------
    
    KEYWORDS = {
        "java": {
            "OOP": ["encapsulation", "inheritance", "polymorphism", "abstraction"],
            "collections": ["arraylist", "linkedlist", "hashmap", "set", "iterator"],
            "memory": ["heap", "stack", "garbage collector", "gc", "jvm"],
            "threads": ["multithreading", "synchronized", "thread", "runnable", "concurrency"],
            "jvm": ["bytecode", "classloader", "jit", "jre"],
        },

        "python": {
            "basics": ["indentation", "dynamic typing", "lists", "tuples", "dict", "set"],
            "oop": ["class", "object", "inheritance", "polymorphism", "method overriding"],
            "advanced": ["decorators", "generators", "lambda", "list comprehension"],
            "modules": ["import", "pip", "virtualenv", "package"],
            "memory": ["garbage collector", "reference counting"],
        },

        "dsa": {
            "arrays": ["array", "index", "time complexity", "big o"],
            "linkedlist": ["node", "pointer", "head", "tail", "insertion"],
            "sorting": ["merge sort", "quick sort", "bubble sort", "insertion sort", "nlogn"],
            "trees": ["binary tree", "bst", "traversal", "dfs", "bfs", "height"],
            "graphs": ["dfs", "bfs", "adjacency", "shortest path", "dijkstra"],
            "dp": ["dynamic programming", "recursion", "memoization", "tabulation"],
        }
    }

    # ------------------------------------------------------------
    # DETECT DOMAIN
    # ------------------------------------------------------------
    detected_domain = None
    q_lower = question.lower()

    if any(word in q_lower for word in ["java", "jvm", "oop", "jdk"]):
        detected_domain = "java"
    elif any(word in q_lower for word in ["python", "py", "indent", "list"]):
        detected_domain = "python"
    else:
        detected_domain = "dsa"  # fallback

    # ------------------------------------------------------------
    # SCORE BASED ON KEYWORD MATCHES
    # ------------------------------------------------------------
    hit = 0

    for category, words in KEYWORDS[detected_domain].items():
        for kw in words:
            if kw.lower() in answer_lower:
                hit += 1

    # Base score with randomness + hits
    base = min(1.0, 0.4 + 0.18 * hit + random.uniform(-0.1, 0.1))
    score = normalize_score(base)

    # ------------------------------------------------------------
    # FEEDBACK & SUGGESTIONS
    # ------------------------------------------------------------
    if score >= 7:
        feedback = f"Strong answer! You covered important {detected_domain.upper()} concepts."
        suggestions = ["Add a short example or pseudo-code to make it even better."]
    elif score >= 4:
        feedback = f"Fair attempt. You mentioned some relevant {detected_domain.upper()} points, but missing details."
        suggestions = ["Explain more steps clearly.", "Add correct terminology and examples."]
    else:
        feedback = f"Weak answer. Missing key {detected_domain.upper()} concepts."
        suggestions = [
            "Cover fundamental concepts.",
            "Provide definitions, examples, and use cases.",
            "Explain in simple steps."
        ]

    return {
        "score": score,
        "feedback": feedback,
        "suggestions": suggestions
    }
