"""
statistics_analysis.py
======================
MDM Mini Project — Typing Speed Before and After Practice
Author  : [Your Name]
Purpose : Calculate all required statistics for the paired typing-speed study.

HOW THIS FILE IS ORGANISED
---------------------------
Section 1 – Imports          : Load the libraries we need.
Section 2 – Data Validation  : Check that incoming data is clean and paired.
Section 3 – Core Statistics  : Mean, standard deviation, differences.
Section 4 – Paired t-test    : Hypothesis test using scipy.
Section 5 – Report Builder   : Bundle all results into one dictionary.
Section 6 – Self-Tests       : Run with a tiny known dataset to verify maths.

GLOSSARY (read this once — it will help everything else make sense)
--------------------------------------------------------------------
WPM          : Words Per Minute — the typing speed measurement we collect.
Student ID   : A unique label (e.g. "S01") that identifies one student.
"Before"     : WPM measured BEFORE the practice session.
"After"      : WPM measured AFTER  the practice session.
Paired data  : The same student appears in BOTH the before and after lists.
               We exploit this pairing — it removes natural differences
               between students and isolates the effect of practice.
n            : Number of valid, matched student pairs.
α (alpha)    : The significance level. We use 0.05, meaning we accept a
               5% chance of wrongly concluding practice helped.
p-value      : The probability of seeing our result (or more extreme) purely
               by random chance, assuming practice had NO effect.
               If p < 0.05 → the improvement is statistically significant.
"""

# =============================================================================
# SECTION 1 — IMPORTS
# =============================================================================
# numpy  : Fast numerical arrays and mathematical functions.
# scipy  : Scientific computing — we use scipy.stats for the t-test.
# math   : Standard-library maths (sqrt, isfinite, isnan).
# typing : Lets us write clearer function signatures (e.g. list[float]).

import math
from typing import Optional

import numpy as np
from scipy import stats


# =============================================================================
# SECTION 2 — DATA VALIDATION
# =============================================================================

class DataValidationError(Exception):
    """
    Custom exception raised when the data does not meet our requirements.
    Using a custom exception makes it easy for the calling code (or the
    dashboard later) to catch exactly this kind of problem and show a
    helpful message to the user.
    """
    pass


def _validate_speed(value: float, label: str, student_id: str) -> None:
    """
    Check that a single WPM value is a real, positive number.

    Parameters
    ----------
    value      : The WPM number to check.
    label      : "before" or "after" — used in error messages.
    student_id : Which student this value belongs to.

    Why do we validate?
    -------------------
    If someone accidentally types -30 or "hello" as a WPM, all our
    calculations will be wrong or crash. It is better to reject the bad
    value early with a clear message than to produce a silently wrong result.
    """
    # math.isfinite returns False for NaN (Not a Number) and +/-Infinity.
    if not math.isfinite(value):
        raise DataValidationError(
            f"Student '{student_id}': {label} WPM is not a finite number "
            f"(got {value}). Please enter a valid speed."
        )
    # Typing speed must be strictly positive — 0 WPM means no data.
    if value <= 0:
        raise DataValidationError(
            f"Student '{student_id}': {label} WPM must be greater than 0 "
            f"(got {value}). A speed of 0 or below is not physically meaningful."
        )


