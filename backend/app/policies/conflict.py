import re
from typing import List, Dict, Any, Tuple
from backend.app.core.logging import logger

class PolicyConflictDetector:
    """
    Detects potential contradictions or conflicting rules across retrieved policy documents
    (e.g., contradictory numerical limits, version discrepancies, or opposing requirements).
    """
    @staticmethod
    def detect_conflicts(documents: List[Dict[str, Any]]) -> Tuple[bool, str, List[Dict[str, Any]]]:
        if len(documents) < 2:
            return False, "", []

        # Check for multiple active versions of the same policy name
        policy_versions = {}
        for doc in documents:
            meta = doc.get("metadata", {})
            name = meta.get("policy_name")
            ver = meta.get("version")
            if name:
                if name not in policy_versions:
                    policy_versions[name] = set()
                policy_versions[name].add(ver)

        for pol_name, versions in policy_versions.items():
            if len(versions) > 1:
                conflict_msg = f"Discrepancy detected: Retrieved multiple differing versions {list(versions)} for policy '{pol_name}'."
                logger.warning(conflict_msg)
                return True, conflict_msg, documents

        # Check for numerical contradictions on key metrics (e.g. days, percentages, allowances)
        num_patterns = {}
        for doc in documents:
            text = doc.get("text", "")
            meta = doc.get("metadata", {})
            policy_name = meta.get("policy_name", "Unknown")
            
            # Look for phrases like "X days", "$X", "X%", "up to X"
            matches = re.findall(r"(?:up to|\b)(\d+)\s*(days|weeks|months|percent|%|hours|dollars|\$)", text, re.IGNORECASE)
            for num, unit in matches:
                key = unit.lower()
                if key not in num_patterns:
                    num_patterns[key] = []
                num_patterns[key].append((num, policy_name, doc))

        # If a single unit has vastly differing limits across policies on similar topic
        # e.g., one doc says 2 days, another says 5 days for the same topic
        for unit, occurrences in num_patterns.items():
            unique_nums = set(o[0] for o in occurrences)
            if len(unique_nums) > 1 and len(set(o[1] for o in occurrences)) > 1:
                # Check if policies are distinct
                pol_names = list(set(o[1] for o in occurrences))
                conflict_msg = f"Potential policy discrepancy across documents {pol_names} regarding '{unit}' limits ({', '.join(unique_nums)})."
                logger.info(f"Conflict note: {conflict_msg}")
                # We flag as potential conflict note without unconditionally blocking unless versions clash
                return False, conflict_msg, documents

        return False, "", []

conflict_detector = PolicyConflictDetector()
