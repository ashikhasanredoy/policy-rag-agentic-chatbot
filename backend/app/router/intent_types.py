from enum import Enum

class IntentType(str, Enum):
    GENERAL_CHAT = "GENERAL_CHAT"           # Greetings, small talk, gratitude, identity, capabilities
    POLICY_CATEGORY = "POLICY_CATEGORY"     # Broad category inquiry (e.g. "Tell me about Benefits & Perks", "Info about HR")
    POLICY_LIST = "POLICY_LIST"             # Asking what policies exist (e.g. "What policies do you have?", "List all policies")
    POLICY_QUERY = "POLICY_QUERY"           # Specific factual policy question needing Hybrid RAG
    OUT_OF_SCOPE = "OUT_OF_SCOPE"           # Completely unrelated questions (e.g. weather, sports, general coding)
