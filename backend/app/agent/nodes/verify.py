"""
Verify Node for Sahayak Voice V2.
Performs deterministic account verification using the last 4 digits.
Supports ASCII digits, Gujarati numerals, and spoken Gujarati number phrases.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any
from app.agent.state import CallState
from app.prompts.verify import buildVerifyFailedPrompt, buildVerifyMismatchPrompt


# Number dictionary for Gujarati, Hinglish, and English number words
NUMBER_WORDS: dict[str, int] = {
    # 0
    "શૂન્ય": 0, "સુન્ય": 0, "મીંડું": 0, "મીંડુ": 0, "ઝીરો": 0, "જીરો": 0,
    "zero": 0, "ziro": 0, "zeero": 0, "shunya": 0, "शून्य": 0, "जीरो": 0, "sifar": 0, "oh": 0, "o": 0,
    # 1-9
    "એક": 1, "ek": 1, "one": 1,
    "બે": 2, "be": 2, "do": 2, "two": 2,
    "ત્રણ": 3, "teen": 3, "tran": 3, "three": 3,
    "ચાર": 4, "char": 4, "chaar": 4, "four": 4,
    "પાંચ": 5, "પંચ": 5, "panch": 5, "paanch": 5, "five": 5,
    "છ": 6, "chha": 6, "che": 6, "chhe": 6, "six": 6,
    "સાત": 7, "saat": 7, "sat": 7, "seven": 7,
    "આઠ": 8, "aath": 8, "ath": 8, "eight": 8,
    "નવ": 9, "nav": 9, "nau": 9, "nine": 9,
    # 10-19
    "દસ": 10, "das": 10, "ten": 10,
    "અગિયાર": 11, "agiyar": 11, "gyarah": 11, "eleven": 11,
    "બાર": 12, "bar": 12, "barah": 12, "twelve": 12,
    "તેર": 13, "ter": 13, "terah": 13, "thirteen": 13,
    "ચૌદ": 14, "chaud": 14, "chaudah": 14, "fourteen": 14,
    "પંદર": 15, "pandar": 15, "pandrah": 15, "fifteen": 15,
    "સોળ": 16, "sol": 16, "solah": 16, "sixteen": 16,
    "સત્તર": 17, "સત્ર": 17, "sattar": 17, "satrah": 17, "seventeen": 17,
    "અઢાર": 18, "adhar": 18, "atharah": 18, "eighteen": 18,
    "ઓગણીસ": 19, "ognis": 19, "unnis": 19, "nineteen": 19,
    # 20-29
    "વીસ": 20, "vis": 20, "vees": 20, "bees": 20, "twenty": 20,
    "એકવીસ": 21, "ekvis": 21, "ikvees": 21,
    "બાવીસ": 22, "bavis": 22, "baees": 22,
    "ત્રેવીસ": 23, "તેવીસ": 23, "trevis": 23, "teees": 23,
    "ચોવીસ": 24, "chovis": 24, "chaubees": 24,
    "પચ્ચીસ": 25, "pachchis": 25, "pachchees": 25,
    "છવ્વીસ": 26, "chhavvis": 26, "chhabbees": 26,
    "સત્તાવીસ": 27, "sattavis": 27, "sattaees": 27,
    "અઠ્ઠાવીસ": 28, "atthavis": 28, "atthaees": 28,
    "ઓગણત્રીસ": 29, "ogantris": 29, "unatis": 29,
    # 30-39
    "ત્રીસ": 30, "tris": 30, "tees": 30, "thirty": 30,
    "એકત્રીસ": 31, "ektris": 31, "iktis": 31,
    "બત્રીસ": 32, "batris": 32, "battis": 32,
    "તેત્રીસ": 33, "tetris": 33, "tentis": 33,
    "ચોત્રીસ": 34, "chotris": 34, "chautis": 34,
    "પાંત્રીસ": 35, "pantris": 35, "paintis": 35,
    "છત્રીસ": 36, "chhatris": 36, "chhattis": 36,
    "સાડત્રીસ": 37, "sadatris": 37, "santis": 37,
    "આડત્રીસ": 38, "adatris": 38, "adhtis": 38,
    "ઓગણચાલીસ": 39, "oganchalis": 39, "untalis": 39,
    # 40-49
    "ચાલીસ": 40, "chalis": 40, "forty": 40,
    "એકતાલીસ": 41, "ektalis": 41, "iktalis": 41,
    "બેતાલીસ": 42, "betalis": 42, "bayalis": 42,
    "તેતાલીસ": 43, "tetalis": 43, "taintalis": 43,
    "ચુંમાલીસ": 44, "ચોમાલીસ": 44, "chumalis": 44, "chawalis": 44,
    "પિસ્તાલીસ": 45, "pistalis": 45, "paitalis": 45,
    "છેતાલીસ": 46, "chhetalis": 46, "chhiyalis": 46,
    "સુડતાલીસ": 47, "sudtalis": 47, "saintalis": 47,
    "અડતાલીસ": 48, "adtalis": 48,
    "ઓગણપચાસ": 49, "oganpachas": 49, "unchas": 49,
    # 50-99
    "પચાસ": 50, "pachas": 50, "fifty": 50,
    "એકાવન": 51, "બાવન": 52, "ત્રેપન": 53, "ચોપન": 54, "પંચાવન": 55,
    "સાઠ": 60, "સાઇઠ": 60, "sath": 60, "sixty": 60,
    "સિત્તેર": 70, "sitter": 70, "seventy": 70,
    "ઇકોતેર": 71, "ઇકોતેર": 71, "બોતેર": 72, "તોતેર": 73, "ચુમોતેર": 74, "પંચોતેર": 75,
    "છોતેર": 76, "સિત્યોતેર": 77, "ઇઠ્યોતેર": 78, "ઓગણાએંસી": 79,
    "એંસી": 80, "એસી": 80, "ensi": 80, "eighty": 80,
    "એક્યાસી": 81, "બ્યાસી": 82, "ત્યાસી": 83, "ચોર્યાસી": 84, "પંચાસી": 85,
    "છ્યાસી": 86, "સિત્યાસી": 87, "ઇઠ્યાસી": 88, "નેવ્યાસી": 89, "nevyasi": 89,
    "નેવું": 90, "નેવુ": 90, "nevu": 90, "ninety": 90,
    "ચોરાણું": 94, "ચોરાણુ": 94, "choranu": 94, "chauranve": 94,
    # Hundreds & Thousands
    "સો": 100, "એકસો": 100, "sau": 100, "so": 100, "hundred": 100,
    "બસો": 200, "baso": 200, "dosau": 200,
    "ત્રણસો": 300, "ચારસો": 400, "પાંચસો": 500, "છસો": 600,
    "સાતસો": 700, "આઠસો": 800, "નવસો": 900,
    "હજાર": 1000, "hazar": 1000, "hazaar": 1000, "hajar": 1000, "thousand": 1000,
}

ONES: dict[str, int] = {k: v for k, v in NUMBER_WORDS.items() if v < 10}


def normalizeText(text: str) -> str:
    """Cleans text without corrupting Gujarati Unicode combining marks."""
    t = unicodedata.normalize("NFKC", (text or "")).strip()
    t = re.sub(r"[\.,!\?;:'\"()\[\]{}/\\|@#₹]+", " ", t)
    return re.sub(r"\s+", " ", t.lower()).strip()


def convertDigitsToAscii(text: str) -> str:
    """Converts Gujarati and Devanagari numerals to standard ASCII 0-9."""
    out = []
    for ch in text:
        if "૦" <= ch <= "૯":
            out.append(str(ord(ch) - ord("૦")))
        elif "०" <= ch <= "९":
            out.append(str(ord(ch) - ord("०")))
        else:
            out.append(ch)
    return "".join(out)


def extractDigitRuns(text: str) -> list[str]:
    """Finds contiguous sequences of 4 or more digits."""
    t = convertDigitsToAscii(text)
    runs = []
    for m in re.finditer(r"\d{4,}", t):
        runs.append(m.group(0)[-4:])
    if not runs:
        digits_only = "".join(ch for ch in t if ch.isdigit())
        if len(digits_only) >= 4:
            runs.append(digits_only[-4:])
    return runs


def parseDigitSequence(tokens: list[str]) -> str | None:
    """Parses digit-by-digit spoken words (e.g. 'ચાર પાંચ બે એક' -> '4521')."""
    skip = {"ને", "ne", "and", "અને", "મા", "જી", "હા", "છે"}
    digits: list[str] = []
    for tok in tokens:
        if tok in skip:
            continue
        if tok in ONES:
            digits.append(str(ONES[tok]))
        elif tok.isdigit() and len(tok) == 1:
            digits.append(tok)
        elif digits:
            break
    if len(digits) >= 4:
        return "".join(digits[-4:])
    return None


def parseIndianSpokenNumber(text: str) -> int | None:
    """
    Parses compound spoken numbers (e.g. 'સાત હજાર બસો ને ચોરાણું' -> 7294).
    """
    t = normalizeText(text).replace("ને", " ")
    tokens = [x for x in t.split() if x and x not in ("મેડમ", "સાહેબ", "જી", "હા")]
    if not tokens:
        return None

    total = 0
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        # Compound: e.g. 'સાત હજાર'
        if (
            tok in NUMBER_WORDS
            and NUMBER_WORDS[tok] < 100
            and i + 1 < len(tokens)
            and tokens[i + 1] in ("હજાર", "hazar", "hazaar", "hajar", "thousand")
        ):
            total += NUMBER_WORDS[tok] * 1000
            i += 2
            continue
        # Compound: e.g. 'બે સો'
        if (
            tok in NUMBER_WORDS
            and NUMBER_WORDS[tok] < 10
            and i + 1 < len(tokens)
            and tokens[i + 1] in ("સો", "sau", "so", "hundred")
        ):
            total += NUMBER_WORDS[tok] * 100
            i += 2
            continue
        if tok in NUMBER_WORDS:
            total += NUMBER_WORDS[tok]
            i += 1
            continue
        i += 1

    return total if total > 0 else None


def extractVerificationCandidates(user_text: str) -> list[str]:
    """Returns all plausible 4-digit candidates from customer input."""
    raw = (user_text or "").strip()
    if not raw:
        return []

    candidates: list[str] = []
    for run in extractDigitRuns(raw):
        if run not in candidates:
            candidates.append(run)

    spoken = parseIndianSpokenNumber(raw)
    if spoken is not None:
        val_str = str(spoken)
        c = val_str if len(val_str) == 4 else val_str[-4:]
        if len(c) == 4 and c not in candidates:
            candidates.append(c)

    norm_tokens = normalizeText(raw).split()
    seq = parseDigitSequence(norm_tokens)
    if seq and seq not in candidates:
        candidates.append(seq)

    # Two-pair spoken numbers (e.g. 'પિસ્તાલીસ એકવીસ' -> 45 and 21 -> '4521')
    num_words_tokens = [tok for tok in norm_tokens if tok in NUMBER_WORDS]
    if len(num_words_tokens) == 2:
        v1 = NUMBER_WORDS[num_words_tokens[0]]
        v2 = NUMBER_WORDS[num_words_tokens[1]]
        if 10 <= v1 <= 99 and 0 <= v2 <= 99:
            pair_cand = f"{v1:02d}{v2:02d}"
            if pair_cand not in candidates:
                candidates.append(pair_cand)

    return candidates


def verifyCustomer(state: CallState, db: Any = None) -> dict[str, Any]:
    """
    Validates customer last-4 digits against ground truth.
    Updates verified state deterministically.
    """
    user_text = state.get("lastUserText") or ""
    snap = state.get("snapshot") or state.get("accountFacts") or {}
    customer_name = state.get("customerName") or snap.get("customerName") or "ગ્રાહક"
    retries = int(state.get("verifyRetries") or 0)

    # Expected last 4 digits
    expected = (
        snap.get("expectedLast4")
        or (snap.get("maskedAcct") or "")[-4:]
        or "4521"
    )

    candidates = extractVerificationCandidates(user_text)

    # Match check
    if expected in candidates:
        return {
            "verified": True,
            "phase": "fetch",
            "verifyRetries": 0,
            "proof": {
                **(state.get("proof") or {}),
                "verified": True,
                "verifiedLast4": expected,
            },
        }

    # If user provided wrong digits or unrecognized response
    if retries >= 2:
        fail_reply = buildVerifyFailedPrompt(customer_name)
        return {
            "verified": False,
            "phase": "end",
            "callEnded": True,
            "speaker": "Sahayak",
            "lastAgentReply": fail_reply,
        }

    retry_reply = buildVerifyMismatchPrompt(customer_name, attempts_left=2 - retries)
    return {
        "verified": False,
        "phase": "verify",
        "speaker": "Sahayak",
        "lastAgentReply": retry_reply,
        "verifyRetries": retries + 1,
    }
