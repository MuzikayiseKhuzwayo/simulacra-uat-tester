"""Streamlit interface for the TestScope AI UAT agent."""

import streamlit as st
from pydantic import ValidationError
from src.excel_export import create_test_pack_excel
from src.agent_service import AgentServiceError
from src.history_repository import (
    STATUS_COMPLETED,
    STATUS_FAILED,
    STATUS_RUNNING,
    complete_execution,
    fail_execution,
    get_execution_json,
    list_executions,
    start_execution,
)


from src.schemas import (
    AcceptanceCriterion,
    RequirementInput,
    TestPack,
)

from src.workflow import (
    WorkflowBlockedError,
    run_uat_workflow,
)


st.set_page_config(
    page_title="TestScope AI",
    page_icon="🧪",
    layout="wide",
)


def parse_acceptance_criteria(
    raw_text: str,
) -> list[AcceptanceCriterion]:
    """Parse one 'ID | description' criterion per line."""

    criteria: list[AcceptanceCriterion] = []

    for line_number, line in enumerate(
        raw_text.splitlines(),
        start=1,
    ):
        line = line.strip()

        if not line:
            continue

        if "|" not in line:
            raise ValueError(
                "Acceptance criterion line "
                f"{line_number} must use: AC-ID | description"
            )

        criterion_id, description = line.split("|", maxsplit=1)

        criteria.append(
            AcceptanceCriterion(
                criterion_id=criterion_id.strip(),
                description=description.strip(),
            )
        )

    return criteria


def parse_list(raw_text: str) -> list[str]:
    """Parse one non-empty item per line."""

    return [
        line.strip()
        for line in raw_text.splitlines()
        if line.strip()
    ]

def record_execution_failure(
    execution_id: int | None,
    failure_stage: str,
    error: Exception,
) -> None:
    """Record a workflow failure without hiding the original error."""

    if execution_id is None:
        return

    try:
        fail_execution(
            execution_id=execution_id,
            failure_stage=failure_stage,
            error_message=str(error),
        )
    except Exception as history_error:
        st.warning(
            "The workflow failed, but its failure status "
            "could not be saved."
        )
        st.code(str(history_error))

def display_execution_history() -> None:
    """Display saved executions in the Streamlit sidebar."""

    st.sidebar.header("Execution history")

    executions = list_executions()

    if not executions:
        st.sidebar.info(
            "No saved executions are available yet."
        )
        return

    execution_by_id = {
        execution.execution_id: execution
        for execution in executions
    }

    status_icons = {
        STATUS_RUNNING: "⏳",
        STATUS_COMPLETED: "✅",
        STATUS_FAILED: "❌",
    }

    selected_execution_id = st.sidebar.selectbox(
        "Select a saved execution",
        options=list(execution_by_id),
        format_func=lambda execution_id: (
            f"{status_icons.get(
                execution_by_id[execution_id].status,
                '•',
            )} "
            f"#{execution_id} | "
            f"{execution_by_id[execution_id].requirement_id} | "
            f"{execution_by_id[execution_id].title}"
        ),
        key="selected_execution_id",
    )

    selected_execution = execution_by_id[
        selected_execution_id
    ]

    st.sidebar.write(
        f"**Status:** {selected_execution.status}"
    )
    st.sidebar.caption(
        f"Started: {selected_execution.started_at}"
    )

    if selected_execution.duration_seconds is not None:
        st.sidebar.write(
            "**Duration:** "
            f"{selected_execution.duration_seconds:.1f} seconds"
        )

    if selected_execution.status == STATUS_RUNNING:
        st.sidebar.info(
            "This execution is currently running."
        )
        return

    if selected_execution.status == STATUS_FAILED:
        st.sidebar.error(
            "This execution did not produce a TestPack."
        )

        if selected_execution.failure_stage:
            st.sidebar.write(
                "**Failure stage:** "
                f"{selected_execution.failure_stage}"
            )

        if selected_execution.error_message:
            with st.sidebar.expander(
                "View error details"
            ):
                st.code(
                    selected_execution.error_message
                )

        return

    st.sidebar.write(
        f"**Generated tests:** "
        f"{selected_execution.test_count}"
    )
    st.sidebar.write(
        f"**Coverage:** "
        f"{selected_execution.coverage_percentage}%"
    )

    if st.sidebar.button(
        "Load saved TestPack",
        use_container_width=True,
    ):
        saved_json = get_execution_json(
            selected_execution_id
        )

        if saved_json is None:
            st.sidebar.error(
                "The completed TestPack could not be found."
            )
            return

        try:
            saved_test_pack = TestPack.model_validate_json(
                saved_json
            )
        except ValidationError as error:
            st.sidebar.error(
                "The saved execution is not a valid TestPack."
            )
            st.sidebar.code(str(error))
            return

        st.session_state["test_pack"] = saved_test_pack
        st.session_state["execution_id"] = (
            selected_execution_id
        )

        st.sidebar.success(
            f"Execution #{selected_execution_id} loaded."
        )

        st.rerun()


