"""
ClaimPilot — UiPath API Client
Handles communication with UiPath Automation Cloud and Maestro APIs.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Optional

import httpx
from dotenv import load_dotenv

from .logger import setup_logger
from .models import CaseRecord, CaseStage, ClaimStatus

load_dotenv()
logger = setup_logger("uipath_client")


class UiPathClient:
    """
    Client for interacting with UiPath Automation Cloud APIs.
    Handles authentication, Maestro case management, and job orchestration.
    """

    def __init__(self):
        self.cloud_url = os.getenv("UIPATH_CLOUD_URL", "https://cloud.uipath.com")
        self.tenant_id = os.getenv("UIPATH_TENANT_ID", "")
        self.client_id = os.getenv("UIPATH_CLIENT_ID", "")
        self.client_secret = os.getenv("UIPATH_CLIENT_SECRET", "")
        self.org_id = os.getenv("UIPATH_ORG_ID", "")
        self.maestro_api_url = os.getenv("MAESTRO_API_URL", "")
        self._access_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        self._http_client = httpx.Client(timeout=30.0)

    async def authenticate(self) -> str:
        """
        Authenticate with UiPath Cloud via OAuth2 client credentials.

        Returns:
            Access token string.
        """
        logger.info("authenticating", cloud_url=self.cloud_url)

        response = self._http_client.post(
            f"{self.cloud_url}/identity_/connect/token",
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "scope": "OR.Default OR.Folders OR.Jobs OR.Machines OR.Robots",
            },
        )
        response.raise_for_status()
        data = response.json()

        self._access_token = data["access_token"]
        logger.info("authenticated_successfully")
        return self._access_token

    @property
    def _headers(self) -> dict[str, str]:
        """Default headers for API requests."""
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
            "X-UIPATH-TenantName": self.tenant_id,
            "X-UIPATH-OrganizationUnitId": self.org_id,
        }

    # ──────────────────────────────────────────────
    # Maestro Case Management
    # ──────────────────────────────────────────────

    async def create_case(self, case: CaseRecord) -> dict[str, Any]:
        """
        Create a new case in UiPath Maestro Case Management.

        Args:
            case: The CaseRecord to create.

        Returns:
            Maestro API response with case details.
        """
        logger.info("creating_maestro_case", case_id=case.case_id, claim_id=case.claim.claim_id)

        payload = {
            "CaseDefinitionId": os.getenv("MAESTRO_CASE_DEFINITION_ID"),
            "DisplayName": f"Claim {case.claim.claim_id} - {case.claim.claim_type.value.upper()}",
            "Priority": self._determine_priority(case),
            "CustomFields": {
                "ClaimId": case.claim.claim_id,
                "ClaimType": case.claim.claim_type.value,
                "ClaimantName": case.claim.claimant.full_name,
                "PolicyNumber": case.claim.claimant.policy_number,
                "ClaimedAmount": case.claim.claimed_amount,
                "IncidentDate": case.claim.incident_date.isoformat(),
                "Description": case.claim.description,
            },
        }

        response = self._http_client.post(
            f"{self.maestro_api_url}/cases",
            headers=self._headers,
            json=payload,
        )
        response.raise_for_status()

        result = response.json()
        logger.info("case_created", case_id=case.case_id, maestro_id=result.get("Id"))
        return result

    async def update_case_stage(
        self,
        maestro_case_id: str,
        new_stage: CaseStage,
        notes: str = "",
    ) -> dict[str, Any]:
        """
        Transition a Maestro case to a new stage.

        Args:
            maestro_case_id: The Maestro case identifier.
            new_stage: Target case stage.
            notes: Optional notes for the transition.

        Returns:
            Updated case data from Maestro.
        """
        logger.info(
            "transitioning_case",
            maestro_id=maestro_case_id,
            new_stage=new_stage.value,
        )

        payload = {
            "Stage": new_stage.value.upper(),
            "Notes": notes,
        }

        response = self._http_client.patch(
            f"{self.maestro_api_url}/cases/{maestro_case_id}/stage",
            headers=self._headers,
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    async def assign_case(
        self,
        maestro_case_id: str,
        assignee_type: str,
        assignee_id: str,
    ) -> dict[str, Any]:
        """
        Assign a case to an agent, robot, or human.

        Args:
            maestro_case_id: The Maestro case identifier.
            assignee_type: "agent", "robot", or "human".
            assignee_id: Identifier of the assignee.

        Returns:
            Updated case data.
        """
        logger.info(
            "assigning_case",
            maestro_id=maestro_case_id,
            assignee_type=assignee_type,
            assignee_id=assignee_id,
        )

        payload = {
            "AssigneeType": assignee_type,
            "AssigneeId": assignee_id,
        }

        response = self._http_client.patch(
            f"{self.maestro_api_url}/cases/{maestro_case_id}/assign",
            headers=self._headers,
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    async def create_human_task(
        self,
        maestro_case_id: str,
        task_title: str,
        task_data: dict,
        assignee_group: str = "adjusters",
    ) -> dict[str, Any]:
        """
        Create a human task in UiPath Action Center for manual review.

        Args:
            maestro_case_id: Associated case ID.
            task_title: Title displayed in Action Center.
            task_data: Data to present to the human reviewer.
            assignee_group: User group to assign the task to.

        Returns:
            Created task details.
        """
        logger.info(
            "creating_human_task",
            maestro_id=maestro_case_id,
            task_title=task_title,
        )

        payload = {
            "Title": task_title,
            "Type": "FormTask",
            "CaseId": maestro_case_id,
            "Data": task_data,
            "AssigneeGroup": assignee_group,
            "Priority": "High",
        }

        response = self._http_client.post(
            f"{self.maestro_api_url}/tasks",
            headers=self._headers,
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    # ──────────────────────────────────────────────
    # Jobs & Workflows
    # ──────────────────────────────────────────────

    async def trigger_workflow(
        self,
        process_name: str,
        input_arguments: dict,
    ) -> dict[str, Any]:
        """
        Start a UiPath job/workflow (RPA robot or Agent Builder agent).

        Args:
            process_name: Name of the process to run.
            input_arguments: Input arguments for the workflow.

        Returns:
            Job execution details.
        """
        logger.info("triggering_workflow", process=process_name)

        payload = {
            "startInfo": {
                "ReleaseKey": process_name,
                "Strategy": "Specific",
                "InputArguments": str(input_arguments),
            }
        }

        response = self._http_client.post(
            f"{self.cloud_url}/{self.org_id}/{self.tenant_id}/odata/Jobs/UiPath.Server.Configuration.OData.StartJobs",
            headers=self._headers,
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    # ──────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────

    @staticmethod
    def _determine_priority(case: CaseRecord) -> str:
        """Determine case priority based on claim amount and type."""
        amount = case.claim.claimed_amount
        if amount > 50000:
            return "Critical"
        elif amount > 20000:
            return "High"
        elif amount > 5000:
            return "Medium"
        return "Low"

    def close(self) -> None:
        """Close the HTTP client connection."""
        self._http_client.close()
