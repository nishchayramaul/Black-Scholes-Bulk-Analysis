from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
import pandas as pd
from app.services.black_scholes import BlackScholesCalculator
import orjson
import numpy as np
import io

router = APIRouter(prefix="/black-scholes", tags=["Black-Scholes Calculator"])


def build_results_fast(result_df):
    """Optimized result builder using numpy array operations and minimal conversions"""
    n = len(result_df)
    
    # Extract all arrays once (avoid repeated .values calls)
    row_idx = result_df['row_index'].values
    S = result_df['S'].values
    K = result_df['K'].values
    T = result_df['T'].values
    r = result_df['r'].values
    sigma = result_df['sigma'].values
    opt_type = result_df['option_type'].values
    prices = result_df['option_price'].values
    deltas = result_df['delta'].values
    gammas = result_df['gamma'].values
    thetas = result_df['theta'].values
    vegas = result_df['vega'].values
    rhos = result_df['rho'].values
    errors = result_df['error'].values
    
    # Pre-check NaN status for all arrays (vectorized)
    S_nan = np.isnan(S)
    K_nan = np.isnan(K)
    T_nan = np.isnan(T)
    r_nan = np.isnan(r)
    sigma_nan = np.isnan(sigma)
    price_nan = np.isnan(prices)
    delta_nan = np.isnan(deltas)
    gamma_nan = np.isnan(gammas)
    theta_nan = np.isnan(thetas)
    vega_nan = np.isnan(vegas)
    rho_nan = np.isnan(rhos)
    
    # Build results using fastest possible method
    results = []
    for i in range(n):
        # Build dict inline with minimal function calls
        r_dict = {
            "row_index": int(row_idx[i]),
            "input_data": {
                "S": None if S_nan[i] else float(S[i]),
                "K": None if K_nan[i] else float(K[i]),
                "T": None if T_nan[i] else float(T[i]),
                "r": None if r_nan[i] else float(r[i]),
                "sigma": None if sigma_nan[i] else float(sigma[i]),
                "option_type": None if opt_type[i] is None or opt_type[i] == '' else str(opt_type[i]),
            },
            "calculated_values": {
                "option_price": None if price_nan[i] else round(float(prices[i]), 4),
                "greeks": {
                    "delta": None if delta_nan[i] else round(float(deltas[i]), 4),
                    "gamma": None if gamma_nan[i] else round(float(gammas[i]), 4),
                    "theta": None if theta_nan[i] else round(float(thetas[i]), 4),
                    "vega": None if vega_nan[i] else round(float(vegas[i]), 4),
                    "rho": None if rho_nan[i] else round(float(rhos[i]), 4),
                },
            }
        }
        
        # Only add error if present
        if errors[i] and errors[i] != "":
            r_dict["error"] = str(errors[i])
        
        results.append(r_dict)
    
    return results


@router.post("/process-stream", response_class=StreamingResponse)
async def process_stream(file: UploadFile = File(...)):
    """
    Final optimized version - minimal overhead, pre-computed NaN checks
    """
    if not file.filename.endswith((".csv", ".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="File must be CSV or Excel")

    async def process_file():
        try:
            content = await file.read()
            
            # Fast file reading
            if file.filename.endswith('.csv'):
                df = pd.read_csv(io.BytesIO(content), engine='c')
            else:
                df = pd.read_excel(io.BytesIO(content), engine='openpyxl')
            
            total_rows = len(df)
            
            # Vectorized Black-Scholes calculation
            result_df = BlackScholesCalculator.process_chunk_vectorized(df)
            
            # Aggregations (vectorized numpy)
            errors = result_df['error'].values
            prices = result_df['option_price'].values
            error_mask = (errors != "") & (errors != None)
            
            failed = int(error_mask.sum())
            successful = int((~error_mask).sum())
            
            valid_prices = prices[~error_mask & ~np.isnan(prices)]
            if len(valid_prices) > 0:
                sum_price = float(valid_prices.sum())
                min_price = round(float(valid_prices.min()), 4)
                max_price = round(float(valid_prices.max()), 4)
                avg_price = round(sum_price / successful, 4)
            else:
                sum_price = avg_price = min_price = max_price = 0.0
            
            # Fast result building with pre-computed NaN checks
            all_results = build_results_fast(result_df)
            
            # Build response
            response_obj = {
                "total_rows": total_rows,
                "successful_calculations": successful,
                "failed_calculations": failed,
                "results": all_results,
                "processing_summary": {
                    "average_option_price": avg_price,
                    "min_option_price": min_price,
                    "max_option_price": max_price,
                    "total_option_value": round(sum_price, 4),
                },
            }
            
            # orjson is fastest JSON serializer
            yield orjson.dumps(response_obj)
            
        except Exception as e:
            yield orjson.dumps({"error": str(e)})
    return StreamingResponse(process_file(), media_type="application/json")
