import {
  type Edge,
  Handle,
  type Node,
  type NodeProps,
  Position,
  ReactFlow,
  ReactFlowProvider,
  useNodesState,
} from "@xyflow/react"
import "@xyflow/react/dist/style.css"
import { createRoot } from "react-dom/client"

const nodes: Node[] = Array.from({ length: 500 }, (_, index) => ({
  id: `claim-${index}`,
  position: { x: (index % 25) * 180, y: Math.floor(index / 25) * 90 },
  data: { label: `Claim ${index}` },
  type: "default",
}))
const edges: Edge[] = Array.from({ length: 499 }, (_, index) => ({
  id: `local-edge-${index}`,
  source: `claim-${index}`,
  target: `claim-${index + 1}`,
  type: "smoothstep",
}))

function ClaimNode({ data }: NodeProps) {
  return (
    <div
      data-testid="claim-node"
      style={{ padding: 8, border: "1px solid #666" }}
    >
      <Handle type="target" position={Position.Left} isConnectable={false} />
      {String(data.label)}
      <Handle type="source" position={Position.Right} isConnectable={false} />
    </div>
  )
}

function App() {
  const [controlledNodes, , onNodesChange] = useNodesState(nodes)
  return (
    <ReactFlowProvider>
      <style>{`
        body { margin: 0; overflow: hidden; }
        .mobile-fallback { display: none; }
        @media (max-width: 600px) {
          .graph-canvas { display: none; }
          .mobile-fallback { display: block; width: 100%; border-collapse: collapse; }
          .mobile-fallback th, .mobile-fallback td { padding: 8px; border-bottom: 1px solid #ccc; }
        }
      `}</style>
      <div
        className="graph-canvas"
        style={{ width: "100vw", height: "100vh" }}
        data-testid="flow-spike"
      >
        <ReactFlow
          nodes={controlledNodes}
          edges={edges}
          nodeTypes={{ default: ClaimNode }}
          fitView
          nodesConnectable={false}
          nodesDraggable
          onNodesChange={onNodesChange}
          onConnect={() => undefined}
        />
      </div>
      <table className="mobile-fallback" data-testid="mobile-table">
        <thead>
          <tr>
            <th>Claim</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {nodes.slice(0, 20).map((node) => (
            <tr key={node.id}>
              <td>{String(node.data.label)}</td>
              <td>Projected</td>
            </tr>
          ))}
        </tbody>
      </table>
    </ReactFlowProvider>
  )
}

createRoot(document.getElementById("root")!).render(<App />)
