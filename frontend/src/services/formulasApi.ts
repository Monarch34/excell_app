import type {
  FormulaPreviewErrorCode,
  FormulaPreviewRequest,
  FormulaPreviewResponse,
  FormulaValidateRequest,
  FormulaValidateResponse,
} from '@/shared/types/api';
import { postData } from '@/services/httpClient';

type FormulaPreviewResponseWire = Omit<FormulaPreviewResponse, 'errorCode'> & {
  errorCode?: FormulaPreviewErrorCode;
  error_code?: FormulaPreviewErrorCode;
};

export async function previewFormula(payload: FormulaPreviewRequest): Promise<FormulaPreviewResponse> {
  const response = await postData<FormulaPreviewResponseWire, FormulaPreviewRequest>(
    '/formulas/preview',
    payload,
  );

  return {
    ...response,
    errorCode: response.errorCode ?? response.error_code,
  };
}

export async function validateFormula(payload: FormulaValidateRequest): Promise<FormulaValidateResponse> {
  return postData<FormulaValidateResponse, FormulaValidateRequest>(
    '/formulas/validate',
    payload
  );
}
