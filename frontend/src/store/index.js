import { configureStore } from '@reduxjs/toolkit'
import agentsReducer from './slices/agentsSlice'
import eventsReducer from './slices/eventsSlice'
import simulationReducer from './slices/simulationSlice'

const store = configureStore({
  reducer: {
    agents: agentsReducer,
    events: eventsReducer,
    simulation: simulationReducer,
  },
})

export default store
