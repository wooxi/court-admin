const CP1252_REVERSE = {
  8364: 0x80,
  8218: 0x82,
  402: 0x83,
  8222: 0x84,
  8230: 0x85,
  8224: 0x86,
  8225: 0x87,
  710: 0x88,
  8240: 0x89,
  352: 0x8a,
  8249: 0x8b,
  338: 0x8c,
  381: 0x8e,
  8216: 0x91,
  8217: 0x92,
  8220: 0x93,
  8221: 0x94,
  8226: 0x95,
  8211: 0x96,
  8212: 0x97,
  732: 0x98,
  8482: 0x99,
  353: 0x9a,
  8250: 0x9b,
  339: 0x9c,
  382: 0x9e,
  376: 0x9f,
}

const mojibakePattern = /[ÃÂÅÆÇÐÑØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôö÷øùúûüýþÿœŒŠšŸ€‚ƒ„…†‡ˆ‰‹›‘’“”•–—˜™]/

export const fixMojibake = (value) => {
  if (typeof value !== 'string' || !value) return value
  if (!mojibakePattern.test(value)) return value

  const bytes = []
  for (const char of value) {
    const code = char.codePointAt(0)

    if (code <= 0xff) {
      bytes.push(code)
      continue
    }

    const mapped = CP1252_REVERSE[code]
    if (mapped === undefined) {
      return value
    }
    bytes.push(mapped)
  }

  try {
    const decoded = new TextDecoder('utf-8', { fatal: true }).decode(new Uint8Array(bytes))
    return decoded || value
  } catch {
    return value
  }
}

export const normalizeText = (payload) => {
  if (typeof payload === 'string') return fixMojibake(payload)

  if (Array.isArray(payload)) {
    return payload.map((item) => normalizeText(item))
  }

  if (payload && typeof payload === 'object') {
    return Object.fromEntries(Object.entries(payload).map(([key, val]) => [key, normalizeText(val)]))
  }

  return payload
}
