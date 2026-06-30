import httpx
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class MCPTransport(ABC):
    """
    Abstract base interface for pluggable Model Context Protocol (MCP) transports.
    """
    @abstractmethod
    def connect(self, endpoint: str) -> bool:
        pass

    @abstractmethod
    def send_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def close(self) -> None:
        pass


class HTTPTransport(MCPTransport):
    """
    HTTP client transport implementing standard request-response JSON-RPC 2.0 communication.
    """
    def __init__(self):
        self.endpoint: Optional[str] = None
        self.client: Optional[httpx.Client] = None

    def connect(self, endpoint: str) -> bool:
        self.endpoint = endpoint
        self.client = httpx.Client(timeout=10.0)
        try:
            # Ping health check
            res = self.client.get(f"{endpoint}/health")
            return res.status_code == 200
        except Exception:
            # Fallback to check connection directly
            try:
                res = self.client.options(endpoint)
                return True
            except Exception:
                return False

    def send_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        if not self.client or not self.endpoint:
            raise RuntimeError("HTTP Transport not connected.")
        
        # Verify JSON-RPC 2.0 packet structure
        if "jsonrpc" not in message:
            message["jsonrpc"] = "2.0"
        
        try:
            res = self.client.post(self.endpoint, json=message)
            if res.status_code == 200:
                return res.json()
            return {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "error": {"code": -32603, "message": f"Server returned status {res.status_code}"}
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "error": {"code": -32603, "message": f"Transport Error: {str(e)}"}
            }

    def close(self) -> None:
        if self.client:
            self.client.close()


class SSETransport(MCPTransport):
    """
    Server-Sent Events (SSE) streaming transport for async notifications and heartbeats.
    """
    def __init__(self):
        self.endpoint: Optional[str] = None
        self.client: Optional[httpx.Client] = None

    def connect(self, endpoint: str) -> bool:
        self.endpoint = endpoint
        self.client = httpx.Client(timeout=15.0)
        try:
            # Test SSE channel connectivity
            res = self.client.get(f"{endpoint}/sse", headers={"Accept": "text/event-stream"})
            return res.status_code == 200
        except Exception:
            return False

    def send_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        if not self.client or not self.endpoint:
            raise RuntimeError("SSE Transport not connected.")
        
        if "jsonrpc" not in message:
            message["jsonrpc"] = "2.0"
            
        try:
            # Send payload via POST channel mapping SSE session
            res = self.client.post(f"{self.endpoint}/message", json=message)
            if res.status_code == 200:
                return res.json()
            return {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "error": {"code": -32603, "message": f"SSE message delivery failed: {res.status_code}"}
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "error": {"code": -32603, "message": f"SSE Transport Error: {str(e)}"}
            }

    def close(self) -> None:
        if self.client:
            self.client.close()
