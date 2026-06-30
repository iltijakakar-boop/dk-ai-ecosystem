from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.mcp_models import MCPServer, MCPConnection, MCPClient
from app.services.mcp_transport import HTTPTransport, SSETransport, MCPTransport


class MCPService:
    def __init__(self):
        # Local connection pool to maintain active transports in memory
        self.active_transports: Dict[int, MCPTransport] = {}

    def register_server(self, db: Session, *, workspace_id: int, name: str, url: str) -> MCPServer:
        server = MCPServer(
            workspace_id=workspace_id,
            name=name,
            url=url,
            status="offline"
        )
        db.add(server)
        db.commit()
        db.refresh(server)
        return server

    def get_servers(self, db: Session, workspace_id: int) -> List[MCPServer]:
        return db.query(MCPServer).filter(MCPServer.workspace_id == workspace_id).all()

    def get_server(self, db: Session, server_id: int) -> Optional[MCPServer]:
        return db.query(MCPServer).filter(MCPServer.id == server_id).first()

    def establish_connection(self, db: Session, *, server_id: int) -> MCPConnection:
        server = self.get_server(db, server_id)
        if not server:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MCP Server not found.")

        # Pluggable Transport Abstraction Selection
        # Choose transport based on endpoint prefix/scheme (e.g. sse-endpoint versus standard rest)
        transport: MCPTransport
        conn_type = "sse" if "/sse" in server.url else "http"
        
        if conn_type == "sse":
            transport = SSETransport()
        else:
            transport = HTTPTransport()

        # Connect
        connected = transport.connect(server.url)
        if connected:
            server.status = "online"
            self.active_transports[server.id] = transport
        else:
            server.status = "offline"
        db.commit()

        # Register Connection log in DB
        conn = MCPConnection(
            workspace_id=server.workspace_id,
            server_id=server.id,
            connection_type=conn_type,
            status="connected" if connected else "failed"
        )
        db.add(conn)
        db.commit()
        db.refresh(conn)
        return conn

    def get_connection(self, server_id: int) -> Optional[MCPTransport]:
        return self.active_transports.get(server_id)

    def ping_heartbeat(self, db: Session, *, server_id: int) -> bool:
        transport = self.get_connection(server_id)
        server = self.get_server(db, server_id)
        if not server:
            return False

        if not transport:
            # Try to reconnect
            try:
                self.establish_connection(db, server_id=server_id)
                transport = self.get_connection(server_id)
            except Exception:
                return False

        if transport:
            # Heartbeat JSON-RPC ping request
            ping_msg = {"jsonrpc": "2.0", "method": "ping", "params": {}, "id": 999}
            res = transport.send_message(ping_msg)
            if "error" not in res:
                server.status = "online"
                db.commit()
                return True

        server.status = "offline"
        db.commit()
        return False


mcp_service = MCPService()