def validate_and_pair(
    records: list,
) -> tuple:
    """
    Validate a list of student records and return matched arrays.

    Each record is a dictionary with keys:
        "id"     : str  — unique student identifier (e.g. "S01")
        "before" : float — typing speed BEFORE practice (WPM)
        "after"  : float — typing speed AFTER  practice (WPM)

    Returns
    -------
    ids    : list of student ID strings (in the order they were processed).
    before : numpy array of "before" WPM values.
    after  : numpy array of "after"  WPM values.

    Raises DataValidationError if:
      * A required key is missing from any record.
      * Any speed is not a positive finite number.
      * The same student ID appears more than once (duplicate).
      * Fewer than 2 valid pairs exist (t-test is meaningless with n < 2).

    WHY numpy arrays?
    -----------------
    numpy arrays support element-wise maths, so  after - before  gives us
    the difference for every student at once, without writing a loop.
    """
    if not records:
        raise DataValidationError(
            "No records were provided. Please add student data before running "
            "the analysis."
        )

    ids = []
    before_list = []
    after_list = []
    seen_ids = set()          # Track IDs we have already processed.

    for i, rec in enumerate(records):
        # -- 2a. Check required keys exist ------------------------------------
        for key in ("id", "before", "after"):
            if key not in rec:
                raise DataValidationError(
                    f"Record #{i + 1} is missing the '{key}' field. "
                    f"Every record must have 'id', 'before', and 'after'."
                )

        student_id = str(rec["id"]).strip()
        if not student_id:
            raise DataValidationError(
                f"Record #{i + 1} has an empty student ID. "
                "Please provide a unique ID for every student."
            )

        # -- 2b. Reject duplicate IDs -----------------------------------------
        # A duplicate almost always means a data-entry mistake. We refuse to
        # continue rather than silently keep one copy and discard the other,
        # because we cannot know which copy is correct.
        if student_id in seen_ids:
            raise DataValidationError(
                f"Duplicate student ID '{student_id}' found. "
                "Each student must appear exactly once. "
                "Please fix the data and try again."
            )
        seen_ids.add(student_id)

        # -- 2c. Convert speeds to float and validate -------------------------
        try:
            before_val = float(rec["before"])
            after_val  = float(rec["after"])
        except (TypeError, ValueError):
            raise DataValidationError(
                f"Student '{student_id}': speeds must be numbers, "
                f"got before='{rec['before']}', after='{rec['after']}'."
            )

        _validate_speed(before_val, "before", student_id)
        _validate_speed(after_val,  "after",  student_id)

        ids.append(student_id)
        before_list.append(before_val)
        after_list.append(after_val)

    # -- 2d. Minimum sample size ----------------------------------------------
    # The paired t-test requires at least 2 pairs.
    # With n = 1 there are 0 degrees of freedom and the test cannot be computed.
    if len(ids) < 2:
        raise DataValidationError(
            f"Only {len(ids)} valid student pair(s) found. "
            "At least 2 paired observations are required to run a t-test."
        )

    return ids, np.array(before_list, dtype=float), np.array(after_list, dtype=float)


# =============================================================================
# SECTION 3 — CORE STATISTICS
# =============================================================================

def compute_mean(values: np.ndarray, label: str = "") -> float:
    """
    Calculate the arithmetic mean (average) of an array.

    FORMULA
    -------
        mean = (x1 + x2 + ... + xn) / n

    In plain English: add up all the values, then divide by how many there are.

    Parameters
    ----------
    values : 1-D numpy array of numbers.
    label  : Optional string (e.g. "before") used only for error messages.

    Returns
    -------
    The mean as a Python float.
    """
    n = len(values)
    if n == 0:
        raise DataValidationError(f"Cannot compute mean of an empty array ({label}).")

    # np.mean does exactly the formula above, but faster and more precisely
    # than a manual Python loop.
    return float(np.mean(values))


def compute_sample_std(values: np.ndarray, label: str = "") -> float:
    """
    Calculate the SAMPLE standard deviation.

    FORMULA
    -------
        s = sqrt( sum((xi - x_bar)^2) / (n - 1) )

    Step by step:
      1. Find the mean  x_bar.
      2. Subtract the mean from each value  ->  (xi - x_bar).
      3. Square each difference             ->  (xi - x_bar)^2.
      4. Sum all the squares                ->  sum((xi - x_bar)^2).
      5. Divide by  (n - 1)  -- NOT by n   ->  this is the sample variance.
      6. Take the square root               ->  this is the sample std deviation.

    WHY (n - 1) instead of n?
    --------------------------
    We are working with a SAMPLE (a subset of all possible students), not the
    entire population. Dividing by (n - 1) -- called "Bessel's correction" --
    corrects for the fact that a sample tends to slightly underestimate the
    true spread of the population. This gives a less biased estimate.

    In numpy, ddof=1 means "subtract 1 from n in the denominator" (ddof stands
    for Delta Degrees of Freedom).

    Returns
    -------
    The sample standard deviation as a float. Returns 0.0 when n = 1 (only
    one observation -- standard deviation is undefined, but we return 0 so
    the caller can decide how to handle it).
    """
    n = len(values)
    if n == 0:
        raise DataValidationError(f"Cannot compute std dev of an empty array ({label}).")
    if n == 1:
        # With a single value there is nothing to spread around; return 0.
        return 0.0

    return float(np.std(values, ddof=1))   # ddof=1 -> sample std deviation


