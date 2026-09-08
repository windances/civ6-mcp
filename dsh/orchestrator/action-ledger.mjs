import { ContractError, validateExecutionResult } from './contracts.mjs'

export class ActionLedger {
  #claimed = new Set()
  #results = new Map()

  constructor({ gameId, turn }) {
    this.gameId = gameId
    this.turn = turn
  }

  claim(action, { gameId, turn }) {
    if (gameId !== this.gameId) throw new ContractError('stale_game', 'ledger game identity changed')
    if (turn !== this.turn) throw new ContractError('stale_turn', 'ledger turn changed')
    if (this.#claimed.has(action.actionId)) {
      throw new ContractError('duplicate_action_id', `action ${action.actionId} was already claimed`)
    }
    this.#claimed.add(action.actionId)
  }

  record(result) {
    const checked = validateExecutionResult(result)
    if (checked.gameId !== this.gameId || checked.turn !== this.turn) {
      throw new ContractError('stale_execution_result', 'execution result does not match ledger identity')
    }
    if (!this.#claimed.has(checked.actionId)) {
      throw new ContractError('unclaimed_action', `action ${checked.actionId} was never claimed`)
    }
    if (this.#results.has(checked.actionId)) {
      throw new ContractError('duplicate_execution_result', `action ${checked.actionId} already has a result`)
    }
    this.#results.set(checked.actionId, checked)
    return checked
  }

  has(actionId) {
    return this.#claimed.has(actionId)
  }

  result(actionId) {
    return this.#results.get(actionId)
  }

  toJSON() {
    return Object.freeze({
      version: 1,
      gameId: this.gameId,
      turn: this.turn,
      claimedActionIds: Object.freeze([...this.#claimed]),
      results: Object.freeze([...this.#results.values()]),
    })
  }
}
