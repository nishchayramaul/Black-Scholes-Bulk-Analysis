from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class BlackScholesInput(BaseModel):
    """Input parameters for Black-Scholes calculation"""
    S: float = Field(..., description="Current stock price", gt=0)
    K: float = Field(..., description="Strike price", gt=0)
    T: float = Field(..., description="Time to expiration in years", ge=0)
    r: float = Field(..., description="Risk-free interest rate", ge=0)
    sigma: float = Field(..., description="Volatility", gt=0)
    option_type: str = Field(default="call", description="Option type: 'call' or 'put'")


class Greeks(BaseModel):
    """Option Greeks"""
    delta: float = Field(..., description="Delta - price sensitivity to underlying asset")
    gamma: float = Field(..., description="Gamma - delta sensitivity to underlying asset")
    theta: float = Field(..., description="Theta - time decay")
    vega: float = Field(..., description="Vega - volatility sensitivity")
    rho: float = Field(..., description="Rho - interest rate sensitivity")


class BlackScholesResult(BaseModel):
    """Single Black-Scholes calculation result"""
    row_index: int = Field(..., description="Row index from Excel file")
    input_data: BlackScholesInput = Field(..., description="Input parameters used")
    calculated_values: Dict[str, Any] = Field(..., description="Calculated option price and Greeks")
    error: Optional[str] = Field(None, description="Error message if calculation failed")


class ExcelProcessingResult(BaseModel):
    """Result of Excel file processing"""
    total_rows: int = Field(..., description="Total number of rows processed")
    successful_calculations: int = Field(..., description="Number of successful calculations")
    failed_calculations: int = Field(..., description="Number of failed calculations")
    results: List[BlackScholesResult] = Field(..., description="List of calculation results")
    processing_summary: Dict[str, Any] = Field(..., description="Summary statistics")


class SingleCalculationRequest(BaseModel):
    """Request for single Black-Scholes calculation"""
    S: float = Field(..., description="Current stock price", gt=0)
    K: float = Field(..., description="Strike price", gt=0)
    T: float = Field(..., description="Time to expiration in years", ge=0)
    r: float = Field(..., description="Risk-free interest rate", ge=0)
    sigma: float = Field(..., description="Volatility", gt=0)
    option_type: str = Field(default="call", description="Option type: 'call' or 'put'")


class SingleCalculationResponse(BaseModel):
    """Response for single Black-Scholes calculation"""
    option_price: float = Field(..., description="Calculated option price")
    greeks: Greeks = Field(..., description="Option Greeks")
    input_parameters: BlackScholesInput = Field(..., description="Input parameters used")