def compute_differences(
    before: np.ndarray,
    after: np.ndarray,
) -> np.ndarray:
    """
    Compute the per-student improvement: difference = after - before.

    A POSITIVE difference means the student got FASTER after practice.
    A NEGATIVE difference means the student got SLOWER  after practice.

    WHY we compute differences (and not just compare group means):
    --------------------------------------------------------------
    Suppose student A naturally types at 80 WPM and student B at 30 WPM.
    Even without practice, comparing their averages would be misleading.
    By computing  (after - before)  for EACH student, we remove their
    individual baseline speed and focus purely on how much EACH PERSON changed.
    This is the whole point of a paired design.

    Parameters
    ----------
    before : numpy array of before-practice WPM values.
    after  : numpy array of after-practice  WPM values.
            Both arrays must be the same length and in the same student order.

    Returns
    -------
    numpy array of differences (same length as inputs).
    """
    if len(before) != len(after):
        # This should never happen if validate_and_pair() was called first,
        # but we guard against programming errors just in case.
        raise DataValidationError(
            f"'before' and 'after' arrays have different lengths "
            f"({len(before)} vs {len(after)}). Data must be paired."
        )

    return after - before   # numpy performs this element-wise (per student)


# =============================================================================
# SECTION 4 — PAIRED t-TEST
# =============================================================================

def run_paired_ttest(
    before: np.ndarray,
    after: np.ndarray,
    alpha: float = 0.05,
) -> dict:
    """
    Perform a paired (dependent-samples) t-test and return all results.

    WHAT IS A PAIRED t-TEST?
    ------------------------
    We want to know: "Did practice genuinely improve typing speed, or could
    the improvement we see be due to random luck?"

    The paired t-test answers this by:
      1. Computing the difference  d = after - before  for each student.
      2. Testing whether the MEAN of those differences (d_bar) is significantly
         different from zero.

    NULL HYPOTHESIS  H0 : d_bar = 0  (practice made no difference on average)
    ALT. HYPOTHESIS  H1 : d_bar != 0 (practice DID make a difference -- two-tailed)

    FORMULA FOR THE t-STATISTIC
    ---------------------------
        t = d_bar / (s_d / sqrt(n))

    Where:
        d_bar   = mean of the individual differences
        s_d     = sample standard deviation of the differences
        n       = number of pairs
        s_d / sqrt(n) = the "standard error" -- how uncertain we are about d_bar

    A large |t| means the mean improvement is large relative to the
    variability, making it unlikely to be due to chance.

    DEGREES OF FREEDOM
    ------------------
        df = n - 1

    This reflects that we "use up" one degree of freedom to estimate the mean.
    The t-distribution with df degrees of freedom is used to find the p-value.

    Parameters
    ----------
    before : numpy array of before-practice WPM values.
    after  : numpy array of after-practice  WPM values.
    alpha  : Significance level (default 0.05).

    Returns
    -------
    dict with keys:
        t_statistic        : float or None
        degrees_of_freedom : int
        p_value            : float or None
        mean_diff          : float  (d_bar)
        std_diff           : float  (s_d)
        significant        : bool   (True if p_value < alpha)
        conclusion         : str    (plain-English verdict)
        alpha              : float  (the alpha used)
    """
    differences = compute_differences(before, after)
    n = len(differences)
    mean_diff = float(np.mean(differences))
    std_diff  = compute_sample_std(differences, label="differences")
    standard_error = std_diff / math.sqrt(n) if n > 0 else 0.0

    # -- 4a. Guard: zero-variance differences ---------------------------------
    # If EVERY student improved by exactly the same amount, std_diff = 0.
    # The t-statistic formula divides by std_diff, which would cause a
    # division-by-zero. We detect this and report it clearly.
    if std_diff == 0.0:
        # All differences are identical -- we still know whether they're all
        # positive (consistent improvement) or all zero (no change).
        if mean_diff > 0:
            conclusion = (
                "Every student improved by exactly the same amount "
                f"({mean_diff:+.2f} WPM). The standard deviation of "
                "differences is 0, so the t-test cannot be computed -- "
                "but the consistent improvement is clear."
            )
        elif mean_diff < 0:
            conclusion = (
                "Every student slowed down by exactly the same amount "
                f"({mean_diff:+.2f} WPM). Standard deviation is 0; "
                "t-test cannot be computed."
            )
        else:
            conclusion = (
                "Every student showed exactly 0 change. "
                "Practice had no effect in this dataset."
            )
        return {
            "t_statistic":        None,
            "degrees_of_freedom": n - 1,
            "p_value":            None,
            "mean_diff":          mean_diff,
            "std_diff":           std_diff,
            "standard_error":     0.0,
            "ci_95_lower":        mean_diff,
            "ci_95_upper":        mean_diff,
            "t_crit":             None,
            "significant":        False,
            "conclusion":         conclusion,
            "alpha":              alpha,
        }

    # -- 4b. Run the paired t-test & 95% Confidence Interval ------------------
    # scipy.stats.ttest_rel does EXACTLY the paired t-test formula above.
    # It takes the raw before/after arrays, computes differences internally,
    # and returns the t-statistic and two-tailed p-value.
    result = stats.ttest_rel(after, before)

    t_stat  = float(result.statistic)
    p_value = float(result.pvalue)
    df      = n - 1                     # degrees of freedom

    # 95% Confidence Interval for the mean difference:
    # CI = mean_diff +/- (t_crit * standard_error)
    t_crit = float(stats.t.ppf(1.0 - alpha / 2.0, df))
    margin_of_error = t_crit * standard_error
    ci_95_lower = mean_diff - margin_of_error
    ci_95_upper = mean_diff + margin_of_error

    # -- 4c. Decision and plain-English conclusion ----------------------------
    significant = p_value < alpha

    if significant:
        direction = "faster" if mean_diff > 0 else "slower"
        conclusion = (
            f"RESULT: Statistically significant (p = {p_value:.4f} < alpha = {alpha}).\n"
            f"We REJECT H0. On average, students typed {abs(mean_diff):.2f} WPM "
            f"{direction} after practice.\n"
            "This improvement is unlikely to be due to random chance -- "
            "practice appears to have had a real effect."
        )
    else:
        conclusion = (
            f"RESULT: Not statistically significant (p = {p_value:.4f} >= alpha = {alpha}).\n"
            "We FAIL TO REJECT H0. There is not enough evidence to conclude "
            "that practice changed typing speed.\n"
            "Note: 'not significant' does NOT mean practice had no effect -- "
            "the sample may simply be too small to detect one."
        )

    return {
        "t_statistic":        t_stat,
        "degrees_of_freedom": df,
        "p_value":            p_value,
        "mean_diff":          mean_diff,
        "std_diff":           std_diff,
        "standard_error":     standard_error,
        "ci_95_lower":        ci_95_lower,
        "ci_95_upper":        ci_95_upper,
        "t_crit":             t_crit,
        "significant":        significant,
        "conclusion":         conclusion,
        "alpha":              alpha,
    }


