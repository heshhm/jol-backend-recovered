"""
Utility functions for common operations across the app.
"""


def get_client_ip(request):
    """
    Extract the client's IP address from the request.
    
    Checks X-Forwarded-For header first (for proxies/load balancers),
    then falls back to REMOTE_ADDR.
    
    Returns the leftmost IP in X-Forwarded-For (the original client IP)
    as subsequent IPs are added by proxies.
    
    Args:
        request: Django HttpRequest object
        
    Returns:
        str: IP address (IPv4 or IPv6)
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # X-Forwarded-For can contain multiple IPs: "client, proxy1, proxy2"
        # We want the first one (original client)
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
