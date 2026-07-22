from backend.prompts.base import StandardPromptTemplate
from backend.prompts.factory import PromptFactory
from backend.prompts.variables import PromptVariableName as V

_SUPPORTED_MODELS = ("llama-3.3-70b-versatile", "qwen/qwen3-32b")
_CATEGORY = "architecture"

REPOSITORY_ANALYSIS = StandardPromptTemplate(
    name="architecture.repository_analysis",
    description="Produces a high-level analysis of a repository's structure and purpose.",
    version="1.0.0",
    category=_CATEGORY,
    system_prompt_text=(
        "You are a software architect producing a high-level orientation "
        "to a repository for an engineer who has never seen it. Explain "
        "what the project does, its tech stack, how it's organized, and "
        "the entry points a new contributor should look at first."
    ),
    user_prompt_template=(
        "Analyze the repository \"{{repository_name}}\" (branch: "
        "{{branch}}).\n\nTech stack: {{tech_stack}}\n\n"
        "Folder structure:\n```\n{{folder_structure}}\n```\n\n"
        "Structure the response as `## Purpose`, `## Tech Stack`, "
        "`## Structure Overview`, and `## Suggested Starting Points`."
    ),
    required_variables=[
        V.REPOSITORY_NAME.value,
        V.BRANCH.value,
        V.TECH_STACK.value,
        V.FOLDER_STRUCTURE.value,
    ],
    supported_models=_SUPPORTED_MODELS,
    default_temperature=0.3,
)

ARCHITECTURE_REVIEW = StandardPromptTemplate(
    name="architecture.architecture_review",
    description="Critically reviews a described system architecture.",
    version="1.0.0",
    category=_CATEGORY,
    system_prompt_text=(
        "You are a principal engineer critically reviewing a system's "
        "architecture. Evaluate separation of concerns, coupling, "
        "single points of failure, and alignment between the "
        "architecture and the stated requirements. Give specific, "
        "actionable critique — not generic architecture platitudes."
    ),
    user_prompt_template=(
        "Review the architecture of \"{{project_name}}\".\n\n"
        "Architecture description:\n```\n{{architecture}}\n```\n\n"
        "Requirements it must satisfy:\n```\n{{requirements}}\n```\n\n"
        "Structure the response as `## Strengths`, `## Concerns` (each "
        "with severity), and `## Recommendations`."
    ),
    required_variables=[V.PROJECT_NAME.value, V.ARCHITECTURE.value, V.REQUIREMENTS.value],
    supported_models=_SUPPORTED_MODELS,
    default_temperature=0.3,
)

FOLDER_STRUCTURE_ANALYSIS = StandardPromptTemplate(
    name="architecture.folder_structure_analysis",
    description="Analyzes a repository's folder structure for organization issues.",
    version="1.0.0",
    category=_CATEGORY,
    system_prompt_text=(
        "You are a software architect evaluating a project's folder "
        "structure. Assess whether the organization follows a "
        "recognizable convention (e.g. layered, feature-based, "
        "domain-driven), flag inconsistencies or misplaced modules, and "
        "suggest improvements only where they'd provide real clarity "
        "benefit."
    ),
    user_prompt_template=(
        "Analyze the folder structure of \"{{repository_name}}\".\n\n"
        "```\n{{folder_structure}}\n```\n\n"
        "Structure the response as `## Organization Pattern Detected`, "
        "`## Inconsistencies`, and `## Suggested Improvements`."
    ),
    required_variables=[V.REPOSITORY_NAME.value, V.FOLDER_STRUCTURE.value],
    supported_models=_SUPPORTED_MODELS,
    default_temperature=0.3,
)

DEPENDENCY_ANALYSIS = StandardPromptTemplate(
    name="architecture.dependency_analysis",
    description="Analyzes a project's dependencies for risk and health.",
    version="1.0.0",
    category=_CATEGORY,
    system_prompt_text=(
        "You are a software architect reviewing a project's "
        "dependencies. Flag dependencies that are commonly associated "
        "with maintenance risk (unmaintained, deprecated, or known to "
        "have had major breaking changes), note any obviously "
        "redundant/overlapping dependencies, and comment on overall "
        "dependency footprint. Be honest about the limits of assessing "
        "this from a dependency list alone — do not fabricate "
        "vulnerability details you cannot verify."
    ),
    user_prompt_template=(
        "Analyze the dependencies of \"{{project_name}}\".\n\n"
        "```\n{{dependencies}}\n```\n\n"
        "Structure the response as `## Notable Risks`, `## Redundant/"
        "Overlapping Dependencies`, and `## General Observations`."
    ),
    required_variables=[V.PROJECT_NAME.value, V.DEPENDENCIES.value],
    supported_models=_SUPPORTED_MODELS,
    default_temperature=0.3,
)

