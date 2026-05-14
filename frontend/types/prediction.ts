/** 1つの数字の予測結果 */
export interface Prediction {
  digit: number;
  probability: number;
}

/** /api/predict レスポンス */
export interface PredictResponse {
  predictions: Prediction[];
}

/** /api/predict エラーレスポンス */
export interface ErrorResponse {
  detail: string;
}

/** /api/health レスポンス */
export interface HealthResponse {
  status: string;
}
