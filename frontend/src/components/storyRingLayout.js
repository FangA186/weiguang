export const ringRadius = 4.2;
export function ringPose(index, count) {
  const angle = index * Math.PI * 2 / count;
  return { x: Math.sin(angle) * ringRadius, z: Math.cos(angle) * ringRadius, angle };
}
export function frontIndex(angle, count) {
  return ((Math.round(-angle / (Math.PI * 2 / count)) % count) + count) % count;
}
