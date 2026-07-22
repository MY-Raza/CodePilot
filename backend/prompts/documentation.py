from backend.prompts.base import StandardPromptTemplate
from backend.prompts.factory import PromptFactory
from backend.prompts.variables import PromptVariableName as V

_SUPPORTED_MODELS = ("llama-3.3-70b-versatile", "qwen/qwen3-32b")
_CATEGORY = "documentation"

README_GENERATION = StandardPromptTemplate(
    name="documentation.readme",
    description="Generates a project README from its structure and metadata.",
    version="1.0.0",
    category=_CATEGORY,
    system_prompt_text=(
        "You are a technical writer producing a clear, welcoming README "
        "for a software project. Write for a developer encountering the "
        "project for the first time: what it does, why it's useful, how "
        "to get started, and how it's organized. Be concrete — derive "
        "content from the provided project details rather than writing "
        "generic filler."
    ),
    user_prompt_template=(
        "Write a README for the project \"{{project_name}}\".\n\n"
        "Tech stack: {{tech_stack}}\n\nFolder structure:\n"
        "```\n{{folder_structure}}\n```\n\n"
        "Include sections: Overview, Features, Tech Stack, Project "
        "Structure, Getting Started, and Contributing."
    ),
    required_variables=[V.PROJECT_NAME.value, V.TECH_STACK.value, V.FOLDER_STRUCTURE.value],
    supported_models=_SUPPORTED_MODELS,
    default_temperature=0.4,
)

API_DOCUMENTATION = StandardPromptTemplate(
    name="documentation.api",
    description="Generates API documentation from an API definition.",
    version="1.0.0",
    category=_CATEGORY,
    system_prompt_text=(
        "You are a technical writer producing API reference "
        "documentation. For each endpoint, document its method, path, "
        "purpose, request parameters/body, response shape, and possible "
        "error responses. Be precise and complete — do not omit any "
        "endpoint or field present in the provided definition, and do "
        "not invent endpoints that aren't there."
    ),
    user_prompt_template=(
        "Generate API documentation from the following API definition "
        "for \"{{project_name}}\".\n\n```\n{{api_definition}}\n```\n\n"
        "Document each endpoint under its own `### METHOD /path` "
        "heading, with Parameters, Request Body, and Responses "
        "subsections/tables."
    ),
    required_variables=[V.PROJECT_NAME.value, V.API_DEFINITION.value],
    supported_models=_SUPPORTED_MODELS,
    default_temperature=0.2,
)

ARCHITECTURE_DOCUMENTATION = StandardPromptTemplate(
    name="documentation.architecture",
    description="Generates architecture documentation describing system design.",
    version="1.0.0",
    category=_CATEGORY,
    system_prompt_text=(
        "You are a software architect documenting a system's "
        "architecture for engineers joining the project. Explain the "
        "major components, how they interact, key design decisions, and "
        "data flow. Use the provided architecture details as ground "
        "truth; where reasoning about a design decision, be explicit "
        "that it's an inference rather than stated fact."
    ),
    user_prompt_template=(
        "Document the architecture of \"{{project_name}}\" based on the "
        "following details.\n\n```\n{{architecture}}\n```\n\n"
        "Include sections: System Overview, Components, Data Flow, and "
        "Key Design Decisions. Use a Mermaid diagram (fenced ```mermaid "
        "block) to illustrate component relationships if the structure "
        "supports it."
    ),
    required_variables=[V.PROJECT_NAME.value, V.ARCHITECTURE.value],
    supported_models=_SUPPORTED_MODELS,
    default_temperature=0.3,
)

DATABASE_DOCUMENTATION = StandardPromptTemplate(
    name="documentation.database",
    description="Generates database schema documentation.",
    version="1.0.0",
    category=_CATEGORY,
    system_prompt_text=(
        "You are a technical writer documenting a database schema. For "
        "each table, describe its purpose, columns (with types and "
        "constraints), and relationships to other tables. Base "
        "everything strictly on the provided schema — do not invent "
        "tables, columns, or relationships."
    ),
    user_prompt_template=(
        "Document the following database schema for "
        "\"{{project_name}}\".\n\n```sql\n{{database_schema}}\n```\n\n"
        "Document each table under its own `### table_name` heading "
        "with a Columns table (Column | Type | Constraints | "
        "Description) and a Relationships subsection."
    ),
    required_variables=[V.PROJECT_NAME.value, V.DATABASE_SCHEMA.value],
    supported_models=_SUPPORTED_MODELS,
    default_temperature=0.2,
)

