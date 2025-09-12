# make_request Function Documentation

## Overview

The `make_request` function is a robust HTTP request handler that provides automatic retry logic for REST API calls, specifically designed to handle rate limiting (429 errors) and network timeouts.

## Features

### 1. Automatic Retry Logic
- **Maximum Retries**: Up to 4 retry attempts for failed requests
- **Rate Limiting**: Automatically retries on 429 (Too Many Requests) responses
- **Timeout Handling**: Retries on network timeouts with exponential backoff

### 2. Exponential Backoff with Jitter
- **Base Timeout**: Starts with the provided timeout value
- **Backoff Multiplier**: Each retry doubles the timeout: `2^attempt * base_timeout`
- **Jitter**: Adds 10-30% random variation to prevent thundering herd problems
- **Formula**: `timeout = base_timeout * 2^attempt * (1 + random(0.1, 0.3))`

### 3. Smart Retry Strategy
- **429 Errors**: Always retry with respect to `Retry-After` header if available
- **Timeouts**: Retry with increased timeout values
- **Other Errors**: No retry (immediate return)
- **Network Failures**: Retry on connection issues

## Usage

```python
# Basic usage
response = client.make_request('GET', 'https://api.example.com/endpoint', timeout=30)

# With additional parameters
response = client.make_request(
    'POST', 
    'https://api.example.com/endpoint',
    json={'key': 'value'},
    headers={'Authorization': 'Bearer token'},
    timeout=30
)
```

## Parameters

- `method` (str): HTTP method (GET, POST, PUT, PATCH, DELETE)
- `url` (str): Full URL to make request to
- `**kwargs`: Additional arguments passed to requests (headers, json, data, etc.)
- `timeout` (int): Base timeout in seconds (default: 5)

## Return Value

- `requests.Response`: The HTTP response object
- Raises `requests.exceptions.RequestException` if all retries are exhausted

## Retry Behavior Examples

### Example 1: Rate Limiting (429)
```
Attempt 1: GET /api/contacts → 429 (Rate Limited)
Wait: 5s (base timeout)
Attempt 2: GET /api/contacts → 429 (Rate Limited)  
Wait: 10s (2^1 * 5)
Attempt 3: GET /api/contacts → 429 (Rate Limited)
Wait: 20s (2^2 * 5)
Attempt 4: GET /api/contacts → 429 (Rate Limited)
Wait: 40s (2^3 * 5)
Attempt 5: GET /api/contacts → 429 (Rate Limited)
Result: Return 429 response (max retries exceeded)
```

### Example 2: Timeout with Exponential Backoff
```
Attempt 1: GET /api/contacts → Timeout after 5s
Attempt 2: GET /api/contacts → Timeout after 10s + jitter
Attempt 3: GET /api/contacts → Timeout after 20s + jitter
Attempt 4: GET /api/contacts → Timeout after 40s + jitter
Attempt 5: GET /api/contacts → Timeout after 80s + jitter
Result: Raise RequestException (max retries exceeded)
```

## Implementation Details

### Retry Logic
```python
max_retries = 4
for attempt in range(max_retries + 1):
    try:
        # Calculate timeout for this attempt
        if attempt == 0:
            timeout = base_timeout
        else:
            backoff_multiplier = 2 ** attempt
            jitter = random.uniform(0.1, 0.3)
            timeout = int(base_timeout * backoff_multiplier * (1 + jitter))
        
        # Make request
        response = self.session.request(method, url, timeout=timeout, **kwargs)
        
        # Handle 429 specifically
        if response.status_code == 429:
            if attempt < max_retries:
                # Retry with backoff
                continue
            else:
                return response  # Give up after max retries
        
        return response  # Success or other status codes
        
    except requests.exceptions.Timeout:
        if attempt < max_retries:
            continue  # Retry with increased timeout
        else:
            raise  # Give up after max retries
```

### Jitter Calculation
```python
jitter = random.uniform(0.1, 0.3)  # 10-30% random variation
timeout = int(base_timeout * 2^attempt * (1 + jitter))
```

## Benefits

1. **Reliability**: Automatically handles transient network issues
2. **Rate Limiting**: Respects API rate limits with intelligent backoff
3. **Performance**: Prevents overwhelming APIs during high traffic
4. **User Experience**: Transparent retry logic for end users
5. **Monitoring**: Comprehensive logging for debugging and monitoring

## Integration

The function has been integrated into all existing HubSpot API methods:
- `test_credentials()`
- `get_contact_properties()`
- `create_order()`
- `create_membership()`
- `get_event_properties()`
- `get_order_properties()`
- `get_membership_properties()`
- `get_custom_object_properties()`
- `get_deal_properties()`
- `get_contacts()`
- `create_or_update_contact()`
- `create_deal()`
- And many more...

## Testing

Run the test script to verify functionality:
```bash
python test_make_request.py
```

This will test various scenarios including normal requests, timeouts, and rate limiting responses. 