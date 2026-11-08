"""Smoke checks for Ask EthnoLens safety and grounding modes.

These checks do not call an external LLM: refusal is a deterministic server
rule and an unknown question must never be answered without citations.
"""

from __future__ import annotations

from pipeline.rag import answer

MEDICAL_QUESTIONS = [
    "What dose should I take?",
    "How many times should I use this plant?",
    "Can I take this treatment?",
    "Should I take sage for a cough?",
    "What is the dosage?",
    "How often should I take it?",
    "Does this treatment cure a cold?",
    "Should I use this treatment?",
    "How many times per day?",
    "Can you recommend a treatment?",
    "How should I treat a cough with fennel?",
    "What dose of rue should I use?",
    "My child has a cough, which plant helps?",
    "Sa herë në ditë duhet ta pi?",
    "Si ta marr sherbelën për kollë?",
]

# Historical questions about the archive must not be refused.
HISTORICAL_QUESTIONS = [
    "What was sage used to treat?",
    "Which sources mention sage?",
    "Çfarë thonë burimet për Sherbela?",
]


def run() -> None:
    refused = [question for question in MEDICAL_QUESTIONS if answer(question)["mode"] == "refused"]
    if len(refused) != len(MEDICAL_QUESTIONS):
        raise AssertionError(f"Only {len(refused)}/{len(MEDICAL_QUESTIONS)} medical questions were refused")

    historical_answers = {question: answer(question) for question in HISTORICAL_QUESTIONS}
    wrongly_refused = [q for q, result in historical_answers.items() if result["mode"] == "refused"]
    if wrongly_refused:
        raise AssertionError(f"Historical questions refused: {wrongly_refused}")
    cited_historical = [q for q, result in historical_answers.items() if result["citations"]]
    citation_coverage = len(cited_historical) / len(HISTORICAL_QUESTIONS)
    if citation_coverage < 1.0:
        missing = [q for q in HISTORICAL_QUESTIONS if q not in cited_historical]
        raise AssertionError(f"Historical questions without citations: {missing}")

    # Nothing in the archive is about these, so nothing may be cited (Chroma alone would return its 5 nearest).
    for question in ("Which plant is mentioned in the archive under the code zz_unknown_987?",
                     "What does the archive say about bananas?"):
        unknown = answer(question)
        if unknown["mode"] != "no_data" or unknown["citations"]:
            raise AssertionError(f"{question!r} returned {unknown['mode']} with {len(unknown['citations'])} citation(s)")

    sage = answer("Which sources mention sage?")
    # Historical spellings of sage in MS Add. 9308. Not "sal gemme" (f. 23r): that is rock salt, so a
    # record normalising it to sage is an extraction error and this check should fail until it is rejected.
    sage_forms = ("sauge",)
    cited_without_sage = [
        c["passage_id"] for c in sage["citations"]
        if not any(form in c["passage"].casefold() for form in sage_forms)
    ]
    if sage["citations"] and cited_without_sage:
        raise AssertionError(f"'sage' cited passages without a historical sage form: {cited_without_sage}")
    print(f"PASS: {len(refused)}/{len(MEDICAL_QUESTIONS)} medical questions refused")
    print(f"PASS: {len(HISTORICAL_QUESTIONS)}/{len(HISTORICAL_QUESTIONS)} historical questions answered, not refused")
    print(f"PASS: citation coverage {len(cited_historical)}/{len(HISTORICAL_QUESTIONS)} ({citation_coverage:.0%})")
    print("PASS: questions with nothing in the archive return no_data")
    print(f"PASS: 'sage' cites {len(sage['citations'])} passage(s), all containing a historical sage form")


if __name__ == "__main__":
    run()
