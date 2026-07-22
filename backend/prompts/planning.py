from backend.prompts.base import StandardPromptTemplate
from backend.prompts.factory import PromptFactory
from backend.prompts.variables import PromptVariableName as V

_SUPPORTED_MODELS = ("llama-3.3-70b-versatile", "qwen/qwen3-32b")
_CATEGORY = "planning"

FEATURE_PLANNING = StandardPromptTemplate(
    name="planning.feature_planning",
    description="Produces an implementation plan for a new feature.",
    version="1.0.0",
    category=_CATEGORY,
    system_prompt_text=(
        "You are a senior engineer turning a feature request into an "
        "actionable implementation plan. Consider the existing "
        "architecture and tech stack provided. Cover what needs to "
        "change, in what order, key risks/unknowns, and rough relative "
        "sizing (Small/Medium/Large) per work item."
    ),
    user_prompt_template=(
        "Create an implementation plan for the following feature "
        "request in \"{{project_name}}\".\n\nRequirements:\n"
        "```\n{{requirements}}\n```\n\nCurrent architecture:\n"
        "```\n{{architecture}}\n```\n\n"
        "Structure the plan as `## Summary`, `## Implementation Steps` "
        "(numbered, each with a size estimate), and `## Risks & Open "
        "Questions`."
    ),
    required_variables=[V.PROJECT_NAME.value, V.REQUIREMENTS.value, V.ARCHITECTURE.value],
    supported_models=_SUPPORTED_MODELS,
    default_temperature=0.4,
)

EPIC_CREATION = StandardPromptTemplate(
    name="planning.epic_creation",
    description="Drafts an epic from a high-level requirement.",
    version="1.0.0",
    category=_CATEGORY,
    system_prompt_text=(
        "You are a product-minded technical lead drafting an epic. An "
        "epic should frame the problem/opportunity, the intended "
        "outcome, high-level scope, and how success will be measured — "
        "without prescribing implementation detail, which belongs in "
        "child stories."
    ),
    user_prompt_template=(
        "Draft an epic for \"{{project_name}}\" based on the following "
        "requirements.\n\n```\n{{requirements}}\n```\n\n"
        "Include: Title, Problem Statement, Goal, Scope (In/Out of "
        "Scope bullet lists), and Success Metrics."
    ),
    required_variables=[V.PROJECT_NAME.value, V.REQUIREMENTS.value],
    supported_models=_SUPPORTED_MODELS,
    default_temperature=0.4,
)

USER_STORIES = StandardPromptTemplate(
    name="planning.user_stories",
    description="Generates user stories from requirements.",
    version="1.0.0",
    category=_CATEGORY,
    system_prompt_text=(
        "You are a product owner writing user stories in the standard "
        "\"As a <role>, I want <capability>, so that <benefit>\" format. "
        "Each story should be independently valuable, testable, and "
        "appropriately small (INVEST principles)."
    ),
    user_prompt_template=(
        "Generate user stories for \"{{project_name}}\" from the "
        "following requirements.\n\n```\n{{requirements}}\n```\n\n"
        "List each story as a `### Story: <short title>` heading, the "
        "As a/I want/So that statement, and a brief note on priority "
        "(Must/Should/Could)."
    ),
    required_variables=[V.PROJECT_NAME.value, V.REQUIREMENTS.value],
    supported_models=_SUPPORTED_MODELS,
    default_temperature=0.4,
)

TASK_BREAKDOWN = StandardPromptTemplate(
    name="planning.task_breakdown",
    description="Breaks a user story or requirement into concrete engineering tasks.",
    version="1.0.0",
    category=_CATEGORY,
    system_prompt_text=(
        "You are a tech lead breaking a requirement into concrete, "
        "independently completable engineering tasks. Each task should "
        "be small enough to implement and review in isolation, and "
        "should note which system layer it touches (e.g. API, "
        "database, frontend)."
    ),
    user_prompt_template=(
        "Break the following requirement for \"{{project_name}}\" into "
        "engineering tasks.\n\n```\n{{requirements}}\n```\n\n"
        "Present as a checklist table: Task | Layer | Estimated Effort "
        "(S/M/L) | Dependencies."
    ),
    required_variables=[V.PROJECT_NAME.value, V.REQUIREMENTS.value],
    supported_models=_SUPPORTED_MODELS,
    default_temperature=0.3,
)

