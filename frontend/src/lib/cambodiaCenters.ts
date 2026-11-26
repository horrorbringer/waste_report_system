// Approximate center coordinates [lat, lng] for Cambodian provinces & Phnom Penh khans
// Used for privacy-safe public map pins (never exposing exact street GPS).

export const PROVINCE_CENTERS: Record<number, [number, number]> = {
  1: [13.5858, 102.9736], // Banteay Meanchey
  2: [13.0957, 103.2022], // Battambang
  3: [11.9934, 105.4635], // Kampong Cham
  4: [12.2530, 104.6660], // Kampong Chhnang
  5: [11.4533, 104.5209], // Kampong Speu
  6: [12.7111, 104.8887], // Kampong Thom
  7: [10.6104, 104.1814], // Kampot
  8: [11.4833, 104.9500], // Kandal
  9: [11.6153, 102.9838], // Koh Kong
  10: [12.4881, 106.0188], // Kratie
  11: [12.4558, 107.1881], // Mondulkiri
  12: [11.5564, 104.9282], // Phnom Penh Capital
  13: [13.8073, 104.9805], // Preah Vihear
  14: [11.4868, 105.3253], // Prey Veng
  15: [12.5388, 103.9192], // Pursat
  16: [13.7394, 106.9873], // Ratanakiri
  17: [13.3633, 103.8564], // Siem Reap
  18: [10.6275, 103.5221], // Preah Sihanouk
  19: [13.5259, 105.9683], // Stung Treng
  20: [11.0879, 105.7993], // Svay Rieng
  21: [10.9908, 104.7850], // Takeo
  22: [14.1818, 103.5176], // Oddar Meanchey
  23: [10.4833, 104.3167], // Kep
  24: [12.8489, 102.6093], // Pailin
  25: [11.9167, 105.6667], // Tboung Khmum
}

export const DISTRICT_CENTERS: Record<number, [number, number]> = {
  1201: [11.5449, 104.9212], // Chamkar Mon
  1202: [11.5730, 104.9228], // Doun Penh
  1203: [11.5646, 104.9125], // Prampir Makara
  1204: [11.5720, 104.8960], // Tuol Kouk
  1205: [11.5034, 104.8810], // Dangkao
  1206: [11.5315, 104.9340], // Mean Chey
  1207: [11.6150, 104.9060], // Russey Keo
  1208: [11.5920, 104.8720], // Saensokh (Sen Sok)
  1209: [11.5430, 104.8250], // Pur SenChey
  1210: [11.5910, 104.9390], // Chraoy Chongvar
  1211: [11.6480, 104.8280], // Praek Pnov
  1212: [11.5350, 104.9600], // Chbar Ampov
  1213: [11.5515, 104.9215], // Boeng Keng Kang
  1214: [11.5200, 104.8400], // Kamboul
}

export function getAreaCoordinates(province: number, district?: number | null): [number, number] {
  if (district && DISTRICT_CENTERS[district]) {
    return DISTRICT_CENTERS[district]
  }
  if (PROVINCE_CENTERS[province]) {
    return PROVINCE_CENTERS[province]
  }
  return [11.5564, 104.9282] // Default Phnom Penh
}
