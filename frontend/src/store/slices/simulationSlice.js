import { createAsyncThunk, createSlice } from '@reduxjs/toolkit'
import apiClient from '../../api/client'

export const fetchSimulationStatus = createAsyncThunk('simulation/fetchStatus', async () => {
  const response = await apiClient.get('/api/simulation/status')
  return response.data
})

export const startSimulation = createAsyncThunk(
  'simulation/start',
  async ({ ticks, intervalSeconds }) => {
    const response = await apiClient.post('/api/simulation/start', {
      ticks: ticks ?? null,
      interval_seconds: intervalSeconds ?? 1.0,
    })
    return response.data
  },
)

export const stopSimulation = createAsyncThunk('simulation/stop', async () => {
  const response = await apiClient.post('/api/simulation/stop')
  return response.data
})

export const fetchRunSummary = createAsyncThunk('simulation/fetchSummary', async (runId) => {
  const response = await apiClient.get(`/api/simulation/runs/${runId}/summary`)
  return response.data
})

const simulationSlice = createSlice({
  name: 'simulation',
  initialState: {
    isRunning: false,
    tickCount: 0,
    decisionLogSize: 0,
    runId: null,
    summary: null,
    error: null,
  },
  reducers: {
    clearSummary: (state) => {
      state.summary = null
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchSimulationStatus.fulfilled, (state, action) => {
        state.isRunning = action.payload.is_running
        state.tickCount = action.payload.tick_count
        state.decisionLogSize = action.payload.decision_log_size
        state.runId = action.payload.run_id
      })
      .addCase(startSimulation.fulfilled, (state, action) => {
        state.isRunning = true
        state.runId = action.payload.run_id
        state.summary = null
      })
      .addCase(startSimulation.rejected, (state, action) => {
        state.error = action.error.message
      })
      .addCase(stopSimulation.fulfilled, (state) => {
        state.isRunning = false
      })
      .addCase(stopSimulation.rejected, (state, action) => {
        state.error = action.error.message
      })
      .addCase(fetchRunSummary.fulfilled, (state, action) => {
        state.summary = action.payload
      })
  },
})

export const { clearSummary } = simulationSlice.actions
export default simulationSlice.reducer
