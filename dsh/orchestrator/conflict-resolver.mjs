import { ContractError, validateProposal } from './contracts.mjs'

const WORKER_ORDER = new Map([
  ['military-map', 0],
  ['economy-cities', 1],
  ['strategy', 2],
  ['diplomacy-victory', 3],
])

function argumentValue(args, keys) {
  for (const key of keys) {
    if (args[key] !== undefined) return args[key]
  }
  return undefined
}

export function actionTarget(action) {
  const unitId = argumentValue(action.arguments, ['unit_id', 'unitId'])
  if (unitId !== undefined) return `unit:${unitId}`
  const cityId = argumentValue(action.arguments, ['city_id', 'cityId'])
  if (cityId !== undefined) return `city:${cityId}`
  if (action.tool === 'set_research') return `global:research:${action.arguments.category ?? 'tech'}`
  if (['set_policies', 'change_government'].includes(action.tool)) return 'global:government'
  return undefined
}

function policyClass(entry) {
  const text = [
    entry.proposal.assessment,
    ...entry.action.preconditions,
    ...entry.action.expectedEffects,
  ].join(' ').toLowerCase()
  if (/mandatory|required|blocker/.test(text)) return 0
  if (/surviv|retreat|heal|defend|save (the )?(unit|city)/.test(text)) return 1
  if (entry.proposal.worker === 'military-map') return 2
  if (['economy-cities', 'strategy'].includes(entry.proposal.worker)) return 3
  if (entry.proposal.worker === 'diplomacy-victory') return 4
  return 5
}

function compareEntries(left, right) {
  return (
    policyClass(left) - policyClass(right)
    || right.proposal.priority - left.proposal.priority
    || right.proposal.confidence - left.proposal.confidence
    || WORKER_ORDER.get(left.proposal.worker) - WORKER_ORDER.get(right.proposal.worker)
    || left.action.actionId.localeCompare(right.action.actionId)
  )
}

export function resolveProposals(snapshot, rawProposals) {
  const seenActionIds = new Set()
  const proposals = []
  const proposalErrors = []
  for (const [index, proposal] of rawProposals.entries()) {
    try {
      proposals.push(validateProposal(proposal, { snapshot, seenActionIds }))
    } catch (error) {
      if (!(error instanceof ContractError)) throw error
      proposalErrors.push(Object.freeze({
        index,
        worker: proposal?.worker ?? 'unknown',
        code: error.code,
        message: error.message,
      }))
    }
  }
  const candidates = proposals.flatMap((proposal) =>
    proposal.actions.map((action) => ({ action, proposal })),
  ).sort(compareEntries)

  const targets = new Map()
  const ordered = []
  const rejected = []
  for (const candidate of candidates) {
    const target = actionTarget(candidate.action)
    if (target !== undefined && targets.has(target)) {
      rejected.push(Object.freeze({
        actionId: candidate.action.actionId,
        reason: 'target_conflict',
        target,
        winnerActionId: targets.get(target).action.actionId,
      }))
      continue
    }
    if (target !== undefined) targets.set(target, candidate)
    ordered.push(Object.freeze({
      ...candidate.action,
      worker: candidate.proposal.worker,
      proposalPriority: candidate.proposal.priority,
      proposalConfidence: candidate.proposal.confidence,
    }))
  }

  return Object.freeze({
    gameId: snapshot.gameId,
    turn: snapshot.turn,
    ordered: Object.freeze(ordered),
    rejected: Object.freeze(rejected),
    proposalErrors: Object.freeze(proposalErrors),
  })
}
