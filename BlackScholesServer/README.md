# Black-Scholes Calculator API

A production-grade FastAPI application for calculating Black-Scholes option prices and Greeks using NumPy.

## Features

- **Single Calculation**: Calculate option prices and Greeks for individual parameters
- **Excel Processing**: Upload Excel files with multiple option parameters for batch processing
- **Comprehensive Greeks**: Calculate Delta, Gamma, Theta, Vega, and Rho
- **Input Validation**: Robust validation for all input parameters
- **Error Handling**: Detailed error messages and handling for edge cases

## Installation

1. **Clone the repository** (if applicable) or navigate to your project directory

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables** (optional):
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## Running the Application

### Development Mode
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### 1. Single Calculation
**POST** `/api/v1/black-scholes/calculate`

Calculate Black-Scholes option price for a single set of parameters.

**Request Body**:
```json
{
  "S": 100.0,
  "K": 100.0,
  "T": 0.25,
  "r": 0.05,
  "sigma": 0.2,
  "option_type": "call"
}
```

**Response**:
```json
{
  "option_price": 4.1234,
  "greeks": {
    "delta": 0.5234,
    "gamma": 0.0123,
    "theta": -0.0456,
    "vega": 0.1234,
    "rho": 0.0123
  },
  "input_parameters": { ... }
}
```

### 2. Excel Processing
**POST** `/api/v1/black-scholes/process-excel`

Upload an Excel file with multiple option parameters for batch processing.

**Expected Excel Columns**:
- `S`: Current stock price (required)
- `K`: Strike price (required)
- `T`: Time to expiration in years (required)
- `r`: Risk-free interest rate (required)
- `sigma`: Volatility (required)
- `option_type`: Option type - "call" or "put" (optional, defaults to "call")

### 3. Example Excel Format
**GET** `/api/v1/black-scholes/example-excel`

Get example Excel format and column descriptions.

## Excel File Format

Your Excel file should have the following structure:

| S    | K    | T    | r    | sigma | option_type |
|------|------|------|------|-------|-------------|
| 100  | 100  | 0.25 | 0.05 | 0.2   | call        |
| 105  | 105  | 0.5  | 0.05 | 0.25  | put         |
| 95   | 95   | 0.75 | 0.05 | 0.3   | call        |

## Black-Scholes Model

The application implements the standard Black-Scholes model for European options:

### Call Option Price:
```
C = S * N(d1) - K * e^(-r*T) * N(d2)
```

### Put Option Price:
```
P = K * e^(-r*T) * N(-d2) - S * N(-d1)
```

Where:
- `d1 = [ln(S/K) + (r + σ²/2)*T] / (σ*√T)`
- `d2 = d1 - σ*√T`
- `N(x)` is the cumulative standard normal distribution

### Greeks Calculated:
- **Delta**: Price sensitivity to underlying asset price
- **Gamma**: Delta sensitivity to underlying asset price
- **Theta**: Time decay
- **Vega**: Volatility sensitivity
- **Rho**: Interest rate sensitivity

## Error Handling

The API provides comprehensive error handling:
- Input validation for all parameters
- File format validation for Excel uploads
- Mathematical error handling (e.g., division by zero)
- Detailed error messages for debugging

## Testing

Run tests with:
```bash
pytest
```

## Development

### Code Formatting
```bash
black app/
isort app/
flake8 app/
```

### Type Checking
```bash
mypy app/
```

## Production Deployment

For production deployment, consider:
1. Using a production ASGI server like Gunicorn with Uvicorn workers
2. Setting up proper logging
3. Using environment variables for configuration
4. Implementing rate limiting
5. Adding authentication if needed
6. Using a reverse proxy like Nginx

## Dependencies

- **FastAPI**: Modern, fast web framework
- **NumPy**: Numerical computing
- **Pandas**: Data manipulation and analysis
- **SciPy**: Scientific computing (for normal distribution)
- **OpenPyXL**: Excel file processing
- **Pydantic**: Data validation
- **Uvicorn**: ASGI server
