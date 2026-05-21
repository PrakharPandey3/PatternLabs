from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import math
import os

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_LIMIT = 10000

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

EXAMPLE_CONJECTURES = [
    {
        "title": "Goldbach Conjecture",
        "description": "Every even integer > 2 is the sum of two primes",
        "formula": "n = p + q where p,q are prime",
    },
    {
        "title": "Twin Prime Conjecture",
        "description": "Infinitely many primes p where p+2 is also prime",
        "formula": "p and p+2 are both prime",
    },
    {
        "title": "Fermat Numbers",
        "description": "Numbers of the form 2^(2^n) + 1",
        "formula": "F_n = 2^(2^n) + 1",
    },
    {
        "title": "Prime Patterns",
        "description": "Testing specific patterns in prime distributions",
        "formula": "p_n ~ n ln(n)",
    },
]


def sieve(limit: int) -> list[int]:
    if limit < 2:
        return []

    is_prime_number = [True] * (limit + 1)
    is_prime_number[0] = is_prime_number[1] = False

    for factor in range(2, int(math.sqrt(limit)) + 1):
        if is_prime_number[factor]:
            start = factor * factor
            is_prime_number[start : limit + 1 : factor] = [False] * (
                ((limit - start) // factor) + 1
            )

    return [number for number, prime in enumerate(is_prime_number) if prime]


PRIMES = sieve(500000)
PRIME_SET = set(PRIMES)


def is_prime(number: int) -> bool:
    if number < 2:
        return False
    if number in PRIME_SET:
        return True
    if number % 2 == 0:
        return False

    limit = int(math.sqrt(number))
    for factor in range(3, limit + 1, 2):
        if number % factor == 0:
            return False
    return True


def chart_data_from_results(results: list[tuple[int, bool]]) -> list[dict[str, int | bool]]:
    if not results:
        return []

    step = max(1, math.ceil(len(results) / 50))
    samples = results[::step][:50]

    return [
        {
            "number": number,
            "result": result,
            "height": (45 + ((number * 17) % 45))
            if result
            else (20 + ((number * 17) % 35)),
        }
        for number, result in samples
    ]


def format_result(theorem: str, results: list[tuple[int, bool]], analysis_note: str) -> dict:
    tested = len(results)
    true_count = sum(1 for _, result in results if result)
    false_count = tested - true_count
    accuracy = (true_count / tested) * 100 if tested else 0

    return {
        "theorem": theorem,
        "tested": tested,
        "true_count": true_count,
        "false_count": false_count,
        "accuracy": f"{accuracy:.1f}",
        "chart_data": chart_data_from_results(results),
        "analysis_note": analysis_note,
    }

def analyze_goldbach(theorem: str) -> dict:
    results = []

    for number in range(1, TEST_LIMIT + 1):
        if number > 2 and number % 2 == 0:
            found_pair = satisfies_goldbach(number)
            results.append((number, found_pair))
        else:
            results.append((number, False))

    return format_result(
        theorem,
        results,
        f"Checked every integer from 1 through {TEST_LIMIT} for Goldbach behavior.",
    )


def satisfies_goldbach(number: int) -> bool:
    for prime in PRIMES:
        if prime > number // 2:
            break

        if (number - prime) in PRIME_SET:
            return True

    return False


def analyze_twin_primes(theorem: str) -> dict:
    results = []

    for number in range(1, TEST_LIMIT + 1):
        is_twin = (
            number in PRIME_SET
            and (number + 2) in PRIME_SET
        )

        results.append((number, is_twin))

    return format_result(
        theorem,
        results,
        f"Checked every integer from 1 through {TEST_LIMIT} for twin prime behavior.",
    )

def analyze_fermat_numbers(theorem: str) -> dict:
    results = []

    for number in range(1, TEST_LIMIT + 1):
        is_fermat = False

        for exponent in range(6):
            fermat_number = (2 ** (2**exponent)) + 1

            if number == fermat_number:
                is_fermat = is_prime(fermat_number)
                break

        results.append((number, is_fermat))

    return format_result(
        theorem,
        results,
        (
            f"Checked integers from 1 through {TEST_LIMIT} "
            "against known Fermat numbers."
        ),
    )


def analyze_prime_approximation(theorem: str) -> dict:
    results = []

    for number in range(1, TEST_LIMIT + 1):
        if number >= len(PRIMES):
            results.append((number, False))
            continue

        prime = PRIMES[number - 1]

        if number == 1:
            results.append((number, False))
            continue

        approximation = number * math.log(number)
        relative_error = abs(prime - approximation) / prime

        results.append((number, relative_error <= 0.20))

    return format_result(
        theorem,
        results,
        (
            f"Checked prime approximation accuracy for indices "
            f"1 through {TEST_LIMIT}."
        ),
    )


def analyze_theorem(theorem: str) -> dict:
    normalized = " ".join(theorem.casefold().split())

    if "goldbach" in normalized or ("p + q" in normalized and "prime" in normalized):
        return analyze_goldbach(theorem)
    if "twin" in normalized or ("p+2" in normalized and "prime" in normalized):
        return analyze_twin_primes(theorem)
    if "fermat" in normalized or "2^(2^n)" in normalized:
        return analyze_fermat_numbers(theorem)
    if "p_n" in normalized or "ln(n)" in normalized:
        return analyze_prime_approximation(theorem)

    return format_result(
        theorem,
        [],
        (
            "This tester currently supports the built-in Goldbach, twin prime, "
            "Fermat number, and prime approximation checks."
        ),
    )


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "example_conjectures": EXAMPLE_CONJECTURES
        }
    )


@app.post("/simulate", response_class=HTMLResponse)
async def simulate(request: Request, theorem: str = Form(...)):
    analysis = analyze_theorem(theorem.strip()[:500])

    return templates.TemplateResponse(
        request=request,
        name="result.html",
        context={
            **analysis,
        }
    )
