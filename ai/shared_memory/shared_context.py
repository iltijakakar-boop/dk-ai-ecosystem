from typing import Dict, Any, List
from app.services.search_service import search_service
from app.core.logging.logger import logger

class SharedContextMemory:
    """
    Implements shared variables, shared reference file registries,
    and semantic vector checks scoped to a workflow execution run.
    """
    def __init__(self, execution_id: int):
        self.execution_id = execution_id

    def set_variable(self, key: str, value: Any) -> None:
        """
        Saves key-value data inside the shared context memory.
        """
        from ai.orchestrator.state_manager import StateManager
        StateManager.update_execution_context(self.execution_id, key, value)

    def get_variable(self, key: str, default: Any = None) -> Any:
        """
        Retrieves key-value data from the shared context memory.
        """
        from ai.orchestrator.state_manager import StateManager
        ctx = StateManager.get_execution_context(self.execution_id)
        return ctx.get(key, default)

    def share_document(self, filename: str) -> None:
        """
        Registers a document as shared context.
        """
        docs = self.get_variable("shared_documents", [])
        if filename not in docs:
            docs.append(filename)
            self.set_variable("shared_documents", docs)
            logger.info(f"[SharedMemory] Document '{filename}' shared in execution {self.execution_id}")

    def get_shared_documents(self) -> List[str]:
        """
        Lists all shared documents in this context.
        """
        return self.get_variable("shared_documents", [])

    def search_shared_context(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Performs semantic vector searches scoped only to the shared documents of this context.
        """
        docs = self.get_shared_documents()
        if not docs:
            return []

        results = []
        for doc in docs:
            # Query similarity searches for specific document filename
            matches = search_service.search_similarity(
                query_text=query, 
                top_k=top_k, 
                filters={"filename": doc}
            )
            results.extend(matches)

        # Re-sort results descending based on scores
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]
