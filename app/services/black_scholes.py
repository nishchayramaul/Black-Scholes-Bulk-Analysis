import numpy as np
from scipy.stats import norm
from typing import Dict, List, Any
import pandas as pd


class BlackScholesCalculator:
    """Black-Scholes model calculator for option pricing"""
    
    @staticmethod
    def calculate_call_price(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """
        Calculate Black-Scholes call option price
        
        Parameters:
        S: Current stock price
        K: Strike price
        T: Time to expiration (in years)
        r: Risk-free interest rate
        sigma: Volatility
        
        Returns:
        Call option price
        """
        if T <= 0:
            return max(S - K, 0)
        
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        call_price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        return call_price
    
    @staticmethod
    def calculate_put_price(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """
        Calculate Black-Scholes put option price
        
        Parameters:
        S: Current stock price
        K: Strike price
        T: Time to expiration (in years)
        r: Risk-free interest rate
        sigma: Volatility
        
        Returns:
        Put option price
        """
        if T <= 0:
            return max(K - S, 0)
        
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        put_price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        return put_price
    
    @staticmethod
    def calculate_greeks(S: float, K: float, T: float, r: float, sigma: float) -> Dict[str, float]:
        """
        Calculate option Greeks
        
        Parameters:
        S: Current stock price
        K: Strike price
        T: Time to expiration (in years)
        r: Risk-free interest rate
        sigma: Volatility
        
        Returns:
        Dictionary containing Delta, Gamma, Theta, Vega, Rho
        """
        if T <= 0:
            return {
                "delta": 1.0 if S > K else 0.0,
                "gamma": 0.0,
                "theta": 0.0,
                "vega": 0.0,
                "rho": 0.0
            }
        
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        # Delta
        delta_call = norm.cdf(d1)
        delta_put = delta_call - 1
        
        # Gamma (same for both call and put)
        gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
        
        # Theta
        theta_call = (-S * norm.pdf(d1) * sigma / (2 * np.sqrt(T)) 
                     - r * K * np.exp(-r * T) * norm.cdf(d2))
        theta_put = (-S * norm.pdf(d1) * sigma / (2 * np.sqrt(T)) 
                    + r * K * np.exp(-r * T) * norm.cdf(-d2))
        
        # Vega (same for both call and put)
        vega = S * norm.pdf(d1) * np.sqrt(T)
        
        # Rho
        rho_call = K * T * np.exp(-r * T) * norm.cdf(d2)
        rho_put = -K * T * np.exp(-r * T) * norm.cdf(-d2)
        
        return {
            "delta_call": delta_call,
            "delta_put": delta_put,
            "gamma": gamma,
            "theta_call": theta_call,
            "theta_put": theta_put,
            "vega": vega,
            "rho_call": rho_call,
            "rho_put": rho_put
        }
    
    @classmethod
    def process_excel_data(cls, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Process Excel data and calculate Black-Scholes values
        
        Expected columns in Excel:
        - S: Stock price
        - K: Strike price
        - T: Time to expiration (in years)
        - r: Risk-free rate
        - sigma: Volatility
        - option_type: 'call' or 'put' (optional, defaults to 'call')
        
        Returns:
        List of dictionaries with calculated values
        """
        results = []
        
        # Validate required columns
        required_columns = ['S', 'K', 'T', 'r', 'sigma']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Add default option_type if not present
        if 'option_type' not in df.columns:
            df['option_type'] = 'call'
        
        for index, row in df.iterrows():
            try:
                S = float(row['S'])
                K = float(row['K'])
                T = float(row['T'])
                r = float(row['r'])
                sigma = float(row['sigma'])
                option_type = str(row.get('option_type', 'call')).lower()
                
                # Calculate option price
                if option_type == 'call':
                    option_price = cls.calculate_call_price(S, K, T, r, sigma)
                elif option_type == 'put':
                    option_price = cls.calculate_put_price(S, K, T, r, sigma)
                else:
                    raise ValueError(f"Invalid option_type: {option_type}. Must be 'call' or 'put'")
                
                # Calculate Greeks
                greeks = cls.calculate_greeks(S, K, T, r, sigma)
                
                result = {
                    "row_index": int(index),
                    "input_data": {
                        "S": S,
                        "K": K,
                        "T": T,
                        "r": r,
                        "sigma": sigma,
                        "option_type": option_type
                    },
                    "calculated_values": {
                        "option_price": round(option_price, 4),
                        "greeks": {
                            "delta": round(greeks[f"delta_{option_type}"], 4),
                            "gamma": round(greeks["gamma"], 4),
                            "theta": round(greeks[f"theta_{option_type}"], 4),
                            "vega": round(greeks["vega"], 4),
                            "rho": round(greeks[f"rho_{option_type}"], 4)
                        }
                    }
                }
                
                results.append(result)
                
            except Exception as e:
                error_result = {
                    "row_index": int(index),
                    "error": str(e),
                    "input_data": row.to_dict()
                }
                results.append(error_result)
        
        return results

    @classmethod
    def process_chunk_vectorized(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Ultra-fast vectorized Black-Scholes for DataFrame chunk.
        
        Optimized for speed: map option_type to int, avoid copies, minimal validation overhead.
        Returns flat DataFrame ready for streaming.
        """
        required_columns = ['S', 'K', 'T', 'r', 'sigma']
        missing_columns = [c for c in required_columns if c not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        # Preserve originals (views, not copies)
        orig_S = df['S'].values
        orig_K = df['K'].values
        orig_T = df['T'].values
        orig_r = df['r'].values
        orig_sigma = df['sigma'].values
        orig_opt = df['option_type'].values if 'option_type' in df.columns else np.array([None] * len(df))

        # Convert to numeric arrays directly
        S = pd.to_numeric(df['S'], errors='coerce').to_numpy(dtype=np.float64)
        K = pd.to_numeric(df['K'], errors='coerce').to_numpy(dtype=np.float64)
        T = pd.to_numeric(df['T'], errors='coerce').to_numpy(dtype=np.float64)
        r = pd.to_numeric(df['r'], errors='coerce').to_numpy(dtype=np.float64)
        sigma = pd.to_numeric(df['sigma'], errors='coerce').to_numpy(dtype=np.float64)

        # Fast error detection with bitmask
        err_mask = (
            np.isnan(S) | np.isnan(K) | np.isnan(T) | np.isnan(r) | np.isnan(sigma) |
            (S <= 0) | (K <= 0) | (T < 0) | (sigma <= 0)
        )

        # option_type: map to 0=call, 1=put for fast indexing
        opt_series = pd.Series(orig_opt).astype('string').str.lower()
        opt_invalid = opt_series.isna() | (opt_series.str.len() == 0) | ~opt_series.isin(['call', 'put'])
        err_mask = err_mask | opt_invalid.to_numpy().astype(bool)
        
        is_put = (opt_series == 'put').to_numpy()

        # Preallocate output arrays
        n = len(df)
        option_price = np.full(n, np.nan, dtype=np.float64)
        delta = np.full(n, np.nan, dtype=np.float64)
        gamma = np.full(n, np.nan, dtype=np.float64)
        theta = np.full(n, np.nan, dtype=np.float64)
        vega = np.full(n, np.nan, dtype=np.float64)
        rho = np.full(n, np.nan, dtype=np.float64)
        errors = np.array([""] * n, dtype=object)

        # Build error strings only for invalid rows (minimal overhead)
        if err_mask.any():
            for i in np.where(err_mask)[0]:
                msgs = []
                if np.isnan(S[i]): msgs.append("S is missing/invalid")
                elif S[i] <= 0: msgs.append("S must be > 0")
                if np.isnan(K[i]): msgs.append("K is missing/invalid")
                elif K[i] <= 0: msgs.append("K must be > 0")
                if np.isnan(T[i]): msgs.append("T is missing/invalid")
                elif T[i] < 0: msgs.append("T must be >= 0")
                if np.isnan(r[i]): msgs.append("r is missing/invalid")
                if np.isnan(sigma[i]): msgs.append("sigma is missing/invalid")
                elif sigma[i] <= 0: msgs.append("sigma must be > 0")
                if opt_invalid.iloc[i]: msgs.append("option_type must be 'call' or 'put'")
                errors[i] = "; ".join(msgs)

        valid = ~err_mask
        if valid.any():
            Sv = S[valid]
            Kv = K[valid]
            Tv = T[valid]
            rv = r[valid]
            sigv = sigma[valid]
            is_put_v = is_put[valid]

            sqrtT = np.sqrt(np.maximum(Tv, 0))
            with np.errstate(divide='ignore', invalid='ignore'):
                d1 = (np.log(Sv / Kv) + (rv + 0.5 * sigv ** 2) * Tv) / (sigv * sqrtT)
                d2 = d1 - sigv * sqrtT

            Nd1 = norm.cdf(d1)
            Nd2 = norm.cdf(d2)
            nd1 = norm.pdf(d1)

            call_price_v = Sv * Nd1 - Kv * np.exp(-rv * Tv) * Nd2
            put_price_v = Kv * np.exp(-rv * Tv) * norm.cdf(-d2) - Sv * norm.cdf(-d1)

            gamma_v = nd1 / (Sv * sigv * sqrtT)
            theta_call_v = (-Sv * nd1 * sigv / (2 * sqrtT)) - rv * Kv * np.exp(-rv * Tv) * Nd2
            theta_put_v = (-Sv * nd1 * sigv / (2 * sqrtT)) + rv * Kv * np.exp(-rv * Tv) * norm.cdf(-d2)
            vega_v = Sv * nd1 * sqrtT
            rho_call_v = Kv * Tv * np.exp(-rv * Tv) * Nd2
            rho_put_v = -Kv * Tv * np.exp(-rv * Tv) * norm.cdf(-d2)

            option_price[valid] = np.where(is_put_v, put_price_v, call_price_v)
            delta[valid] = np.where(is_put_v, Nd1 - 1, Nd1)
            theta[valid] = np.where(is_put_v, theta_put_v, theta_call_v)
            rho[valid] = np.where(is_put_v, rho_put_v, rho_call_v)
            gamma[valid] = gamma_v
            vega[valid] = vega_v

        return pd.DataFrame({
            'row_index': df.index,
            'S': orig_S,
            'K': orig_K,
            'T': orig_T,
            'r': orig_r,
            'sigma': orig_sigma,
            'option_type': orig_opt,
            'option_price': option_price,
            'delta': delta,
            'gamma': gamma,
            'theta': theta,
            'vega': vega,
            'rho': rho,
            'error': errors,
        })