# =============================================================================
# SECTION 5 — REPORT BUILDER
# =============================================================================

def analyse(records: list, alpha: float = 0.05) -> dict:
    """
    Master function -- validate data then compute all statistics.

    This is the single function that the Streamlit dashboard (or tests) will
    call. It returns every number and label needed to build the results page.

    Parameters
    ----------
    records : List of dicts, each with keys  "id", "before", "after".
    alpha   : Significance level (default 0.05).

    Returns
    -------
    dict with keys:
        ids          : list of str  -- student IDs in processed order
        before       : np.ndarray  -- validated before-WPM values
        after        : np.ndarray  -- validated after-WPM  values
        differences  : np.ndarray  -- per-student (after - before)
        n            : int         -- number of valid pairs
        mean_before  : float
        mean_after   : float
        std_before   : float       -- sample std dev of before speeds
        std_after    : float       -- sample std dev of after  speeds
        mean_diff    : float       -- mean of differences
        std_diff     : float       -- sample std dev of differences
        t_statistic  : float or None
        df           : int
        p_value      : float or None
        significant  : bool
        conclusion   : str
        alpha        : float
    """
    # Step 1 -- Validate inputs and build matched arrays.
    ids, before, after = validate_and_pair(records)

    # Step 2 -- Compute descriptive statistics.
    mean_before = compute_mean(before, "before")
    mean_after  = compute_mean(after,  "after")
    std_before  = compute_sample_std(before, "before")
    std_after   = compute_sample_std(after,  "after")
    differences = compute_differences(before, after)

    # Step 3 -- Run the paired t-test (also computes mean_diff & std_diff).
    ttest = run_paired_ttest(before, after, alpha=alpha)

    return {
        # Raw data (useful for building tables in the dashboard)
        "ids":         ids,
        "before":      before,
        "after":       after,
        "differences": differences,
        "n":           len(ids),

        # Descriptive statistics
        "mean_before": mean_before,
        "mean_after":  mean_after,
        "std_before":  std_before,
        "std_after":   std_after,

        # Difference statistics + t-test results
        "mean_diff":      ttest["mean_diff"],
        "std_diff":       ttest["std_diff"],
        "standard_error": ttest["standard_error"],
        "ci_95_lower":    ttest["ci_95_lower"],
        "ci_95_upper":    ttest["ci_95_upper"],
        "t_crit":         ttest["t_crit"],
        "t_statistic":    ttest["t_statistic"],
        "df":             ttest["degrees_of_freedom"],
        "p_value":        ttest["p_value"],
        "significant":    ttest["significant"],
        "conclusion":     ttest["conclusion"],
        "alpha":          alpha,
    }


