import type { ReportArea, ReportProvince } from '@/types'

const alternateNames: Record<number, string[]> = {
  8: ['Kandal'],
  12: ['Phnom Penh', 'ភ្នំពេញ'],
  17: ['Siem Reap', 'Siem Reab'],
  18: ['Sihanoukville', 'Preah Sihanouk', 'Kampong Som'],
  1201: ['Chamkar Morn', 'Chamkarmon', 'Chamkarmorn'],
  1202: ['Daun Penh', 'Daunpenh', 'Dounpenh'],
  1203: ['7 Makara', '៧ មករា', 'Prampi Makara', 'Prampir Makkara'],
  1204: ['Tuol Kork', 'Toul Kork', 'Toul Kouk', 'Tuolkok'],
  1205: ['Dangkor', 'Dang Koa', 'Dang Kao'],
  1206: ['Meanchey'],
  1207: ['Russei Keo', 'Russeykeo', 'Ruessei Kaev'],
  1208: ['Sen Sok', 'Sensok', 'Saen Sokh', 'Sen Sokh'],
  1209: ['Por Sen Chey', 'Por Senchey', 'Pou Senchey', 'Pur Sen Chey'],
  1210: ['Chroy Changvar', 'Chroy Chongvar', 'Chraoy Chongvar', 'Chrouy Changva'],
  1211: ['Prek Pnov', 'Preaek Pnov'],
  1212: ['Chbar Ampeou'],
  1213: ['Boeung Keng Kang', 'Boeng Kengkang', 'Boeung Kengkang', 'BKK1', 'BKK2', 'BKK3'],
}

function normalize(value: string) {
  return value.normalize('NFC').toLowerCase().replace(/[\u200b-\u200d\ufeff]/g, '')
    .replace(/[^\p{L}\p{M}\p{N}]+/gu, ' ').trim()
}

function shortName(name: string) {
  return normalize(name).replace(/^(?:ខេត្ត|រាជធានី|ក្រុង|ស្រុក|ខណ្ឌ)\s*/, '')
    .replace(/\s+(?:province|capital|municipality|district|khan|city)$/, '')
}

function matches(area: ReportArea, address: string, parent?: ReportProvince) {
  const fullNames = [normalize(area.name), normalize(area.name_km)]
  const shortNames = [shortName(area.name), shortName(area.name_km), ...(alternateNames[area.code] ?? []).map(normalize)]
  const parentNames = parent ? [shortName(parent.name), shortName(parent.name_km), ...(alternateNames[parent.code] ?? []).map(normalize)] : []
  return [...fullNames, ...shortNames.filter((name) => !parentNames.includes(name))].some((name) =>
    name && (/^[\u1780-\u17ff]/.test(name) ? address.includes(name) : address.includes(' ' + name + ' ')),
  )
}

export function provinceFromAddress(address: string, areas: ReportProvince[]) {
  const normalized = ' ' + normalize(address) + ' '
  const recognized = areas.filter((province) => matches(province, normalized))
  return recognized.length === 1 ? recognized[0].code : null
}

export function districtFromAddress(address: string, areas: ReportProvince[], provinceCode: number | null = null) {
  const normalized = ' ' + normalize(address) + ' '
  const provinces = provinceCode ? areas.filter(({ code }) => code === provinceCode) : areas
  const recognized = provinces.flatMap((province) => province.districts.filter((district) => matches(district, normalized, province)))
  return recognized.length === 1 ? recognized[0].code : null
}

export function suggestReportArea(address: string, mapDistrict: number | null, areas: ReportProvince[]) {
  const province = provinceFromAddress(address, areas)
  const addressDistrict = districtFromAddress(address, areas, province)
  if (mapDistrict && (addressDistrict && addressDistrict !== mapDistrict || province && province !== Math.trunc(mapDistrict / 100))) {
    return { province: null, district: null }
  }
  const district = mapDistrict ?? addressDistrict
  return { province: district ? Math.trunc(district / 100) : province, district }
}
