/**
 * Shared domain models matching Mission API serializers.
 */

export type Region = 'ANDINA' | 'CONO_SUR' | 'CENTROAMERICA' | 'CARIBE';
export type RiskLevel = 'BAJO' | 'MODERADO' | 'ALTO' | 'CRITICO';
export type IndicatorType =
  | 'PIB'
  | 'INFLACION'
  | 'DESEMPLEO'
  | 'BALANZA_COMERCIAL'
  | 'DEUDA_PIB'
  | 'PIB_PERCAPITA';
export type AssetType = 'RENTA_FIJA' | 'RENTA_VARIABLE' | 'COMMODITIES' | 'MONEDA';
export type AlertType = 'RIESGO' | 'TIPO_CAMBIO' | 'INDICADOR';
export type AlertSeverity = 'INFO' | 'WARNING' | 'CRITICAL';

export interface Country {
  codigo_iso: string;
  nombre: string;
  moneda_codigo: string;
  moneda_nombre: string;
  region: Region;
  latitud: string | number;
  longitud: string | number;
  poblacion: number | null;
  bandera_url?: string;
  activo: boolean;
}

export interface EconomicIndicator {
  id: number;
  pais: string;
  tipo: IndicatorType | string;
  valor: string | number;
  unidad: string;
  anio: number;
  fuente: string;
  fecha_actualizacion: string;
}

export interface RiskIndex {
  fecha_calculo: string;
  score_economico: string | number;
  score_cambiario: string | number;
  score_estabilidad: string | number;
  indice_compuesto: string | number;
  nivel_riesgo: RiskLevel;
}

export interface CountryDetail extends Country {
  indicadores_recientes: EconomicIndicator[];
  riesgo_actual: RiskIndex | null;
}

export interface ExchangeRate {
  id: number;
  moneda_origen: string;
  moneda_destino: string;
  tasa: string | number;
  fecha: string;
  variacion_porcentual: string | number | null;
  fuente: string;
}

export interface RiskRankingItem {
  codigo_iso: string;
  nombre: string;
  region: Region;
  fecha_calculo: string;
  score_economico: string | number;
  score_cambiario: string | number;
  score_estabilidad: string | number;
  indice_compuesto: string | number;
  nivel_riesgo: RiskLevel;
  variacion?: number | null;
  tendencia?: 'ALCISTA' | 'BAJISTA' | 'ESTABLE' | string;
}

export interface DashboardSummary {
  total_paises: number;
  alertas_activas: number;
  portafolios_usuario: number;
  promedio_irpc_region: number | null;
  fecha: string;
}

export interface MapCountry {
  codigo_iso: string;
  nombre: string;
  latitud: string | number;
  longitud: string | number;
  indice_compuesto: string | number;
  nivel_riesgo: RiskLevel;
  color: string;
}

export interface DashboardMap {
  paises: MapCountry[];
}

export interface TrendPoint {
  anio: number;
  valor: string | number;
  unidad: string;
}

export interface TrendSeries {
  codigo_iso: string;
  nombre: string;
  indicador: string;
  puntos: TrendPoint[];
}

export interface DashboardTrends {
  indicador: string;
  anio_desde: number;
  anio_hasta: number;
  series: TrendSeries[];
}

export interface Portfolio {
  id: number;
  nombre: string;
  descripcion: string;
  usuario: number;
  usuario_email: string;
  fecha_creacion: string;
  fecha_modificacion: string;
  activo: boolean;
  es_publico: boolean;
  total_posiciones: number;
}

export interface Position {
  id: number;
  pais: string;
  pais_nombre: string;
  tipo_activo: AssetType;
  monto_inversion_usd: string | number;
  fecha_entrada: string;
  fecha_salida: string | null;
  notas: string;
}

export interface PortfolioMetrics {
  monto_total_usd: string | number;
  riesgo_promedio_ponderado: string | number | null;
  posiciones_abiertas: number;
}

export interface PortfolioDetail extends Portfolio {
  posiciones: Position[];
  metricas: PortfolioMetrics;
}

export interface PortfolioSummary {
  portafolio_id: number;
  monto_total_usd: string | number;
  distribucion_por_pais: Array<{
    pais: string;
    monto_usd: string | number;
    porcentaje: string | number;
  }>;
  distribucion_por_tipo_activo: Array<{
    tipo_activo: AssetType | string;
    monto_usd: string | number;
    porcentaje: string | number;
  }>;
  riesgo_promedio_ponderado: string | number | null;
}

export interface AlertItem {
  id: number;
  usuario: number | null;
  pais: string | null;
  pais_nombre: string | null;
  tipo_alerta: AlertType;
  severidad: AlertSeverity;
  titulo: string;
  mensaje: string;
  leida: boolean;
  fecha_creacion: string;
}

export interface AlertsSummary {
  total: number;
  no_leidas: number;
  por_tipo: Array<{ tipo_alerta: AlertType; total: number; no_leidas: number }>;
  por_severidad: Array<{ severidad: AlertSeverity; total: number; no_leidas: number }>;
}