def print_report(results: dict) -> None:
    """
    Print a formatted summary of all statistics to the console.

    Useful for quick command-line checks before the dashboard exists.
    The dashboard will display the same information in a nicer visual form.
    """
    sep = "=" * 60
    print(f"\n{sep}")
    print("  TYPING SPEED ANALYSIS REPORT")
    print(sep)
    print(f"  Students analysed (n)  : {results['n']}")
    print(f"  Significance level (a) : {results['alpha']}")
    print(sep)

    print("\n[DESCRIPTIVE STATISTICS]")
    print(f"  Mean WPM -- Before practice : {results['mean_before']:.2f}")
    print(f"  Mean WPM -- After  practice : {results['mean_after']:.2f}")
    print(f"  Sample SD -- Before         : {results['std_before']:.2f}")
    print(f"  Sample SD -- After          : {results['std_after']:.2f}")

    print("\n[DIFFERENCE STATISTICS  (after - before, per student)]")
    print(f"  Mean difference  (d_bar) : {results['mean_diff']:+.2f} WPM")
    print(f"  SD of differences        : {results['std_diff']:.2f}")

    print("\n[PAIRED t-TEST]")
    if results["t_statistic"] is not None:
        print(f"  t-statistic : {results['t_statistic']:.4f}")
        print(f"  df          : {results['df']}")
        print(f"  p-value     : {results['p_value']:.4f}")
    else:
        print("  t-test could not be computed (zero variance in differences).")

    print("\n[STUDENT-LEVEL RESULTS]")
    header = f"  {'ID':<8} {'Before':>8} {'After':>8} {'Diff':>8}"
    print(header)
    print("  " + "-" * (len(header) - 2))
    for sid, b, a, d in zip(
        results["ids"],
        results["before"],
        results["after"],
        results["differences"],
    ):
        sign = "+" if d >= 0 else ""
        print(f"  {sid:<8} {b:>8.1f} {a:>8.1f} {sign}{d:>7.1f}")

    print(f"\n[CONCLUSION]\n  {results['conclusion']}")
    print(f"\n{sep}\n")


# =============================================================================
# SECTION 6 — SELF-TESTS
# =============================================================================
# These tests use a SMALL KNOWN DATASET where we can verify the answers
# by hand (or with a calculator). If the functions are correct, every
# assert statement passes silently. If any assert fails, Python raises
# AssertionError and tells you exactly which check failed.
#
# HOW TO READ AN ASSERTION:
#   assert <condition>, "message shown if condition is False"
#   e.g.  assert 2 + 2 == 4, "basic maths broken"

def _approx_equal(a: float, b: float, tol: float = 1e-6) -> bool:
    """
    Return True if two floats are within `tol` of each other.
    Floating-point arithmetic is not perfectly exact, so we allow a tiny
    tolerance instead of checking  a == b  directly.
    """
    return abs(a - b) < tol