API_DESIGN_REVIEW = StandardPromptTemplate(
    name="architecture.api_design_review",
    description="Reviews an API's design for consistency and REST/API best practices.",
    version="1.0.0",
    category=_CATEGORY,
    system_prompt_text=(
        "You are an API design expert reviewing an API definition. "
        "Evaluate resource naming consistency, HTTP method/status code "
        "usage, versioning approach, pagination, and error response "
        "consistency. Ground every point in the specific endpoints "
        "provided."
    ),
    user_prompt_template=(
        "Review the API design of \"{{project_name}}\".\n\n"
        "```\n{{api_definition}}\n```\n\n"
        "Structure the response as `## Strengths`, `## Design Issues` "
        "(each with the affected endpoint(s)), and `## Recommendations`."
    ),
    required_variables=[V.PROJECT_NAME.value, V.API_DEFINITION.value],
    supported_models=_SUPPORTED_MODELS,
    default_temperature=0.3,
)

DATABASE_DESIGN_REVIEW = StandardPromptTemplate(
    name="architecture.database_design_review",
    description="Reviews a database schema for normalization, indexing, and design issues.",
    version="1.0.0",
    category=_CATEGORY,
    system_prompt_text=(
        "You are a database architect reviewing a schema. Evaluate "
        "normalization level, key/index choices, relationship "
        "modeling (foreign keys, cardinality), and naming consistency. "
        "Flag specific tables/columns rather than giving generic "
        "database-design advice."
    ),
    user_prompt_template=(
        "Review the database design of \"{{project_name}}\".\n\n"
        "```sql\n{{database_schema}}\n```\n\n"
        "Structure the response as `## Strengths`, `## Design Issues` "
        "(each citing the specific table/column), and "
        "`## Recommendations`."
    ),
    required_variables=[V.PROJECT_NAME.value, V.DATABASE_SCHEMA.value],
    supported_models=_SUPPORTED_MODELS,
    default_temperature=0.3,
)

SCALABILITY_REVIEW = StandardPromptTemplate(
    name="architecture.scalability_review",
    description="Reviews an architecture for scalability bottlenecks.",
    version="1.0.0",
    category=_CATEGORY,
    system_prompt_text=(
        "You are a systems architect reviewing an architecture for "
        "scalability. Identify likely bottlenecks under increased load "
        "(single points of failure, unscaled stateful components, "
        "synchronous chains that should be async, missing caching "
        "layers), and propose concrete mitigations, noting which apply "
        "at moderate vs. very large scale."
    ),
    user_prompt_template=(
        "Review the scalability of \"{{project_name}}\"'s "
        "architecture.\n\n```\n{{architecture}}\n```\n\n"
        "Structure the response as `## Current Scaling Limits`, "
        "`## Bottlenecks` (each with the load level at which it "
        "becomes a problem), and `## Recommendations`."
    ),
    required_variables=[V.PROJECT_NAME.value, V.ARCHITECTURE.value],
    supported_models=_SUPPORTED_MODELS,
    default_temperature=0.3,
)

TECHNOLOGY_RECOMMENDATIONS = StandardPromptTemplate(
    name="architecture.technology_recommendations",
    description="Recommends technology choices for a set of requirements.",
    version="1.0.0",
    category=_CATEGORY,
    system_prompt_text=(
        "You are a pragmatic technical advisor recommending technology "
        "choices. Ground recommendations in the stated requirements and "
        "existing tech stack (prefer consistency with what's already in "
        "use unless there's a strong reason not to). For each "
        "recommendation, give the alternative(s) considered and why "
        "this one wins for this specific context."
    ),
    user_prompt_template=(
        "Recommend technology choices for \"{{project_name}}\".\n\n"
        "Requirements:\n```\n{{requirements}}\n```\n\n"
        "Existing tech stack: {{tech_stack}}\n\n"
        "Structure the response as a `## Recommendations` table "
        "(Need | Recommendation | Alternatives Considered | Why) "
        "followed by `## Notes on Fit with Existing Stack`."
    ),
    required_variables=[V.PROJECT_NAME.value, V.REQUIREMENTS.value, V.TECH_STACK.value],
    supported_models=_SUPPORTED_MODELS,
    default_temperature=0.4,
)

_ALL_PROMPTS = (
    REPOSITORY_ANALYSIS,
    ARCHITECTURE_REVIEW,
    FOLDER_STRUCTURE_ANALYSIS,
    DEPENDENCY_ANALYSIS,
    API_DESIGN_REVIEW,
    DATABASE_DESIGN_REVIEW,
    SCALABILITY_REVIEW,
    TECHNOLOGY_RECOMMENDATIONS,
)

for _prompt in _ALL_PROMPTS:
    PromptFactory.register(_prompt)