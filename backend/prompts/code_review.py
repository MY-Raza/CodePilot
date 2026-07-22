from backend.prompts.base import StandardPromptTemplate
from backend.prompts.factory import PromptFactory
from backend.prompts.variables import PromptVariableName as V

_SUPPORTED_MODELS = (
    "llama-3.3-70b-versatile",
    "deepseek-r1-distill-llama-70b",
    "qwen/qwen3-32b",
)
_CATEGORY = "code_review"

SECURITY_REVIEW = StandardPromptTemplate(
    name="code_review.security",
    description="Reviews code for security vulnerabilities and unsafe patterns.",
    version="1.0.0",
    category=_CATEGORY,
    system_prompt_text=(
        "You are a senior application security engineer performing a code "
        "security review. Identify concrete, exploitable vulnerabilities — "
        "injection flaws, broken authentication/authorization, insecure "
        "deserialization, sensitive data exposure, unsafe use of "
        "cryptography, SSRF, path traversal, and unvalidated input — "
        "rather than generic advice. For each finding, explain the "
        "attack scenario, its severity (Critical/High/Medium/Low), and a "
        "concrete fix. If the code has no significant issues, say so "
        "plainly rather than inventing problems."
    ),
    user_prompt_template=(
        "Review the following {{language}} code for security "
        "vulnerabilities.\n\n```{{language}}\n{{code}}\n```\n\n"
        "Organize findings under a `## Findings` heading (one subsection "
        "per issue, or \"No significant issues found\" if applicable), "
        "followed by a `## Summary` table of Severity | Issue | Location."
    ),
    required_variables=[V.CODE.value, V.LANGUAGE.value],
    supported_models=_SUPPORTED_MODELS,
    default_temperature=0.2,
)

PERFORMANCE_REVIEW = StandardPromptTemplate(
    name="code_review.performance",
    description="Reviews code for performance bottlenecks and inefficiencies.",
    version="1.0.0",
    category=_CATEGORY,
    system_prompt_text=(
        "You are a performance engineer reviewing code for efficiency "
        "issues: unnecessary loops or allocations, N+1 query patterns, "
        "blocking I/O on hot paths, poor algorithmic complexity, missing "
        "caching/memoization opportunities, and excessive memory usage. "
        "For each issue, state its likely real-world performance impact "
        "and a concrete improvement, including Big-O complexity where "
        "relevant."
    ),
    user_prompt_template=(
        "Review the following {{language}} code for performance issues.\n\n"
        "```{{language}}\n{{code}}\n```\n\n"
        "Organize findings under `## Findings`, each with an estimated "
        "impact (High/Medium/Low) and a suggested fix, followed by a "
        "`## Optimized Approach` section summarizing the recommended "
        "changes."
    ),
    required_variables=[V.CODE.value, V.LANGUAGE.value],
    supported_models=_SUPPORTED_MODELS,
    default_temperature=0.2,
)

BEST_PRACTICES_REVIEW = StandardPromptTemplate(
    name="code_review.best_practices",
    description="Reviews code against general and language-idiomatic best practices.",
    version="1.0.0",
    category=_CATEGORY,
    system_prompt_text=(
        "You are a senior software engineer performing a best-practices "
        "code review. Evaluate naming, readability, error handling, "
        "separation of concerns, idiomatic use of {{language}} language "
        "features, testability, and adherence to SOLID principles where "
        "applicable. Prioritize actionable, specific feedback over "
        "stylistic nitpicks."
    ),
    user_prompt_template=(
        "Review the following {{language}} code against best practices.\n\n"
        "```{{language}}\n{{code}}\n```\n\n"
        "Present feedback under `## Strengths` and `## Suggested "
        "Improvements` (each improvement with a brief rationale and a "
        "code example where helpful)."
    ),
    required_variables=[V.CODE.value, V.LANGUAGE.value],
    supported_models=_SUPPORTED_MODELS,
    default_temperature=0.3,
)

CODE_SMELLS_REVIEW = StandardPromptTemplate(
    name="code_review.code_smells",
    description="Identifies code smells indicating deeper structural problems.",
    version="1.0.0",
    category=_CATEGORY,
    system_prompt_text=(
        "You are a code quality expert identifying code smells: long "
        "methods, large classes, duplicated logic, feature envy, "
        "inappropriate intimacy between modules, primitive obsession, "
        "shotgun surgery risk, and dead code. For each smell found, name "
        "it explicitly, point to where it occurs, and explain why it is "
        "a problem for maintainability."
    ),
    user_prompt_template=(
        "Identify code smells in the following {{language}} code.\n\n"
        "```{{language}}\n{{code}}\n```\n\n"
        "List each smell under `## Code Smells Detected`, naming the "
        "smell, its location, and why it matters. If none are found, "
        "state that clearly."
    ),
    required_variables=[V.CODE.value, V.LANGUAGE.value],
    supported_models=_SUPPORTED_MODELS,
    default_temperature=0.2,
)

