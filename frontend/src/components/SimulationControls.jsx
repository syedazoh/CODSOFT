import { useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { startSimulation, stopSimulation } from '../store/slices/simulationSlice'
import { STATUS } from '../theme/palette'

function SimulationControls() {
  const dispatch = useDispatch()
  const { isRunning, tickCount, decisionLogSize, runId, error } = useSelector(
    (state) => state.simulation,
  )
  const [ticks, setTicks] = useState(20)
  const [intervalSeconds, setIntervalSeconds] = useState(1)

  const handleStart = () => {
    dispatch(startSimulation({ ticks: Number(ticks) || null, intervalSeconds: Number(intervalSeconds) }))
  }

  const handleStop = () => {
    dispatch(stopSimulation())
  }

  return (
    <div className="bg-white rounded-lg shadow p-4 flex flex-wrap items-end gap-4">
      <div>
        <label className="block text-xs text-gray-500 mb-1" htmlFor="ticks">Ticks</label>
        <input
          id="ticks"
          type="number"
          min="1"
          value={ticks}
          onChange={(e) => setTicks(e.target.value)}
          disabled={isRunning}
          className="border rounded px-2 py-1 w-24 text-sm disabled:bg-gray-100"
        />
      </div>
      <div>
        <label className="block text-xs text-gray-500 mb-1" htmlFor="interval">Interval (s)</label>
        <input
          id="interval"
          type="number"
          min="0"
          step="0.1"
          value={intervalSeconds}
          onChange={(e) => setIntervalSeconds(e.target.value)}
          disabled={isRunning}
          className="border rounded px-2 py-1 w-24 text-sm disabled:bg-gray-100"
        />
      </div>
      <button
        type="button"
        onClick={handleStart}
        disabled={isRunning}
        className="px-4 py-2 rounded text-white text-sm font-medium disabled:opacity-50"
        style={{ backgroundColor: STATUS.good }}
      >
        Start Simulation
      </button>
      <button
        type="button"
        onClick={handleStop}
        disabled={!isRunning}
        className="px-4 py-2 rounded text-white text-sm font-medium disabled:opacity-50"
        style={{ backgroundColor: STATUS.critical }}
      >
        Stop Simulation
      </button>
      <div className="text-sm text-gray-600 ml-auto">
        <span className="mr-4">
          Status:{' '}
          <span className="font-medium" style={{ color: isRunning ? STATUS.good : undefined }}>
            {isRunning ? 'Running' : 'Idle'}
          </span>
        </span>
        <span className="mr-4">Ticks: {tickCount}</span>
        <span className="mr-4">Decisions: {decisionLogSize}</span>
        {runId && <span className="text-xs text-gray-400">run: {runId.slice(0, 8)}</span>}
      </div>
      {error && <p className="text-sm w-full" style={{ color: STATUS.critical }}>{error}</p>}
    </div>
  )
}

export default SimulationControls
