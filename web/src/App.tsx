import React, { useState, useEffect } from "react";

interface Node {
  id: string;
  type: string;
  label: string;
  config: Record<string, any>;
  x: number;
  y: number;
  status?: string; // 'pending', 'executing', 'completed'
}

interface Edge {
  id: string;
  source: string;
  target: string;
}

interface Deployment {
  id: number;
  version: number;
  environment: string;
  status: string;
  timestamp: string;
}

interface MCPServer {
  id: number;
  name: string;
  url: string;
  status: string; // 'online', 'offline', 'pinging'
}

interface Connector {
  id: number;
  name: string;
  type: string;
  enabled: boolean;
  configured: boolean;
}

interface Webhook {
  id: number;
  url: string;
  events: string[];
  status: string;
}

interface ModelItem {
  id: number;
  name: string;
  version: string;
  status: string;
  environment: string;
}

interface GPUWorker {
  id: number;
  name: string;
  load: number;
}

// Sprint 018 Observability types
interface LogEntry {
  id: number;
  level: string;
  message: string;
  time: string;
}

interface AlertEntry {
  id: number;
  message: string;
  severity: string;
  status: string;
}

interface TraceEntry {
  id: number;
  span: string;
  duration: number;
  status: string;
}

// Sprint 019 Infrastructure types
interface ClusterItem {
  id: number;
  name: string;
  endpoint: string;
  status: string;
}

interface PodItem {
  id: number;
  name: string;
  status: string;
  cores: number;
}

interface EdgeNodeItem {
  id: number;
  name: string;
  status: string;
  sync: string;
}

// Sprint 020 DevOps types
interface PipelineItem {
  id: number;
  name: string;
  status: string;
  runCount: number;
}

interface ArtifactItem {
  id: number;
  name: string;
  tag: string;
  digest: string;
}

interface ApprovalItem {
  id: number;
  title: string;
  version: string;
  status: string;
}

// Sprint 021 Data Platform types
interface DPDatasetItem {
  id: number;
  name: string;
  format: string;
  quality: number;
}

interface DPFeatureGroupItem {
  id: number;
  name: string;
  entity: string;
  featuresCount: number;
}

interface DPSearchMatch {
  id: string;
  score: number;
  text: string;
}

// Sprint 022 Identity & IAM types
interface SSOProviderItem {
  id: number;
  name: string;
  type: string;
  enabled: boolean;
}

interface SessionItem {
  id: number;
  user: string;
  ip: string;
  device: string;
  active: boolean;
}