def display_test_pack(test_pack) -> None:
    """Display a validated TestPack in review-friendly sections."""

    summary_tab, analysis_tab, tests_tab, coverage_tab, json_tab = st.tabs(
        [
            "Summary",
            "Requirement analysis",
            "UAT test cases",
            "Coverage",
            "Raw JSON",
        ]
    )

    with summary_tab:
        st.subheader(test_pack.requirement.title)

        first, second, third = st.columns(3)

        first.metric(
            "Acceptance criteria",
            test_pack.coverage_summary.total_criteria,
        )
        second.metric(
            "Generated UAT tests",
            len(test_pack.test_cases),
        )
        third.metric(
            "Coverage",
            f"{test_pack.coverage_summary.coverage_percentage}%",
        )

        st.write(test_pack.analysis.requirement_summary)

    with analysis_tab:
        st.subheader("Business rules")

        for rule in test_pack.analysis.business_rules:
            st.markdown(
                f"**{rule.rule_id}:** {rule.description}"
            )
            st.caption(
                "Criteria: " + ", ".join(rule.source_criteria)
            )

        st.subheader("Ambiguities")

        if not test_pack.analysis.ambiguities:
            st.success("No ambiguities identified.")

        for ambiguity in test_pack.analysis.ambiguities:
            with st.expander(
                f"{ambiguity.ambiguity_id}: "
                f"{ambiguity.description}"
            ):
                st.write(f"**Impact:** {ambiguity.impact}")
                st.write(
                    "**Clarification question:** "
                    f"{ambiguity.clarification_question}"
                )
                st.write(
                    "**Related criteria:** "
                    + ", ".join(ambiguity.related_criteria)
                )

        st.subheader("Assumptions")

        if not test_pack.analysis.assumptions:
            st.success("No assumptions generated.")

        for assumption in test_pack.analysis.assumptions:
            st.write(
                f"**{assumption.assumption_id}:** "
                f"{assumption.description}"
            )
            st.caption(
                f"Status: {assumption.status} | "
                f"Approval required: {assumption.approval_required}"
            )

        st.subheader("Business risks")

        for risk in test_pack.analysis.business_risks:
            with st.expander(
                f"{risk.risk_id} — {risk.severity}"
            ):
                st.write(risk.description)
                st.write(f"**Rationale:** {risk.rationale}")
                st.write(
                    "**Related criteria:** "
                    + ", ".join(risk.related_criteria)
                )

    with tests_tab:
        for test_case in test_pack.test_cases:
            heading = (
                f"{test_case.test_id} — {test_case.title} "
                f"[{test_case.status}]"
            )

            with st.expander(heading):
                left, right = st.columns(2)

                left.write(
                    f"**Type:** {test_case.test_type}"
                )
                left.write(
                    f"**Priority:** {test_case.priority}"
                )
                right.write(
                    f"**Risk level:** {test_case.risk_level}"
                )
                right.write(
                    "**Criteria:** "
                    + ", ".join(
                        test_case.acceptance_criteria_ids
                    )
                )

                st.write(
                    f"**Objective:** {test_case.objective}"
                )

                st.write("**Preconditions**")
                for item in test_case.preconditions:
                    st.write(f"- {item}")

                st.write("**Test data**")
                for item in test_case.test_data:
                    st.write(f"- {item}")

                st.write("**Test steps**")
                st.table(
                    [
                        {
                            "Step": step.step_number,
                            "Action": step.action,
                        }
                        for step in test_case.steps
                    ]
                )

                st.write(
                    "**Expected result:** "
                    f"{test_case.expected_result}"
                )

                if test_case.risk_ids:
                    st.write(
                        "**Risks:** "
                        + ", ".join(test_case.risk_ids)
                    )

                if test_case.ambiguity_ids:
                    st.warning(
                        "Unresolved ambiguities: "
                        + ", ".join(test_case.ambiguity_ids)
                    )

                if test_case.assumption_ids:
                    st.info(
                        "Assumptions: "
                        + ", ".join(test_case.assumption_ids)
                    )

    with coverage_tab:
        coverage = test_pack.coverage_summary

        st.metric(
            "Acceptance-criteria coverage",
            f"{coverage.coverage_percentage}%",
        )

        st.write(
            "**Covered criteria:** "
            + ", ".join(coverage.covered_criteria)
        )

        if coverage.uncovered_criteria:
            st.error(
                "Uncovered criteria: "
                + ", ".join(coverage.uncovered_criteria)
            )
        else:
            st.success("Every acceptance criterion is traceable.")

        st.subheader("Tests by type")

        st.json(
            {
                str(test_type): count
                for test_type, count in coverage.tests_by_type.items()
            }
        )

        st.write(
            "**High-risk tests:** "
            + ", ".join(coverage.high_risk_tests)
        )

    test_pack_json = test_pack.model_dump_json(indent=2)
    test_pack_excel = create_test_pack_excel(test_pack)

    with json_tab:
        st.json(test_pack.model_dump(mode="json"))

    json_column, excel_column = st.columns(2)

    with json_column:

        st.download_button(
            label="Download TestPack JSON",
            data=test_pack_json,
            file_name="test_pack.json",
            mime="application/json",
            use_container_width=True,
            key="download_test_pack_json",
        )

    with excel_column:

        st.download_button(
            label="Download TestPack Excel",
            data=test_pack_excel,
            file_name="test_pack.xlsx",
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            use_container_width=True,
            key="download_test_pack_excel",
        )