def run_tests() -> None:
    """
    Run all self-tests. Call this function to verify the module is working.

    TEST DATASET
    ------------
    5 students. We chose simple numbers so you can verify by hand.

        ID    Before   After   Diff (After-Before)
        S01     40      50       +10
        S02     55      60        +5
        S03     30      45       +15
        S04     65      70        +5
        S05     50      55        +5

    Hand calculations:
        mean_before = (40+55+30+65+50)/5 = 240/5 = 48.00
        mean_after  = (50+60+45+70+55)/5 = 280/5 = 56.00

        differences = [10, 5, 15, 5, 5]
        mean_diff   = (10+5+15+5+5)/5 = 40/5 = 8.00

        Variance of differences (sample, ddof=1):
            deviations = [10-8, 5-8, 15-8, 5-8, 5-8] = [2, -3, 7, -3, -3]
            sq_devs    = [4, 9, 49, 9, 9]   -> sum = 80
            variance   = 80 / (5-1) = 20.00
            std_diff   = sqrt(20) ~= 4.4721

        t = d_bar / (s_d / sqrt(n)) = 8 / (4.4721 / sqrt(5)) = 8 / 2.0000 = 4.0000
        df = 4
        Two-tailed p-value for t=4, df=4 ~= 0.0160  (from t-table / scipy)
        Since p < 0.05 -> significant
    """
    print("Running self-tests ...")

    # -- Shared test data -----------------------------------------------------
    test_records = [
        {"id": "S01", "before": 40, "after": 50},
        {"id": "S02", "before": 55, "after": 60},
        {"id": "S03", "before": 30, "after": 45},
        {"id": "S04", "before": 65, "after": 70},
        {"id": "S05", "before": 50, "after": 55},
    ]

    results = analyse(test_records)

    # -- Test 1: Sample size --------------------------------------------------
    assert results["n"] == 5, f"Expected n=5, got {results['n']}"
    print("  PASS Test 1: n = 5")

    # -- Test 2: Mean before --------------------------------------------------
    assert _approx_equal(results["mean_before"], 48.0), (
        f"Expected mean_before=48.0, got {results['mean_before']}"
    )
    print("  PASS Test 2: mean_before = 48.00")

    # -- Test 3: Mean after ---------------------------------------------------
    assert _approx_equal(results["mean_after"], 56.0), (
        f"Expected mean_after=56.0, got {results['mean_after']}"
    )
    print("  PASS Test 3: mean_after = 56.00")

    # -- Test 4: Mean difference ----------------------------------------------
    assert _approx_equal(results["mean_diff"], 8.0), (
        f"Expected mean_diff=8.0, got {results['mean_diff']}"
    )
    print("  PASS Test 4: mean_diff = +8.00")

    # -- Test 5: Std dev of differences ---------------------------------------
    expected_std_diff = math.sqrt(20.0)          # ~= 4.4721
    assert _approx_equal(results["std_diff"], expected_std_diff, tol=1e-4), (
        f"Expected std_diff~=4.4721, got {results['std_diff']:.4f}"
    )
    print(f"  PASS Test 5: std_diff ~= {expected_std_diff:.4f}")

    # -- Test 6: t-statistic --------------------------------------------------
    # t = 8 / (sqrt(20)/sqrt(5)) = 8 / sqrt(4) = 8/2 = 4.0
    assert results["t_statistic"] is not None, "t_statistic should not be None"
    assert _approx_equal(results["t_statistic"], 4.0, tol=1e-4), (
        f"Expected t=4.0, got {results['t_statistic']:.4f}"
    )
    print("  PASS Test 6: t-statistic = 4.0000")

    # -- Test 7: Degrees of freedom -------------------------------------------
    assert results["df"] == 4, f"Expected df=4, got {results['df']}"
    print("  PASS Test 7: df = 4")

    # -- Test 8: p-value and significance -------------------------------------
    assert results["p_value"] is not None, "p_value should not be None"
    assert results["p_value"] < 0.05, (
        f"Expected p < 0.05 (significant), got p = {results['p_value']:.4f}"
    )
    assert results["significant"] is True, "Expected significant = True"
    print(f"  PASS Test 8: p = {results['p_value']:.4f} < 0.05 -> significant")

    # -- Test 9: Individual differences ---------------------------------------
    expected_diffs = np.array([10.0, 5.0, 15.0, 5.0, 5.0])
    assert np.allclose(results["differences"], expected_diffs), (
        f"Differences mismatch. Expected {expected_diffs}, got {results['differences']}"
    )
    print("  PASS Test 9: per-student differences = [10, 5, 15, 5, 5]")

    # -- Test 10: Duplicate ID rejection --------------------------------------
    dup_records = [
        {"id": "S01", "before": 40, "after": 50},
        {"id": "S01", "before": 55, "after": 60},   # duplicate!
    ]
    try:
        analyse(dup_records)
        assert False, "Should have raised DataValidationError for duplicate ID"
    except DataValidationError as e:
        assert "Duplicate" in str(e), f"Unexpected error message: {e}"
    print("  PASS Test 10: duplicate ID correctly rejected")

    # -- Test 11: Negative speed rejection ------------------------------------
    bad_records = [
        {"id": "S01", "before": -10, "after": 50},
        {"id": "S02", "before":  55, "after": 60},
    ]
    try:
        analyse(bad_records)
        assert False, "Should have raised DataValidationError for negative WPM"
    except DataValidationError as e:
        assert "greater than 0" in str(e), f"Unexpected error message: {e}"
    print("  PASS Test 11: negative WPM correctly rejected")

    # -- Test 12: Insufficient data rejection ---------------------------------
    one_record = [{"id": "S01", "before": 40, "after": 50}]
    try:
        analyse(one_record)
        assert False, "Should have raised DataValidationError for n < 2"
    except DataValidationError as e:
        assert "At least 2" in str(e), f"Unexpected error message: {e}"
    print("  PASS Test 12: single record correctly rejected (need n >= 2)")

    # -- Test 13: Zero-variance differences (handled gracefully) --------------
    # All students improved by exactly the same amount -> std_diff = 0.
    uniform_records = [
        {"id": "S01", "before": 40, "after": 50},   # diff = 10
        {"id": "S02", "before": 60, "after": 70},   # diff = 10
        {"id": "S03", "before": 30, "after": 40},   # diff = 10
    ]
    zero_var_result = analyse(uniform_records)
    assert zero_var_result["t_statistic"] is None, (
        "Expected t_statistic=None when std_diff=0"
    )
    assert zero_var_result["p_value"] is None, (
        "Expected p_value=None when std_diff=0"
    )
    assert (
        "0" in zero_var_result["conclusion"]
        or "same" in zero_var_result["conclusion"]
    ), "Expected zero-variance conclusion to mention consistency"
    print("  PASS Test 13: zero-variance differences handled gracefully")

    # -- Test 14: Standard error & 95% Confidence Interval ---------------------
    # For n=5, df=4: t_crit(0.975, 4) ~= 2.776445. SE = 4.472136 / sqrt(5) = 2.0
    # Margin of error = 2.776445 * 2.0 = 5.55289
    # 95% CI = [8.0 - 5.55289, 8.0 + 5.55289] = [2.4471, 13.5529]
    assert _approx_equal(results["standard_error"], 2.0, tol=1e-4), (
        f"Expected SE=2.0, got {results['standard_error']}"
    )
    assert _approx_equal(results["ci_95_lower"], 8.0 - 2.776445 * 2.0, tol=1e-3), (
        f"Expected CI lower ~= 2.4471, got {results['ci_95_lower']}"
    )
    assert _approx_equal(results["ci_95_upper"], 8.0 + 2.776445 * 2.0, tol=1e-3), (
        f"Expected CI upper ~= 13.5529, got {results['ci_95_upper']}"
    )
    print(f"  PASS Test 14: SE = {results['standard_error']:.2f}, 95% CI = [{results['ci_95_lower']:.2f}, {results['ci_95_upper']:.2f}]")

    print("\nAll 14 tests passed!\n")


# =============================================================================
# ENTRY POINT — run this file directly to see the tests + a demo report
# =============================================================================
if __name__ == "__main__":
    # Run all tests first.
    run_tests()

    # Then show a sample report using the same test data.
    demo_records = [
        {"id": "S01", "before": 40, "after": 50},
        {"id": "S02", "before": 55, "after": 60},
        {"id": "S03", "before": 30, "after": 45},
        {"id": "S04", "before": 65, "after": 70},
        {"id": "S05", "before": 50, "after": 55},
    ]

    print("-" * 60)
    print("DEMO REPORT (same data used in the tests)")
    print("-" * 60)
    results = analyse(demo_records)
    print_report(results)
