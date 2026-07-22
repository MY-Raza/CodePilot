from backend.prompts.base import StandardPromptTemplate
from backend.prompts.factory import PromptFactory
from backend.prompts.variables import PromptVariableName as V

_SUPPORTED_MODELS = (
    "llama-3.3-70b-versatile",
    "deepseek-r1-distill-llama-70b",
    "qwen/qwen3-32b",
)
_CATEGORY = "debugging"

STACK_TRACE_ANALYSIS = StandardPromptTemplate(
    name="debugging.stack_trace_analysis",
    description="Analyzes a stack trace to explain what went wrong and where.",
    version="1.0.0",
    category=_CATEGORY,
    system_prompt_text=(
        "You are a debugging expert analyzing a stack trace. Identify "
        "the exception type, the exact failure point, and walk through "
        "the call chain that led there in plain language. Distinguish "
        "the root frame (where the error actually occurred) from "
        "intermediate frames."
    ),
    user_prompt_template=(
        "Analyze the following stack trace from \"{{project_name}}\".\n\n"
        "```\n{{stack_trace}}\n```\n\n"
        "Structure the response as `## Error Summary`, `## Call Chain "
        "Walkthrough`, and `## Likely Cause`."
    ),
    required_variables=[V.PROJECT_NAME.value, V.STACK_TRACE.value],
    supported_models=_SUPPORTED_MODELS,
    default_temperature=0.2,
)

ROOT_CAUSE_ANALYSIS = StandardPromptTemplate(
    name="debugging.root_cause_analysis",
    description="Performs root cause analysis on a described issue, using code context.",
    version="1.0.0",
    category=_CATEGORY,
    system_prompt_text=(
        "You are a senior engineer performing root cause analysis. "
        "Distinguish symptoms from the actual root cause, reason "
        "through the relevant code to support your conclusion, and "
        "avoid stopping at the first plausible-sounding explanation "
        "without checking it against the provided code."
    ),
    user_prompt_template=(
        "Perform root cause analysis for the following issue in "
        "\"{{project_name}}\".\n\nIssue description:\n"
        "{{issue_description}}\n\nRelevant {{language}} code:\n"
        "```{{language}}\n{{code}}\n```\n\n"
        "Structure the response as `## Symptom`, `## Investigation`, "
        "and `## Root Cause`."
    ),
    required_variables=[
        V.PROJECT_NAME.value,
        V.ISSUE_DESCRIPTION.value,
        V.LANGUAGE.value,
        V.CODE.value,
    ],
    supported_models=_SUPPORTED_MODELS,
    default_temperature=0.2,
)

BUG_EXPLANATION = StandardPromptTemplate(
    name="debugging.bug_explanation",
    description="Explains a known bug in plain language for a non-author reader.",
    version="1.0.0",
    category=_CATEGORY,
    system_prompt_text=(
        "You are a senior engineer explaining a bug to a teammate who "
        "didn't write the original code. Explain what the code was "
        "supposed to do, what it actually does, and exactly where the "
        "two diverge, in plain language."
    ),
    user_prompt_template=(
        "Explain the following bug in \"{{project_name}}\".\n\n"
        "Issue description: {{issue_description}}\n\n"
        "Relevant {{language}} code:\n```{{language}}\n{{code}}\n```\n\n"
        "Structure the response as `## Intended Behavior`, `## Actual "
        "Behavior`, and `## Where They Diverge`."
    ),
    required_variables=[
        V.PROJECT_NAME.value,
        V.ISSUE_DESCRIPTION.value,
        V.LANGUAGE.value,
        V.CODE.value,
    ],
    supported_models=_SUPPORTED_MODELS,
    default_temperature=0.3,
)

