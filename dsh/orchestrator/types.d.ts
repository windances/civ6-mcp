export type WorkerRole = 'strategy' | 'military-map' | 'economy-cities' | 'diplomacy-victory'
export type Risk = 'low' | 'medium' | 'high'

export interface TurnSnapshot {
  readonly version: 1
  readonly gameId: string
  readonly turn: number
  readonly overview: Readonly<Record<string, unknown>>
  readonly units: readonly Readonly<Record<string, unknown>>[]
  readonly cities: readonly Readonly<Record<string, unknown>>[]
  readonly map: Readonly<Record<string, unknown>>
  readonly diplomacy: readonly Readonly<Record<string, unknown>>[]
  readonly victory: Readonly<Record<string, unknown>>
  readonly blockers: readonly Readonly<Record<string, unknown>>[]
  readonly recentEvents: readonly Readonly<Record<string, unknown>>[]
}

export interface ProposedAction {
  readonly actionId: string
  readonly tool: string
  readonly arguments: Readonly<Record<string, unknown>>
  readonly preconditions: readonly string[]
  readonly expectedEffects: readonly string[]
  readonly risk: Risk
}

export interface WorkerProposal {
  readonly version: 1
  readonly gameId: string
  readonly turn: number
  readonly worker: WorkerRole
  readonly assessment: string
  readonly priority: number
  readonly actions: readonly ProposedAction[]
  readonly warnings: readonly string[]
  readonly confidence: number
}

export interface ExecutionResult {
  readonly version: 1
  readonly gameId: string
  readonly turn: number
  readonly actionId: string
  readonly status: 'executed' | 'rejected' | 'failed' | 'uncertain'
  readonly toolResult: string
  readonly verified: boolean
  readonly observedEffects: readonly string[]
  readonly replanRequired: boolean
}
