
export interface GeoJSONFeature {
  type: string;
  geometry: {
    type: string;
    coordinates: number[][][] | number[][];
  };
  properties: Record<string, any>;
}

export interface AnalysisResult {
  taskId: string;
  documentId: string;
  summary: string;
  riskScore: number;
  entities: {
    text: string;
    label: string;
  }[];
  indicators: string[];
  geospatialData: {
    type: string;
    features: GeoJSONFeature[];
  };
  timestamp: string;
}

export enum EntityLabel {
  LOCATION = 'LOC',
  ORGANIZATION = 'ORG',
  DAMAGE_TYPE = 'DMG',
  URGENCY = 'URG'
}