ACCEPTANCE_CRITERIA = StandardPromptTemplate(
    name="planning.acceptance_criteria",
    description="Writes acceptance criteria for a requirement or user story.",
    version="1.0.0",
    category=_CATEGORY,
    system_prompt_text=(
        "You are a QA-minded product owner writing acceptance criteria "
        "using Given/When/Then format where practical. Cover the happy "
        "path, key edge cases, and error conditions. Criteria must be "
        "specific and verifiable, not vague."
    ),
    user_prompt_template=(
        "Write acceptance criteria for the following requirement in "
        "\"{{project_name}}\".\n\n```\n{{requirements}}\n```\n\n"
        "List each criterion under `## Acceptance Criteria` using "
        "Given/When/Then bullets, grouped by scenario."
    ),
    required_variables=[V.PROJECT_NAME.value, V.REQUIREMENTS.value],
    supported_models=_SUPPORTED_MODELS,
    default_temperature=0.3,
)

TEST_CASES = StandardPromptTemplate(
    name="planning.test_cases",
    description="Generates test cases for a requirement or piece of code.",
    version="1.0.0",
    category=_CATEGORY,
    system_prompt_text=(
        "You are a QA engineer designing test cases using "
        "{{test_framework}}. Cover happy-path, boundary, negative, and "
        "error-handling cases. Each test case should state its purpose, "
        "setup, action, and expected result clearly enough to implement "
        "directly."
    ),
    user_prompt_template=(
        "Generate test cases for the following requirement in "
        "\"{{project_name}}\", using {{test_framework}}.\n\n"
        "```\n{{requirements}}\n```\n\n"
        "Present as a table: Test Case | Type (Happy Path/Edge Case/"
        "Negative) | Steps | Expected Result."
    ),
    required_variables=[V.PROJECT_NAME.value, V.REQUIREMENTS.value, V.TEST_FRAMEWORK.value],
    supported_models=_SUPPORTED_MODELS,
    default_temperature=0.3,
)

JIRA_TICKET_GENERATION = StandardPromptTemplate(
    name="planning.jira_ticket_generation",
    description="Drafts a Jira ticket (of a given type) from a requirement.",
    version="1.0.0",
    category=_CATEGORY,
    system_prompt_text=(
        "You are a technical project manager drafting a well-formed "
        "Jira ticket. Match the level of detail to the ticket type "
        "provided (e.g. Bug tickets need reproduction steps; Story "
        "tickets need acceptance criteria; Task tickets need a clear "
        "definition of done)."
    ),
    user_prompt_template=(
        "Draft a Jira {{ticket_type}} for \"{{project_name}}\" based on "
        "the following description.\n\n```\n{{issue_description}}\n```"
        "\n\nInclude: Title, Description, and the fields appropriate to "
        "a {{ticket_type}} ticket (e.g. Acceptance Criteria, Steps to "
        "Reproduce, or Definition of Done as applicable), plus a "
        "suggested Priority and Labels."
    ),
    required_variables=[
        V.PROJECT_NAME.value,
        V.TICKET_TYPE.value,
        V.ISSUE_DESCRIPTION.value,
    ],
    supported_models=_SUPPORTED_MODELS,
    default_temperature=0.3,
)

SPRINT_PLANNING = StandardPromptTemplate(
    name="planning.sprint_planning",
    description="Proposes a sprint plan from a backlog and sprint goal.",
    version="1.0.0",
    category=_CATEGORY,
    system_prompt_text=(
        "You are a scrum-master-minded tech lead proposing a sprint "
        "plan. Given a sprint goal and a set of candidate work items, "
        "select and sequence the items that best serve the goal, flag "
        "anything that seems out of scope for the goal, and note "
        "obvious dependency ordering."
    ),
    user_prompt_template=(
        "Propose a sprint plan for \"{{project_name}}\".\n\n"
        "Sprint goal: {{sprint_goal}}\n\nCandidate work items:\n"
        "```\n{{requirements}}\n```\n\n"
        "Present `## Recommended Sprint Scope` (ordered list with brief "
        "rationale) and `## Deferred / Out of Scope` with reasons."
    ),
    required_variables=[V.PROJECT_NAME.value, V.SPRINT_GOAL.value, V.REQUIREMENTS.value],
    supported_models=_SUPPORTED_MODELS,
    default_temperature=0.4,
)

_ALL_PROMPTS = (
    FEATURE_PLANNING,
    EPIC_CREATION,
    USER_STORIES,
    TASK_BREAKDOWN,
    ACCEPTANCE_CRITERIA,
    TEST_CASES,
    JIRA_TICKET_GENERATION,
    SPRINT_PLANNING,
)

for _prompt in _ALL_PROMPTS:
    PromptFactory.register(_prompt)