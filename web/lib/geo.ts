import type { FeatureCollectionIVM, GeometriaGeoJSON, Semaforo } from "./types";

// Projeção equirretangular simples (lon/lat → x/y), preservando proporção. Sem lib de mapa.

export interface Forma {
  codigo_ibge: string;
  nome: string;
  ivm: number | null;
  semaforo: Semaforo | null;
  d: string; // path SVG
}

export interface Projecao {
  viewBox: string;
  largura: number;
  altura: number;
  formas: Forma[];
}

function poligonos(geom: GeometriaGeoJSON): number[][][][] {
  return geom.type === "Polygon" ? [geom.coordinates] : geom.coordinates;
}

export function projetar(
  fc: FeatureCollectionIVM,
  largura = 800,
  altura = 800,
  pad = 8,
): Projecao {
  let minLon = Infinity;
  let minLat = Infinity;
  let maxLon = -Infinity;
  let maxLat = -Infinity;
  for (const f of fc.features) {
    if (!f.geometry) continue;
    for (const poly of poligonos(f.geometry)) {
      for (const ring of poly) {
        for (const [lon, lat] of ring) {
          if (lon < minLon) minLon = lon;
          if (lon > maxLon) maxLon = lon;
          if (lat < minLat) minLat = lat;
          if (lat > maxLat) maxLat = lat;
        }
      }
    }
  }
  const dLon = maxLon - minLon || 1;
  const dLat = maxLat - minLat || 1;
  const escala = Math.min((largura - 2 * pad) / dLon, (altura - 2 * pad) / dLat);
  const x = (lon: number) => pad + (lon - minLon) * escala;
  const y = (lat: number) => altura - pad - (lat - minLat) * escala; // eixo Y invertido

  const formas: Forma[] = fc.features.map((f) => ({
    codigo_ibge: f.properties.codigo_ibge,
    nome: f.properties.nome,
    ivm: f.properties.ivm,
    semaforo: f.properties.semaforo,
    d: f.geometry ? caminho(f.geometry, x, y) : "",
  }));
  return { viewBox: `0 0 ${largura} ${altura}`, largura, altura, formas };
}

function caminho(
  geom: GeometriaGeoJSON,
  x: (lon: number) => number,
  y: (lat: number) => number,
): string {
  const partes: string[] = [];
  for (const poly of poligonos(geom)) {
    for (const ring of poly) {
      const pts = ring.map(([lon, lat]) => `${x(lon).toFixed(1)},${y(lat).toFixed(1)}`);
      if (pts.length > 0) {
        partes.push(`M${pts.join("L")}Z`);
      }
    }
  }
  return partes.join("");
}