FIX_SUGGESTIONS = StandardPromptTemplate(
    name="debugging.fix_suggestions",
    description="Suggests one or more fixes for a described bug.",
    version="1.0.0",
    category=_CATEGORY,
    system_prompt_text=(
        "You are a senior engineer proposing fixes for a bug. Offer the "
        "most direct fix first, then note any alternative approaches "
        "with their tradeoffs. Be explicit about any assumptions your "
        "fix depends on, and flag if the provided code doesn't give "
        "enough information to be fully confident."
    ),
    user_prompt_template=(
        "Suggest fixes for the following bug in \"{{project_name}}\".\n\n"
        "Issue description: {{issue_description}}\n\n"
        "Relevant {{language}} code:\n```{{language}}\n{{code}}\n```\n\n"
        "Structure the response as `## Recommended Fix` (with a code "
        "example) and `## Alternative Approaches` (if any), each with "
        "tradeoffs."
    ),
    required_variables=[
        V.PROJECT_NAME.value,
        V.ISSUE_DESCRIPTION.value,
        V.LANGUAGE.value,
        V.CODE.value,
    ],
    supported_models=_SUPPORTED_MODELS,
    default_temperature=0.3,
)

PATCH_GENERATION = StandardPromptTemplate(
    name="debugging.patch_generation",
    description="Generates a minimal patch for a described bug.",
    version="1.0.0",
    category=_CATEGORY,
    system_prompt_text=(
        "You are a senior engineer producing a minimal, focused patch "
        "for a bug. Change only what's necessary to fix the described "
        "issue — do not perform unrelated refactoring. Output the "
        "patch as a unified-diff-style code block, and briefly explain "
        "the change below it."
    ),
    user_prompt_template=(
        "Generate a patch for the following bug in "
        "\"{{project_name}}\" (target: {{patch_target}}).\n\n"
        "Issue description: {{issue_description}}\n\n"
        "Relevant {{language}} code:\n```{{language}}\n{{code}}\n```\n\n"
        "Provide the patch under `## Patch` as a fenced diff code "
        "block, followed by `## Explanation`."
    ),
    required_variables=[
        V.PROJECT_NAME.value,
        V.PATCH_TARGET.value,
        V.ISSUE_DESCRIPTION.value,
        V.LANGUAGE.value,
        V.CODE.value,
    ],
    supported_models=_SUPPORTED_MODELS,
    default_temperature=0.2,
)

PERFORMANCE_BOTTLENECK_ANALYSIS = StandardPromptTemplate(
    name="debugging.performance_bottleneck_analysis",
    description="Analyzes performance metrics/code to locate a bottleneck.",
    version="1.0.0",
    category=_CATEGORY,
    system_prompt_text=(
        "You are a performance engineer diagnosing a bottleneck using "
        "both the provided performance metrics and code. Correlate the "
        "metrics with specific code paths, identify the most likely "
        "bottleneck, and explain the reasoning connecting the two."
    ),
    user_prompt_template=(
        "Diagnose the performance bottleneck in \"{{project_name}}\" "
        "using the following data.\n\nPerformance metrics:\n"
        "```\n{{performance_metrics}}\n```\n\n"
        "Relevant {{language}} code:\n```{{language}}\n{{code}}\n```\n\n"
        "Structure the response as `## Metrics Interpretation`, "
        "`## Likely Bottleneck`, and `## Recommended Optimization`."
    ),
    required_variables=[
        V.PROJECT_NAME.value,
        V.PERFORMANCE_METRICS.value,
        V.LANGUAGE.value,
        V.CODE.value,
    ],
    supported_models=_SUPPORTED_MODELS,
    default_temperature=0.2,
)

_ALL_PROMPTS = (
    STACK_TRACE_ANALYSIS,
    ROOT_CAUSE_ANALYSIS,
    BUG_EXPLANATION,
    FIX_SUGGESTIONS,
    PATCH_GENERATION,
    PERFORMANCE_BOTTLENECK_ANALYSIS,
)

for _prompt in _ALL_PROMPTS:
    PromptFactory.register(_prompt)