export default function App() {
  // Navigation active view: 'studio', 'mcp', 'multimodal', 'models', 'observability', 'infrastructure', 'devops', 'dataplatform', 'identity'
  const [activeView, setActiveView] = useState<string>("studio");

  // Preseeded default nodes for visual designer
  const [nodes, setNodes] = useState<Node[]>([
    {
      id: "node_start",
      type: "trigger",
      label: "Start Node",
      config: { trigger_type: "Webhook" },
      x: 100,
      y: 200,
      status: "pending",
    },
    {
      id: "node_prompt",
      type: "prompt",
      label: "Generate Summary",
      config: {
        template: "Summarize the customer request: {user_input}",
        variables: ["user_input"],
      },
      x: 350,
      y: 120,
      status: "pending",
    },
    {
      id: "node_agent",
      type: "agent",
      label: "Coding Agent",
      config: {
        model: "gpt-4o",
        temperature: 0.2,
        system_prompt: "You are an AI developer. Write code conforming to standards.",
      },
      x: 350,
      y: 280,
      status: "pending",
    },
    {
      id: "node_end",
      type: "output",
      label: "End Node",
      config: { output_format: "JSON" },
      x: 650,
      y: 200,
      status: "pending",
    },
  ]);

  const [edges] = useState<Edge[]>([
    { id: "e1", source: "node_start", target: "node_prompt" },
    { id: "e2", source: "node_start", target: "node_agent" },
    { id: "e3", source: "node_prompt", target: "node_end" },
    { id: "e4", source: "node_agent", target: "node_end" },
  ]);

  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>("console");
  const [logs, setLogs] = useState<string[]>([
    "[System] Visual AI Studio initialized.",
    "[Workspace] Scoped to Organization: 'Default' | Workspace: 'Main Workspace'.",
  ]);
  const [deployments, setDeployments] = useState<Deployment[]>([
    { id: 101, version: 1, environment: "Testing", status: "Active", timestamp: "2026-06-30T14:30:00Z" },
    { id: 102, version: 2, environment: "Staging", status: "Active", timestamp: "2026-06-30T15:10:00Z" },
  ]);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [draggedNodeType, setDraggedNodeType] = useState<string | null>(null);
  
  // Prompt studio versions comparison state
  const [promptInput, setPromptInput] = useState<string>("Make it extra creative.");
  const [renderedA, setRenderedA] = useState<string>("");
  const [renderedB, setRenderedB] = useState<string>("");

  // MCP Integration Hub states
  const [mcpServers, setMcpServers] = useState<MCPServer[]>([
    { id: 1, name: "Gemini Search Tool Server", url: "http://localhost:5001/mcp", status: "online" },
    { id: 2, name: "Local File System Server", url: "http://localhost:5002/mcp", status: "offline" },
  ]);

  const [connectors, setConnectors] = useState<Connector[]>([
    { id: 1, name: "Google Gemini AI", type: "gemini", enabled: true, configured: true },
    { id: 2, name: "Slack Alerts Messenger", type: "slack", enabled: true, configured: true },
    { id: 3, name: "GitHub Repository Hook", type: "github", enabled: false, configured: false },
    { id: 4, name: "PostgreSQL Database Vector", type: "postgres", enabled: true, configured: true },
  ]);

  const [webhooks] = useState<Webhook[]>([
    { id: 1, url: "https://callback.domain.com/inbox", events: ["agent_finished"], status: "Active" },
    { id: 2, url: "https://analytics-service.local/webhook", events: ["workflow_completed"], status: "Active" },
  ]);

  const [isConfiguringConnector, setIsConfiguringConnector] = useState<number | null>(null);
  const [tempApiKey, setTempApiKey] = useState<string>("");

  // Multi-Modal state
  const [multiModalTab, setMultiModalTab] = useState<string>("image");
  const [imagePrompt, setImagePrompt] = useState<string>("An astronaut riding a horse on Mars");
  const [isGeneratingImage, setIsGeneratingImage] = useState<boolean>(false);
  const [generatedImg, setGeneratedImg] = useState<string>("");
  const [ocrResult, setOcrResult] = useState<string>("");
  const [ttsText, setTtsText] = useState<string>("Hello, welcome to the speech synthesis platform.");
  const [isSynthesizing, setIsSynthesizing] = useState<boolean>(false);
  const [synthesizedAudio, setSynthesizedAudio] = useState<string>("");

  // Model Registry states
  const [modelTab, setModelTab] = useState<string>("models");
  const [models] = useState<ModelItem[]>([
    { id: 1, name: "Llama-3-8B-Custom", version: "v1.2.0", status: "Ready", environment: "Production" },
    { id: 2, name: "Gemini-1.5-Pro-Lora", version: "v2.1.0-alpha", status: "Testing", environment: "Staging" },
  ]);
  const [gpuWorkers] = useState<GPUWorker[]>([
    { id: 1, name: "GPU-Worker-Node01-A100", load: 42.5 },
    { id: 2, name: "GPU-Worker-Node02-H100", load: 12.0 },
  ]);
  const [fineTuningLogs, setFineTuningLogs] = useState<string[]>([
    "Training log stream initialized...",
  ]);
  const [isTraining, setIsTraining] = useState<boolean>(false);

  // Sprint 018 Observability states
  const [obsTab, setObsTab] = useState<string>("logs");
  const [systemMetrics] = useState({ cpu: 45.2, memory: 62.1, network: 14.5 });
  const [obsLogs] = useState<LogEntry[]>([
    { id: 1, level: "INFO", message: "User workspace resolved mapping main context.", time: "18:10:02" },
    { id: 2, level: "WARNING", message: "Intrusion threshold warning: rate limit breach alert.", time: "18:10:45" },
    { id: 3, level: "INFO", message: "Topological graph compile verification succeeded.", time: "18:11:12" },
  ]);
  const [obsAlerts] = useState<AlertEntry[]>([
    { id: 101, message: "Credential leak threat scan completed successfully.", severity: "INFO", status: "RESOLVED" },
    { id: 102, message: "Suspicious API rate limit breach warning on workspace 1.", severity: "WARNING", status: "ACTIVE" },
  ]);
  const [obsTraces] = useState<TraceEntry[]>([
    { id: 1, span: "POST /api/v1/agents/chat/run", duration: 185, status: "200 OK" },
    { id: 2, span: "SQL SELECT FROM mcp_servers", duration: 12, status: "200 OK" },
  ]);

  // Sprint 019 Infrastructure states
  const [infraTab, setInfraTab] = useState<string>("clusters");
  const [clusters] = useState<ClusterItem[]>([
    { id: 1, name: "k8s-prod-us-east", endpoint: "https://10.150.0.1:6443", status: "healthy" },
    { id: 2, name: "k8s-staging-us-west", endpoint: "https://10.152.0.1:6443", status: "healthy" },
  ]);
  const [pods, setPods] = useState<PodItem[]>([
    { id: 1, name: "nginx-web-pod-0", status: "Running", cores: 0.5 },
    { id: 2, name: "nginx-web-pod-1", status: "Running", cores: 0.5 },
  ]);
  const [edgeNodes] = useState<EdgeNodeItem[]>([
    { id: 1, name: "jetson-nano-edge-01", status: "online", sync: "synced" },
    { id: 2, name: "raspberry-pi-edge-02", status: "offline", sync: "unsynced" },
  ]);
  const [backupPolicy, setBackupPolicy] = useState<string>("daily");
  const [isRestoring, setIsRestoring] = useState<boolean>(false);

  // Sprint 020 DevOps states
  const [devopsTab, setDevopsTab] = useState<string>("pipelines");
  const [pipelines] = useState<PipelineItem[]>([
    { id: 1, name: "production-ci-cd", status: "completed", runCount: 14 },
    { id: 2, name: "staging-pr-builder", status: "completed", runCount: 42 },
  ]);
  const [artifacts] = useState<ArtifactItem[]>([
    { id: 1, name: "dk-ai-agent-core", tag: "latest", digest: "sha256:4a58ff01" },
    { id: 2, name: "dk-ai-builder-web", tag: "v1.2.0", digest: "sha256:bb52ac02" },
  ]);
  const [approvals, setApprovals] = useState<ApprovalItem[]>([
    { id: 1, title: "Promote v2.0.0-rc to Production", version: "v2.0.0-rc", status: "PENDING" },
  ]);
  const [isPipelineRunning, setIsPipelineRunning] = useState<boolean>(false);
  const [pipelineStep, setPipelineStep] = useState<number>(0);

  // Sprint 021 Data Platform states
  const [dpTab, setDpTab] = useState<string>("lakehouse");
  const [dpDatasets] = useState<DPDatasetItem[]>([
    { id: 1, name: "customer_reviews_lakehouse", format: "parquet", quality: 98.5 },
    { id: 2, name: "raw_clickstream_logs", format: "csv", quality: 92.0 },
  ]);
  const [dpFeatureGroups] = useState<DPFeatureGroupItem[]>([
    { id: 1, name: "user_behavior_features", entity: "User", featuresCount: 4 },
    { id: 2, name: "workspace_usage_aggregates", entity: "Workspace", featuresCount: 12 },
  ]);
  const [vectorSearchQuery, setVectorSearchQuery] = useState<string>("agent canvas layout coordinate");
  const [vectorResults, setVectorResults] = useState<DPSearchMatch[]>([]);
  const [isSearchingVectors, setIsSearchingVectors] = useState<boolean>(false);

  // Sprint 022 Identity & IAM states
  const [iamTab, setIamTab] = useState<string>("providers");
  const [ssoProviders, setSsoProviders] = useState<SSOProviderItem[]>([
    { id: 1, name: "Google Workspace OIDC", type: "OIDC", enabled: true },
    { id: 2, name: "Okta Enterprise IDP", type: "SAML 2.0", enabled: false },
    { id: 3, name: "Keycloak Federation", type: "OAuth2", enabled: true },
  ]);
  const [sessions, setSessions] = useState<SessionItem[]>([
    { id: 1, user: "admin@example.com", ip: "192.168.1.102", device: "Chrome / macOS", active: true },
    { id: 2, user: "developer@example.com", ip: "10.0.4.15", device: "Firefox / Linux", active: true },
  ]);
  const [policyMfa, setPolicyMfa] = useState<boolean>(true);
  const [policyDeviceTrust, setPolicyDeviceTrust] = useState<boolean>(false);
  const [passkeyStatus, setPasskeyStatus] = useState<string>("Register device passkey to activate passwordless access.");

  const selectedNode = nodes.find((n) => n.id === selectedNodeId);

  // Drag and drop new nodes handler
  const handleDragStart = (type: string) => {
    setDraggedNodeType(type);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (!draggedNodeType) return;

    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left - 100;
    const y = e.clientY - rect.top - 25;

    const newNodeId = `node_${Date.now()}`;
    const newNode: Node = {
      id: newNodeId,
      type: draggedNodeType,
      label: `New ${draggedNodeType.toUpperCase()}`,
      config: draggedNodeType === "agent" ? { model: "gpt-4o", temperature: 0.7 } : {},
      x,
      y,
      status: "pending",
    };

    setNodes((prev) => [...prev, newNode]);
    setLogs((prev) => [...prev, `[Canvas] Added new node: ${newNode.label}`]);
    setDraggedNodeType(null);
  };

  // Run debug play simulation
  const runDebuggerSimulation = async () => {
    if (isRunning) return;
    setIsRunning(true);
    setLogs((prev) => [...prev, "[Debugger] Initiating visual execution testing session..."]);

    const executionOrder = ["node_start", "node_prompt", "node_agent", "node_end"];

    for (const nodeId of executionOrder) {
      setNodes((prev) =>
        prev.map((n) => (n.id === nodeId ? { ...n, status: "executing" } : n))
      );
      setLogs((prev) => [...prev, `[Debugger] Executing node: '${nodeId}'...`]);
      await new Promise((resolve) => setTimeout(resolve, 1000));
      setNodes((prev) =>
        prev.map((n) => (n.id === nodeId ? { ...n, status: "completed" } : n))
      );
      setLogs((prev) => [...prev, `[Debugger] Node '${nodeId}' completed successfully.`]);
    }

    setIsRunning(false);
    setLogs((prev) => [...prev, "[Debugger] Execution session finished. Result output saved."]);
  };

  // Visual compile and deploy handler
  const handleDeploy = () => {
    const nextVer = deployments.length + 1;
    const newDep: Deployment = {
      id: Date.now(),
      version: nextVer,
      environment: "Production",
      status: "Active",
      timestamp: new Date().toISOString(),
    };
    setDeployments((prev) => [newDep, ...prev]);
    setLogs((prev) => [...prev, `[Deployment] Visual canvas successfully compiled and deployed as Version ${nextVer} to Production.`]);
  };

  // Rollback deploy handler
  const handleRollback = (id: number) => {
    setDeployments((prev) =>
      prev.map((d) => (d.id === id ? { ...d, status: "RolledBack" } : d))
    );
    setLogs((prev) => [...prev, `[Deployment] Rolled back deployment ID ${id} to historical version.`]);
  };

  // Ping heartbeat server simulation
  const pingMcpServer = async (id: number) => {
    setMcpServers((prev) =>
      prev.map((s) => (s.id === id ? { ...s, status: "pinging" } : s))
    );
    setLogs((prev) => [...prev, `[MCP Hub] Querying server heartbeat handshake (ID: ${id})...`]);
    await new Promise((resolve) => setTimeout(resolve, 800));
    setMcpServers((prev) =>
      prev.map((s) => (s.id === id ? { ...s, status: "online" } : s))
    );
    setLogs((prev) => [...prev, `[MCP Hub] Heartbeat handshake returned: Status ONLINE (200 OK).`]);
  };

  // Toggle connector enabled status
  const handleToggleConnector = (id: number, val: boolean) => {
    setConnectors((prev) =>
      prev.map((c) => (c.id === id ? { ...c, enabled: val } : c))
    );
    setLogs((prev) => [...prev, `[MCP Hub] Connector ID ${id} toggled state: ${val ? "ENABLED" : "DISABLED"}`]);
  };

  // Save integration credentials
  const saveCredentials = () => {
    if (isConfiguringConnector === null) return;
    setConnectors((prev) =>
      prev.map((c) => (c.id === isConfiguringConnector ? { ...c, configured: true } : c))
    );
    setLogs((prev) => [
      ...prev,
      `[MCP Hub] Decrypted API key and credentials successfully encrypted and saved to database connection credentials table.`,
    ]);
    setIsConfiguringConnector(null);
    setTempApiKey("");
  };

  // Multi-Modal simulations
  const triggerImageGeneration = async () => {
    setIsGeneratingImage(true);
    setLogs((prev) => [...prev, `[Multi-Modal] Dispatching image generation request: "${imagePrompt}"...`]);
    await new Promise((resolve) => setTimeout(resolve, 1500));
    setGeneratedImg(`https://generated-images.local/astronaut_horse.png`);
    setLogs((prev) => [...prev, `[Multi-Modal] Image generation successful. Asset saved in Media Library.`]);
    setIsGeneratingImage(false);
  };

  const triggerOcr = () => {
    setOcrResult(`[OCR Extracted Text]\nINVOICE #10243\nDate: 2026-06-30\nTotal Amount: $500.00\nMerchant: Gemini Cloud Services\n[Extracted Metadata JSON]\n{\n  "invoice_id": "10243",\n  "total": "500.00",\n  "merchant": "Gemini Cloud Services"\n}`);
    setLogs((prev) => [...prev, `[Multi-Modal] OCR extraction completed for invoice document.`]);
  };

  const triggerTts = async () => {
    setIsSynthesizing(true);
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setSynthesizedAudio("Synthesized Audio Output Waveform (Simulated Playback)");
    setLogs((prev) => [...prev, `[Multi-Modal] Text-to-speech synthesis completed.`]);
    setIsSynthesizing(false);
  };

  // Model Tuning simulations
  const startFineTuningRun = async () => {
    setIsTraining(true);
    setFineTuningLogs((prev) => [...prev, "[Fine-Tune] Initializing Distributed PEFT LoRA training queue...", "[Fine-Tune] Allocating GPU worker resources..."]);
    await new Promise((resolve) => setTimeout(resolve, 800));
    setFineTuningLogs((prev) => [...prev, "[GPU] GPU worker Node01 (A100) status: Allocated.", "[Fine-Tune] Loading ShareGPT dataset, splitting train/test (90/10)..."]);
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setFineTuningLogs((prev) => [
      ...prev,
      "Epoch 1/3 - loss: 1.4582 - accuracy: 0.72",
      "Epoch 2/3 - loss: 0.9851 - accuracy: 0.84",
      "Epoch 3/3 - loss: 0.5420 - accuracy: 0.92",
      "[Fine-Tune] Training successfully completed. Model Checkpoint v1.3.0 saved in registry.",
    ]);
    setIsTraining(false);
  };

  // Infrastructure scaling simulator
  const handleScaleDeployment = (val: number) => {
    const newPods: PodItem[] = [];
    for (let i = 0; i < val; i++) {
      newPods.push({ id: i + 1, name: `nginx-web-pod-${i}`, status: "Running", cores: 0.5 });
    }
    setPods(newPods);
    setLogs((prev) => [...prev, `[Infra] Scaling deployment replicas count to: ${val}`]);
  };

  // Trigger snapshot restore
  const handleRestore = async () => {
    setIsRestoring(true);
    setLogs((prev) => [...prev, `[Infra] Initiating high availability cross-region backup restoration...`]);
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setLogs((prev) => [...prev, `[Infra] Restoration completed successfully. State synchronized.`]);
    setIsRestoring(false);
  };

  // Trigger CI/CD Pipeline stepper simulation
  const handleTriggerPipeline = async () => {
    if (isPipelineRunning) return;
    setIsPipelineRunning(true);
    setPipelineStep(1);
    setLogs((prev) => [...prev, `[DevOps] Triggering CI/CD pipeline production run...`]);
    
    for (let step = 2; step <= 5; step++) {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      setPipelineStep(step);
    }
    
    await new Promise((resolve) => setTimeout(resolve, 500));
    setIsPipelineRunning(false);
    setLogs((prev) => [...prev, `[DevOps] Pipeline run completed successfully. Images built.`]);
  };

  // Process approval gate action
  const handleProcessApproval = (id: number, approved: boolean) => {
    setApprovals((prev) =>
      prev.map((a) => (a.id === id ? { ...a, status: approved ? "APPROVED" : "REJECTED" } : a))
    );
    setLogs((prev) => [
      ...prev,
      `[DevOps] Production Change request ID ${id} was: ${approved ? "APPROVED" : "REJECTED"}`,
    ]);
  };

  // Similarity search simulation
  const triggerVectorSearch = async () => {
    setIsSearchingVectors(true);
    setLogs((prev) => [...prev, `[Data Platform] Processing similarity index search on vector index...`]);
    await new Promise((resolve) => setTimeout(resolve, 800));
    setVectorResults([
      { id: "doc_101", score: 0.942, text: "Visual Studio canvas nodes placement logic." },
      { id: "doc_205", score: 0.815, text: "Distributed Kubernetes service node replica scheduler." },
    ]);
    setIsSearchingVectors(false);
    setLogs((prev) => [...prev, `[Data Platform] Vector search query completed.`]);
  };

  // Toggle SSO state
  const handleToggleSSO = (id: number, val: boolean) => {
    setSsoProviders((prev) =>
      prev.map((p) => (p.id === id ? { ...p, enabled: val } : p))
    );
    setLogs((prev) => [...prev, `[IAM] Identity Provider ID ${id} enabled state toggled to: ${val}`]);
  };

  // Revoke IAM User session
  const handleRevokeSession = (id: number) => {
    setSessions((prev) =>
      prev.map((s) => (s.id === id ? { ...s, active: false } : s))
    );
    setLogs((prev) => [...prev, `[IAM] Revoked active token session ID: ${id}`]);
  };

  // Setup device WebAuthn passkey
  const handleRegisterPasskey = async () => {
    setPasskeyStatus("Generating WebAuthn Challenge keys...");
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setPasskeyStatus("Passkey registered. Credential ID: cred_abc_12345");
    setLogs((prev) => [...prev, `[IAM] Registered new device passkey credentials successfully.`]);
  };

  // Prompt Compare render simulator
  useEffect(() => {
    setRenderedA(`[Version 1] Rendered text with input: "${promptInput}"`);
    setRenderedB(`[Version 2] Senior review rendering: "${promptInput}"`);
  }, [promptInput]);

  return (
    <div className="app-container">
      {/* Header Panel */}
      <header className="header-bar">
        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          <div className="header-logo">DK AI Studio</div>
          <span style={{ fontSize: "12px", background: "#1b2336", padding: "4px 8px", borderRadius: "4px", color: "#9ca3af" }}>
            Workspace: Main Workspace
          </span>
          {/* Main Navigation Tabs */}
          <nav style={{ display: "flex", gap: "8px", marginLeft: "24px" }}>
            <button
              className={`btn ${activeView === "studio" ? "btn-primary" : "btn-secondary"}`}
              onClick={() => setActiveView("studio")}
              style={{ padding: "4px 12px", fontSize: "12px" }}
            >
              AI Studio Canvas
            </button>
            <button
              className={`btn ${activeView === "mcp" ? "btn-primary" : "btn-secondary"}`}
              onClick={() => setActiveView("mcp")}
              style={{ padding: "4px 12px", fontSize: "12px" }}
            >
              MCP Integration Hub
            </button>
            <button
              className={`btn ${activeView === "multimodal" ? "btn-primary" : "btn-secondary"}`}
              onClick={() => setActiveView("multimodal")}
              style={{ padding: "4px 12px", fontSize: "12px" }}
            >
              Multi-Modal Studio
            </button>
            <button
              className={`btn ${activeView === "models" ? "btn-primary" : "btn-secondary"}`}
              onClick={() => setActiveView("models")}
              style={{ padding: "4px 12px", fontSize: "12px" }}
            >
              Model Registry & Tuning
            </button>
            <button
              className={`btn ${activeView === "observability" ? "btn-primary" : "btn-secondary"}`}
              onClick={() => setActiveView("observability")}
              style={{ padding: "4px 12px", fontSize: "12px" }}
            >
              Observability Hub
            </button>
            <button
              className={`btn ${activeView === "infrastructure" ? "btn-primary" : "btn-secondary"}`}
              onClick={() => setActiveView("infrastructure")}
              style={{ padding: "4px 12px", fontSize: "12px" }}
            >
              Infrastructure Hub
            </button>
            <button
              className={`btn ${activeView === "devops" ? "btn-primary" : "btn-secondary"}`}
              onClick={() => setActiveView("devops")}
              style={{ padding: "4px 12px", fontSize: "12px" }}
            >
              DevOps Hub
            </button>
            <button
              className={`btn ${activeView === "dataplatform" ? "btn-primary" : "btn-secondary"}`}
              onClick={() => setActiveView("dataplatform")}
              style={{ padding: "4px 12px", fontSize: "12px" }}
            >
              Data Platform
            </button>
            <button
              className={`btn ${activeView === "identity" ? "btn-primary" : "btn-secondary"}`}
              onClick={() => setActiveView("identity")}
              style={{ padding: "4px 12px", fontSize: "12px" }}
            >
              IAM & Security
            </button>
          </nav>
        </div>
        {activeView === "studio" && (
          <div className="header-actions">
            <button className="btn btn-secondary" onClick={runDebuggerSimulation} disabled={isRunning}>
              {isRunning ? "Running..." : "▶ Run Debug Simulation"}
            </button>
            <button className="btn btn-primary" onClick={handleDeploy}>
              🚀 Compile & Deploy
            </button>
          </div>
        )}
      </header>

      {/* Conditional Rendering of Views */}
      {activeView === "studio" && (
        /* Visual Studio Builder View */
        <div className="studio-workspace">
          {/* Left Library Sidebar */}
          <aside className="sidebar-panel sidebar-left">
            <div className="panel-header">Node Library</div>
            <div className="panel-content">
              <p style={{ fontSize: "11px", color: "#9ca3af", marginBottom: "16px" }}>
                Drag nodes onto the canvas to construct your AI agent workflow:
              </p>
              <div className="node-library-item" draggable onDragStart={() => handleDragStart("agent")}>
                <span style={{ color: "#8b5cf6" }}>🤖</span> Agent Node
              </div>
              <div className="node-library-item" draggable onDragStart={() => handleDragStart("prompt")}>
                <span style={{ color: "#6366f1" }}>✍️</span> Prompt Node
              </div>
              <div className="node-library-item" draggable onDragStart={() => handleDragStart("tool")}>
                <span style={{ color: "#10b981" }}>🛠️</span> MCP Tool Node
              </div>
              <div className="node-library-item" draggable onDragStart={() => handleDragStart("router")}>
                <span style={{ color: "#f59e0b" }}>🔀</span> Router Node
              </div>
            </div>
          </aside>

          {/* Visual Graph Editor Canvas */}
          <main className="visual-canvas" onDragOver={(e) => e.preventDefault()} onDrop={handleDrop}>
            <svg className="edge-svg">
              {edges.map((edge) => {
                const srcNode = nodes.find((n) => n.id === edge.source);
                const tgtNode = nodes.find((n) => n.id === edge.target);
                if (!srcNode || !tgtNode) return null;
                
                const x1 = srcNode.x + 200;
                const y1 = srcNode.y + 35;
                const x2 = tgtNode.x;
                const y2 = tgtNode.y + 35;

                return (
                  <path
                    key={edge.id}
                    className={`edge-path ${srcNode.status === "completed" && tgtNode.status === "executing" ? "active" : ""}`}
                    d={`M ${x1} ${y1} C ${(x1 + x2) / 2} ${y1}, ${(x1 + x2) / 2} ${y2}, ${x2} ${y2}`}
                  />
                );
              })}
            </svg>

            {nodes.map((node) => {
              let typeColor = "var(--color-indigo)";
              if (node.type === "agent") typeColor = "var(--color-violet)";
              if (node.type === "tool") typeColor = "var(--color-emerald)";
              if (node.type === "trigger") typeColor = "var(--color-amber)";

              return (
                <div
                  key={node.id}
                  className={`canvas-node ${selectedNodeId === node.id ? "selected" : ""} ${node.status === "executing" ? "executing" : ""}`}
                  style={{
                    left: `${node.x}px`,
                    top: `${node.y}px`,
                    borderLeftColor: typeColor,
                  }}
                  onClick={() => setSelectedNodeId(node.id)}
                >
                  <div className="node-header">
                    <span>{node.label}</span>
                    <span className="node-type-tag">{node.type}</span>
                  </div>
                  <div className="node-content">
                    {node.type === "agent" && `Model: ${node.config.model || "gpt-4o"}`}
                    {node.type === "prompt" && "Template: Summary Chain"}
                    {node.type === "trigger" && `Event: ${node.config.trigger_type}`}
                    {node.type === "output" && "Format: JSON"}
                  </div>
                  {node.type !== "trigger" && <div className="node-port node-port-in" />}
                  {node.type !== "output" && <div className="node-port node-port-out" />}
                </div>
              );
            })}
          </main>

          {/* Right Properties Inspector */}
          <aside className="sidebar-panel">
            <div className="panel-header">Property Inspector</div>
            <div className="panel-content">
              {selectedNode ? (
                <div>
                  <h4 style={{ margin: "0 0 16px 0", color: "var(--color-violet)" }}>{selectedNode.label}</h4>
                  <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                    <div>
                      <label style={{ fontSize: "11px", color: "var(--text-secondary)" }}>Node Title</label>
                      <input
                        type="text"
                        className="btn"
                        style={{ background: "var(--bg-secondary)", border: "1px solid var(--border-color)", width: "90%", color: "white", padding: "6px", textAlign: "left" }}
                        value={selectedNode.label}
                        onChange={(e) => {
                          const val = e.target.value;
                          setNodes((prev) => prev.map((n) => (n.id === selectedNode.id ? { ...n, label: val } : n)));
                        }}
                      />
                    </div>

                    {selectedNode.type === "agent" && (
                      <>
                        <div>
                          <label style={{ fontSize: "11px", color: "var(--text-secondary)" }}>Model Selection</label>
                          <select
                            className="btn"
                            style={{ background: "var(--bg-secondary)", border: "1px solid var(--border-color)", width: "90%", color: "white", padding: "6px" }}
                            value={selectedNode.config.model}
                            onChange={(e) => {
                              const val = e.target.value;
                              setNodes((prev) =>
                                prev.map((n) =>
                                  n.id === selectedNode.id ? { ...n, config: { ...n.config, model: val } } : n
                                )
                              );
                            }}
                          >
                            <option value="gpt-4o">gpt-4o</option>
                            <option value="claude-3-5-sonnet">claude-3-5-sonnet</option>
                            <option value="gemini-1.5-pro">gemini-1.5-pro</option>
                          </select>
                        </div>
                        <div>
                          <label style={{ fontSize: "11px", color: "var(--text-secondary)" }}>System Prompt</label>
                          <textarea
                            rows={4}
                            style={{ background: "var(--bg-secondary)", border: "1px solid var(--border-color)", width: "90%", color: "white", padding: "6px", borderRadius: "6px" }}
                            value={selectedNode.config.system_prompt}
                            onChange={(e) => {
                              const val = e.target.value;
                              setNodes((prev) =>
                                prev.map((n) =>
                                  n.id === selectedNode.id ? { ...n, config: { ...n.config, system_prompt: val } } : n
                                )
                              );
                            }}
                          />
                        </div>
                      </>
                    )}
                  </div>
                </div>
              ) : (
                <p style={{ fontSize: "12px", color: "var(--text-secondary)", textAlign: "center", marginTop: "40px" }}>
                  Select a node to edit its parameters.
                </p>
              )}
            </div>
          </aside>
        </div>
      )}

      {activeView === "mcp" && (
        /* MCP Integration Hub View */
        <div className="studio-workspace" style={{ padding: "24px", display: "flex", gap: "24px", overflowY: "auto" }}>
          {/* Column 1: MCP Server Registry */}
          <div style={{ flex: 1, background: "var(--bg-secondary)", border: "1px solid var(--border-color)", borderRadius: "10px", padding: "16px", display: "flex", flexDirection: "column" }}>
            <h3 style={{ margin: "0 0 16px 0", borderBottom: "1px solid var(--border-color)", paddingBottom: "12px" }}>
              MCP Server Registry
            </h3>
            {mcpServers.map((srv) => (
              <div key={srv.id} style={{ background: "var(--bg-tertiary)", padding: "12px", borderRadius: "8px", border: "1px solid var(--border-color)", marginBottom: "12px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                  <strong style={{ fontSize: "14px" }}>{srv.name}</strong>
                  <span style={{
                    padding: "2px 8px",
                    borderRadius: "4px",
                    fontSize: "10px",
                    background: srv.status === "online" ? "rgba(16,185,129,0.15)" : srv.status === "pinging" ? "rgba(245,158,11,0.15)" : "rgba(244,63,94,0.15)",
                    color: srv.status === "online" ? "var(--color-emerald)" : srv.status === "pinging" ? "var(--color-amber)" : "var(--color-rose)"
                  }}>
                    {srv.status.toUpperCase()}
                  </span>
                </div>
                <div style={{ fontSize: "11px", color: "var(--text-secondary)", marginBottom: "8px" }}>
                  Endpoint: {srv.url}
                </div>
                <button className="btn btn-secondary" style={{ padding: "4px 10px", fontSize: "11px" }} onClick={() => pingMcpServer(srv.id)} disabled={srv.status === "pinging"}>
                  {srv.status === "pinging" ? "Pinging..." : "⚡ Ping Heartbeat"}
                </button>
              </div>
            ))}
          </div>

          {/* Column 2: Connectors Gallery */}
          <div style={{ flex: 1.2, background: "var(--bg-secondary)", border: "1px solid var(--border-color)", borderRadius: "10px", padding: "16px" }}>
            <h3 style={{ margin: "0 0 16px 0", borderBottom: "1px solid var(--border-color)", paddingBottom: "12px" }}>
              Official Connectors
            </h3>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
              {connectors.map((c) => (
                <div key={c.id} style={{ background: "var(--bg-tertiary)", padding: "12px", borderRadius: "8px", border: "1px solid var(--border-color)", display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
                  <div>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                      <strong style={{ fontSize: "13px" }}>{c.name}</strong>
                      <input
                        type="checkbox"
                        checked={c.enabled}
                        onChange={(e) => handleToggleConnector(c.id, e.target.checked)}
                      />
                    </div>
                    <span style={{ fontSize: "10px", background: "rgba(255,255,255,0.05)", padding: "2px 6px", borderRadius: "4px" }}>
                      Type: {c.type}
                    </span>
                  </div>
                  <div style={{ marginTop: "12px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span style={{ fontSize: "11px", color: c.configured ? "var(--color-emerald)" : "var(--color-rose)" }}>
                      {c.configured ? "● Key Configured" : "○ Key Missing"}
                    </span>
                    <button className="btn btn-secondary" style={{ padding: "2px 8px", fontSize: "11px" }} onClick={() => setIsConfiguringConnector(c.id)}>
                      Configure
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Column 3: Webhooks & Stats */}
          <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: "24px" }}>
            <div style={{ background: "var(--bg-secondary)", border: "1px solid var(--border-color)", borderRadius: "10px", padding: "16px" }}>
              <h4 style={{ margin: "0 0 12px 0", borderBottom: "1px solid var(--border-color)", paddingBottom: "8px" }}>
                Webhook Endpoints
              </h4>
              {webhooks.map((h) => (
                <div key={h.id} style={{ background: "var(--bg-tertiary)", padding: "8px", borderRadius: "6px", border: "1px solid var(--border-color)", marginBottom: "8px", fontSize: "11px" }}>
                  <div>URL: {h.url}</div>
                  <div style={{ color: "var(--text-secondary)", marginTop: "4px" }}>Events: {h.events.join(", ")}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeView === "multimodal" && (
        /* Multi-Modal Studio View */
        <div className="studio-workspace" style={{ padding: "24px", display: "flex", gap: "24px", overflowY: "auto" }}>
          <div style={{ width: "220px", background: "var(--bg-secondary)", border: "1px solid var(--border-color)", borderRadius: "10px", padding: "16px", display: "flex", flexDirection: "column", gap: "8px" }}>
            <button className={`btn ${multiModalTab === "image" ? "btn-primary" : "btn-secondary"}`} onClick={() => setMultiModalTab("image")}>
              🎨 Image Generator
            </button>
            <button className={`btn ${multiModalTab === "ocr" ? "btn-primary" : "btn-secondary"}`} onClick={() => setMultiModalTab("ocr")}>
              📄 OCR Document AI
            </button>
            <button className={`btn ${multiModalTab === "speech" ? "btn-primary" : "btn-secondary"}`} onClick={() => setMultiModalTab("speech")}>
              🔊 Speech Studio
            </button>
          </div>

          <div style={{ flex: 1, background: "var(--bg-secondary)", border: "1px solid var(--border-color)", borderRadius: "10px", padding: "24px" }}>
            {multiModalTab === "image" && (
              <div>
                <h3>Text-to-Image Generator</h3>
                <div style={{ display: "flex", flexDirection: "column", gap: "12px", marginTop: "16px" }}>
                  <textarea
                    rows={3}
                    style={{ background: "var(--bg-tertiary)", border: "1px solid var(--border-color)", color: "white", padding: "8px", borderRadius: "6px" }}
                    value={imagePrompt}
                    onChange={(e) => setImagePrompt(e.target.value)}
                  />
                  <button className="btn btn-primary" onClick={triggerImageGeneration} disabled={isGeneratingImage}>
                    {isGeneratingImage ? "Generating..." : "Generate Image"}
                  </button>

                  {generatedImg && (
                    <div style={{ border: "2px dashed var(--border-color)", padding: "16px", borderRadius: "8px", display: "flex", justifyContent: "center", alignItems: "center" }}>
                      <div style={{ width: "200px", height: "200px", background: "linear-gradient(135deg, var(--color-indigo), var(--color-violet))", borderRadius: "8px", display: "flex", justifyContent: "center", alignItems: "center", color: "white", fontSize: "12px" }}>
                        Generated Image Preview
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {multiModalTab === "ocr" && (
              <div>
                <h3>OCR Document Studio</h3>
                <div style={{ display: "flex", flexDirection: "column", gap: "12px", marginTop: "16px" }}>
                  <button className="btn btn-primary" onClick={triggerOcr}>
                    📄 Upload Invoice & Parse OCR
                  </button>

                  {ocrResult && (
                    <pre style={{ background: "#07090e", border: "1px solid var(--border-color)", padding: "12px", borderRadius: "6px", color: "#10b981", fontSize: "11px", overflowX: "auto" }}>
                      {ocrResult}
                    </pre>
                  )}
                </div>
              </div>
            )}

            {multiModalTab === "speech" && (
              <div>
                <h3>Speech Synthesis (Text-to-Speech)</h3>
                <div style={{ display: "flex", flexDirection: "column", gap: "12px", marginTop: "16px" }}>
                  <input
                    type="text"
                    className="btn"
                    style={{ background: "var(--bg-tertiary)", border: "1px solid var(--border-color)", color: "white", padding: "8px", textAlign: "left" }}
                    value={ttsText}
                    onChange={(e) => setTtsText(e.target.value)}
                  />
                  <button className="btn btn-primary" onClick={triggerTts} disabled={isSynthesizing}>
                    {isSynthesizing ? "Synthesizing..." : "🔊 Synthesize Speech"}
                  </button>

                  {synthesizedAudio && (
                    <div style={{ background: "rgba(16,185,129,0.1)", border: "1px solid var(--color-emerald)", padding: "12px", borderRadius: "6px", color: "var(--color-emerald)", fontSize: "12px" }}>
                      🔊 {synthesizedAudio}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {activeView === "models" && (
        /* Model Registry & Fine-Tuning View */
        <div className="studio-workspace" style={{ padding: "24px", display: "flex", gap: "24px", overflowY: "auto" }}>
          <div style={{ width: "220px", background: "var(--bg-secondary)", border: "1px solid var(--border-color)", borderRadius: "10px", padding: "16px", display: "flex", flexDirection: "column", gap: "8px" }}>
            <button className={`btn ${modelTab === "models" ? "btn-primary" : "btn-secondary"}`} onClick={() => setModelTab("models")}>
              📦 Model Registry
            </button>
            <button className={`btn ${modelTab === "tuning" ? "btn-primary" : "btn-secondary"}`} onClick={() => setModelTab("tuning")}>
              ⚙️ Fine-Tuning Console
            </button>
            <button className={`btn ${modelTab === "gpu" ? "btn-primary" : "btn-secondary"}`} onClick={() => setModelTab("gpu")}>
              🖥️ GPU Workers Monitor
            </button>
          </div>

          <div style={{ flex: 1, background: "var(--bg-secondary)", border: "1px solid var(--border-color)", borderRadius: "10px", padding: "24px" }}>
            {modelTab === "models" && (
              <div>
                <h3>Model Registry Catalog</h3>
                <table style={{ width: "100%", borderCollapse: "collapse", color: "var(--text-secondary)", marginTop: "16px" }}>
                  <thead>
                    <tr style={{ borderBottom: "1px solid var(--border-color)", textAlign: "left" }}>
                      <th style={{ padding: "8px" }}>Model Name</th>
                      <th style={{ padding: "8px" }}>Version</th>
                      <th style={{ padding: "8px" }}>Target Env</th>
                      <th style={{ padding: "8px" }}>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {models.map((m) => (
                      <tr key={m.id} style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
                        <td style={{ padding: "8px", color: "white" }}>{m.name}</td>
                        <td style={{ padding: "8px" }}>{m.version}</td>
                        <td style={{ padding: "8px" }}>{m.environment}</td>
                        <td style={{ padding: "8px", color: "var(--color-emerald)" }}>{m.status}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {modelTab === "tuning" && (
              <div>
                <h3>Fine-Tuning Execution</h3>
                <button className="btn btn-primary" onClick={startFineTuningRun} disabled={isTraining}>
                  {isTraining ? "Training in progress..." : "🚀 Launch Fine-Tuning Job"}
                </button>
                <div style={{ marginTop: "16px", background: "#07090e", padding: "16px", borderRadius: "8px", border: "1px solid var(--border-color)", fontFamily: "monospace", fontSize: "11px", height: "200px", overflowY: "auto", color: "#10b981" }}>
                  {fineTuningLogs.map((log, idx) => (
                    <div key={idx} style={{ marginBottom: "6px" }}>{log}</div>
                  ))}
                </div>
              </div>
            )}

            {modelTab === "gpu" && (
              <div>
                <h3>GPU Scheduler Workers</h3>
                {gpuWorkers.map((g) => (
                  <div key={g.id} style={{ background: "var(--bg-tertiary)", padding: "16px", borderRadius: "8px", border: "1px solid var(--border-color)", marginBottom: "12px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
                      <strong>{g.name}</strong>
                      <span style={{ color: "var(--color-indigo)" }}>{g.load}% Load</span>
                    </div>
                    <div style={{ height: "6px", background: "var(--border-color)", borderRadius: "3px" }}>
                      <div style={{ height: "100%", width: `${g.load}%`, background: "var(--color-indigo)", borderRadius: "3px" }} />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {activeView === "observability" && (
        /* Sprint 018: Observability & Security Dashboard View */
        <div className="studio-workspace" style={{ padding: "24px", display: "flex", gap: "24px", overflowY: "auto" }}>
          {/* Sub Navigation Left Column */}
          <div style={{ width: "220px", background: "var(--bg-secondary)", border: "1px solid var(--border-color)", borderRadius: "10px", padding: "16px", display: "flex", flexDirection: "column", gap: "8px" }}>
            <button className={`btn ${obsTab === "logs" ? "btn-primary" : "btn-secondary"}`} onClick={() => setObsTab("logs")}>
              📋 Log Explorer
            </button>
            <button className={`btn ${obsTab === "traces" ? "btn-primary" : "btn-secondary"}`} onClick={() => setObsTab("traces")}>
              ⏱️ Traces Viewer
            </button>
            <button className={`btn ${obsTab === "security" ? "btn-primary" : "btn-secondary"}`} onClick={() => setObsTab("security")}>
              🛡️ Security Center
            </button>
          </div>

          {/* Sub Content Area */}
          <div style={{ flex: 1, background: "var(--bg-secondary)", border: "1px solid var(--border-color)", borderRadius: "10px", padding: "24px" }}>
            {obsTab === "logs" && (
              <div>
                <h3>Structured Log Explorer</h3>
                <table style={{ width: "100%", borderCollapse: "collapse", color: "var(--text-secondary)", marginTop: "16px" }}>
                  <thead>
                    <tr style={{ borderBottom: "1px solid var(--border-color)", textAlign: "left" }}>
                      <th style={{ padding: "8px" }}>Time</th>
                      <th style={{ padding: "8px" }}>Level</th>
                      <th style={{ padding: "8px" }}>Message</th>
                    </tr>
                  </thead>
                  <tbody>
                    {obsLogs.map((log) => (
                      <tr key={log.id} style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
                        <td style={{ padding: "8px", color: "white" }}>{log.time}</td>
                        <td style={{ padding: "8px" }}>
                          <span style={{
                            padding: "2px 6px", borderRadius: "4px", fontSize: "10px",
                            background: log.level === "INFO" ? "rgba(16,185,129,0.15)" : "rgba(245,158,11,0.15)",
                            color: log.level === "INFO" ? "var(--color-emerald)" : "var(--color-amber)"
                          }}>{log.level}</span>
                        </td>
                        <td style={{ padding: "8px" }}>{log.message}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {obsTab === "traces" && (
              <div>
                <h3>Request Trace spans</h3>
                <div style={{ display: "flex", flexDirection: "column", gap: "16px", marginTop: "16px" }}>
                  {obsTraces.map((trace) => (
                    <div key={trace.id} style={{ background: "var(--bg-tertiary)", padding: "16px", borderRadius: "8px", border: "1px solid var(--border-color)" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px", fontSize: "13px" }}>
                        <strong>{trace.span}</strong>
                        <span>{trace.duration} ms</span>
                      </div>
                      <div style={{ height: "6px", background: "var(--border-color)", borderRadius: "3px" }}>
                        <div style={{ height: "100%", width: `${Math.min(100, (trace.duration / 300) * 100)}%`, background: "var(--color-emerald)", borderRadius: "3px" }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {obsTab === "security" && (
              <div>
                <h3>Security Center & Threats</h3>
                <div style={{ display: "flex", flexDirection: "column", gap: "12px", marginTop: "16px" }}>
                  {obsAlerts.map((alert) => (
                    <div key={alert.id} style={{ background: "var(--bg-tertiary)", padding: "12px", borderRadius: "8px", border: "1px solid var(--border-color)" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <strong>{alert.message}</strong>
                        <span style={{
                          padding: "2px 6px", borderRadius: "4px", fontSize: "10px",
                          background: alert.status === "ACTIVE" ? "rgba(244,63,94,0.15)" : "rgba(16,185,129,0.15)",
                          color: alert.status === "ACTIVE" ? "var(--color-rose)" : "var(--color-emerald)"
                        }}>{alert.status}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Metrics Right Column panel */}
          <div style={{ width: "260px", background: "var(--bg-secondary)", border: "1px solid var(--border-color)", borderRadius: "10px", padding: "16px", display: "flex", flexDirection: "column", gap: "20px" }}>
            <h4>Live System Metrics</h4>
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", marginBottom: "4px" }}>
                <span>CPU Load</span>
                <strong>{systemMetrics.cpu}%</strong>
              </div>
              <div style={{ height: "4px", background: "var(--border-color)", borderRadius: "2px" }}>
                <div style={{ height: "100%", width: `${systemMetrics.cpu}%`, background: "var(--color-indigo)", borderRadius: "2px" }} />
              </div>
            </div>
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", marginBottom: "4px" }}>
                <span>Memory load</span>
                <strong>{systemMetrics.memory}%</strong>
              </div>
              <div style={{ height: "4px", background: "var(--border-color)", borderRadius: "2px" }}>
                <div style={{ height: "100%", width: `${systemMetrics.memory}%`, background: "var(--color-violet)", borderRadius: "2px" }} />
              </div>
            </div>
          </div>
        </div>
      )}

      {activeView === "infrastructure" && (
        /* Sprint 019: Distributed Infrastructure & Kubernetes Hub View */
        <div className="studio-workspace" style={{ padding: "24px", display: "flex", gap: "24px", overflowY: "auto" }}>
          {/* Sub Navigation Left Column */}
          <div style={{ width: "220px", background: "var(--bg-secondary)", border: "1px solid var(--border-color)", borderRadius: "10px", padding: "16px", display: "flex", flexDirection: "column", gap: "8px" }}>
            <button className={`btn ${infraTab === "clusters" ? "btn-primary" : "btn-secondary"}`} onClick={() => setInfraTab("clusters")}>
              🌐 Clusters & Nodes
            </button>
            <button className={`btn ${infraTab === "edge" ? "btn-primary" : "btn-secondary"}`} onClick={() => setInfraTab("edge")}>
              📱 Edge AI Nodes
            </button>
            <button className={`btn ${infraTab === "recovery" ? "btn-primary" : "btn-secondary"}`} onClick={() => setInfraTab("recovery")}>
              💾 Backups & DR
            </button>
          </div>

          {/* Sub Content Area */}
          <div style={{ flex: 1, background: "var(--bg-secondary)", border: "1px solid var(--border-color)", borderRadius: "10px", padding: "24px" }}>
            {infraTab === "clusters" && (
              <div>
                <h3>Kubernetes Clusters Registry</h3>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginTop: "16px" }}>
                  {clusters.map((c) => (
                    <div key={c.id} style={{ background: "var(--bg-tertiary)", padding: "16px", borderRadius: "8px", border: "1px solid var(--border-color)" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
                        <strong>{c.name}</strong>
                        <span style={{ color: "var(--color-emerald)", fontSize: "11px" }}>● {c.status}</span>
                      </div>
                      <div style={{ fontSize: "11px", color: "var(--text-secondary)", marginBottom: "12px" }}>Endpoint: {c.endpoint}</div>
                    </div>
                  ))}
                </div>

                <h4 style={{ marginTop: "24px" }}>Active Microservice Pods Allocation</h4>
                <div style={{ display: "flex", flexDirection: "column", gap: "8px", marginTop: "12px" }}>
                  {pods.map((p) => (
                    <div key={p.id} style={{ background: "var(--bg-tertiary)", padding: "12px", borderRadius: "6px", border: "1px solid var(--border-color)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <span>{p.name}</span>
                      <div style={{ display: "flex", gap: "16px", fontSize: "12px", color: "var(--text-secondary)" }}>
                        <span>Allocated Cores: {p.cores}</span>
                        <span style={{ color: "var(--color-emerald)" }}>{p.status}</span>
                      </div>
                    </div>
                  ))}
                </div>

                <div style={{ marginTop: "16px", display: "flex", alignItems: "center", gap: "12px" }}>
                  <label style={{ fontSize: "12px" }}>Scale Web Replicas:</label>
                  <input
                    type="range" min="1" max="6" defaultValue={pods.length}
                    onChange={(e) => handleScaleDeployment(parseInt(e.target.value))}
                  />
                  <span>{pods.length} Pods</span>
                </div>
              </div>
            )}

            {infraTab === "edge" && (
              <div>
                <h3>Edge AI Devices</h3>
                <div style={{ display: "flex", flexDirection: "column", gap: "12px", marginTop: "16px" }}>
                  {edgeNodes.map((node) => (
                    <div key={node.id} style={{ background: "var(--bg-tertiary)", padding: "16px", borderRadius: "8px", border: "1px solid var(--border-color)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <div>
                        <strong>{node.name}</strong>
                        <div style={{ fontSize: "11px", color: "var(--text-secondary)" }}>Sync: {node.sync}</div>
                      </div>
                      <span style={{
                        padding: "2px 8px", borderRadius: "4px", fontSize: "10px",
                        background: node.status === "online" ? "rgba(16,185,129,0.15)" : "rgba(244,63,94,0.15)",
                        color: node.status === "online" ? "var(--color-emerald)" : "var(--color-rose)"
                      }}>{node.status.toUpperCase()}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {infraTab === "recovery" && (
              <div>
                <h3>Disaster Recovery Plan</h3>
                <div style={{ display: "flex", flexDirection: "column", gap: "16px", marginTop: "16px" }}>
                  <div>
                    <label style={{ display: "block", fontSize: "12px", marginBottom: "6px" }}>Backup Frequency:</label>
                    <select
                      className="btn" style={{ background: "var(--bg-tertiary)", border: "1px solid var(--border-color)", color: "white", padding: "6px 12px" }}
                      value={backupPolicy} onChange={(e) => setBackupPolicy(e.target.value)}
                    >
                      <option value="hourly">Hourly cross-region replication</option>
                      <option value="daily">Daily snapshot archives</option>
                    </select>
                  </div>
                  <button className="btn btn-primary" onClick={handleRestore} disabled={isRestoring}>
                    {isRestoring ? "Restoring backup state..." : "💾 Trigger Disaster Recovery Failover"}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {activeView === "devops" && (
        /* Sprint 020: DevOps & CI/CD Hub View */
        <div className="studio-workspace" style={{ padding: "24px", display: "flex", gap: "24px", overflowY: "auto" }}>
          {/* Sub Navigation Left Column */}
          <div style={{ width: "220px", background: "var(--bg-secondary)", border: "1px solid var(--border-color)", borderRadius: "10px", padding: "16px", display: "flex", flexDirection: "column", gap: "8px" }}>
            <button className={`btn ${devopsTab === "pipelines" ? "btn-primary" : "btn-secondary"}`} onClick={() => setDevopsTab("pipelines")}>
              ⚙️ CI/CD Pipelines
            </button>
            <button className={`btn ${devopsTab === "artifacts" ? "btn-primary" : "btn-secondary"}`} onClick={() => setDevopsTab("artifacts")}>
              📦 Artifact Registry
            </button>
            <button className={`btn ${devopsTab === "approvals" ? "btn-primary" : "btn-secondary"}`} onClick={() => setDevopsTab("approvals")}>
              🛡️ Release Gates
            </button>
          </div>

          {/* Sub Content Area */}
          <div style={{ flex: 1, background: "var(--bg-secondary)", border: "1px solid var(--border-color)", borderRadius: "10px", padding: "24px" }}>
            {devopsTab === "pipelines" && (
              <div>
                <h3>CI/CD Build Pipelines</h3>
                <div style={{ display: "flex", flexDirection: "column", gap: "16px", marginTop: "16px" }}>
                  {pipelines.map((p) => (
                    <div key={p.id} style={{ background: "var(--bg-tertiary)", padding: "16px", borderRadius: "8px", border: "1px solid var(--border-color)" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "12px" }}>
                        <strong>{p.name}</strong>
                        <span>Total Runs: {p.runCount}</span>
                      </div>
                      <button className="btn btn-primary" onClick={handleTriggerPipeline} disabled={isPipelineRunning}>
                        {isPipelineRunning ? "Running Pipeline..." : "⚡ Trigger Pipeline Execution"}
                      </button>

                      {isPipelineRunning && (
                        <div style={{ display: "flex", gap: "8px", marginTop: "16px" }}>
                          {["Commit", "Test", "Scan", "Deploy"].map((s, idx) => (
                            <div key={idx} style={{
                              flex: 1, padding: "8px", borderRadius: "4px", textAlign: "center", fontSize: "11px",
                              background: pipelineStep > idx ? "rgba(16,185,129,0.15)" : "rgba(255,255,255,0.05)",
                              color: pipelineStep > idx ? "var(--color-emerald)" : "var(--text-secondary)",
                              border: pipelineStep > idx ? "1px solid var(--color-emerald)" : "1px solid transparent"
                            }}>
                              {s}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {devopsTab === "artifacts" && (
              <div>
                <h3>Artifact & Container Image Registry</h3>
                <table style={{ width: "100%", borderCollapse: "collapse", color: "var(--text-secondary)", marginTop: "16px" }}>
                  <thead>
                    <tr style={{ borderBottom: "1px solid var(--border-color)", textAlign: "left" }}>
                      <th style={{ padding: "8px" }}>Image Name</th>
                      <th style={{ padding: "8px" }}>Tag</th>
                      <th style={{ padding: "8px" }}>Digest Hash</th>
                    </tr>
                  </thead>
                  <tbody>
                    {artifacts.map((art) => (
                      <tr key={art.id} style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
                        <td style={{ padding: "8px", color: "white" }}>{art.name}</td>
                        <td style={{ padding: "8px" }}>
                          <span style={{ background: "rgba(99,102,241,0.15)", color: "var(--color-indigo)", padding: "2px 6px", borderRadius: "4px", fontSize: "11px" }}>
                            {art.tag}
                          </span>
                        </td>
                        <td style={{ padding: "8px", fontFamily: "monospace" }}>{art.digest}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {devopsTab === "approvals" && (
              <div>
                <h3>Production Release Gates</h3>
                <div style={{ display: "flex", flexDirection: "column", gap: "12px", marginTop: "16px" }}>
                  {approvals.map((app) => (
                    <div key={app.id} style={{ background: "var(--bg-tertiary)", padding: "16px", borderRadius: "8px", border: "1px solid var(--border-color)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <div>
                        <strong>{app.title}</strong>
                        <div style={{ fontSize: "11px", color: "var(--text-secondary)", marginTop: "4px" }}>Target: {app.version}</div>
                      </div>
                      <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                        {app.status === "PENDING" ? (
                          <>
                            <button className="btn btn-secondary" style={{ padding: "4px 10px", fontSize: "11px", background: "rgba(244,63,94,0.1)", color: "var(--color-rose)" }} onClick={() => handleProcessApproval(app.id, false)}>
                              Reject
                            </button>
                            <button className="btn btn-primary" style={{ padding: "4px 10px", fontSize: "11px" }} onClick={() => handleProcessApproval(app.id, true)}>
                              Approve
                            </button>
                          </>
                        ) : (
                          <span style={{
                            padding: "2px 8px", borderRadius: "4px", fontSize: "10px",
                            background: app.status === "APPROVED" ? "rgba(16,185,129,0.15)" : "rgba(244,63,94,0.15)",
                            color: app.status === "APPROVED" ? "var(--color-emerald)" : "var(--color-rose)"
                          }}>{app.status}</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {activeView === "dataplatform" && (
        /* Sprint 021: AI Data Platform & Feature Store View */
        <div className="studio-workspace" style={{ padding: "24px", display: "flex", gap: "24px", overflowY: "auto" }}>
          {/* Sub Navigation Left Column */}
          <div style={{ width: "220px", background: "var(--bg-secondary)", border: "1px solid var(--border-color)", borderRadius: "10px", padding: "16px", display: "flex", flexDirection: "column", gap: "8px" }}>
            <button className={`btn ${dpTab === "lakehouse" ? "btn-primary" : "btn-secondary"}`} onClick={() => setDpTab("lakehouse")}>
              🗄️ Lakehouse Catalog
            </button>
            <button className={`btn ${dpTab === "features" ? "btn-primary" : "btn-secondary"}`} onClick={() => setDpTab("features")}>
              🧬 Feature Store
            </button>
            <button className={`btn ${dpTab === "vector" ? "btn-primary" : "btn-secondary"}`} onClick={() => setDpTab("vector")}>
              🔍 Vector Search index
            </button>
          </div>

          {/* Sub Content Area */}
          <div style={{ flex: 1, background: "var(--bg-secondary)", border: "1px solid var(--border-color)", borderRadius: "10px", padding: "24px" }}>
            {dpTab === "lakehouse" && (
              <div>
                <h3>Lakehouse Datasets</h3>
                <table style={{ width: "100%", borderCollapse: "collapse", color: "var(--text-secondary)", marginTop: "16px" }}>
                  <thead>
                    <tr style={{ borderBottom: "1px solid var(--border-color)", textAlign: "left" }}>
                      <th style={{ padding: "8px" }}>Dataset Name</th>
                      <th style={{ padding: "8px" }}>Format</th>
                      <th style={{ padding: "8px" }}>Data Quality Score</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dpDatasets.map((d) => (
                      <tr key={d.id} style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
                        <td style={{ padding: "8px", color: "white" }}>{d.name}</td>
                        <td style={{ padding: "8px" }}>{d.format}</td>
                        <td style={{ padding: "8px", color: "var(--color-emerald)" }}>{d.quality}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {dpTab === "features" && (
              <div>
                <h3>Feature Store Groups</h3>
                <table style={{ width: "100%", borderCollapse: "collapse", color: "var(--text-secondary)", marginTop: "16px" }}>
                  <thead>
                    <tr style={{ borderBottom: "1px solid var(--border-color)", textAlign: "left" }}>
                      <th style={{ padding: "8px" }}>Feature Group</th>
                      <th style={{ padding: "8px" }}>Primary Entity</th>
                      <th style={{ padding: "8px" }}>Features count</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dpFeatureGroups.map((g) => (
                      <tr key={g.id} style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
                        <td style={{ padding: "8px", color: "white" }}>{g.name}</td>
                        <td style={{ padding: "8px" }}>{g.entity}</td>
                        <td style={{ padding: "8px" }}>{g.featuresCount} columns</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {dpTab === "vector" && (
              <div>
                <h3>Vector Embedding Similarity Search</h3>
                <div style={{ display: "flex", gap: "8px", marginTop: "16px" }}>
                  <input
                    type="text" className="btn" style={{ background: "var(--bg-tertiary)", border: "1px solid var(--border-color)", color: "white", padding: "8px", width: "350px", textAlign: "left" }}
                    value={vectorSearchQuery} onChange={(e) => setVectorSearchQuery(e.target.value)}
                  />
                  <button className="btn btn-primary" onClick={triggerVectorSearch} disabled={isSearchingVectors}>
                    {isSearchingVectors ? "Querying..." : "Search Index"}
                  </button>
                </div>

                {vectorResults.length > 0 && (
                  <div style={{ display: "flex", flexDirection: "column", gap: "8px", marginTop: "20px" }}>
                    {vectorResults.map((r, idx) => (
                      <div key={idx} style={{ background: "var(--bg-tertiary)", padding: "12px", borderRadius: "6px", border: "1px solid var(--border-color)", display: "flex", justifyContent: "space-between" }}>
                        <span>{r.text}</span>
                        <strong style={{ color: "var(--color-indigo)" }}>Score: {r.score}</strong>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {activeView === "identity" && (
        /* Sprint 022: Identity, IAM, & Zero Trust Security View */
        <div className="studio-workspace" style={{ padding: "24px", display: "flex", gap: "24px", overflowY: "auto" }}>
          {/* Sub Navigation Left Column */}
          <div style={{ width: "220px", background: "var(--bg-secondary)", border: "1px solid var(--border-color)", borderRadius: "10px", padding: "16px", display: "flex", flexDirection: "column", gap: "8px" }}>
            <button className={`btn ${iamTab === "providers" ? "btn-primary" : "btn-secondary"}`} onClick={() => setIamTab("providers")}>
              🔑 SSO Providers
            </button>
            <button className={`btn ${iamTab === "policies" ? "btn-primary" : "btn-secondary"}`} onClick={() => setIamTab("policies")}>
              🛡️ Access Policies
            </button>
            <button className={`btn ${iamTab === "sessions" ? "btn-primary" : "btn-secondary"}`} onClick={() => setIamTab("sessions")}>
              ⏱️ Active Sessions
            </button>
            <button className={`btn ${iamTab === "passkeys" ? "btn-primary" : "btn-secondary"}`} onClick={() => setIamTab("passkeys")}>
              📱 Passkeys Setup
            </button>
          </div>

          {/* Sub Content Area */}
          <div style={{ flex: 1, background: "var(--bg-secondary)", border: "1px solid var(--border-color)", borderRadius: "10px", padding: "24px" }}>
            {iamTab === "providers" && (
              <div>
                <h3>Federated Single Sign-On (SSO) Providers</h3>
                <div style={{ display: "flex", flexDirection: "column", gap: "12px", marginTop: "16px" }}>
                  {ssoProviders.map((p) => (
                    <div key={p.id} style={{ background: "var(--bg-tertiary)", padding: "16px", borderRadius: "8px", border: "1px solid var(--border-color)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <div>
                        <strong>{p.name}</strong>
                        <div style={{ fontSize: "11px", color: "var(--text-secondary)", marginTop: "4px" }}>Protocol: {p.type}</div>
                      </div>
                      <input
                        type="checkbox" checked={p.enabled}
                        onChange={(e) => handleToggleSSO(p.id, e.target.checked)}
                      />
                    </div>
                  ))}
                </div>
              </div>
            )}

            {iamTab === "policies" && (
              <div>
                <h3>Conditional Access Policies (Zero Trust)</h3>
                <div style={{ display: "flex", flexDirection: "column", gap: "16px", marginTop: "16px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", background: "var(--bg-tertiary)", padding: "12px", borderRadius: "6px" }}>
                    <span>Enforce Multi-Factor Authentication (MFA)</span>
                    <input type="checkbox" checked={policyMfa} onChange={(e) => setPolicyMfa(e.target.checked)} />
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", background: "var(--bg-tertiary)", padding: "12px", borderRadius: "6px" }}>
                    <span>Enforce Device Trust Verification check</span>
                    <input type="checkbox" checked={policyDeviceTrust} onChange={(e) => setPolicyDeviceTrust(e.target.checked)} />
                  </div>
                </div>
              </div>
            )}

            {iamTab === "sessions" && (
              <div>
                <h3>Active User Sessions</h3>
                <div style={{ display: "flex", flexDirection: "column", gap: "12px", marginTop: "16px" }}>
                  {sessions.map((s) => (
                    <div key={s.id} style={{ background: "var(--bg-tertiary)", padding: "16px", borderRadius: "8px", border: "1px solid var(--border-color)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <div>
                        <strong>{s.user}</strong>
                        <div style={{ fontSize: "11px", color: "var(--text-secondary)", marginTop: "4px" }}>Device: {s.device} | IP: {s.ip}</div>
                      </div>
                      <div>
                        {s.active ? (
                          <button className="btn btn-secondary" style={{ background: "rgba(244,63,94,0.1)", color: "var(--color-rose)", padding: "4px 10px", fontSize: "11px" }} onClick={() => handleRevokeSession(s.id)}>
                            Revoke Device Access
                          </button>
                        ) : (
                          <span style={{ fontSize: "11px", color: "var(--text-secondary)" }}>REVOKED</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {iamTab === "passkeys" && (
              <div>
                <h3>FIDO2 Passkeys Setup</h3>
                <div style={{ display: "flex", flexDirection: "column", gap: "16px", marginTop: "16px" }}>
                  <p style={{ fontSize: "13px", color: "var(--text-secondary)" }}>{passkeyStatus}</p>
                  <button className="btn btn-primary" onClick={handleRegisterPasskey}>
                    🔑 Register Security Key / Passkey
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* frosted modal configuration dialog */}
      {isConfiguringConnector !== null && (
        <div style={{
          position: "fixed", top: 0, left: 0, width: "100vw", height: "100vh",
          background: "rgba(0,0,0,0.6)", backdropFilter: "blur(6px)",
          display: "flex", alignItems: "center", justifyContent: "center", zIndex: 100
        }}>
          <div style={{
            background: "var(--bg-secondary)", border: "1px solid var(--border-color)",
            borderRadius: "10px", width: "400px", padding: "24px", boxShadow: "0 10px 25px rgba(0,0,0,0.5)"
          }}>
            <h3 style={{ margin: "0 0 16px 0" }}>Configure Credentials</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              <div>
                <label style={{ fontSize: "11px", color: "var(--text-secondary)", display: "block", marginBottom: "4px" }}>
                  Decrypted Key / Bearer Access Token
                </label>
                <input
                  type="password"
                  className="btn"
                  style={{ background: "var(--bg-tertiary)", border: "1px solid var(--border-color)", width: "90%", color: "white", padding: "8px", textAlign: "left" }}
                  placeholder="Enter API credential key"
                  value={tempApiKey}
                  onChange={(e) => setTempApiKey(e.target.value)}
                />
              </div>
              <div style={{ display: "flex", gap: "12px", justifyContent: "flex-end", marginTop: "12px" }}>
                <button className="btn btn-secondary" onClick={() => setIsConfiguringConnector(null)}>Cancel</button>
                <button className="btn btn-primary" onClick={saveCredentials}>Encrypt & Save</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Bottom Console Panel */}
      {activeView === "studio" && (
        <footer className="bottom-console-panel">
          <div className="console-tabs">
            <div className={`console-tab ${activeTab === "console" ? "active" : ""}`} onClick={() => setActiveTab("console")}>
              Debug Console
            </div>
            <div className={`console-tab ${activeTab === "prompts" ? "active" : ""}`} onClick={() => setActiveTab("prompts")}>
              Prompt Studio Compare
            </div>
            <div className={`console-tab ${activeTab === "deployments" ? "active" : ""}`} onClick={() => setActiveTab("deployments")}>
              Deployments History
            </div>
          </div>
          
          <div className="console-body">
            {activeTab === "console" && (
              <div style={{ color: "#10b981", display: "flex", flexDirection: "column", gap: "6px" }}>
                {logs.map((log, idx) => (
                  <div key={idx}>{log}</div>
                ))}
              </div>
            )}

            {activeTab === "prompts" && (
              <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
                  <span style={{ color: "var(--text-secondary)" }}>Prompt Inputs:</span>
                  <input
                    type="text"
                    className="btn"
                    style={{ background: "#1b2336", border: "1px solid var(--border-color)", color: "white", padding: "4px 8px", width: "300px" }}
                    value={promptInput}
                    onChange={(e) => setPromptInput(e.target.value)}
                  />
                </div>
                <div style={{ display: "flex", gap: "24px" }}>
                  <div style={{ flex: 1, padding: "8px", background: "#0a0f18", border: "1px solid var(--border-color)", borderRadius: "6px" }}>
                    <h5 style={{ margin: "0 0 6px 0", color: "var(--color-indigo)" }}>Prompt A (Version 1)</h5>
                    <p style={{ color: "#d1d5db" }}>{renderedA}</p>
                  </div>
                  <div style={{ flex: 1, padding: "8px", background: "#0a0f18", border: "1px solid var(--border-color)", borderRadius: "6px" }}>
                    <h5 style={{ margin: "0 0 6px 0", color: "var(--color-violet)" }}>Prompt B (Version 2)</h5>
                    <p style={{ color: "#d1d5db" }}>{renderedB}</p>
                  </div>
                </div>
              </div>
            )}

            {activeTab === "deployments" && (
              <table style={{ width: "100%", borderCollapse: "collapse", color: "var(--text-secondary)" }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid var(--border-color)", textAlign: "left" }}>
                    <th style={{ padding: "8px" }}>ID</th>
                    <th style={{ padding: "8px" }}>Version</th>
                    <th style={{ padding: "8px" }}>Environment</th>
                    <th style={{ padding: "8px" }}>Status</th>
                    <th style={{ padding: "8px" }}>Timestamp</th>
                    <th style={{ padding: "8px" }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {deployments.map((d) => (
                    <tr key={d.id} style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
                      <td style={{ padding: "8px", color: "white" }}>{d.id}</td>
                      <td style={{ padding: "8px" }}>v{d.version}</td>
                      <td style={{ padding: "8px" }}>{d.environment}</td>
                      <td style={{ padding: "8px" }}>
                        <span style={{
                          padding: "2px 6px",
                          borderRadius: "4px",
                          fontSize: "11px",
                          background: d.status === "Active" ? "rgba(16,185,129,0.15)" : "rgba(244,63,94,0.15)",
                          color: d.status === "Active" ? "var(--color-emerald)" : "var(--color-rose)"
                        }}>
                          {d.status}
                        </span>
                      </td>
                      <td style={{ padding: "8px" }}>{d.timestamp}</td>
                      <td style={{ padding: "8px" }}>
                        {d.status === "Active" && (
                          <button
                            className="btn btn-secondary"
                            style={{ padding: "2px 8px", fontSize: "11px" }}
                            onClick={() => handleRollback(d.id)}
                          >
                            Rollback
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </footer>
      )}
    </div>
  );
}
