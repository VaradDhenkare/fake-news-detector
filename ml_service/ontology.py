"""
ontology.py — Service Ontology Abstraction for Bruviti Applied AI Platform
==========================================================================
Demonstrates how the TruthLens NLP triage engine conceptually maps to
Bruviti's Aftermarket Intelligence Platform.

Bruviti Domain Context:
  Bruviti specializes in Aftermarket Intelligence for complex equipment,
  using Service Ontologies, Small Language Models (SLMs), and Agentic Workflows
  to diagnose failure modes and recommend spare parts with high confidence in
  secure/air-gapped industrial environments.

Domain Analogy Mapping:
  -----------------------------------------------------------------------------
  TruthLens (Content Verification)       Bruviti (Aftermarket Service Intelligence)
  -----------------------------------------------------------------------------
  News Source / Publisher          <---> Equipment / OEM Hierarchy
  Full Article / Headline          <---> Service Ticket / Technician Field Notes
  Claim Text Under Analysis        <---> Failure Mode / Reported Symptom Description
  Verdict (REAL / FAKE / UNCERTAIN)<---> Root Cause Category / Fault Triage
  Prediction Confidence Score      <---> Parts Prediction / Recommended SKU Confidence
  Dual TF-IDF / SLM Classifier     <---> Domain-Adapted Small Language Model (SLM)
  -----------------------------------------------------------------------------
"""

from typing import Dict, Any, Optional


class ServiceOntology:
    """
    Maps Fake News domain to Aftermarket Service domain.

    Fake News Domain Hierarchy:
      Source -> Article -> Claim -> Verdict

    Aftermarket Service Domain Hierarchy:
      Equipment -> Assembly -> FailureMode -> Part Prediction
    """

    # Domain entity relationships
    DOMAIN_MAPPING = {
        "Source": "Equipment (Make, Model, Serial, Customer)",
        "Article": "Assembly / Sub-system (Compressor, Hydraulics, Control Board)",
        "Claim": "FailureMode / Symptom Description (Error Code, Vibration, Overheat)",
        "Verdict": "Root Cause Triage (Verified Defect vs False Alarm / Operator Error)",
        "Confidence": "Parts Prediction Confidence (SKU recommendation probability)",
    }

    # Bruviti mapping references:
    # In Bruviti: News Text = Service Ticket Description
    # Real/Fake = Root Cause Category
    # Confidence = Parts Prediction Confidence

    @classmethod
    def get_ontology_hierarchy(cls) -> Dict[str, Any]:
        """Returns the formal ontology structure bridging both problem spaces."""
        return {
            "fake_news_ontology": [
                "Source (Origin credibility & domain reputation)",
                "Article (Context, temporal freshness, publication metadata)",
                "Claim (Core factual assertion or syntactic feature pattern)",
                "Verdict (REAL, FAKE, or UNCERTAIN under threshold)",
            ],
            "aftermarket_service_ontology": [
                "Equipment (Industrial asset hierarchy, BOM, operational hours)",
                "Assembly (Component grouping, schematic nodes, telemetry)",
                "FailureMode (Root cause diagnosis, wear pattern, DTC code)",
                "Part Prediction (Optimal replacement SKU, kit recommendation)",
            ],
            "cross_domain_equivalences": cls.DOMAIN_MAPPING,
        }

    @classmethod
    def map_triage_result(
        cls,
        text_snippet: str,
        label: str,
        confidence: float,
        model_version: str = "1.0.0",
    ) -> Dict[str, Any]:
        """
        Transforms a classification outcome into an Aftermarket Service Ontology triage representation.
        Shows how this classification pipeline would act as an automated service triage agent.
        """
        # Map label to root cause triage category
        if label == "REAL":
            root_cause_triage = "VERIFIED_FAILURE_MODE"
            recommended_action = "Auto-dispatch repair kit and schedule Level-1 field technician"
            sku_recommendation = "OEM-KIT-STANDARD-REPLACE"
        elif label == "FAKE":
            root_cause_triage = "ANOMALOUS_REPORT_OR_NO_FAULT_FOUND"
            recommended_action = "Flag for sensor recalibration; suppress false part dispatch"
            sku_recommendation = "NONE (Telemetry re-calibration recommended)"
        else:
            root_cause_triage = "UNCERTAIN_AMBIGUOUS_SYMPTOMS"
            recommended_action = "Escalate ticket to Bruviti Agentic Diagnostic Workflow (Tier-2 Specialist)"
            sku_recommendation = "REQUIRES_DIAGNOSTIC_CONFIRMATION"

        return {
            "ontology_version": "bruviti-aftermarket-v2.1",
            "model_version": model_version,
            "concept_mapping": {
                "input_complaint": text_snippet[:150] + "..." if len(text_snippet) > 150 else text_snippet,
                "analogous_service_ticket_field": "Technician Complaint / Telemetry Description",
                "diagnosed_root_cause_category": root_cause_triage,
                "parts_prediction_confidence": confidence,
                "recommended_service_action": recommended_action,
                "recommended_part_sku": sku_recommendation,
            },
            "service_ontology_path": [
                "Equipment:HeavyMachineryAsset",
                "Assembly:DiagnosticTelemetrySubsystem",
                f"FailureMode:{root_cause_triage}",
                f"Action:{recommended_action[:30]}...",
            ],
        }