CLASS_DOCUMENTATION = StandardPromptTemplate(
    name="documentation.class",
    description="Generates documentation for a single class.",
    version="1.0.0",
    category=_CATEGORY,
    system_prompt_text=(
        "You are a technical writer documenting a single class. Explain "
        "its purpose/responsibility, its public methods and attributes, "
        "and how it's typically used, based strictly on the provided "
        "code."
    ),
    user_prompt_template=(
        "Document the class `{{class_name}}` from the following "
        "{{language}} code.\n\n```{{language}}\n{{code}}\n```\n\n"
        "Include: Purpose, Public Methods (with parameters/return "
        "values), Attributes, and a usage example."
    ),
    required_variables=[V.CLASS_NAME.value, V.LANGUAGE.value, V.CODE.value],
    supported_models=_SUPPORTED_MODELS,
    default_temperature=0.3,
)

FUNCTION_DOCUMENTATION = StandardPromptTemplate(
    name="documentation.function",
    description="Generates documentation for a single function or method.",
    version="1.0.0",
    category=_CATEGORY,
    system_prompt_text=(
        "You are a technical writer documenting a single function. "
        "Describe its purpose, parameters (with types), return value, "
        "exceptions it may raise, and provide a short usage example, "
        "based strictly on the provided code."
    ),
    user_prompt_template=(
        "Document the function `{{function_name}}` from the following "
        "{{language}} code.\n\n```{{language}}\n{{code}}\n```\n\n"
        "Include: Purpose, Parameters table, Returns, Raises, and a "
        "usage example."
    ),
    required_variables=[V.FUNCTION_NAME.value, V.LANGUAGE.value, V.CODE.value],
    supported_models=_SUPPORTED_MODELS,
    default_temperature=0.3,
)

CODE_EXPLANATION = StandardPromptTemplate(
    name="documentation.code_explanation",
    description="Explains what a piece of code does in plain language.",
    version="1.0.0",
    category=_CATEGORY,
    system_prompt_text=(
        "You are a patient senior engineer explaining code to a "
        "teammate. Explain what the code does, step by step, in plain "
        "language, calling out any non-obvious logic, edge cases "
        "handled, or assumptions the code makes. Avoid simply "
        "restating the code line-by-line without adding understanding."
    ),
    user_prompt_template=(
        "Explain what the following {{language}} code does.\n\n"
        "```{{language}}\n{{code}}\n```\n\n"
        "Structure the explanation as `## Overview` (a 2-3 sentence "
        "summary) followed by `## Step-by-Step Breakdown`."
    ),
    required_variables=[V.LANGUAGE.value, V.CODE.value],
    supported_models=_SUPPORTED_MODELS,
    default_temperature=0.4,
)

INSTALLATION_GUIDE = StandardPromptTemplate(
    name="documentation.installation_guide",
    description="Generates an installation/setup guide for a project.",
    version="1.0.0",
    category=_CATEGORY,
    system_prompt_text=(
        "You are a technical writer producing a setup guide a new "
        "developer can follow start-to-finish without prior context on "
        "the project. Base steps on the provided dependencies and tech "
        "stack; include prerequisite installation, dependency "
        "installation, configuration/environment setup, and how to "
        "verify the setup worked."
    ),
    user_prompt_template=(
        "Write an installation guide for \"{{project_name}}\".\n\n"
        "Tech stack: {{tech_stack}}\n\nDependencies:\n"
        "```\n{{dependencies}}\n```\n\n"
        "Include sections: Prerequisites, Installation, Configuration, "
        "and Verifying the Setup, using numbered steps with exact "
        "commands in fenced code blocks."
    ),
    required_variables=[V.PROJECT_NAME.value, V.TECH_STACK.value, V.DEPENDENCIES.value],
    supported_models=_SUPPORTED_MODELS,
    default_temperature=0.3,
)

_ALL_PROMPTS = (
    README_GENERATION,
    API_DOCUMENTATION,
    ARCHITECTURE_DOCUMENTATION,
    DATABASE_DOCUMENTATION,
    CLASS_DOCUMENTATION,
    FUNCTION_DOCUMENTATION,
    CODE_EXPLANATION,
    INSTALLATION_GUIDE,
)

for _prompt in _ALL_PROMPTS:
    PromptFactory.register(_prompt)