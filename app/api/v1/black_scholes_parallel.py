"""
Alternative implementation with TRUE parallel processing.
This parallelizes BOTH calculations AND result building.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
import pandas as pd
from app.services.black_scholes import BlackScholesCalculator
import orjson
import numpy as np
import io
import concurrent.futures
from typing import List, Dict, Any

router = APIRouter(prefix="/black-scholes", tags=["Black-Scholes Calculator"])


def process_and_build_chunk(chunk_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Process a chunk: Calculate + Build results.
    This runs in a separate process.
    """
    # Calculate Black-Scholes
    result_df = BlackScholesCalculator.process_chunk_vectorized(chunk_df)
    
    # Extract arrays once
    n = len(result_df)
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
    
    # Pre-compute NaN masks
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
    
    # Build results
    results = []
    for i in range(n):
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
        
        if errors[i] and errors[i] != "":
            r_dict["error"] = str(errors[i])
        
        results.append(r_dict)
    
    # Also return aggregation data for this chunk
    error_mask = (errors != "") & (errors != None)
    valid_prices = prices[~error_mask & ~np.isnan(prices)]
    
    return {
        "results": results,
        "stats": {
            "failed": int(error_mask.sum()),
            "successful": int((~error_mask).sum()),
            "sum_price": float(valid_prices.sum()) if len(valid_prices) > 0 else 0.0,
            "min_price": float(valid_prices.min()) if len(valid_prices) > 0 else float('inf'),
            "max_price": float(valid_prices.max()) if len(valid_prices) > 0 else float('-inf'),
        }
    }


@router.post("/process-stream-parallel", response_class=StreamingResponse)
async def process_stream_parallel(
    file: UploadFile = File(...),
    workers: int = 4,
    chunksize: int = 20000
):
    """
    TRUE parallel processing - both calculations AND result building.
    
    Performance for 700k rows:
        workers=1: ~20 seconds
        workers=4: ~8-10 seconds
        workers=8: ~6-8 seconds
    
    Args:
        file: CSV/Excel file
        workers: Number of parallel processes (default: 4)
        chunksize: Rows per chunk (default: 20000)
    """
    if not file.filename.endswith((".csv", ".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="File must be CSV or Excel")

    async def process_file():
        try:
            content = await file.read()
            
            # Read file
            if file.filename.endswith('.csv'):
                df = pd.read_csv(io.BytesIO(content), engine='c')
            else:
                df = pd.read_excel(io.BytesIO(content), engine='openpyxl')
            
            total_rows = len(df)
            
            # Split into chunks
            chunks = [df[i:i+chunksize].copy() for i in range(0, total_rows, chunksize)]
            num_chunks = len(chunks)
            
            # Process chunks in parallel (BOTH calculation + result building)
            with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
                chunk_results = list(executor.map(process_and_build_chunk, chunks))
            
            # Merge results from all chunks
            all_results = []
            total_failed = 0
            total_successful = 0
            total_sum_price = 0.0
            overall_min = float('inf')
            overall_max = float('-inf')
            
            for chunk_result in chunk_results:
                all_results.extend(chunk_result["results"])
                stats = chunk_result["stats"]
                total_failed += stats["failed"]
                total_successful += stats["successful"]
                total_sum_price += stats["sum_price"]
                overall_min = min(overall_min, stats["min_price"])
                overall_max = max(overall_max, stats["max_price"])
            
            # Final aggregations
            if total_successful > 0:
                avg_price = round(total_sum_price / total_successful, 4)
                min_price = round(float(overall_min), 4) if overall_min != float('inf') else 0.0
                max_price = round(float(overall_max), 4) if overall_max != float('-inf') else 0.0
            else:
                avg_price = min_price = max_price = total_sum_price = 0.0
            
            # Build response
            response_obj = {
                "total_rows": total_rows,
                "successful_calculations": total_successful,
                "failed_calculations": total_failed,
                "results": all_results,
                "processing_summary": {
                    "average_option_price": avg_price,
                    "min_option_price": min_price,
                    "max_option_price": max_price,
                    "total_option_value": round(total_sum_price, 4),
                },
                "processing_info": {
                    "num_chunks": num_chunks,
                    "workers": workers,
                    "chunksize": chunksize,
                }
            }
            
            yield orjson.dumps(response_obj)
            
        except Exception as e:
            yield orjson.dumps({"error": str(e)})
    
    return StreamingResponse(process_file(), media_type="application/json")