st.title("🧪 TestScope AI")
st.caption(
    "Risk-aware UAT test design with deterministic guardrails"
)
display_execution_history()

with st.form("requirement_form"):
    st.subheader("Business requirement")

    requirement_id = st.text_input(
        "Requirement ID",
        value="BR-001",
    )

    title = st.text_input(
        "Title",
        value="Transfer money to an existing UK beneficiary",
    )

    domain = st.text_input(
        "Domain",
        value="Retail Banking",
    )

    feature = st.text_input(
        "Feature",
        value="Digital Payments",
    )

    user_story = st.text_area(
        "User story",
        value=(
            "As an authenticated customer, I want to transfer "
            "money to an existing UK beneficiary."
        ),
        height=100,
    )

    acceptance_criteria_text = st.text_area(
        "Acceptance criteria",
        value=(
            "AC-001 | The customer must be logged in and have "
            "an active current account.\n"
            "AC-002 | The customer must select an existing UK "
            "beneficiary.\n"
            "AC-003 | The customer must enter an amount and "
            "payment reference.\n"
            "AC-004 | The maximum daily transfer limit is £10,000.\n"
            "AC-005 | The transfer must be prevented when available "
            "funds are insufficient.\n"
            "AC-006 | A successful transfer must update the balance "
            "and display a unique transaction reference.\n"
            "AC-007 | A failed transfer must not debit the account."
        ),
        height=240,
        help="Enter one criterion per line using: AC-ID | description",
    )

    business_context_text = st.text_area(
        "Business context",
        value=(
            "Transfers are initiated through online banking.\n"
            "The feature is used by UK retail-banking customers."
        ),
        height=100,
        help="Enter one context item per line.",
    )

    known_risks_text = st.text_area(
        "Known risks",
        value=(
            "Duplicate submissions could create multiple payments.\n"
            "A failed transfer could incorrectly debit the customer.\n"
            "An incorrect balance update could mislead the customer."
        ),
        height=120,
        help="Enter one risk per line.",
    )

    submitted = st.form_submit_button(
        "Generate UAT Test Pack",
        use_container_width=True,
    )

if submitted:
    execution_id: int | None = None

    try:
        requirement = RequirementInput(
            requirement_id=requirement_id,
            title=title,
            domain=domain or None,
            feature=feature or None,
            user_story=user_story,
            acceptance_criteria=parse_acceptance_criteria(
                acceptance_criteria_text
            ),
            business_context=parse_list(
                business_context_text
            ),
            known_risks=parse_list(
                known_risks_text
            ),
        )
        execution_id = start_execution(
            requirement_id=requirement.requirement_id,
            title=requirement.title,
        )

        with st.spinner(
            "Running local AI analysis and generating UAT tests. "
            "This may take several minutes..."
        ):
            generated_test_pack = run_uat_workflow(
                requirement
            )

            test_pack_json = (
                generated_test_pack.model_dump_json(
                    indent=2
                )
            )

            complete_execution(
                execution_id=execution_id,
                test_count=len(
                    generated_test_pack.test_cases
                ),
                coverage_percentage=(
                    generated_test_pack
                    .coverage_summary
                    .coverage_percentage
                ),
                test_pack_json=test_pack_json,
            )

            st.session_state["test_pack"] = (
                generated_test_pack
            )
            st.session_state["execution_id"] = (
                execution_id
            )

        st.success(
            "The validated UAT TestPack was generated "
            "successfully. "
            f"Execution ID: {execution_id}"
        )

    except ValueError as error:
        record_execution_failure(
            execution_id,
            "input-or-validation",
            error,
        )
        st.error(str(error))

    except ValidationError as error:
        record_execution_failure(
            execution_id,
            "schema-validation",
            error,
        )
        st.error("The requirement input is invalid.")
        st.code(str(error))

    except WorkflowBlockedError as error:
        record_execution_failure(
            execution_id,
            error.stage,
            error,
        )

        st.error(
            f"The workflow was blocked during {error.stage}."
        )

        for issue in error.issues:
            st.write(f"- {issue}")

    except AgentServiceError as error:
        record_execution_failure(
            execution_id,
            "agent-service",
            error,
        )
        st.error("The local Ollama agent could not complete.")
        st.code(str(error))

    except Exception as error:
        record_execution_failure(
            execution_id,
            "unexpected",
            error,
        )
        st.error("An unexpected error occurred.")
        st.exception(error)

if "test_pack" in st.session_state:
    display_test_pack(
        st.session_state["test_pack"]
    )