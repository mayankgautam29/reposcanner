export const ZONES = [
  { from: 0, to: 40, text: "text-vermilion", bar: "bg-vermilion/30" },
  { from: 40, to: 60, text: "text-ochre", bar: "bg-ochre/30" },
  { from: 60, to: 80, text: "text-moss", bar: "bg-moss/30" },
  { from: 80, to: 100, text: "text-moss", bar: "bg-moss/60" },
];

export function getZone(score) {
  return ZONES.find((zone) => score < zone.to) || ZONES[ZONES.length - 1];
}