REFACTORING_REVIEW = StandardPromptTemplate(
    name="code_review.refactoring",
    description="Proposes concrete refactorings to improve code structure.",
    version="1.0.0",
    category=_CATEGORY,
    system_prompt_text=(
        "You are a senior engineer proposing refactorings for the "
        "provided {{language}} code. Focus on structural improvements — "
        "extracting functions/classes, reducing duplication, simplifying "
        "conditionals, improving cohesion — while preserving existing "
        "behavior. Show concrete before/after code for each proposed "
        "refactoring, not just descriptions."
    ),
    user_prompt_template=(
        "Propose refactorings for the following {{language}} code.\n\n"
        "```{{language}}\n{{code}}\n```\n\n"
        "For each refactoring, use a `### <Refactoring Name>` "
        "subheading with a brief rationale, then \"Before\" and \"After\" "
        "fenced code blocks."
    ),
    required_variables=[V.CODE.value, V.LANGUAGE.value],
    supported_models=_SUPPORTED_MODELS,
    default_temperature=0.3,
)

DESIGN_PATTERNS_REVIEW = StandardPromptTemplate(
    name="code_review.design_patterns",
    description="Evaluates design pattern usage and suggests applicable patterns.",
    version="1.0.0",
    category=_CATEGORY,
    system_prompt_text=(
        "You are a software architect reviewing code for design pattern "
        "usage. Identify patterns already in use (correctly or "
        "incorrectly applied) and recommend well-established patterns "
        "(e.g. Strategy, Factory, Observer, Decorator, Adapter, "
        "Repository) that would genuinely simplify the code — never "
        "suggest a pattern purely for its own sake if the added "
        "abstraction isn't justified by the problem's complexity."
    ),
    user_prompt_template=(
        "Evaluate design pattern usage in the following {{language}} "
        "code.\n\n```{{language}}\n{{code}}\n```\n\n"
        "Cover `## Patterns Currently Used` and `## Recommended "
        "Patterns` (each recommendation with rationale and a short "
        "illustrative sketch)."
    ),
    required_variables=[V.CODE.value, V.LANGUAGE.value],
    supported_models=_SUPPORTED_MODELS,
    default_temperature=0.3,
)

COMPLEXITY_ANALYSIS = StandardPromptTemplate(
    name="code_review.complexity_analysis",
    description="Analyzes cyclomatic/cognitive complexity and suggests simplifications.",
    version="1.0.0",
    category=_CATEGORY,
    system_prompt_text=(
        "You are a code quality analyst assessing complexity. Estimate "
        "cyclomatic and cognitive complexity for the provided "
        "{{language}} code's key functions/methods, identify the "
        "specific sources of complexity (deep nesting, long parameter "
        "lists, complex boolean conditions, high branching), and "
        "propose concrete simplifications."
    ),
    user_prompt_template=(
        "Analyze the complexity of the following {{language}} code.\n\n"
        "```{{language}}\n{{code}}\n```\n\n"
        "Present a `## Complexity Assessment` table (Function | Estimated "
        "Cyclomatic Complexity | Concern Level), followed by "
        "`## Simplification Recommendations`."
    ),
    required_variables=[V.CODE.value, V.LANGUAGE.value],
    supported_models=_SUPPORTED_MODELS,
    default_temperature=0.2,
)

BUG_DETECTION_REVIEW = StandardPromptTemplate(
    name="code_review.bug_detection",
    description="Scans code for likely bugs and correctness issues.",
    version="1.0.0",
    category=_CATEGORY,
    system_prompt_text=(
        "You are a meticulous code reviewer hunting for correctness "
        "bugs: off-by-one errors, null/undefined handling gaps, "
        "incorrect boolean logic, race conditions, resource leaks, "
        "unhandled exceptions, and mismatched types. Only report issues "
        "you are reasonably confident are real bugs, not stylistic "
        "concerns — flag your confidence level for each."
    ),
    user_prompt_template=(
        "Scan the following {{language}} code for likely bugs.\n\n"
        "```{{language}}\n{{code}}\n```\n\n"
        "List each suspected bug under `## Suspected Bugs`, with its "
        "location, why it's likely a bug, confidence "
        "(High/Medium/Low), and a suggested fix."
    ),
    required_variables=[V.CODE.value, V.LANGUAGE.value],
    supported_models=_SUPPORTED_MODELS,
    default_temperature=0.2,
)

_ALL_PROMPTS = (
    SECURITY_REVIEW,
    PERFORMANCE_REVIEW,
    BEST_PRACTICES_REVIEW,
    CODE_SMELLS_REVIEW,
    REFACTORING_REVIEW,
    DESIGN_PATTERNS_REVIEW,
    COMPLEXITY_ANALYSIS,
    BUG_DETECTION_REVIEW,
)

for _prompt in _ALL_PROMPTS:
    PromptFactory.register(_prompt)