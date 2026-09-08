import { ActionLedger } from './action-ledger.mjs'
import { ContractError, EXECUTOR_TOOL_ALLOWLIST } from './contracts.mjs'

function assertIdentity(expected, actual) {
  if (actual.gameId !== expected.gameId) {
    throw new ContractError('stale_game', `current game ${actual.gameId} does not match ${expected.gameId}`)
  }
  if (actual.turn !== expected.turn) {
    throw new ContractError('stale_turn', `current turn ${actual.turn} does not match ${expected.turn}`)
  }
}

function normalizeCheck(value, defaultEffect) {
  if (typeof value === 'boolean') {
    return { ok: value, observedEffects: value && defaultEffect ? [defaultEffect] : [] }
  }
  return {
    ok: Boolean(value?.ok),
    observedEffects: Array.isArray(value?.observedEffects) ? value.observedEffects : [],
    reason: value?.reason,
  }
}

function executionResult(plan, action, fields) {
  return {
    version: 1,
    gameId: plan.gameId,
    turn: plan.turn,
    actionId: action.actionId,
    toolResult: '',
    observedEffects: [],
    ...fields,
  }
}

export class SoleWriterExecutor {
  constructor({ readState, invokeTool, checkPreconditions, verifyEffect, onResult }) {
    this.readState = readState
    this.invokeTool = invokeTool
    this.checkPreconditions = checkPreconditions ?? (async () => true)
    this.verifyEffect = verifyEffect
    this.onResult = onResult ?? (async () => {})
  }

  async execute(plan) {
    const ledger = new ActionLedger(plan)
    const actionIds = new Set()
    for (const action of plan.ordered) {
      if (actionIds.has(action.actionId)) {
        throw new ContractError('duplicate_action_id', `plan repeats ${action.actionId}`)
      }
      if (!EXECUTOR_TOOL_ALLOWLIST.includes(action.tool)) {
        throw new ContractError('forbidden_tool', `executor cannot invoke ${action.tool}`)
      }
      actionIds.add(action.actionId)
    }

    const results = []
    for (const action of plan.ordered) {
      const before = await this.readState(action)
      assertIdentity(plan, before)
      ledger.claim(action, before)

      const precondition = normalizeCheck(await this.checkPreconditions(action, before))
      if (!precondition.ok) {
        const result = ledger.record(executionResult(plan, action, {
          status: 'rejected',
          verified: false,
          observedEffects: precondition.observedEffects,
          replanRequired: true,
          toolResult: precondition.reason ?? 'Precondition failed',
        }))
        results.push(result)
        await this.onResult({ action, result })
        break
      }

      let rawResult
      let invocationError
      try {
        rawResult = await this.invokeTool(action.tool, action.arguments)
      } catch (error) {
        invocationError = error
      }

      const after = await this.readState(action)
      if (after.gameId !== plan.gameId) {
        throw new ContractError('stale_game', 'game identity changed during execution')
      }
      const verification = normalizeCheck(
        await this.verifyEffect(action, { before, after, rawResult, invocationError }),
      )
      const verified = verification.ok
      const status = verified ? 'executed' : (invocationError ? 'uncertain' : 'failed')
      const result = ledger.record(executionResult(plan, action, {
        status,
        verified,
        observedEffects: verification.observedEffects,
        replanRequired: !verified,
        toolResult: invocationError
          ? `${invocationError.name}: ${invocationError.message}`
          : String(rawResult ?? ''),
      }))
      results.push(result)
      await this.onResult({ action, result })
      if (!verified) break
    }

    return Object.freeze({
      results: Object.freeze(results),
      ledger: ledger.toJSON(),
      completed: results.length === plan.ordered.length && results.every((result) => result.verified),
    })
  }
}
