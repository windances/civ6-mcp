import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

import Ajv2020 from 'ajv/dist/2020.js'

const here = dirname(fileURLToPath(import.meta.url))
const contractRoot = join(here, '..', '..', 'contracts')

function loadSchema(name) {
  return JSON.parse(readFileSync(join(contractRoot, name), 'utf8'))
}

const ajv = new Ajv2020({ allErrors: true, strict: true })
const validators = {
  snapshot: ajv.compile(loadSchema('turn-snapshot.schema.json')),
  proposal: ajv.compile(loadSchema('worker-proposal.schema.json')),
  execution: ajv.compile(loadSchema('execution-result.schema.json')),
}

export const WORKER_TOOL_ALLOWLISTS = Object.freeze({
  strategy: Object.freeze([
    'set_research',
    'set_policies',
    'change_government',
    'choose_dedication',
  ]),
  'military-map': Object.freeze([
    'unit_action',
    'promote_unit',
    'upgrade_unit',
    'skip_remaining_units',
    'spy_action',
  ]),
  'economy-cities': Object.freeze([
    'city_action',
    'set_city_production',
    'purchase_item',
    'purchase_tile',
    'set_city_focus',
    'appoint_governor',
    'assign_governor',
    'promote_governor',
    'send_envoy',
    'recruit_great_person',
    'patronize_great_person',
    'reject_great_person',
  ]),
  'diplomacy-victory': Object.freeze([
    'respond_to_trade',
    'propose_trade',
    'propose_peace',
    'respond_to_diplomacy',
    'send_diplomatic_action',
    'form_alliance',
    'choose_pantheon',
    'found_religion',
    'queue_wc_votes',
    'spy_action',
  ]),
})

export const WORKER_PROPOSAL_TOOL_ALLOWLIST = Object.freeze(
  [...new Set(Object.values(WORKER_TOOL_ALLOWLISTS).flat())],
)

export const EXECUTOR_TOOL_ALLOWLIST = Object.freeze([
  ...WORKER_PROPOSAL_TOOL_ALLOWLIST,
  'end_turn',
])

export class ContractError extends Error {
  constructor(code, message, details = []) {
    super(message)
    this.name = 'ContractError'
    this.code = code
    this.details = details
  }
}

function cloneAndFreeze(value) {
  const clone = structuredClone(value)
  const freeze = (item) => {
    if (item && typeof item === 'object' && !Object.isFrozen(item)) {
      Object.freeze(item)
      for (const child of Object.values(item)) freeze(child)
    }
    return item
  }
  return freeze(clone)
}

function assertSchema(kind, value) {
  const validator = validators[kind]
  if (!validator(value)) {
    throw new ContractError(
      `invalid_${kind}`,
      `${kind} does not match its JSON Schema`,
      structuredClone(validator.errors ?? []),
    )
  }
}

function entityIds(items, keys) {
  const ids = new Set()
  for (const item of items) {
    for (const key of keys) {
      if (item[key] !== undefined) ids.add(String(item[key]))
    }
  }
  return ids
}

function argumentValue(args, keys) {
  for (const key of keys) {
    if (args[key] !== undefined) return args[key]
  }
  return undefined
}

function validateActionReferences(action, snapshot) {
  const unitId = argumentValue(action.arguments, ['unit_id', 'unitId'])
  const cityId = argumentValue(action.arguments, ['city_id', 'cityId'])
  const unitIds = entityIds(snapshot.units, ['id', 'unitId', 'unit_id'])
  const cityIds = entityIds(snapshot.cities, ['id', 'cityId', 'city_id'])

  if (unitId !== undefined && unitIds.size > 0 && !unitIds.has(String(unitId))) {
    throw new ContractError('missing_unit', `action ${action.actionId} references missing unit ${unitId}`)
  }
  if (cityId !== undefined && cityIds.size > 0 && !cityIds.has(String(cityId))) {
    throw new ContractError('missing_city', `action ${action.actionId} references missing city ${cityId}`)
  }

  const x = action.arguments.x
  const y = action.arguments.y
  for (const [name, coordinate] of [['x', x], ['y', y]]) {
    if (coordinate !== undefined && (!Number.isInteger(coordinate) || coordinate < 0)) {
      throw new ContractError('invalid_coordinate', `${name} must be a non-negative integer`)
    }
  }
  if (Number.isInteger(snapshot.map.width) && x !== undefined && x >= snapshot.map.width) {
    throw new ContractError('invalid_coordinate', `x ${x} is outside map width ${snapshot.map.width}`)
  }
  if (Number.isInteger(snapshot.map.height) && y !== undefined && y >= snapshot.map.height) {
    throw new ContractError('invalid_coordinate', `y ${y} is outside map height ${snapshot.map.height}`)
  }
}

export function validateSnapshot(value) {
  assertSchema('snapshot', value)
  return cloneAndFreeze(value)
}

export function validateProposal(value, { snapshot, seenActionIds = new Set() }) {
  assertSchema('proposal', value)
  if (value.gameId !== snapshot.gameId) {
    throw new ContractError('stale_game', `proposal game ${value.gameId} does not match ${snapshot.gameId}`)
  }
  if (value.turn !== snapshot.turn) {
    throw new ContractError('stale_turn', `proposal turn ${value.turn} does not match ${snapshot.turn}`)
  }

  const localIds = new Set()
  const domainTools = WORKER_TOOL_ALLOWLISTS[value.worker]
  for (const action of value.actions) {
    if (!action.actionId.startsWith(`T${snapshot.turn}-`)) {
      throw new ContractError('stale_action_id', `action ${action.actionId} does not identify turn ${snapshot.turn}`)
    }
    if (localIds.has(action.actionId) || seenActionIds.has(action.actionId)) {
      throw new ContractError('duplicate_action_id', `duplicate actionId ${action.actionId}`)
    }
    if (!WORKER_PROPOSAL_TOOL_ALLOWLIST.includes(action.tool)) {
      throw new ContractError('forbidden_tool', `worker proposals cannot use ${action.tool}`)
    }
    if (!domainTools.includes(action.tool)) {
      throw new ContractError('wrong_worker_domain', `${value.worker} cannot propose ${action.tool}`)
    }
    validateActionReferences(action, snapshot)
    localIds.add(action.actionId)
  }

  for (const actionId of localIds) seenActionIds.add(actionId)
  return cloneAndFreeze(value)
}

export function validateExecutionResult(value) {
  assertSchema('execution', value)
  return cloneAndFreeze(value)
}
