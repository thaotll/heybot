import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"
import type { CodeAnalysis } from "./code-analysis-dashboard"

interface SystemMetricsProps {
  analysis: CodeAnalysis
}

// Mock data for system metrics
const cpuData = [
  { time: "00:00", value: 45 },
  { time: "01:00", value: 42 },
  { time: "02:00", value: 48 },
  { time: "03:00", value: 51 },
  { time: "04:00", value: 55 },
  { time: "05:00", value: 60 },
  { time: "06:00", value: 62 },
  { time: "07:00", value: 58 },
  { time: "08:00", value: 65 },
  { time: "09:00", value: 70 },
  { time: "10:00", value: 75 },
  { time: "11:00", value: 80 },
  { time: "12:00", value: 85 },
]

const memoryData = [
  { time: "00:00", value: 60 },
  { time: "01:00", value: 62 },
  { time: "02:00", value: 65 },
  { time: "03:00", value: 63 },
  { time: "04:00", value: 68 },
  { time: "05:00", value: 70 },
  { time: "06:00", value: 72 },
  { time: "07:00", value: 75 },
  { time: "08:00", value: 78 },
  { time: "09:00", value: 82 },
  { time: "10:00", value: 85 },
  { time: "11:00", value: 88 },
  { time: "12:00", value: 90 },
]

const networkData = [
  { time: "00:00", value: 20 },
  { time: "01:00", value: 15 },
  { time: "02:00", value: 18 },
  { time: "03:00", value: 25 },
  { time: "04:00", value: 30 },
  { time: "05:00", value: 35 },
  { time: "06:00", value: 40 },
  { time: "07:00", value: 45 },
  { time: "08:00", value: 50 },
  { time: "09:00", value: 55 },
  { time: "10:00", value: 60 },
  { time: "11:00", value: 65 },
  { time: "12:00", value: 70 },
]

export function SystemMetrics({ analysis }: SystemMetricsProps) {
  return (
    <div className="p-4 space-y-4">
      <div className="p-4 rounded-md bg-[#0d1117] border border-[#30363d]">
        <h3 className="font-medium text-[#c9d1d9] mb-2">System-Metriken</h3>
        <p className="text-[#8b949e]">
          Leistungsmetriken für die letzten 12 Stunden. Die Daten werden alle 5 Minuten aktualisiert.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="border border-[#30363d] rounded-md overflow-hidden">
          <div className="bg-[#0d1117] p-3 border-b border-[#30363d]">
            <span className="font-medium text-[#c9d1d9]">CPU-Auslastung (%)</span>
          </div>
          <div className="p-4 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={cpuData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#30363d" />
                <XAxis dataKey="time" stroke="#8b949e" tick={{ fill: "#8b949e" }} />
                <YAxis stroke="#8b949e" tick={{ fill: "#8b949e" }} domain={[0, 100]} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#161b22",
                    borderColor: "#30363d",
                    color: "#c9d1d9",
                  }}
                  labelStyle={{ color: "#c9d1d9" }}
                  itemStyle={{
                    color: "#c9d1d9",
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke="#58a6ff"
                  strokeWidth={2}
                  dot={{ fill: "#58a6ff", r: 4 }}
                  activeDot={{ fill: "#58a6ff", r: 6, stroke: "#161b22", strokeWidth: 2 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="border border-[#30363d] rounded-md overflow-hidden">
          <div className="bg-[#0d1117] p-3 border-b border-[#30363d]">
            <span className="font-medium text-[#c9d1d9]">Speicherauslastung (%)</span>
          </div>
          <div className="p-4 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={memoryData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#30363d" />
                <XAxis dataKey="time" stroke="#8b949e" tick={{ fill: "#8b949e" }} />
                <YAxis stroke="#8b949e" tick={{ fill: "#8b949e" }} domain={[0, 100]} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#161b22",
                    borderColor: "#30363d",
                    color: "#c9d1d9",
                  }}
                  labelStyle={{ color: "#c9d1d9" }}
                  itemStyle={{
                    color: "#c9d1d9",
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke="#3fb950"
                  strokeWidth={2}
                  dot={{ fill: "#3fb950", r: 4 }}
                  activeDot={{ fill: "#3fb950", r: 6, stroke: "#161b22", strokeWidth: 2 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="border border-[#30363d] rounded-md overflow-hidden md:col-span-2">
          <div className="bg-[#0d1117] p-3 border-b border-[#30363d]">
            <span className="font-medium text-[#c9d1d9]">Netzwerkverkehr (MB/s)</span>
          </div>
          <div className="p-4 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={networkData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#30363d" />
                <XAxis dataKey="time" stroke="#8b949e" tick={{ fill: "#8b949e" }} />
                <YAxis stroke="#8b949e" tick={{ fill: "#8b949e" }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#161b22",
                    borderColor: "#30363d",
                    color: "#c9d1d9",
                  }}
                  labelStyle={{ color: "#c9d1d9" }}
                  itemStyle={{
                    color: "#c9d1d9",
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke="#d29922"
                  strokeWidth={2}
                  dot={{ fill: "#d29922", r: 4 }}
                  activeDot={{ fill: "#d29922", r: 6, stroke: "#161b22", strokeWidth: 2 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="border border-[#30363d] bg-[#0d1117] rounded-md p-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-[#c9d1d9]">85%</div>
            <p className="text-xs text-[#8b949e] mt-1">CPU-Spitze</p>
          </div>
        </div>
        <div className="border border-[#30363d] bg-[#0d1117] rounded-md p-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-[#c9d1d9]">90%</div>
            <p className="text-xs text-[#8b949e] mt-1">RAM-Spitze</p>
          </div>
        </div>
        <div className="border border-[#30363d] bg-[#0d1117] rounded-md p-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-[#c9d1d9]">70 MB/s</div>
            <p className="text-xs text-[#8b949e] mt-1">Netzwerk-Spitze</p>
          </div>
        </div>
        <div className="border border-[#30363d] bg-[#0d1117] rounded-md p-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-[#c9d1d9]">12h</div>
            <p className="text-xs text-[#8b949e] mt-1">Uptime</p>
          </div>
        </div>
      </div>
    </div>
  )
}
